import os
import sqlite3
import re
import time
import logging
import base64
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Optional, Any, Dict, List, Tuple

# Infrastructure imports
from src.infrastructure.database.db_manager import DBManager
from src.infrastructure.repositories.secret_repo import SecretRepository
from src.infrastructure.repositories.user_repo import UserRepository
from src.infrastructure.repositories.audit_repo import AuditRepository
from src.infrastructure.crypto_engine import CryptoEngine

# Domain imports
from src.domain.services.session_service import SessionService
from src.domain.services.security_service import SecurityService

# Config imports
from config.config import (
    SESSION_SHORT_TIMEOUT, SESSION_LONG_TIMEOUT, 
    SECURITY_LEVEL_DEFAULT, TOTP_SYSTEM_KEY
)

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
        
        # Dynamic properties for legacy compatibility (no more copying values)
        # These properties always reflect current session state
    
    # --- DYNAMIC PROPERTIES FOR LEGACY ACCESS ---
    @property
    def current_user(self) -> Optional[str]:
        return self.session.current_user
    
    @current_user.setter
    def current_user(self, value: Optional[str]) -> None:
        self.session.current_user = value
    
    @property
    def current_user_id(self) -> Optional[str]:
        return self.session.current_user_id
    
    @current_user_id.setter
    def current_user_id(self, value: Optional[str]) -> None:
        self.session.current_user_id = value
    
    @property
    def user_role(self) -> str:
        return self.session.user_role
    
    @user_role.setter
    def user_role(self, value: str) -> None:
        self.session.user_role = value
    
    @property
    def master_key(self) -> Optional[bytearray]:
        return self.session.master_key
    
    @master_key.setter
    def master_key(self, value: Optional[bytearray]) -> None:
        self.session.master_key = value
    
    @property
    def personal_key(self) -> Optional[bytearray]:
        return self.session.personal_key
    
    @personal_key.setter
    def personal_key(self, value: Optional[bytearray]) -> None:
        self.session.personal_key = value
    
    @property
    def vault_key(self) -> Optional[bytearray]:
        return self.session.vault_key
    
    @vault_key.setter
    def vault_key(self, value: Optional[bytearray]) -> None:
        self.session.vault_key = value
    
    @property
    def current_vault_id(self) -> Optional[str]:
        """Vault ID activo (delegado a session)."""
        return self.session.current_vault_id
    
    @current_vault_id.setter
    def current_vault_id(self, value: Optional[str]) -> None:
        """Establece el vault ID activo."""
        self.session.current_vault_id = value
    
    @property
    def session_id(self) -> str:
        return self.session.session_id
    
    @session_id.setter
    def session_id(self, value: str) -> None:
        self.session.session_id = value
    
    @property
    def kek_candidates(self) -> dict:
        return self.session.kek_candidates
    
    @kek_candidates.setter
    def kek_candidates(self, value: dict) -> None:
        self.session.kek_candidates = value
    
    @property
    def conn(self):
        return self.db.conn
    
    @property
    def db_path(self):
        return self.db.db_path

    # --- DATABASEDO & META ---
    def get_meta(self, key: str) -> Optional[str]: return self.users.get_meta(key)
    def set_meta(self, key: str, value: Any) -> None: self.users.set_meta(key, value)
    
    def _initialize_db(self, name: str) -> None:
        self.db._initialize_db(name)

    def nuclear_reset(self) -> int:
        """Removes local state to force cloud sync. Destructive."""
        from src.domain.services.maintenance_service import MaintenanceService
        return MaintenanceService.nuke_local_state()

    def repair_vault_key(self, username: str, password: str) -> bool:
        """Attempts to regenerate a vault key for a specific user."""
        from src.domain.services.maintenance_service import MaintenanceService
        return MaintenanceService.repair_vault_key(username, password, self.db)

    def reconnect(self, username: str) -> None:
        """Cambia el contexto de base de datos de forma segura, con guarda anti-redundancia."""
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', str(username).lower().strip())
        current_db = self.db.db_path.name if self.db and self.db.db_path else ""
        
        # [GUARD] Si ya estamos conectados a esta DB, no perdemos tiempo reconectando
        if f"vault_{safe_name}.db" == current_db or (safe_name == "vultrax" and current_db == "vultrax.db"):
            logger.debug(f"[Sync] Already connected to database for {username}. Skipping reconnect.")
            return

        logger.info(f"[Sync] Switching database context to {username}...")
        self._initialize_db(username)
        logger.info(f"[Sync] Context switched successfully.")

    # --- USER & SESSION ---
    def get_local_user_profile(self, username: str) -> Optional[Dict[str, Any]]: 
        return self.users.get_profile(username)

    def save_local_user_profile(self, *args: Any, **kwargs: Any) -> None:
        self.users.save_profile(*args, **kwargs)

    def set_active_user(self, username: str, password: str) -> None:
        """
        Activates a user session by loading their profile, deriving KEKs, 
        and unwrapping cryptographic keys. Implements auto-healing for 
        corrupt vault keys.
        """
        new_user = str(username).upper().strip().replace(" ", "")
        
        if self.session.current_user == new_user and self.session.master_key is not None:
            return

        logger.info(f"[Auth] Activating session for {new_user}")
        self.reconnect(new_user)
        profile = self.get_local_user_profile(new_user)
        
        if not profile: 
            logger.warning(f"[Auth] No profile found for {new_user}")
            return

        # 1. Setup Session Context
        self._setup_user_session(new_user, profile)
        
        # 2. Key Derivation & Primary Unwrapping
        v_salt = self._ensure_valid_salt(new_user, profile)
        kek = self._derive_session_keks(password, v_salt)
        self.session.personal_key = self.security.decrypt_protected_key(profile.get("protected_key"), kek)

        # 3. Vault Key Acquisition (with fallback and healing)
        self._acquire_vault_key(new_user, password, v_salt, profile)

        # 4. Finalize Session (with Silent Security Upgrade for Password Hash)
        self.session.master_key = self.session.personal_key or self.session.vault_key or kek
        
        # [SECURITY UPGRADE] Migrate security context to Argon2id if it's currently PBKDF2
        self._migrate_security_context_to_argon2(new_user, password, profile)
        
        logger.info(f"Session Started: {self.session.current_user} | ID: {self.session.session_id}")

    def _migrate_security_context_to_argon2(self, username: str, password: str, profile: Dict[str, Any]) -> None:
        """
        [ETAPA 2 PLUS] Migrates user security context to Argon2id.
        Handles both Password Hash upgrade AND Vault Key Re-Wrap.
        """
        from src.infrastructure.crypto_engine import ARGON2_AVAILABLE, ARGON2_PREFIX
        
        # Check if migration is needed (Current is PBKDF2 or kdf_version is 1)
        kdf_version = profile.get("kdf_version", 1)
        stored_hash = profile.get("password_hash")
        
        if ARGON2_AVAILABLE and (kdf_version == 1 or not stored_hash.startswith(ARGON2_PREFIX)):
            try:
                logger.info(f"[Security Upgrade] Starting full migration to Argon2id for {username}...")
                
                # 1. Generate NEW Password Hash (Argon2id)
                new_hash = CryptoEngine.hash_user_password_argon2(password)
                
                # 2. PERFORM RE-WRAP OF VAULT KEY
                # We already have the decrypted vault_key in our current session!
                # It was decrypted using the old PBKDF2 KEK during set_active_user flow.
                current_vault_key = bytes(self.session.vault_key) if self.session.vault_key else None
                new_wrapped_vault_key = None
                
                if current_vault_key:
                    # Re-wrap using NEW algorithm (Argon2id)
                    # CryptoEngine.wrap_vault_key now uses Argon2id if available/enabled
                    new_wrapped_vault_key = CryptoEngine.wrap_vault_key(current_vault_key, password, profile.get("vault_salt"))
                    logger.debug("[Security Upgrade] Vault key re-wrapped with Argon2id.")

                # 3. Update locally
                # Update hash and KDF version
                self.users.update_password_hash(username, new_hash, b'', kdf_version=2)
                
                # Update wrapped vault key if re-wrap was successful
                if new_wrapped_vault_key:
                    self.users.update_wrapped_vault_key(username, new_wrapped_vault_key)
                    # Also update vault_access table for consistency
                    if profile.get("vault_id"):
                        self.users.save_vault_access(profile["vault_id"], new_wrapped_vault_key, synced=0) # Mark for cloud sync

                # 4. [CLOUD SYNC] Push changes to Supabase
                try:
                    from src.infrastructure.user_manager import UserManager
                    um = UserManager(self)
                    update_payload = {
                        "password_hash": new_hash,
                        "salt": "", 
                        "kdf_version": 2
                    }
                    um.supabase.table("users").update(update_payload).eq("username", username.upper()).execute()
                    
                    if new_wrapped_vault_key and profile.get("vault_id") and profile.get("id"):
                        um.supabase.table("vault_access").update({
                            "wrapped_master_key": new_wrapped_vault_key.hex()
                        }).eq("user_id", profile["id"]).eq("vault_id", profile["vault_id"]).execute()
                        
                    logger.info(f"[Security Upgrade] Cloud security context for {username} upgraded to Argon2id.")
                except Exception as ce:
                    logger.warning(f"Could not sync security migration to cloud: {ce}")

                logger.info(f"[Security Upgrade] Full security migration for {username} completed successfully.")
            except Exception as e:
                logger.error(f"Failed to migrate security context to Argon2id: {e}")

    def _setup_user_session(self, username: str, profile: Dict[str, Any]) -> None:
        """Initializes the session service with user metadata."""
        self.session.set_user(
            username, 
            profile.get("user_id"), 
            profile.get("role") or "user", 
            profile.get("vault_id")
        )

    def _ensure_valid_salt(self, username: str, profile: Dict[str, Any]) -> bytes:
        """Ensures a valid vault salt exists, generating one if necessary."""
        v_salt = self.security.ensure_bytes(profile.get("vault_salt"))
        if not v_salt or len(v_salt) < 16:
            v_salt = self._get_or_create_salt()
            self.save_local_user_profile(
                username, 
                profile.get("password_hash") or "LEGACY", 
                profile.get("salt") or "LEGACY", 
                v_salt,
                role=self.session.user_role, 
                vault_id=self.session.current_vault_id,
                user_id=profile.get("user_id")
            )
        return v_salt

    def _derive_session_keks(self, password: str, v_salt: bytes) -> bytes:
        """Derives the Key Encryption Key (KEK) for the current session."""
        from src.infrastructure.secure_memory import SecureBytes
        raw_kek = self.security.derive_keke(password, v_salt)
        self.session.kek_candidates["p100"] = SecureBytes(raw_kek)
        return raw_kek

    def _acquire_vault_key(self, username: str, password: str, v_salt: bytes, profile: Dict[str, Any]) -> None:
        """Attempts to unwrap the vault key with automatic security migration (PBKDF2 -> Argon2id)."""
        v_key_blob = self.security.ensure_bytes(profile.get("wrapped_vault_key"))
        
        # Fallback to vault_access table if primary blob is missing
        if not v_key_blob and self.session.current_vault_id:
            va = self.users.get_vault_access(self.session.current_vault_id)
            if va: v_key_blob = self.security.ensure_bytes(va.get("wrapped_master_key"))

        if not v_key_blob:
            logger.warning(f"[Security] No vault key available for {username}")
            return

        # Attempt Unwrapping
        try:
            # unwrap_key now returns (key, algorithm)
            dec_v_key, algo = self.security.unwrap_key(v_key_blob, password, v_salt)
            self.session.vault_key = bytearray(dec_v_key)
            
            # Silent Security Upgrade (Healing)
            if algo == "pbkdf2" and CryptoEngine.ARGON2_AVAILABLE:
                logger.info(f"[Security Upgrade] Silently migrating {username} to Argon2id...")
                new_v_blob = self.security.wrap_key(dec_v_key, password, v_salt)
                self.users.update_wrapped_vault_key(username, new_v_blob)
                
        except Exception as e:
            logger.info(f"[Forensic] Primary unwrap failed for {username}: {e}")
            self._handle_vault_key_failure(username, password, v_salt, v_key_blob)

    def _handle_vault_key_failure(self, username: str, password: str, v_salt: bytes, w_v_raw: bytes) -> None:
        """Orchestrates forensic recovery when primary unwrapping fails."""
        # Try vault_access fallback
        if self._try_vault_access_fallback(username, password, v_salt, w_v_raw):
            return

        # Try extreme recovery (auto-healing)
        logger.info(f"[Forensic] Attempting auto-healing for {username}...")
        healed_key = self._attempt_vault_key_soft_recovery(username, password, w_v_raw, v_salt)
        
        # Try alternative keys in vault_access
        if not healed_key:
            healed_key = self._try_alternative_vault_keys(username, password, v_salt, w_v_raw)
        
        if healed_key:
            self.session.vault_key = bytearray(healed_key)
            logger.info(f"[Forensic] Vault access HEALED successfully for {username}")
        else:
            logger.warning(f"[Security] All recovery paths failed for {username}")

    def _try_vault_access_fallback(self, username: str, password: str, v_salt: bytes, w_v_raw: bytes) -> bool:
        """Checks if a secondary key in the vault_access table works."""
        if not self.session.current_vault_id: return False
        
        va = self.users.get_vault_access(self.session.current_vault_id)
        if va:
            w_va_raw = va.get("wrapped_master_key")
            if w_va_raw and w_va_raw != w_v_raw:
                try:
                    dec_v_key = self.security.unwrap_key(w_va_raw, password, v_salt)
                    self.session.vault_key = bytearray(dec_v_key)
                    logger.info("[Forensic] Vault access found in fallback table!")
                    # Heal primary table
                    try:
                        self.users.update_vault_access(username, self.session.current_vault_id, w_va_raw, synced=1)
                    except Exception: pass
                    return True
                except Exception: pass
        return False

    def _try_alternative_vault_keys(self, username: str, password: str, v_salt: bytes, w_v_raw: bytes) -> Optional[bytes]:
        """Iterates through all possible vault access keys to find a match."""
        all_va = self.users.get_all_vault_accesses()
        for va in all_va:
            alt_w_key = self.security.ensure_bytes(va.get("wrapped_master_key"))
            if alt_w_key and alt_w_key != w_v_raw:
                 candidate = self._attempt_vault_key_soft_recovery(username, password, alt_w_key, v_salt)
                 if candidate: return candidate
        return None



    def _attempt_vault_key_soft_recovery(self, username: str, password: str, wrapped_key: bytes, current_salt: bytes) -> Optional[bytes]:
        """
        Extreme Recovery Protocol (V4.0)
        Tries combinations of salts, iterations, and legacy patterns.
        """
        # 1. Salt Candidates (Enriquecido para Rescate Senior)
        salt_candidates = [
            current_salt,
            b"public_salt", 
            b"", 
            b"salt_123",
            username.upper().encode(),
            username.lower().encode(),
            username.encode(),
            # [RESCUE] Try matching the text salt from profile if available
            self.security.ensure_bytes(self.get_local_user_profile(username).get("salt")) if self.get_local_user_profile(username) else None,
            self.get_meta('master_salt') or b"",
            self.get_meta('salt') or b"",
            self.get_meta('vault_salt') or b"",
            self.session.current_vault_id.encode() if self.session.current_vault_id else None
        ]
        
        # 2. Iteration Candidates (Prioridad máxima para velocidad)
        iteration_candidates = [100000, 600000]
        
        # Deduplicación y limpieza profesional
        processed_salts = []
        for s in salt_candidates:
            b_s = self.security.ensure_bytes(s)
            if b_s is not None and len(b_s) > 0 and b_s not in processed_salts:
                processed_salts.append(b_s)

        total_trials = len(processed_salts) * len(iteration_candidates)
        logger.info(f"[Forensic] Starting Ultra Recovery V5.0: {total_trials} combinations for {username}...")

        # 3. Optimized Trial Loop (Level-based for performance)
        password_candidates = [password, password.strip()]
        trial_count = 0
        
        # LEVEL 1: Standard PBKDF2 (UTF-8, SHA256) - Most Likely
        logger.info("[Forensic] Level 1: Standard PBKDF2 (UTF-8, SHA256)")
        for p_cand in password_candidates:
            for iter_count in iteration_candidates:
                for salt in processed_salts:
                    trial_count += 1
                    if trial_count % 20 == 0:
                        logger.info(f"[Forensic] Recovery Progress: {trial_count} trials completed...")
                    try:
                        kdf = PBKDF2HMAC(
                            algorithm=hashes.SHA256(),
                            length=32,
                            salt=salt,
                            iterations=iter_count,
                            backend=default_backend()
                        )
                        kek = kdf.derive(p_cand.encode("utf-8"))
                        dec_key = AESGCM(kek).decrypt(wrapped_key[:12], wrapped_key[12:], None)
                        if dec_key and len(dec_key) == 32:
                            logger.info(f"[Forensic] SUCCESS! PBKDF2 recovered | Iter: {iter_count}, Salt: {salt.hex()[:6]}")
                            return self._heal_and_return(username, p_cand, dec_key, salt)
                    except Exception: continue

        # LEVEL 2: Legacy Raw Hashes (High Speed)
        logger.info("[Forensic] Level 2: Legacy Raw Hashes (SHA256 Raw/Hex)")
        for p_cand in password_candidates:
            for salt in processed_salts:
                try:
                    # Raw binary concat
                    raw_key = hashlib.sha256(p_cand.encode('utf-8') + salt).digest()
                    dec_key = AESGCM(raw_key).decrypt(wrapped_key[:12], wrapped_key[12:], None)
                    if dec_key and len(dec_key) == 32:
                        logger.info(f"[Forensic] SUCCESS! Legacy Raw recovered | Salt: {salt.hex()[:6]}")
                        return self._heal_and_return(username, p_cand, dec_key, current_salt)
                    
                    # Hex text concat
                    hex_key = hashlib.sha256((p_cand + salt.hex()).encode('utf-8')).digest()
                    dec_key = AESGCM(hex_key).decrypt(wrapped_key[:12], wrapped_key[12:], None)
                    if dec_key and len(dec_key) == 32:
                        logger.info(f"[Forensic] SUCCESS! Legacy Hex recovered | Salt: {salt.hex()[:6]}")
                        return self._heal_and_return(username, p_cand, dec_key, salt)
                except Exception: continue

        # [PERFORMANCE] Level 3 disabled for synchronous login to prevent blocking.
        logger.warning(f"[Forensic] Fast recovery failed for {username}. Deep scan skipped to restore responsiveness.")
        
        return None
        
        return None
        
        return None

    def _heal_and_return(self, username: str, password: str, dec_key: bytes, working_salt: bytes) -> bytes:
        """Sana la llave local re-envolviéndola con parámetros estándar."""
        try:
             # Use the salt that actually WORKED for re-wrapping to stay consistent
             new_wrap = self.security.wrap_key(dec_key, password, working_salt)
             self.users.update_vault_access(username, self.session.current_vault_id or "default", new_wrap, vault_salt=working_salt)
             self.users.db.commit()
             logger.info(f"[Forensic] Vault key healed and persisted for {username} using working salt: {working_salt.hex()[:6]}")
        except Exception as e:
             logger.error(f"Heal persistence failed: {e}")
        return dec_key
        
        return None

    def refresh_vault_context(self) -> bool:
        if not self.session.current_user: return False
        profile = self.get_local_user_profile(self.session.current_user)
        if not profile: return False

        self.session.current_vault_id = profile.get("vault_id")
        w_v_raw = profile.get("wrapped_vault_key")
        kek = self.session.kek_candidates.get("p100")
        
        if w_v_raw and kek:
            try:
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
                    current_user, current_uid, integrity, notes, priv, current_vid, None
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
    def get_all_encrypted(self, only_mine: bool = False, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieves encrypted records with optional pagination for massive scalability.
        """
        raw = self.secrets.get_all_encrypted(self.session.current_user, only_mine, limit, offset)
        for r in raw:
            r["secret_blob"] = self.security.ensure_bytes(r["secret"])
            r["nonce_blob"] = self.security.ensure_bytes(r["nonce"])
        return raw

    def add_secret_encrypted(self, service: str, username: str, secret_blob: bytes, nonce_blob: bytes, 
                             integrity: str, notes: Optional[str] = None, deleted: int = 0, 
                             synced: int = 1, sid: Optional[int] = None, is_private: int = 0, 
                             owner_name: Optional[str] = None, vault_id: Optional[str] = None, 
                             cloud_id: Optional[str] = None, version: Optional[str] = None) -> None:
        data = {
            "service": service, "username": username, "secret": secret_blob, "nonce": nonce_blob,
            "integrity_hash": integrity, "notes": notes, "deleted": deleted, "synced": synced,
            "is_private": int(is_private or 0), "owner_name": str(owner_name or self.session.current_user).upper(),
            "vault_id": vault_id or self.session.current_vault_id, "cloud_id": cloud_id, 
            "version": version, "updated_at": int(time.time())
        }
        if sid: data["id"] = sid
        self.secrets.add_encrypted_direct(data)

    def mark_as_synced(self, sid: int, status: int = 1) -> None: 
        self.db.execute("UPDATE secrets SET synced = ? WHERE id = ?", (int(status), sid))
        self.db.commit()

    # --- AUDIT ---
    def log_event(self, action: str, service: str = "-", status: str = "SUCCESS", details: str = "-", 
                  user_name: Optional[str] = None, user_id: Optional[str] = None, **kwargs: Any) -> None:
        u = user_name if user_name else self.session.current_user
        uid = user_id if user_id else self.session.current_user_id
        self.audit.log_event(u, uid, action, service, status, details, **kwargs)

    def get_audit_logs(self, limit: int = 500) -> List[Dict[str, Any]]:
        return self.audit.get_logs(self.session.current_user, self.session.user_role, limit)

    def get_audit_log_count(self) -> int: return self.audit.get_count()

    def get_pending_audit_logs(self) -> List[tuple]:
        return self.audit.get_pending_logs()

    def mark_audit_logs_as_synced(self) -> None:
        self.audit.mark_as_synced()

    # --- UTILS & LEGACY ---
    def cleanup_vault_cache(self) -> None:
        """
        Cleanup vault cache and vacuum database.
        CRITICAL: Does NOT clear session keys if user is logged in OR if vault_key exists.
        """
        # SECURITY FIX: Only clear session if BOTH conditions are met:
        # 1. No active user logged in
        # 2. No vault_key in memory (prevents loss during secondary user creation)
        if not self.session.current_user and not self.session.vault_key:
            self.session.clear()
            logger.info("Session cleared (no active user and no vault key)")
        else:
            if self.session.current_user:
                logger.debug(f"Skipping session clear - user {self.session.current_user} is logged in")
            if self.session.vault_key:
                logger.debug("Skipping session clear - vault_key exists in memory")
        
        self.db.vacuum()

    def _ensure_bytes(self, data: Any) -> Optional[bytes]:
        """Legacy internal helper for byte conversion, delegated to SecurityService."""
        return self.security.ensure_bytes(data)

    # --- BACKUP & RESTORE (LOCAL) ---
    def create_local_backup(self) -> str:
        """Create a timestamped backup of the current database."""
        if not self.db.conn or not self.db.db_path:
            raise RuntimeError("Database not initialized")
        
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
    def save_vault_access_local(self, vault_id: str, wrapped_key: bytes, synced: int = 0, force: bool = False, vault_salt: Optional[bytes] = None) -> bool: 
        if not self.session.current_user:
            logger.debug("Vault access save attempted before user activation (normal during initialization)")
            return False
        return self.users.update_vault_access(self.session.current_user, vault_id, wrapped_key, synced=synced, force=force, vault_salt=vault_salt)

    def change_login_password(self, old_password: str, new_password: str, user_manager: Optional[Any] = None, progress_callback: Optional[Any] = None) -> None:
        """
        Updates the user's master password and re-encrypts all associated keys.
        Synchronizes with both local and cloud storage.
        """
        if not self.session.current_user:
            raise ValueError("No hay sesión activa.")

        logger.info(f"[Auth] Starting password rotation for {self.session.current_user}...")
        
        # 1. Identity Verification
        cloud_p = self._verify_current_password(old_password, user_manager)
        
        # 2. Key Rescuing (Ensuring we have the real keys before rotating)
        if not self.session.personal_key:
            self._rescue_personal_key(old_password, cloud_p)
            
        # 3. Generating new Identity Salts and Hash
        new_salt = os.urandom(16).hex()
        new_hash, _ = CryptoEngine.hash_user_password(new_password, bytes.fromhex(new_salt))
        new_v_salt = os.urandom(16)
        
        # 4. Re-wrap Personal Identity Key
        new_protected_key = self.security.wrap_key(self.session.personal_key, new_password, new_v_salt)
        
        # 5. Rotate All Vault Accesses
        rehashed_vaults = self._rotate_vault_keys(old_password, new_password, new_v_salt, cloud_p, user_manager)

        # 6. Synchronization (Cloud then Local)
        self._perform_password_change_sync(
            new_password, new_hash, new_salt, new_v_salt, 
            new_protected_key, rehashed_vaults, user_manager
        )
        
        # 7. Finalize Session
        self._finalize_password_change(new_password, new_v_salt, rehashed_vaults)

    def _verify_current_password(self, old_password: str, user_manager: Optional[Any]) -> Optional[Dict[str, Any]]:
        """Verifies the current password against local profile and cloud identity."""
        try:
            profile = self.get_local_user_profile(self.session.current_user)
            p_key_blob = self.security.ensure_bytes(profile.get("protected_key"))
            v_salt = self.security.ensure_bytes(profile.get("vault_salt"))
            
            if self.session.personal_key:
                logger.info("Session key verified for rotation.")
            elif p_key_blob and v_salt:
                try:
                    self.security.unwrap_key(p_key_blob, old_password, v_salt)
                except Exception as unwrap_err:
                    if user_manager:
                         cloud_p = user_manager.validate_user_access(self.session.current_user)
                         c_salt = self.security.ensure_bytes(cloud_p.get("vault_salt"))
                         if c_salt and c_salt != v_salt:
                              self.security.unwrap_key(p_key_blob, old_password, c_salt)
                              return cloud_p
                         else: raise unwrap_err
                    else: raise unwrap_err
            else:
                raise ValueError("Identity data missing.")
            
            # Fetch cloud profile for subsequent steps if online
            if user_manager:
                 return user_manager.validate_user_access(self.session.current_user)
            return None
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            raise ValueError("La firma maestra actual es incorrecta.")

    def _rescue_personal_key(self, old_password: str, cloud_p: Optional[Dict[str, Any]]) -> None:
        """Emergency recovery of the personal key using old credentials."""
        logger.info("[Auth] Rescuing personal key...")
        try:
            profile = self.get_local_user_profile(self.session.current_user)
            p_key_blob = self.security.ensure_bytes((cloud_p or {}).get("protected_key")) or \
                         self.security.ensure_bytes(profile.get("protected_key"))
            v_salt = self.security.ensure_bytes((cloud_p or {}).get("vault_salt")) or \
                     self.security.ensure_bytes(profile.get("vault_salt"))
            
            # Try multiple iteration counts for legacy support
            for iters in [600000, 100000, 1000]:
                try:
                    kek = self.security.CryptoEngine.derive_kek_from_password(old_password, v_salt, iterations=iters)
                    res = self.security.decrypt_protected_key(p_key_blob, kek)
                    if res:
                        self.session.personal_key = res
                        logger.info(f"Personal key rescued ({iters} iters).")
                        return
                except: continue
            raise ValueError("Rescue failed.")
        except Exception as e:
            logger.error(f"Personal key rescue failed: {e}")
            raise ValueError("No se puede recuperar la identidad personal para la rotación.")

    def _rotate_vault_keys(self, old_password: str, new_password: str, new_v_salt: bytes, 
                          cloud_p: Optional[Dict[str, Any]], user_manager: Optional[Any]) -> List[Tuple]:
        """Iterates and re-encrypts all accessible vault keys with the new password."""
        all_accesses = self.users.get_all_vault_accesses()
        rehashed_vaults = []
        
        # Prepare decryption environment
        local_v_salt = self.security.ensure_bytes(self.get_local_user_profile(self.session.current_user).get("vault_salt"))
        cloud_v_salt = self.security.ensure_bytes((cloud_p or {}).get("vault_salt"))
        salt_candidates = [s for s in [cloud_v_salt, local_v_salt, b"public_salt"] if s]
        
        cloud_accesses = []
        if user_manager and self.session.current_user_id:
             try: cloud_accesses = user_manager.get_cloud_vault_accesses(self.session.current_user_id)
             except Exception: pass

        for acc in all_accesses:
            v_id = acc['vault_id']
            try:
                m_key = self._acquire_master_key_for_rotation(v_id, old_password, salt_candidates, cloud_accesses, user_manager, acc)
                if m_key:
                    new_wrap = self.security.wrap_key(m_key, new_password, new_v_salt)
                    rehashed_vaults.append((v_id, new_wrap, acc.get('access_level', 'member')))
            except Exception as e:
                logger.error(f"Failed to re-wrap vault {v_id}: {e}")

        # Ensure active vault is secure
        self._ensure_active_vault_rotation(rehashed_vaults, new_password, new_v_salt)
        return rehashed_vaults

    def _acquire_master_key_for_rotation(self, vault_id: str, password: str, salts: list, 
                                        cloud_acc: list, user_manager: Optional[Any], acc: dict) -> Optional[bytes]:
        """Tries all available paths to get the raw master key for re-encryption."""
        # 1. Active Session Key
        if vault_id and self.session.current_vault_id and str(vault_id).lower() == str(self.session.current_vault_id).lower():
            if self.session.vault_key: return bytes(self.session.vault_key)

        # 2. Local Decryption
        wrapped_blob = self.security.ensure_bytes(acc.get('wrapped_master_key'))
        for s in salts:
            try:
                # unwrap_vault_key returns (key, algorithm)
                k, algo = self.security.unwrap_key(wrapped_blob, password, s)
                if k: return k
            except: continue

        # 3. Cloud Rescue
        if user_manager:
            match = next((c for c in cloud_acc if str(c['vault_id']).lower() == str(vault_id).lower()), None)
            if match:
                c_blob = self.security.ensure_bytes(match.get('wrapped_master_key') or match.get('wrapped_vault_key'))
                for s in salts:
                    try:
                        k, algo = self.security.unwrap_key(c_blob, password, s)
                        if k: return k
                    except: continue
        return None

    def _ensure_active_vault_rotation(self, rehashed_vaults: list, password: str, salt: bytes) -> None:
        """Guarantees that at least the active vault key is rotated successfully."""
        target_v_id = str(self.session.current_vault_id).lower() if self.session.current_vault_id else None
        active_ok = any(str(v[0]).lower() == target_v_id for v in rehashed_vaults) if target_v_id else True
        
        if not active_ok and target_v_id and self.session.vault_key:
            logger.info("[Auth] Emergency active vault re-wrap.")
            new_wrap = self.security.wrap_key(bytes(self.session.vault_key), password, salt)
            rehashed_vaults.append((self.session.current_vault_id, new_wrap, "manager"))
        elif not active_ok:
            raise RuntimeError(f"Rotación fallida para bóveda activa: {self.session.current_vault_id}")

    def _perform_password_change_sync(self, new_password, new_hash, new_salt, new_v_salt, 
                                     new_protected_key, rehashed_vaults, user_manager):
        """Synchronizes the new credentials and keys with Cloud and Local stores."""
        # 1. Cloud Sync (Atomic Priority)
        if user_manager:
            success, _ = user_manager.update_user_password(
                self.session.current_user, 
                new_password,
                new_protected_key=base64.b64encode(new_protected_key).decode('ascii'),
                new_vault_salt=base64.b64encode(new_v_salt).decode('ascii')
            )
            if not success: raise RuntimeError("Sync cloud fallido.")
            
            cloud_map = [(v_id, w_key.hex()) for v_id, w_key, lvl in rehashed_vaults]
            user_manager.update_bulk_vault_access(self.session.current_user_id, cloud_map)
        
        # 2. Local Update
        for v_id, new_wrap, lvl in rehashed_vaults:
             self.users.save_vault_access(v_id, new_wrap, lvl, synced=1)
        
        # Determine active vault key for profile redundancy
        active_w_key = next((w for i, w, l in rehashed_vaults if str(i).lower() == str(self.session.current_vault_id).lower()), None)

        self.save_local_user_profile(
            self.session.current_user, new_hash, new_salt, new_v_salt,
            role=self.session.user_role,
            vault_id=self.session.current_vault_id,
            protected_key=new_protected_key,
            wrapped_vault_key=active_w_key,
            user_id=self.session.current_user_id
        )

    def _finalize_password_change(self, password, salt, rehashed_vaults):
        """Updates the active session with the new credentials."""
        # [GOD-LEVEL] Argon2id KEK derivation for session
        if CryptoEngine.ARGON2_AVAILABLE:
            self.session.master_key = CryptoEngine.derive_kek_argon2id(password, salt)
        else:
            self.session.master_key = self.security.derive_keke(password, salt)
        
        # Refresh active vault key in memory
        target_v_id = str(self.session.current_vault_id).lower() if self.session.current_vault_id else None
        active_w_key = next((w for i, w, l in rehashed_vaults if str(i).lower() == target_v_id), None)
        
        if active_w_key:
            try:
                active_key, algo = self.security.unwrap_key(active_w_key, password, salt)
                self.session.vault_key = bytearray(active_key)
            except Exception as e:
                logger.error(f"Session re-sync failed: {e}")

        self.log_event("CHANGE PASSWORD", details="User password and vault keys rotated")

    def admin_reset_user_identity(self, target_username: str, new_password: str, user_manager: Optional[Any] = None, progress_callback: Optional[Any] = None) -> None:
        """
        [ADMIN PROTOCOL - SMART UNIFIED RESET] 
        Force-resets a user identity using the same robust logic as the rotation engine.
        """
        is_self_reset = (target_username.upper() == (self.session.current_user or "").upper())
        logger.info(f"Admin Force-Reset for {target_username} (Self={is_self_reset}).")
        
        # 1. New identity parameters
        new_salt = os.urandom(16).hex()
        new_hash, _ = CryptoEngine.hash_user_password(new_password, bytes.fromhex(new_salt))
        new_v_salt = os.urandom(16)
        
        # 2. Identity key preservation
        if is_self_reset and self.session.personal_key:
             target_personal_key = self.session.personal_key
             logger.info("Preserving identity from active session.")
        else:
             # Generamos una nueva identidad personal (SVK) para el usuario
             target_personal_key = os.urandom(32)
             logger.warning(f"Generating NEW personal identity key for {target_username}.")

        new_protected_key = self.security.wrap_key(target_personal_key, new_password, new_v_salt)
        
        # 3. ROBUST VAULT RE-WRAPPING
        all_accesses = self.users.get_all_vault_accesses()
        rehashed_vaults = []
        
        for acc in all_accesses:
            v_id = acc['vault_id']
            try:
                m_key = None
                # Path 1: Session Memory (Strongest)
                if v_id and self.session.current_vault_id and str(v_id).lower() == str(self.session.current_vault_id).lower():
                    if self.session.vault_key: 
                        m_key = bytes(self.session.vault_key)
                
                # Path 2: Local DB Fallback (Si el admin no tiene la llave en RAM pero sí en su DB local)
                if not m_key:
                    va_local = self.users.get_vault_access(v_id)
                    if va_local and va_local.get("wrapped_master_key"):
                        # NOTA: Esto solo funcionará si el admin tiene acceso a esta bóveda también
                        # y su llave está activa. 
                        if self.session.vault_key:
                            m_key = bytes(self.session.vault_key)

                if m_key:
                    new_wrap = self.security.wrap_key(m_key, new_password, new_v_salt)
                    rehashed_vaults.append((v_id, new_wrap, acc.get('access_level', 'member')))
                    logger.info(f"Vault {v_id} re-wrapped for {target_username}")
            except Exception as e:
                logger.error(f"Admin reset failed to re-wrap vault {v_id}: {e}")

        # 4. Atomic Sync to Cloud
        if user_manager:
            if progress_callback: progress_callback(20, 100, 0, 0)
            
            # Verificamos que el usuario existe en la nube
            target_profile = user_manager.validate_user_access(target_username)
            if not target_profile or not target_profile.get("exists"):
                raise RuntimeError(f"El usuario {target_username} no existe en la nube.")
            
            target_uid = target_profile.get("id")

            # A. Actualizar Perfil (Login/Auth)
            success, msg = user_manager.update_user_password(
                target_username, new_password,
                new_protected_key=base64.b64encode(new_protected_key).decode('ascii'),
                new_vault_salt=base64.b64encode(new_v_salt).decode('ascii')
            )
            if not success: raise RuntimeError(f"Fallo al actualizar perfil en nube: {msg}")

            # B. Actualizar Bóvedas (Acceso/Decryption) - USANDO UPSERT RESILIENTE
            if rehashed_vaults:
                cloud_map = [(v_id, w_key.hex()) for v_id, w_key, lvl in rehashed_vaults]
                user_manager.update_bulk_vault_access(target_uid, cloud_map)
            
            if progress_callback: progress_callback(100, 100, 1, 0)

        # 5. Local Persistence (Self-healing si es el propio admin el que se cambia la clave)
        if is_self_reset:
             self.session.master_key = self.security.derive_keke(new_password, new_v_salt)
             self.session.personal_key = target_personal_key
             self.users.db.execute("UPDATE users SET password_hash = ?, salt = ?, vault_salt = ?, protected_key = ? WHERE UPPER(username) = ?",
                                  (new_hash, new_salt, sqlite3.Binary(new_v_salt), sqlite3.Binary(new_protected_key), target_username.upper()))
             # También actualizar acceso local
             for v_id, w_key, lvl in rehashed_vaults:
                  self.users.save_vault_access(v_id, w_key, access_level=lvl, synced=1, force=True)
             self.users.db.commit()

        self.log_event("ADMIN_RESET_PASSWORD", details=f"Identity and vaults for {target_username} rotated via Admin Console.")


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
        [SENIOR REPAIR PROTOCOL]
        Rescues both Personal key and Vault keys using the OLD password and re-wraps them 
        with the NEW password, updating legacy and multi-tenant tables.
        """
        try:
            logger.info(f"[Forensic] Starting FULL REPAIR protocol for {username}...")
            
            # 1. Environment Setup
            self.reconnect(username)
            profile = self.get_local_user_profile(username)
            
            if not profile:
                return False, "No se encontró perfil local para este usuario."

            # Salts
            v_salt = self.security.ensure_bytes(profile.get("vault_salt"))
            meta_salt = self.security.ensure_bytes(self.get_meta("master_salt"))
            salts_to_try = [v_salt] if v_salt else []
            if meta_salt: salts_to_try.append(meta_salt)
            
            # 2. PERSONAL KEY REPAIR (Protected Key)
            rescued_personal = None
            p_key_blob = self.security.ensure_bytes(profile.get("protected_key"))
            
            if p_key_blob and len(p_key_blob) >= 28:
                nonce = p_key_blob[:12]
                ciphertext = p_key_blob[12:]
                for salt in salts_to_try:
                    try:
                        old_kek = CryptoEngine.derive_kek_from_password(old_password, salt, iterations=100_000)
                        rescued_personal = AESGCM(old_kek).decrypt(nonce, ciphertext, None)
                        logger.info("[Forensic] Personal key rescued!")
                        break
                    except: continue

            # 3. VAULT KEY REPAIR (Wrapped Vault Key)
            rescued_vault = None
            v_key_blob = self.security.ensure_bytes(profile.get("wrapped_vault_key"))
            
            if v_key_blob and len(v_key_blob) >= 28:
                for salt in salts_to_try:
                    try:
                        # unwrap_vault_key now returns (key, algorithm)
                        rescued_vault, algo = CryptoEngine.unwrap_vault_key(v_key_blob, old_password, salt)
                        logger.info(f"[Forensic] Vault key rescued using {algo}!")
                        break
                    except: continue

            if not rescued_personal and not rescued_vault:
                return False, "La contraseña ANTERIOR es incorrecta o no hay llaves para rescatar."

            # 4. RE-ENCRYPTION AND STORAGE
            target_salt = v_salt if v_salt else meta_salt
            if not target_salt: target_salt = os.urandom(16)
            
            if rescued_personal:
                new_p_blob = self.security.wrap_key(rescued_personal, new_password, target_salt)
                self.users.update_protected_key(username, new_p_blob)
            
            if rescued_vault:
                new_v_blob = self.security.wrap_key(rescued_vault, new_password, target_salt)
                # Update users table (Legacy)
                self.users.db.execute("UPDATE users SET wrapped_vault_key = ?, vault_salt = ? WHERE UPPER(username) = ?", 
                                     (sqlite3.Binary(new_v_blob), sqlite3.Binary(target_salt), username.upper()))
                # Update vault_access table (Multi-tenant)
                if self.session.current_vault_id:
                    self.users.save_vault_access(self.session.current_vault_id, new_v_blob)
                self.users.db.commit()

            self.log_event("REPAIR_PROTOCOL_FULL", details=f"Full key repair successful for {username}")
            return True, "Acceso reparado exitosamente. Las llaves han sido re-encriptadas."
            
        except Exception as e:
            logger.error(f"[Forensic] Full repair failed: {e}")
            return False, str(e)
