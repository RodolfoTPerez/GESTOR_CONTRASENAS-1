import os
import sqlite3
import re
import time
import logging
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional, Any, Dict, List, Tuple

# Infrastructure imports
from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.secret_repo import SecretRepository
from src.infrastructure.repositories.user_repo import UserRepository
from src.infrastructure.repositories.audit_repo import AuditRepository

# Domain imports
from src.domain.services.session_service import SessionService
from src.domain.services.security_service import SecurityService

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    SecretsManager (Refactored Facade v3.0)
    =========================================
    Orchestrates the security system by delegating to specialized modules.
    Maintains full backward compatibility with the existing UI.
    """
    def __init__(self, master_password: Optional[str] = None) -> None:
        # Initialize Core Modules
        self.db = DBManager("vultrax")
        self.users = UserRepository(self.db)
        self.secrets = SecretRepository(self.db)
        self.audit = AuditRepository(self.db)
        self.session = SessionService()
        self.security = SecurityService()
        
        # Legacy attribute access for compatibility
        self._sync_legacy_attributes()

    def _sync_legacy_attributes(self) -> None:
        """Maintains attributes that UI classes might access directly."""
        self.conn = self.db.conn
        self.db_path = self.db.db_path
        # Map properties for direct access
        self.current_user = self.session.current_user
        self.current_user_id = self.session.current_user_id
        self.user_role = self.session.user_role
        self.master_key = self.session.master_key
        self.personal_key = self.session.personal_key
        self.vault_key = self.session.vault_key
        self.current_vault_id = self.session.current_vault_id
        self.session_id = self.session.session_id
        self.kek_candidates = self.session.kek_candidates

    # --- DATABASE & META ---
    def get_meta(self, key: str) -> Optional[str]: return self.users.get_meta(key)
    def set_meta(self, key: str, value: Any) -> None: self.users.set_meta(key, value)
    
    def _initialize_db(self, name: str) -> None:
        self.db._initialize_db(name)
        self._sync_legacy_attributes()

    def reconnect(self, username: str) -> None:
        logger.info(f"[DEBUG] Attempting to reconnect for {username}...")
        self._initialize_db(username)
        logger.info(f"[DEBUG] Reconnected for {username}.")

    # --- USER & SESSION ---
    def get_local_user_profile(self, username: str) -> Optional[Dict[str, Any]]: 
        return self.users.get_profile(username)

    def save_local_user_profile(self, *args: Any, **kwargs: Any) -> None:
        self.users.save_profile(*args, **kwargs)

    def set_active_user(self, username: str, password: str) -> None:
        new_user = str(username).upper().strip().replace(" ", "")
        
        if self.session.current_user == new_user and self.session.master_key is not None:
            return

        logger.info(f"[DEBUG] set_active_user started for {new_user}")
        self.reconnect(new_user)
        profile = self.get_local_user_profile(new_user)
        logger.info(f"[DEBUG] Profile found: {profile is not None}")
        if not profile: 
            logger.warning(f"[DEBUG] No profile found for {new_user}, returning early.")
            return

        # Load IDs and roles
        self.session.set_user(new_user, profile.get("user_id"), profile.get("role") or "user", profile.get("vault_id"))
        
        # Crypto setup
        v_salt = self.security.ensure_bytes(profile.get("vault_salt"))
        if not v_salt or len(v_salt) < 16:
            logger.info("[DEBUG] No vault salt found, creating one...")
            v_salt = self._get_or_create_salt()
            self.save_local_user_profile(new_user, profile["password_hash"], profile["salt"], v_salt,
                                        role=self.session.user_role, vault_id=self.session.current_vault_id)

        # Derive KEK
        logger.info("[DEBUG] Deriving KEK...")
        self.session.kek_candidates["p100"] = self.security.derive_keke(password, v_salt)
        kek = self.session.kek_candidates["p100"]

        # Unwrap Keys
        logger.info("[DEBUG] Unwrapping keys...")
        self.session.personal_key = self.security.decrypt_protected_key(profile.get("protected_key"), kek)
        
        w_v_raw = profile.get("wrapped_vault_key")
        if w_v_raw:
            try:
                logger.info("[DEBUG] Unwrapping vault key...")
                dec_v_key = self.security.unwrap_key(w_v_raw, password, v_salt)
                self.session.vault_key = bytearray(dec_v_key)
            except Exception as e:
                logger.error(f"Failed to unwrap vault key for {new_user}: {e}")

        self.session.master_key = self.session.personal_key or self.session.vault_key
        self._sync_legacy_attributes()
        logger.info(f"Session Started: {self.session.current_user} | ID: {self.session.session_id}")

    def refresh_vault_context(self) -> bool:
        if not self.session.current_user: return False
        profile = self.get_local_user_profile(self.session.current_user)
        if not profile: return False

        self.session.current_vault_id = profile.get("vault_id")
        w_v_raw = profile.get("wrapped_vault_key")
        kek = self.session.kek_candidates.get("p100")
        
        if w_v_raw and kek:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                dec_v_key = AESGCM(kek).decrypt(self.security.ensure_bytes(w_v_raw)[:12], self.security.ensure_bytes(w_v_raw)[12:], None)
                self.session.vault_key = bytearray(dec_v_key)
                if not self.session.master_key: self.session.master_key = self.session.vault_key
                self._sync_legacy_attributes()
                return True
            except Exception as e:
                logger.debug(f"Vault context refresh failed: {e}")
        return False

    def _get_or_create_salt(self) -> bytes:
        val = self.get_meta('master_salt')
        if val: return self.security.ensure_bytes(val)
        
        # Generar y guardar salt inmediatamente para evitar huérfanos
        try:
            salt = os.urandom(16)
            self.set_meta('master_salt', sqlite3.Binary(salt))
            # Forzar persistencia inmediata
            if self.db.conn:
                self.db.conn.commit()
            return salt
        except Exception as e:
            logger.critical(f"Failed to generate/save system salt: {e}")
            raise

    # --- SECRETS OPERATIONS ---
    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        records = self.secrets.get_all(self.session.current_user, include_deleted)
        keys = []
        if self.session.vault_key: keys.append(self.session.vault_key)
        if self.session.personal_key: keys.append(self.session.personal_key)
        if self.session.master_key: keys.append(self.session.master_key)
        keys.extend(self.session.kek_candidates.values())
        
        for r in records:
            enc_data = self.security.ensure_bytes(r.get("secret"))
            nonce = self.security.ensure_bytes(r.get("nonce"))
            if not nonce or not enc_data or len(nonce) != 12:
                r["secret"] = "[Dato Corrupto]"
                continue
            r["secret"] = self.security.decrypt_data(enc_data, nonce, keys)
        return records

    def get_record(self, service: str, username: str) -> Optional[Dict[str, Any]]:
        """Busca un registro específico por servicio y usuario."""
        records = self.get_all(include_deleted=True)
        for r in records:
            if r["service"].strip().lower() == service.strip().lower() and \
               r["username"].strip().lower() == username.strip().lower():
                return r
        return None

    def add_secret(self, service: str, username: str, secret_plain: str, notes: Optional[str] = None, is_private: int = 0) -> Optional[int]:
        key = self.session.personal_key if int(is_private) == 1 else self.session.vault_key
        if not key: key = self.session.master_key
        
        if not key or len(key) != 32:
            raise ValueError("Falla de seguridad: No hay llave disponible para cifrar.")
            
        enc, nonce, integrity = self.security.encrypt_data(secret_plain, key)
        sid = self.secrets.add_secret(service, username, enc, nonce, integrity, notes, is_private, 
                                     self.session.current_user, self.session.current_user_id, self.session.current_vault_id)
        
        self.log_event("CREATE SECRET", service=service, details=f"New secret created")
        return sid

    def bulk_add_secrets(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Versión Senior Pro: Procesa y cifra múltiples registros con validación robusa,
        detección de duplicados ultra-rápida y transacciones atómicas.
        """
        import time
        import sqlite3
        stats = {"added": 0, "skipped": 0, "errors": 0}
        
        # 1. Mapeo inteligente de cabeceras (Case Insensitive & Multi-idioma)
        def _find(row, variants):
            for k in row.keys():
                if str(k).strip().lower() in variants:
                    return str(row[k])
            return None

        # 2. Cargar llaves existentes (Optimizado: solo service y user en minúsculas)
        existing_map = self.secrets.get_existing_keys(self.session.current_user)
            
        to_insert = []
        batch_time = int(time.time())
        current_user = self.session.current_user
        current_uid = self.session.current_user_id
        current_vid = self.session.current_vault_id
        
        # 3. Preparar candidatos (Cifrado eficiente)
        for r in records:
            try:
                # Normalización de cabeceras
                svc = (_find(r, ["service", "servicio", "app", "sitio"]) or "").strip()
                usr = (_find(r, ["username", "user", "usuario", "login", "email"]) or current_user).strip()
                sec = _find(r, ["secret", "password", "contraseña", "clave", "pwd"])
                notes = (_find(r, ["notes", "notas", "comentario", "desc"]) or "").strip()
                priv_val = _find(r, ["is_private", "privado", "personal"])
                priv = 1 if priv_val and str(priv_val).strip() in ["1", "True", "true", "S", "Si"] else 0
                
                if not svc or not sec:
                    stats["errors"] += 1
                    continue
                    
                # Detección de duplicados (Service + Username)
                dupe_key = (svc.lower(), usr.lower())
                if dupe_key in existing_map:
                    stats["skipped"] += 1
                    continue
                
                # Selección de llave según privacidad
                key = self.session.personal_key if priv == 1 else self.session.vault_key
                if not key: key = self.session.master_key
                if not key or len(key) != 32: raise ValueError("No key")
                
                enc, nonce, integrity = self.security.encrypt_data(sec, key)
                
                to_insert.append((
                    svc, usr, sqlite3.Binary(enc), sqlite3.Binary(nonce), batch_time,
                    current_user, current_uid, integrity, notes, priv, current_vid
                ))
                
                existing_map.add(dupe_key) # Evitar duplicados dentro del lote
                stats["added"] += 1
                
            except Exception as e:
                logger.error(f"Error preparing record for bulk import: {e}")
                stats["errors"] += 1
                
        # 4. Transacción única en BD
        if to_insert:
            if not self.secrets.batch_add_secrets(to_insert):
                stats["errors"] += stats["added"]
                stats["added"] = 0
                
        self.log_event("IMPORT_BULK", details=f"Bulk import: {stats['added']} added, {stats['skipped']} skipped")
        return stats

    def update_secret(self, sid: int, service: str, username: str, secret_plain: str, notes: Optional[str] = None, is_private: int = 0) -> None:
        key = self.session.personal_key if int(is_private) == 1 else self.session.vault_key
        if not key: key = self.session.master_key

        if not key or len(key) != 32:
            raise ValueError("Falla de seguridad: No hay llave disponible para re-cifrar.")

        enc, nonce, integrity = self.security.encrypt_data(secret_plain, key)
        self.secrets.update_secret(sid, service, username, enc, nonce, integrity, notes, is_private)
        self.log_event("UPDATE SECRET", service=service, details=f"Secret updated")

    def delete_secret(self, sid: int) -> None:
        svc_name = self.secrets.get_service_name_by_id(sid)
        self.secrets.delete_secret(sid)
        self.log_event("DELETE SECRET", service=svc_name, details=f"Secret {sid} deleted")

    def hard_delete_secret(self, sid: int) -> None:
        svc = self.secrets.get_service_name_by_id(sid)
        self.secrets.hard_delete(sid)
        self.log_event("DELETE SECRET", service=svc, details=f"Permanently deleted {sid}")

    def restore_secret(self, sid: int) -> None: self.secrets.restore_secret(sid)
    
    def physical_purge_private(self) -> bool:
        """Eliminación física permanente de todos los registros privados del usuario."""
        try:
            self.db.execute("DELETE FROM secrets WHERE is_private = 1 AND UPPER(owner_name) = ?", (self.session.current_user.upper(),))
            self.db.commit()
            self.db.vacuum()
            self.log_event("PURGE_PRIVATE", details="User purged all private secrets physically")
            return True
        except Exception as e:
            logger.error(f"Error purging private secrets: {e}")
            return False

    def check_service_exists(self, service_name: str) -> bool: return self.secrets.check_exists(service_name)
    
    def purge_locked_secrets(self) -> Tuple[int, str]:
        records = self.get_all()
        locked_ids = [r["id"] for r in records if r.get("secret") == "[Bloqueado 🔑]"]
        for sid in locked_ids: self.delete_secret(sid)
        return len(locked_ids), f"Se purgaron {len(locked_ids)} registros."

    # --- SYNC & DIRECT OPS ---
    def get_all_encrypted(self, only_mine: bool = False) -> List[Dict[str, Any]]:
        raw = self.secrets.get_all_encrypted(self.session.current_user, only_mine)
        for r in raw:
            r["secret_blob"] = self.security.ensure_bytes(r["secret"])
            r["nonce_blob"] = self.security.ensure_bytes(r["nonce"])
        return raw

    def add_secret_encrypted(self, service: str, username: str, secret_blob: bytes, nonce_blob: bytes, 
                             integrity: str, notes: Optional[str] = None, deleted: int = 0, 
                             synced: int = 1, sid: Optional[int] = None, is_private: int = 0, 
                             owner_name: Optional[str] = None, vault_id: Optional[str] = None, 
                             cloud_id: Optional[str] = None) -> None:
        data = {
            "service": service, "username": username, "secret": secret_blob, "nonce": nonce_blob,
            "integrity_hash": integrity, "notes": notes, "deleted": deleted, "synced": synced,
            "is_private": int(is_private or 0), "owner_name": str(owner_name or self.session.current_user).upper(),
            "vault_id": vault_id or self.session.current_vault_id, "cloud_id": cloud_id, 
            "updated_at": int(time.time())
        }
        if sid: data["id"] = sid
        self.secrets.add_encrypted_direct(data)

    def mark_as_synced(self, sid: int, status: int = 1) -> None: 
        self.db.execute("UPDATE secrets SET synced = ? WHERE id = ?", (int(status), sid))
        self.db.commit()

    # --- AUDIT ---
    def log_event(self, action: str, service: str = "-", status: str = "SUCCESS", details: str = "-", **kwargs: Any) -> None:
        self.audit.log_event(self.session.current_user, self.session.current_user_id, action, service, status, details, **kwargs)

    def get_audit_logs(self, limit: int = 500) -> List[Dict[str, Any]]:
        return self.audit.get_logs(self.session.current_user, self.session.user_role, limit)

    def get_audit_log_count(self) -> int: return self.audit.get_count()

    def get_pending_audit_logs(self) -> List[tuple]:
        return self.audit.get_pending_logs()

    def mark_audit_logs_as_synced(self) -> None:
        self.audit.mark_as_synced()

    # --- UTILS & LEGACY ---
    def cleanup_vault_cache(self) -> None:
        self.session.clear()
        self.db.vacuum()
        self._sync_legacy_attributes()

    def _ensure_bytes(self, data: Any) -> Optional[bytes]:
        """Legacy internal helper for byte conversion, delegated to SecurityService."""
        return self.security.ensure_bytes(data)

    # --- BACKUP & RESTORE (LOCAL) ---
    def create_local_backup(self) -> str:
        """Create a timestamped backup of the current database."""
        if not self.db.conn or not self.db.db_path:
            raise RuntimeError("Database not initialized")
        
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.db.db_path.parent / "backups" / self.session.current_user.lower()
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_filename = f"backup_{timestamp}.enc"
        backup_path = backup_dir / backup_filename
        
        # Flush pending changes
        self.db.commit()
        
        # Create backup (copy file)
        shutil.copy2(self.db.db_path, backup_path)
        return str(backup_path)

    def local_restore(self, backup_path: str) -> None:
        """Restore database from a local backup file."""
        import shutil
        from pathlib import Path
        
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
        # Close current connection
        self.db.close()
        
        try:
            # Restore file
            shutil.copy2(backup_path, self.db.db_path)
        except Exception as e:
            # Re-open connection even if restore failed
            self.reconnect(self.session.current_user)
            raise e
            
        # Re-connect to restored DB
        self.reconnect(self.session.current_user)

    def clear_local_secrets(self) -> bool:
        try:
            self.db.execute("DELETE FROM secrets")
            self.db.execute("DELETE FROM security_audit")
            self.db.commit()
            self.db.vacuum()
            return True
        except Exception as e:
            logger.error(f"Error clearing local secrets: {e}")
            return False

    def wrap_key(self, data: Any, password: str, salt: Any) -> bytes: return self.security.wrap_key(data, password, salt)
    def unwrap_key(self, wrapped_data: Any, password: str, salt: Any) -> bytes: return self.security.unwrap_key(wrapped_data, password, salt)
    def save_vault_access_local(self, vault_id: str, wrapped_key: bytes) -> bool: 
        return self.users.update_vault_access(self.session.current_user, vault_id, wrapped_key)

    def change_login_password(self, old_password: str, new_password: str, user_manager: Optional[Any] = None, progress_callback: Optional[Any] = None) -> None:
        """
        Updates the user masters password and re-encrypts all associated keys.
        Synchronizes with both local and cloud storage.
        """
        if not self.session.current_user:
            raise ValueError("No hay sesión activa.")

        logger.info(f"Changing password for {self.session.current_user}...")
        
        # 1. Generate new salts and hash
        new_salt = os.urandom(16).hex()
        new_hash, _ = CryptoEngine.hash_user_password(new_password, bytes.fromhex(new_salt))
        
        # 2. Re-wrap Personal Key (SVK)
        new_v_salt = os.urandom(16)
        new_protected_key = self.security.wrap_key(self.session.personal_key, new_password, new_v_salt)
        
        # 3. Sync to Cloud via UserManager
        if user_manager:
            success = user_manager.update_user_password(
                self.session.current_user, 
                new_password,
                new_protected_key=new_protected_key,
                new_vault_salt=new_v_salt
            )
            if not success:
                raise RuntimeError("Falló la sincronización de contraseña con la nube.")
        
        # 4. Sync Local
        self.save_local_user_profile(
            self.session.current_user, 
            new_hash, 
            new_salt, 
            new_v_salt,
            role=self.session.user_role,
            vault_id=self.session.current_vault_id,
            protected_key=new_protected_key
        )
        
        # 5. Update session
        self.session.master_key = self.security.derive_keke(new_password, new_v_salt)
        self.log_event("CHANGE PASSWORD", details="User password and keys successfully rotated")

    def attempt_legacy_recovery(self) -> Tuple[int, str]:
        """
        Intenta recuperar secretos que no pudieron ser descifrados con las llaves actuales.
        Prueba con patrones históricos de llaves de bóveda compartidas.
        """
        logger.info("[Forensic] Starting forensic analysis of encrypted secrets...")
        recovered_count = 0
        
        # 1. Obtener todos los registros (incluyendo los que fallaron en el login normal)
        # Usamos el repositorio directamente para tener acceso a los blobs originales
        raw_records = self.secrets.get_all(self.session.current_user, include_deleted=True)
        
        # 2. Repercutir llaves actuales para filtrado
        current_keys = []
        if self.session.vault_key: current_keys.append(self.session.vault_key)
        if self.session.personal_key: current_keys.append(self.session.personal_key)
        if self.session.master_key: current_keys.append(self.session.master_key)
        current_keys.extend(self.session.kek_candidates.values())

        to_analyze = []
        for r in raw_records:
            enc_data = self.security.ensure_bytes(r.get("secret"))
            nonce = self.security.ensure_bytes(r.get("nonce"))
            if not enc_data or not nonce or len(nonce) != 12: continue
            
            # Si ya se abre con las actuales, no es candidato
            if self.security.decrypt_data(enc_data, nonce, current_keys) != "[Bloqueado 🔑]":
                continue
            to_analyze.append(r)

        if not to_analyze:
            return 0, "No se encontraron registros bloqueados para analizar."

        # 3. Generar llaves candidatas históricas
        candidate_keys = []
        possible_ids = [None, "None", "null", "", "0", "1", "2", "3", "4", "5", "default", "KAREN", "admin"]
        import hashlib
        for pid in possible_ids:
            shared_secret = f"PASSGUARDIAN_VAULT_{pid}_SHARED_KEY"
            # PBKDF2 con iterations=100k y salt 'public_salt' (como en el legado)
            k = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
            candidate_keys.append(k)

        # 4. Probar recuperación
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        for r in to_analyze:
            enc_data = self.security.ensure_bytes(r.get("secret"))
            nonce = self.security.ensure_bytes(r.get("nonce"))
            rid = r.get("id")
            service = r.get("service")
            username = r.get("username")
            is_private = r.get("is_private", 0)

            for k in candidate_keys:
                try:
                    decrypted = AESGCM(k).decrypt(nonce, enc_data, None).decode("utf-8")
                    
                    # ¡Éxito! Ahora lo actualizamos con la llave actual para "sanarlo"
                    # Usamos update_secret que lo guardará con la llave de sesión correcta
                    self.update_secret(rid, service, username, decrypted, f"Recuperado: {r.get('notes', '')}", is_private)
                    recovered_count += 1
                    logger.info(f"[Forensic] Recovered record {rid} ({service})")
                    break
                except Exception:
                    continue

        return recovered_count, f"Análisis finalizado. Se recuperaron {recovered_count} de {len(to_analyze)} registros analizados."

    def repair_vault_access(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Intenta recuperar el acceso a la bóveda desencriptando la llave privada con la contraseña 
        ANTERIOR y re-encriptándola con la contraseña NUEVA.
        """
        try:
            logger.info(f"[Forensic] Starting REPAIR protocol for {username}...")
            
            # 1. Asegurar entorno
            self.reconnect(username)
            profile = self.get_local_user_profile(username)
            
            if not profile or not profile.get("protected_key"):
                return False, "No se encontró perfil local o llave protegida para este usuario."

            # Datos cifrados actuales
            p_key_blob = self.security.ensure_bytes(profile["protected_key"])
            if not p_key_blob or len(p_key_blob) < 28:
                return False, "La llave protegida está corrupta o ausente."
                
            nonce = p_key_blob[:12]
            ciphertext = p_key_blob[12:]
            
            # Salts (Intentamos con v_salt preferiblemente)
            v_salt = self.security.ensure_bytes(profile.get("vault_salt"))
            meta_salt = self.security.ensure_bytes(self.get_meta("salt"))
            salts_to_try = [v_salt] if v_salt else []
            if meta_salt: salts_to_try.append(meta_salt)

            # 2. INTENTO DE RESCATE (Usando Old Password)
            rescued_key = None
            from src.infrastructure.crypto_engine import CryptoEngine
            for salt in salts_to_try:
                try:
                    old_kek = CryptoEngine.derive_kek_from_password(old_password, salt, iterations=100_000)
                    rescued_key = AESGCM(old_kek).decrypt(nonce, ciphertext, None)
                    logger.info("[Forensic] Key rescued successfully using old password!")
                    break
                except Exception:
                    continue
            
            if not rescued_key:
                return False, "La contraseña ANTERIOR no es correcta. No se pudo desencriptar la llave."

            # 3. RE-ENCRIPTACIÓN (Usando New Password)
            target_salt = v_salt if v_salt else meta_salt
            new_blob = self.security.wrap_key(rescued_key, new_password, target_salt)
            
            # 4. GUARDADO
            self.users.update_protected_key(username, new_blob)
            
            self.log_event("REPAIR VAULT ACCESS", details=f"Access repaired for {username}")
            return True, "Llave de acceso reparada localmente."
        except Exception as e:
            logger.error(f"[Forensic] Repair failed: {e}")
            return False, str(e)
