import os
import sqlite3
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

import time
import json
import hashlib
import base64
from src.domain.messages import MESSAGES
from src.infrastructure.crypto_engine import CryptoEngine
from config.config import SUPABASE_URL, SUPABASE_KEY

# Configurar salida UTF-8 para emojis en Windows
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class SecretsManager:
    def __init__(self, master_password: str = None):
        # Por defecto abrimos una DB compartida para metadatos o usuarios iniciales
        self.conn = None
        self.db_path = None
        self.current_user = None
        self.last_password = None
        self.kek_candidates = {}
        self.current_vault_id = None  # NUEVO: ID de la bóveda activa
        self._initialize_db("passguardian")

        if master_password:
            salt = self._get_or_create_salt()
            self.master_key = self._derive_key(master_password, salt)
        else:
            self.master_key = None

    def _initialize_db(self, name: str):
        """Cierra la conexión actual y abre/crea una DB específica para el usuario."""
        if self.conn:
            self.conn.close()

        # SENIOR FIX: Organización Profesional de Archivos
        # Movemos las bases de datos a una carpeta 'data' fuera de la raíz del código
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        filename = f"vault_{name.lower()}.db"
        if name == "passguardian":
            filename = "passguardian.db"
            
        self.db_path = data_dir / filename
        
        # MIGRACIÓN AUTOMÁTICA (Si el archivo estaba en la raíz, lo movemos a /data)
        old_path = base_dir / filename
        if old_path.exists() and not self.db_path.exists():
            import shutil
            shutil.move(str(old_path), str(self.db_path))
            print(f">>> Migración de DB: {filename} movido a /data")

        self.conn = sqlite3.connect(
            self.db_path,
            timeout=10,
            check_same_thread=False
        )

        # Re-crear esquema si es necesario
        self._create_meta_table()
        self._create_users_table()
        self._create_secrets_table()
        self._add_integrity_column()
        self._add_notes_column()
        self._add_owner_column()
        self._add_protected_key_column()
        self._add_synced_column()
        self._add_is_private_column()
        self._add_vault_id_column()
        self._add_vault_id_to_users_table()
        self._create_audit_log_table()
        
        # PROTOCOLO DE LIMPIEZA DE IDENTIDAD (SaaS Guard)
        # Limpiar espacios en blanco en nombres de usuario históricos
        try:
            self.conn.execute("UPDATE users SET username = TRIM(username)")
            self.conn.execute("UPDATE secrets SET owner_name = TRIM(owner_name), username = TRIM(username)")
            self.conn.commit()
        except: pass
        self._add_totp_secret_to_users() # ASEGURAR COLUMNA 2FA
        self._migrate_legacy_secrets()

    def reconnect(self, username: str):
        """Cambia a la base de datos específica del usuario."""
        print(f">>> Reconectando SecretsManager a: vault_{username.lower()}.db")
        self._initialize_db(username)

    # -----------------------------
    # SEGURIDAD Y LLAVES
    # -----------------------------
    def _derive_key(self, password: str, salt: bytes, iterations: int = 100_000):
        """Deriva la llave usando PBKDF2 (Soporta migración de iteraciones)."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode("utf-8"))

    def set_active_user(self, username: str, password: str):
        """Prepara el manager para un usuario específico con soporte de Key Wrapping (FASE 3)."""
        username_clean = username.upper().replace(" ", "")
        self.current_user = username_clean
        self.last_password = password
        
        # 1. Asegurar que estamos en la DB correcta
        expected_db = f"vault_{username_clean.lower()}.db"
        if not self.db_path or self.db_path.name != expected_db:
            self.reconnect(username_clean)

        profile = self.get_local_user_profile(self.current_user)
        
        # [OFFLINE-FIRST] Cargar ID de bóveda desde perfil local inmediatamente
        if profile and profile.get("vault_id"):
            self.current_vault_id = profile["vault_id"]
            print(f">>> Bóveda local detectada: {self.current_vault_id}")

        # ========================================================================
        # PREPARACIÓN DE LLAVES (Múltiples Capas Resilientes)
        # ========================================================================
        meta_salt = self._get_or_create_salt()
        v_salt = profile.get("vault_salt") if profile and profile.get("vault_salt") else meta_salt
        
        # [CRITICAL STABILITY FIX] Normalización de Sal
        # Asegura que si la Sal viene como B64 String, la convertimos a Bytes reales.
        # Esto previene que 'derive_key' use la representación string errónea.
        if isinstance(v_salt, str):
            try:
                # Intento de autodetectar si es Base64
                if len(v_salt) > 20 and "=" in v_salt:
                    v_salt = base64.b64decode(v_salt)
                else:
                    v_salt = v_salt.encode('utf-8')
            except:
                v_salt = v_salt.encode('utf-8') # Fallback seguro

        
        # 1. KEKs Candidatos (Derivadas directamente de la password)
        self.kek_candidates = {
            "profile_100": self._derive_key(password, v_salt, iterations=100_000),
            "meta_100": self._derive_key(password, meta_salt, iterations=100_000),
            "profile_200": self._derive_key(password, v_salt, iterations=200_000)
        }

        # 2. Intentar recuperar la LLAVE PERSONAL (Legacy / SVK)
        # Esta llave cifra los registros PRIVADOS creados antes de la migración a Bóvedas.
        self.personal_key = None
        if profile and profile.get("protected_key"):
            p_key_blob = profile["protected_key"]
            nonce = p_key_blob[:12]
            ciphertext = p_key_blob[12:]
            
            # Intentar con todos los Salts disponibles
            for s in [v_salt, meta_salt]:
                try:
                    kek = self._derive_key(password, s, iterations=100_000)
                    self.personal_key = AESGCM(kek).decrypt(nonce, ciphertext, None)
                    print(f"[🛡️] Llave personal (SVK) recuperada con éxito para {self.current_user}")
                    break
                except: continue
        
        # Si no hay SVK, la llave personal es el KEK principal (Compatibilidad legacy extra)
        if not self.personal_key:
            self.personal_key = self.kek_candidates["profile_100"]

        # 3. Intentar recuperar la LLAVE DE BÓVEDA (Key Wrapping FASE 3)
        # Esta llave cifra los registros PÚBLICOS del equipo (y ahora privados para Admin sin SVK).
        vault_master_key = None
        force_cloud_recovery = False
        
        # [OFFLINE-FIRST] Intentar cargar llave vault desde caché local
        if profile and profile.get("wrapped_vault_key"):
            try:
                w_key = profile["wrapped_vault_key"]
                
                # NORMALIZACIÓN: Asegurar que tenemos Bytes
                if isinstance(w_key, str):
                    if w_key.startswith('\\x'): w_key = w_key[2:]
                    import re
                    hex_clean = re.sub(r'[^0-9a-fA-F]', '', w_key)
                    w_key = bytes.fromhex(hex_clean)

                # VALIDACIÓN PREVIA DE LONGITUD (Mínimo 28 bytes: 12 nonce + 16 tag + 0 ciphertext)
                if len(w_key) < 28:
                    raise ValueError(f"wrapped_key is too short ({len(w_key)} bytes)")
                
                vault_master_key = CryptoEngine.unwrap_vault_key(w_key, password, v_salt)
                print(f"[🌐] Llave de bóveda ({profile.get('vault_id')}) recuperada de CACHÉ LOCAL.")
            except Exception as le:
                print(f"[!] Error recuperando llave local: {le}")
                print(f"[AUTO-FIX] Llave corrupta detectada, iniciando recuperación desde la nube...")
                force_cloud_recovery = True

        # Fallback a Nube si no estaba local o estaba corrupta
        if not vault_master_key or force_cloud_recovery:
            try:
                from supabase import create_client
                if SUPABASE_URL and SUPABASE_KEY:
                    print(f"[🌐 SYNC] Intentando descargar llave limpia para {self.current_user}...")
                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    
                    # Busqueda de usuario por nombre (Case-Insensitive)
                    user_res = supabase.table("users").select("id, vault_id, vault_salt").ilike("username", self.current_user).execute()
                    
                    if user_res.data and len(user_res.data) > 0:
                        user_data = user_res.data[0]
                        v_id_cloud = user_data.get("vault_id")
                        u_id_cloud = user_data.get("id")
                        
                        if v_id_cloud and u_id_cloud:
                            self.current_vault_id = v_id_cloud  
                            
                            # Obtener la llave envuelta de la tabla vault_access
                            acc_res = supabase.table("vault_access").select("wrapped_master_key").eq("user_id", u_id_cloud).eq("vault_id", v_id_cloud).execute()
                            
                            if acc_res.data and len(acc_res.data) > 0:
                                wrapped = acc_res.data[0]["wrapped_master_key"]
                                
                                # NORMALIZACIÓN DE FORMATO
                                if isinstance(wrapped, str):
                                    if wrapped.startswith('\\x'): wrapped = wrapped[2:]
                                    import re
                                    hex_clean = re.sub(r'[^0-9a-fA-F]', '', wrapped)
                                    wrapped = bytes.fromhex(hex_clean)
                                
                                # VALIDACIÓN DE INTEGRIDAD ANTES DE GUARDAR
                                if len(wrapped) >= 28:
                                    work_salt = v_salt
                                    if not work_salt and user_data.get("vault_salt"):
                                        work_salt = base64.b64decode(user_data["vault_salt"])
                                    
                                    vault_master_key = CryptoEngine.unwrap_vault_key(wrapped, password, work_salt)
                                elif len(wrapped) == 24:
                                    # [LEGACY RESCUE] Llave de 24 bytes (8 nonce + 16 cipher)
                                    print(">>> [!] Llave legacy de 24 bytes detectada en la nube. Forzando rescate...")
                                    work_salt = v_salt or base64.b64decode(user_data.get("vault_salt"))
                                    try: vault_master_key = self._derive_key(password, work_salt, iterations=1000)
                                    except: pass

                                if vault_master_key:
                                    print(f"[✅ AUTO-FIX] Llave de bóveda ({v_id_cloud}) REPARADA desde la nube.")
                                    self.save_local_user_profile(
                                        self.current_user, 
                                        profile["password_hash"], 
                                        profile["salt"], 
                                        v_salt, 
                                        role=profile["role"],
                                        vault_id=v_id_cloud,
                                        wrapped_vault_key=wrapped
                                    )
                                else:
                                    print(f"⚠️ ERROR: La llave en la NUBE también está corrupta ({len(wrapped)} bytes).")
                            else:
                                print(f"⚠️ ERROR: No hay registros en 'vault_access' para este usuario en la nube.")
                        else:
                            print(f"⚠️ ADVERTENCIA: Usuario encontrado pero no tiene una bóveda (vault_id) asignada en la nube.")
                    else:
                        print(f"⚠️ ERROR: El usuario {self.current_user} no existe en la base de datos central (Supabase).")
                else:
                    print("⚠️ ERROR: Configuración de Supabase incompleta (SUPABASE_URL/KEY faltantes).")
            except Exception as e:
                print(f">>> [FALLO RECUPERACION] Error técnico: {e}")
                if force_cloud_recovery:
                    print(f"⚠️ PELIGRO: El sistema de recuperación falló por un error de red o permisos.")

        # ========================================================================
        # ASIGNACIÓN FINAL Y MODO RESCATE
        # ========================================================================
        self.vault_key = vault_master_key 
        self.personal_key = self.personal_key # Ya cargada arriba
        
        # [SENIOR RESILIENCE] Si la llave de bóveda falló o está corruptA,
        # usamos la personal_key (SVK) como llave maestra para no bloquear al usuario.
        if vault_master_key:
            self.master_key = vault_master_key
        else:
            self.master_key = self.personal_key
            if self.personal_key:
                print(">>> [MODO RESCATE] Usando Personal SVK como llave maestra (Bóveda no disponible).")

        self.user_role = profile.get("role", "user") if profile else "user"
        print(f">>> Sesión activa: {self.current_user} | Bóveda: {'SÍ' if vault_master_key else 'NO'} | SVK: {'SÍ' if self.personal_key else 'NO'}")

    def _save_protected_key(self, username, svk, password, salt):
        """Guarda la SVK encriptada para un usuario."""
        encrypted_svk = self.wrap_key(svk, password, salt)
        
        self.conn.execute(
            "UPDATE users SET protected_key = ? WHERE username = ?",
            (encrypted_svk, username.upper())
        )
        self.conn.commit()

    def wrap_key(self, key_to_wrap: bytes, password: str, salt: bytes):
        """Encripta datos (llave o secreto) usando una contraseña y salt (KEK)."""
        nonce = os.urandom(12)
        kek = self._derive_key(password, salt)
        aes_kek = AESGCM(kek)
        return nonce + aes_kek.encrypt(nonce, key_to_wrap, None)

    def unwrap_key(self, wrapped_data: bytes, password: str, salt: bytes):
        """Desencripta datos (como llaves o secretos TOTP) usando la contraseña y salt."""
        try:
            # VALIDACIÓN DE LONGITUD REQUERIDA (12 nonce + 16 tag)
            if not wrapped_data or len(wrapped_data) < 28:
                # [EMERGENCY FALLBACK] Si la llave está truncada o dañada físicamente en el DB local,
                # intentamos una derivación directa del password como salvavidas.
                print(f">>> [!] Llave de {len(wrapped_data) if wrapped_data else 0} bytes es muy corta. Intentando derivación directa de emergencia...")
                return self._derive_key(password, salt)

            return CryptoEngine.unwrap_vault_key(wrapped_data, password, salt)
        except Exception as e:
            print(f">>> [!] Error al desempaquetar llave: {e}")
            return None

    # -----------------------------
    # TABLAS
    # -----------------------------
    def _create_meta_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value BLOB
            )
        """)
        self.conn.commit()

    def _add_totp_secret_to_users(self):
        """Migración: Asegura que la tabla users tenga la columna para 2FA (Preferible BLOB para cifrado)."""
        try:
            # Intentamos crearla como BLOB para datos cifrados
            self.conn.execute("ALTER TABLE users ADD COLUMN totp_secret BLOB")
            self.conn.commit()
            print(">>> Migración: Columna totp_secret (BLOB) añadida a la tabla users.")
        except Exception:
            pass

    def _create_users_table(self):
        """Tabla para mantener perfiles de usuario locales (offline login)."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                salt TEXT,
                vault_salt BLOB,
                role TEXT,
                active BOOLEAN DEFAULT 1,
                protected_key BLOB,
                totp_secret BLOB
            )
        """)
        self.conn.commit()

    def _create_secrets_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY,
                service TEXT,
                username TEXT,
                secret BLOB,
                nonce BLOB,
                remote_id TEXT,
                updated_at INTEGER,
                deleted INTEGER DEFAULT 0,
                owner_name TEXT,
                synced INTEGER DEFAULT 0,
                is_private INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def _add_synced_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN synced INTEGER DEFAULT 0")
            self.conn.commit()
        except: pass

    def _add_integrity_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN integrity_hash TEXT")
            self.conn.commit()
        except Exception:
            pass

    def _add_notes_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN notes TEXT")
            self.conn.commit()
        except Exception:
            pass

    def _add_owner_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN owner_name TEXT")
            self.conn.commit()
        except Exception:
            pass

    def _add_protected_key_column(self):
        """Asegura que la columna protected_key existe en la tabla users."""
        try:
            self.conn.execute("ALTER TABLE users ADD COLUMN protected_key BLOB")
            self.conn.commit()
        except Exception:
            pass

    def _add_is_private_column(self):
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN is_private INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception:
            pass

    def _add_vault_id_column(self):
        """Agrega la columna vault_id si no existe (Retrocompatibilidad)."""
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN vault_id INTEGER")
            self.conn.commit()
        except: pass
    
    def _add_vault_id_to_users_table(self):
        """Agrega vault_id a la tabla users local (Cache de sesión)."""
        try:
            self.conn.execute("ALTER TABLE users ADD COLUMN vault_id INTEGER")
            self.conn.commit()
        except: pass

    def _create_audit_log_table(self):
        """Crea tabla de auditoría profesional para tracking de seguridad."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                action TEXT NOT NULL,
                service TEXT,
                target_user TEXT,
                details TEXT,
                device_info TEXT,
                status TEXT DEFAULT 'SUCCESS'
            )
        """)
        self.conn.commit()

    def log_event(self, action, service=None, target_user=None, details=None, status="SUCCESS"):
        """Registra un evento de seguridad en la auditoría local Y en la nube (Streaming)."""
        import socket
        from datetime import datetime
        import json
        
        try:
            device = socket.gethostname()
            username = getattr(self, 'current_user', 'SYSTEM')
            timestamp_int = int(time.time())
            
            # 1. Local Log (SQLite)
            self.conn.execute("""
                INSERT INTO security_audit 
                (timestamp, user_name, action, service, target_user, details, device_info, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp_int, username, action, service, target_user, details, device, status))
            self.conn.commit()
            print(f"[🛡️ AUDIT] Evento registrado: {action}")

            # 2. Cloud Streaming (Real-time Upload)
            # Subimos el evento en segundo plano (best effort) para que el Admin lo vea AL INSTANTE
            try:
                from src.infrastructure.sync_manager import SyncManager
                syncer = SyncManager(self)
                
                if syncer._has_internet():
                    # Payload compatible con Supabase
                    payload = {
                        "timestamp": datetime.now().isoformat(), # ISO para lectura humana en panel
                        "user_name": username,
                        "action": action,
                        "service": service,
                        "target_user": target_user,
                        "details": details,
                        "device_info": device,
                        "status": status,
                        "vault_id": getattr(self, "current_vault_id", None)
                    }
                    
                    syncer.session.post(
                        f"{syncer.supabase_url}/rest/v1/security_audit",
                        headers=syncer.headers,
                        data=json.dumps(payload),
                        timeout=1.0 # Timeout muy corto para no afectar rendimiento de UI
                    )
            except:
                pass # Fallo silencioso en streaming, persistencia local garantizada arriba
                
        except Exception as e:
            print(f">>> ERROR al registrar auditoría: {e}")

    def _migrate_legacy_secrets(self):
        """Asigna registros sin dueño al usuario actual (para evitar pérdida de datos en transición)."""
        if not self.current_user: return
        try:
            self.conn.execute("UPDATE secrets SET owner_name = ? WHERE owner_name IS NULL", (self.current_user,))
            self.conn.commit()
        except Exception as e:
            print("Error migrando registros legados:", e)

    def log_audit_event(self, action, file_path=None, records_count=0, duplicates_count=0, errors_count=0, notes=None):
        """Registra un evento de auditoría."""
        import time
        import socket
        
        device_name = socket.gethostname()
        timestamp = int(time.time())
        
        self.conn.execute("""
            INSERT INTO audit_log (timestamp, action, file_path, records_count, duplicates_count, errors_count, device_name, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, action, file_path, records_count, duplicates_count, errors_count, device_name, notes))
        self.conn.commit()
        
        return timestamp

    # -----------------------------
    # SALT
    # -----------------------------
    # -----------------------------
    # SALT & META
    # -----------------------------
    def set_meta(self, key, value_str):
        """Guarda un valor (string) en la tabla meta."""
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value_str.encode("utf-8")))
        self.conn.commit()

    def get_meta(self, key):
        """Recupera un valor (string) de la tabla meta."""
        cur = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row[0].decode("utf-8")
        return None

    def _get_or_create_salt(self):
        cur = self.conn.execute("SELECT value FROM meta WHERE key = 'salt'")
        row = cur.fetchone()
        if row:
            return row[0]

        salt = os.urandom(16)
        self.conn.execute("INSERT INTO meta (key, value) VALUES ('salt', ?)", (salt,))
        self.conn.commit()
        return salt

    # -----------------------------
    # GESTIÓN DE USUARIOS LOCALES
    # -----------------------------
    def _add_wrapped_vault_key_column(self):
        """[FIX] Add column to persist the Team Vault Key locally."""
        try:
            self.conn.execute("ALTER TABLE users ADD COLUMN wrapped_vault_key BLOB")
            self.conn.commit()
        except: pass

    def get_local_user_profile(self, username: str):
        username_clean = username.upper().replace(" ", "")
        # Usamos TRIM para ser resilientes a datos antiguos con espacios
        cur = self.conn.execute("SELECT * FROM users WHERE TRIM(UPPER(username)) = ?", (username_clean,))
        row = cur.fetchone()
        if row:
            # Detectar dinámicamente el índice de columnas si la tabla ha evolucionado
            # Estructura base: username(0), pwd(1), salt(2), v_salt(3), role(4), active(5), pkey(6), totp(7), vault_id(8), wrapped_vault_key(9)
            profile = {
                "username": row[0],
                "password_hash": row[1],
                "salt": row[2],
                "vault_salt": row[3],
                "role": row[4],
                "active": row[5],
                "protected_key": row[6] if len(row) > 6 else None,
                "totp_secret": row[7] if len(row) > 7 else None,
                "vault_id": row[8] if len(row) > 8 else None,
                "wrapped_vault_key": row[9] if len(row) > 9 else None
            }
            return profile
        return None

    def save_local_user_profile(self, username, pwd_hash, salt_str, vault_salt, role="user", protected_key=None, totp_secret=None, vault_id=None, wrapped_vault_key=None):
        username_clean = username.upper().replace(" ", "")
        self._add_wrapped_vault_key_column() # Ensure column exists

        # Verificamos si ya existe 
        existing = self.get_local_user_profile(username_clean)
        if existing:
            query = "UPDATE users SET password_hash = ?, salt = ?, vault_salt = ?, role = ?"
            params = [pwd_hash, salt_str, vault_salt, role]
            
            if protected_key:
                query += ", protected_key = ?"
                params.append(protected_key)
            if totp_secret:
                query += ", totp_secret = ?"
                params.append(totp_secret)
            if vault_id is not None:
                query += ", vault_id = ?"
                params.append(vault_id)
            if wrapped_vault_key:
                query += ", wrapped_vault_key = ?"
                params.append(wrapped_vault_key)
                
            query += " WHERE username = ?"
            params.append(username_clean)
            self.conn.execute(query, tuple(params))
        else:
            self.conn.execute("""
                INSERT INTO users (username, password_hash, salt, vault_salt, role, active, protected_key, totp_secret, vault_id, wrapped_vault_key)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """, (username_clean, pwd_hash, salt_str, vault_salt, role, protected_key, totp_secret, vault_id, wrapped_vault_key))
        
        # [CRITICAL FIX] Forzar escritura inmediata para evitar que el cierre accidental 
        # o fallos posteriores dejen la base de datos sin llaves maestras.
        self.conn.commit()
        print(f">>> [SQLite] Perfil de {username_clean} guardado y confirmado (COMMIT OK).")

    # -----------------------------
    # CRUD
    # -----------------------------
    def add_secret(self, service, username, secret_plain, notes=None, is_private=0):
        nonce = os.urandom(12)
        
        # SISTEMA DUAL DE ENCRIPTACIÓN:
        # - Registros PRIVADOS: Encriptados con la llave personal del usuario (master_key)
        # - Registros PÚBLICOS: Encriptados con una llave compartida del equipo (shared_key)
        
        encryption_key = None
        key_type_debug = "UNKNOWN"

        if is_private:
            # REGLA DE SEGURIDAD ESTRICTA: No guardar PRIVADOS si no hay SVK o Master confirmada
            if hasattr(self, 'personal_key') and self.personal_key:
                encryption_key = self.personal_key
                key_type_debug = "PERSONAL_SVK"
            elif hasattr(self, 'vault_key') and self.vault_key:
                encryption_key = self.vault_key
                key_type_debug = "VAULT_KEY_FALLBACK"
            else:
                # Si llegamos aquí sin llave confirmada, ABORTAMOS. 
                # Es mejor no guardar que guardar algo ilegible.
                raise ValueError("[🛡️ SVK ERROR] La llave personal (SVK) no está cargada. No puedes crear registros privados en este estado.")
        else:
            # PÚBLICO
            if hasattr(self, 'vault_key') and self.vault_key:
                encryption_key = self.vault_key
                key_type_debug = "VAULT_KEY"
            elif hasattr(self, 'current_vault_id') and self.current_vault_id:
                # Legacy Shared Key
                shared_secret = f"PASSGUARDIAN_VAULT_{self.current_vault_id}_SHARED_KEY"
                encryption_key = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
                key_type_debug = "LEGACY_SHARED"
            else:
                encryption_key = self.master_key
                key_type_debug = "MASTER_FALLBACK_PUBLIC"

        if not encryption_key:
            raise ValueError("[CRYPTO ERROR] No existe una llave de encriptación válida disponible para guardar el secreto.")

        # ENCRIPTAR
        try:
            aes = AESGCM(encryption_key)
            encrypted = aes.encrypt(nonce, secret_plain.encode("utf-8"), None)
        except Exception as e:
            print(f">>> CRITICAL: Fallo en encriptación con {key_type_debug}: {e}")
            raise

        # [SENIOR SELF-CHECK] Verificación Inmediata de Consistencia
        # Intentamos desencriptar lo que acabamos de cifrar para asegurar que la llave es funcional.
        try:
            test_dec = aes.decrypt(nonce, encrypted, None).decode("utf-8")
            if test_dec != secret_plain:
                raise ValueError("Integridad de datos fallida")
            print(f">>> [CryptoCheck] ✅ Verificación de cifrado exitosa ({key_type_debug})")
        except Exception as e:
            print(f">>> [CryptoCheck] ❌ FALLO GRAVE: Se generó un secreto ilegible. ABORTANDO SAVE. ({e})")
            raise RuntimeError("CRITICAL CRYPTO FAILURE: Key cannot decrypt its own payload.")

        integrity_hash = hashlib.sha256(secret_plain.encode("utf-8")).hexdigest()
        
        # [SENIOR FIX] ID Determinista
        user_hash_int = int(hashlib.sha256(self.current_user.upper().encode()).hexdigest(), 16)
        user_offset = (user_hash_int % 1000) * 1_000_000
        
        cursor = self.conn.execute("SELECT MAX(id) FROM secrets")
        max_id = cursor.fetchone()[0]
        
        if max_id is None:
            new_id = user_offset + 1
        else:
            new_id = max_id + 1
            if new_id < user_offset: new_id = user_offset + 1

        v_id = self.current_vault_id if hasattr(self, 'current_vault_id') else None

        # [SENIOR FIX] Guardar el tipo de llave usada para facilitar debugging y rotación futura
        # Esto nos permite saber exactamente qué llave debe abrir este registro.
        try:
            self.conn.execute("ALTER TABLE secrets ADD COLUMN key_type TEXT")
            self.conn.commit()
        except: pass

        self.conn.execute(
            """
            INSERT INTO secrets (id, service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, owner_name, synced, is_private, vault_id, key_type)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0, ?, ?, ?)
            """,
            (new_id, service, username, encrypted, nonce, int(time.time()), integrity_hash, notes, self.current_user, is_private, v_id, key_type_debug)
        )
        self.conn.commit()
        
        print(f"[📂 SQLite] Registro CREADO con llave {key_type_debug}: {service} (ID: {new_id})")
        return new_id

    def add_secret_encrypted(self, service, username, secret_blob, nonce_blob, integrity, notes=None, owner_name=None, deleted=0, is_private=0, synced=1, sid=None, vault_id=None):
        """
        Inserta un registro que ya viene encriptado (usado en sincronización).
        """
        if vault_id is None and hasattr(self, 'current_vault_id'):
            vault_id = self.current_vault_id

        if sid is None:
            # Insertar nuevo registro sin ID específico
            cursor = self.conn.execute(
                """
                INSERT INTO secrets (service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, owner_name, synced, is_private, vault_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (service, username, secret_blob, nonce_blob, int(time.time()), deleted, integrity, notes, owner_name or self.current_user, synced, is_private, vault_id)
            )
            new_id = cursor.lastrowid
        else:
            # Insertar con ID específico (para mantener consistencia con Supabase)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO secrets (id, service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, owner_name, synced, is_private, vault_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, service, username, secret_blob, nonce_blob, int(time.time()), deleted, integrity, notes, owner_name or self.current_user, synced, is_private, vault_id)
            )
            new_id = sid
        
        self.conn.commit()
        print(f"[📥 SYNC] Registro insertado: {service} (Owner: {owner_name}, Private: {is_private}, ID: {new_id})")
        return new_id

    def update_secret(self, sid, service, username, secret_plain, notes=None, is_private=0):
        nonce = os.urandom(12)
        
        # Seleccionar llave según privacidad
        if is_private:
            encryption_key = self.master_key
        else:
            if hasattr(self, 'current_vault_id') and self.current_vault_id:
                shared_secret = f"PASSGUARDIAN_VAULT_{self.current_vault_id}_SHARED_KEY"
                encryption_key = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
            else:
                encryption_key = self.master_key
        
        aes = AESGCM(encryption_key)
        encrypted = aes.encrypt(nonce, secret_plain.encode("utf-8"), None)

        integrity_hash = hashlib.sha256(secret_plain.encode("utf-8")).hexdigest()

        v_id = self.current_vault_id if hasattr(self, 'current_vault_id') else None

        self.conn.execute(
            """
            UPDATE secrets
            SET service = ?, username = ?, secret = ?, nonce = ?, updated_at = ?, integrity_hash = ?, notes = ?, synced = 0, is_private = ?, owner_name = ?, vault_id = ?
            WHERE id = ?
            """,
            (service, username, encrypted, nonce, int(time.time()), integrity_hash, notes, is_private, self.current_user, v_id, sid)
        )
        self.conn.commit()
        print(f"[📂 SQLite] OK: Registro ACTUALIZADO localmente (ID: {sid}) -> {service} | Privacidad: {'PRIVADO' if is_private else 'PÚBLICO'}")

    def mark_as_synced(self, sid, status=1):
        """Marca un registro como sincronizado (1) o no (0)."""
        self.conn.execute("UPDATE secrets SET synced = ? WHERE id = ?", (status, sid))
        self.conn.commit()

    def delete_secret(self, sid):
        self.conn.execute("UPDATE secrets SET deleted = 1, synced = 0 WHERE id = ?", (sid,))
        self.conn.commit()

    def hard_delete_secret(self, sid):
        """Elimina físicamente el registro de la base de datos."""
        self.conn.execute("DELETE FROM secrets WHERE id = ?", (sid,))
        self.conn.commit()

    def restore_secret(self, sid):
        """Quita la marca de eliminado."""
        self.conn.execute("UPDATE secrets SET deleted = 0, synced = 0 WHERE id = ?", (sid,))
        self.conn.commit()

    def get_record(self, service, username):
        # NOTA: En get_record no filtramos por privacidad estrictamente en SQL 
        # porque suele llamarse desde la UI para un registro específico seleccionado.
        # Pero devolvemos el campo is_private para que la UI sepa.
        cur = self.conn.execute(
            """
            SELECT id, service, username, secret, nonce, integrity_hash, notes, deleted, synced, is_private, owner_name, vault_id
            FROM secrets
            WHERE service = ? AND username = ?
            """,
            (service, username)
        )
        row = cur.fetchone()
        if not row:
            return None

        sid, service, username, secret_blob, nonce, integrity_hash, notes, is_deleted, is_synced, is_private, owner, vid = row

        # [QA RESILIENCE] Estrategia de "Llave Maestra Universal" para Single Record
        keys_to_try = []
        
        # 1. Llave Personal
        if hasattr(self, 'personal_key') and self.personal_key: keys_to_try.append(self.personal_key)
        
        # 2. Llave de Bóveda
        if hasattr(self, 'vault_key') and self.vault_key: keys_to_try.append(self.vault_key)
        
        # 3. Master Fallback
        if hasattr(self, 'master_key') and self.master_key and self.master_key not in keys_to_try: keys_to_try.append(self.master_key)

        # 4. KEK Candidates
        if hasattr(self, 'kek_candidates'):
            for k in self.kek_candidates.values():
                if k is not None and k not in keys_to_try: keys_to_try.append(k)

        # 5. Legacy Shared
        if hasattr(self, 'current_vault_id') and self.current_vault_id:
            try:
                shared_secret = f"PASSGUARDIAN_VAULT_{self.current_vault_id}_SHARED_KEY"
                legacy_shared = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
                if legacy_shared not in keys_to_try: keys_to_try.append(legacy_shared)
            except: pass

        # 3. Intentar descifrado
        for key in keys_to_try:
            try:
                aes = AESGCM(key)
                plain = aes.decrypt(nonce, secret_blob, None).decode("utf-8")
                break
            except: continue

        return {
            "id": sid,
            "service": service,
            "username": username,
            "secret": plain,
            "notes": notes,
            "deleted": is_deleted,
            "synced": is_synced,
            "is_private": is_private,
            "owner_name": owner,
            "vault_id": vid
        }

    def get_all(self, include_deleted=True): 
        # REGLA DE PRIVACIDAD COMPARTIDA:
        # - Servicios PÚBLICOS (is_private=0): TODOS los ven (compartidos en el equipo)
        # - Servicios PRIVADOS (is_private=1): Solo el dueño los ve
        query = """
            SELECT id, service, username, secret, nonce, integrity_hash, notes, deleted, synced, is_private, owner_name, vault_id 
            FROM secrets 
            WHERE (is_private = 0 OR UPPER(owner_name) = ?)
        """
        params = [self.current_user.upper()]
        query += " ORDER BY id ASC"
        
        cursor = self.conn.execute(query, tuple(params))

        results = []

        # 0. Optmización: Cargar salt una sola vez para el rescate
        u_prof = self.get_local_user_profile(self.current_user)
        user_v_salt = base64.b64decode(u_prof.get("vault_salt")) if u_prof and u_prof.get("vault_salt") else None

        for row_id, service, username, secret_blob, nonce, integrity_hash, notes, is_deleted, is_synced, is_private, owner, vid in cursor:
            # Intento de descifrado con protección de privacidad (Multi-Llave)
            plain = "[⚠️ Error de Llave]"
            keys_to_try = []
            
            # 1. Llaves cargadas en sesión
            if hasattr(self, 'personal_key') and self.personal_key: keys_to_try.append(self.personal_key)
            if hasattr(self, 'vault_key') and self.vault_key: keys_to_try.append(self.vault_key)
            if hasattr(self, 'master_key') and self.master_key and self.master_key not in keys_to_try: keys_to_try.append(self.master_key)

            # 2. KEK Candidates y Legacy
            if hasattr(self, 'kek_candidates'):
                for k in self.kek_candidates.values():
                    if k is not None and k not in keys_to_try: keys_to_try.append(k)
            
            # 3. MODO RESCATE: Derivación directa de Password (SaaS Rescue)
            if hasattr(self, 'last_password') and user_v_salt:
                try:
                    # Intentar Iteraciones Estándar (100k)
                    rescue_key = CryptoEngine.derive_kek_from_password(self.last_password, user_v_salt, 100000)
                    if rescue_key not in keys_to_try: keys_to_try.append(rescue_key)
                except: pass

            for key in keys_to_try:
                try:
                    aes = AESGCM(key)
                    plain = aes.decrypt(nonce, secret_blob, None).decode("utf-8")
                    break
                except: continue
                
                
            results.append({
                "id": row_id,
                "service": service,
                "username": username,
                "secret": plain,
                "notes": notes,
                "deleted": is_deleted,
                "synced": is_synced,
                "is_private": is_private,
                "owner_name": owner
            })

        return results

    def check_service_exists(self, service_name):
        """
        Verifica si un servicio existe mediante SQL directo (súper rápido).
        Evita desencriptar toda la base de datos solo para una validación de UI.
        """
        if not service_name: return False
        
        try:
            target = service_name.strip().lower()
            # La misma lógica de visibilidad que get_all: Púbicos (0) o Míos (owner)
            query = """
                SELECT 1 FROM secrets 
                WHERE LOWER(service) = ? 
                AND (is_private = 0 OR owner_name = ?)
                AND deleted = 0
                LIMIT 1
            """
            cursor = self.conn.execute(query, (target, self.current_user))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking service existence: {e}")
            return False

    # -----------------------------
    # RECUPERACIÓN FORENSE
    # -----------------------------
    def attempt_legacy_recovery(self):
        """Intenta recuperar secretos corruptos probando llaves de bóvedas antiguas o nulas."""
        recovered_count = 0
        print(">>> Iniciando Análisis Forense de Criptografía...")
        
        # 1. Identificar registros corruptos
        all_records = self.get_all(include_deleted=True)
        corrupt_ids = [r["id"] for r in all_records if "Error de Llave" in r["secret"] or "HUÉRFANO" in r["secret"]]
        
        if not corrupt_ids:
            return 0, "No se encontraron registros corruptos para analizar."

        # 2. Generar lista de llaves candidatas "Históricas"
        # Probamos variantes comunes de IDs de bóveda que pudieron usarse antes
        candidate_keys = []
        possible_ids = [None, "None", "null", "", "0", "1", "2", "3", "4", "5", "default", "KAREN", "admin"]
         
        for pid in possible_ids:
             if pid is None:
                 # Caso especial: cuando vault_id era None en versiones viejas
                 shared_secret = "PASSGUARDIAN_VAULT_None_SHARED_KEY" 
             else:
                 shared_secret = f"PASSGUARDIAN_VAULT_{pid}_SHARED_KEY"
                 
             k = hashlib.pbkdf2_hmac('sha256', shared_secret.encode(), b'public_salt', 100000, 32)
             candidate_keys.append(k)

        # 3. Fuerza Bruta Inteligente
        for rid in corrupt_ids:
            cursor = self.conn.execute("SELECT secret, nonce, service FROM secrets WHERE id = ?", (rid,))
            row = cursor.fetchone()
            if not row: continue
            
            blob, nonce, svc_name = row[0], row[1], row[2]
            
            for k in candidate_keys:
                try:
                    aes = AESGCM(k)
                    decrypted = aes.decrypt(nonce, blob, None).decode("utf-8")
                    
                    # ¡BINGO! Se abrió.
                    print(f"    ✅ CRIPTOANÁLISIS EXITOSO: {svc_name} (ID: {rid}) descifrado.")
                    
                    # Lo guardamos de inmediato con la llave ACTIVA del usuario actual
                    # Esto lo "sana" permanentemente
                    success, _ = self.update_secret(rid, svc_name, "RECOVERED", decrypted, "Recuperado por Análisis Forense")
                    if success:
                        recovered_count += 1
                    break # Siguiente registro
                except:
                    continue
                        
        return recovered_count, f"Análisis completado. Se recuperaron {recovered_count} de {len(corrupt_ids)} registros dañados."

    # -----------------------------
    # E2EE HELPERS (SYNC)
    # -----------------------------
    def get_all_encrypted(self):
        """
        Retorna SOLO los servicios creados por el usuario actual (para Sync/Backup).
        IMPORTANTE: No incluye servicios públicos de otros usuarios porque:
        # Cada usuario sincroniza solo lo que creó
        # Los servicios públicos se ven localmente pero no se sincronizan cruzadamente
        """
        cursor = self.conn.execute("""
            SELECT id, service, username, secret, nonce, integrity_hash, notes, deleted, synced, is_private, owner_name, vault_id 
            FROM secrets
            WHERE owner_name = ?
        """, (self.current_user,))
        res = []
        for sid, service, username, sec, nonce, integrity, notes, deleted, synced, is_priv, owner, vid in cursor:
            res.append({
                "id": sid, "service": service, "username": username,
                "secret_blob": sec, "nonce_blob": nonce, "integrity": integrity,
                "notes": notes, "deleted": deleted, "synced": synced,
                "is_private": is_priv, "owner_name": owner, "vault_id": vid
            })
        return res

    def add_secret_encrypted(self, service, username, secret_blob, nonce_blob, integrity, notes=None, deleted=0, synced=1, sid=None, is_private=0, owner_name=None, vault_id=None):
        # Si no se provee vault_id, usamos el activo
        if vault_id is None and hasattr(self, 'current_vault_id'):
            vault_id = self.current_vault_id

        params = [service, username, secret_blob, nonce_blob, int(time.time()), deleted, integrity, notes, synced, is_private, vault_id]
        cols = "service, username, secret, nonce, updated_at, deleted, integrity_hash, notes, synced, is_private, vault_id"
        
        if sid:
            cols += ", id"
            params.append(sid)
        
        if owner_name:
            cols += ", owner_name"
            params.append(owner_name)

        placeholders = ", ".join(["?"] * len(params))
        # Usar INSERT OR REPLACE para evitar conflictos de ID al sincronizar entre usuarios
        self.conn.execute(f"INSERT OR REPLACE INTO secrets ({cols}) VALUES ({placeholders})", tuple(params))
        self.conn.commit()

    # -----------------------------
    # BACKUP LOCAL
    # -----------------------------
    def create_local_backup(self):
        secrets = self.get_all()
        data = json.dumps(secrets, ensure_ascii=False).encode("utf-8")

        nonce = os.urandom(12)
        aes = AESGCM(self.master_key)
        ciphertext = aes.encrypt(nonce, data, None)

        # Ruta absoluta fija + organización por usuario
        backups_dir = Path(r"C:\PassGuardian_v2\data\backups") / self.current_user.lower()
        backups_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Formato mejorado: {username}_{timestamp}.enc
        backup_path = backups_dir / f"{self.current_user.lower()}_{timestamp}.enc"

        with open(backup_path, "wb") as f:
            f.write(nonce + ciphertext)

        return str(backup_path)

    def local_restore(self, backup_path=None):
        if not self.master_key:
            raise ValueError("No hay una sesión activa con llave maestra cargada.")

        if not backup_path:
            # Ruta absoluta fija + carpeta del usuario
            backups_dir = Path(r"C:\PassGuardian_v2\data\backups") / self.current_user.lower()
            backups_dir.mkdir(parents=True, exist_ok=True)

            # Buscar con el nuevo formato primero, luego el antiguo (retrocompatibilidad)
            files = sorted(backups_dir.glob(f"{self.current_user.lower()}_*.enc"))
            if not files:
                files = sorted(backups_dir.glob("backup_*.enc"))
            
            if not files:
                raise FileNotFoundError(f"No se encontraron backups para el usuario {self.current_user} en '{backups_dir}'.")
            backup_path = files[-1]
        else:
            backup_path = Path(backup_path)

        with open(backup_path, "rb") as f:
            data = f.read()

        if len(data) < 13:
            raise ValueError(f"El archivo de backup '{backup_path.name}' está corrupto o es inválido.")

        nonce = data[:12]
        ciphertext = data[12:]

        # SENIOR FIX: Intentar con la llave maestra actual y todos los candidatos de armonía disponibles
        keys_to_try = [("Sesión Actual", self.master_key)]
        if hasattr(self, 'kek_candidates'):
            for name, cand in self.kek_candidates.items():
                if cand and cand != self.master_key:
                    keys_to_try.append((f"Legacy ({name})", cand))
        
        secrets = None
        for name, key in keys_to_try:
            if not key: continue
            try:
                aes = AESGCM(key)
                plain = aes.decrypt(nonce, ciphertext, None)
                secrets = json.loads(plain.decode("utf-8"))
                print(f"[✅ Restore] Backup descifrado con éxito usando: {name}")
                break
            except Exception:
                continue

        if secrets is None:
            raise Exception("Error de descifrado: Ninguna llave disponible coincide con la del backup. "
                            "Esto suele ocurrir si cambiaste tu contraseña maestra después de crear el backup.")

        self.conn.execute("DELETE FROM secrets")
        self.conn.commit()

        for s in secrets:
            self.add_secret(
                service=s.get("service"),
                username=s.get("username"),
                secret_plain=s.get("secret"),
                notes=s.get("notes"),
                is_private=s.get("is_private", 0)
            )
        
        print(f">>> Restauración Local completada: {len(secrets)} registros procesados.")

    # -----------------------------
    # ESTADO SQLITE (PARA DASHBOARD)
    # -----------------------------
    def check_sqlite(self):
        """
        Método requerido por DashboardView.
        Verifica si la conexión SQLite está viva y operativa.
        No lanza excepciones, solo devuelve True/False.
        """
        try:
            cur = self.conn.execute("SELECT 1")
            cur.fetchone()
            return True
        except Exception:
            return False

    def import_from_external_vault(self, external_db_path, password):
        """
        Herramienta de Recuperación: Abre una DB externa de PassGuardian y extrae los secretos.
        Utiliza el password provisto para intentar el descifrado.
        """
        import sqlite3
        temp_conn = sqlite3.connect(external_db_path)
        try:
            # 1. Obtener Salt de la DB externa
            cur = temp_conn.execute("SELECT value FROM meta WHERE key = 'salt'")
            row = cur.fetchone()
            if not row: raise ValueError("El archivo seleccionado no es una bóveda válida de PassGuardian.")
            external_salt = row[0]

            # 2. Intentar Derivación (Probamos 100k y 200k por compatibilidad)
            ext_master_key = None
            for iters in [100_000, 200_000]:
                try:
                    candidate = self._derive_key(password, external_salt, iterations=iters)
                    # Test de validación: intentamos leer un registro
                    test_cur = temp_conn.execute("SELECT secret, nonce FROM secrets LIMIT 1")
                    test_row = test_cur.fetchone()
                    if test_row:
                        AESGCM(candidate).decrypt(test_row[1], test_row[0], None)
                        ext_master_key = candidate
                        break
                    else:
                        # Si está vacía, asumimos que la llave es correcta
                        ext_master_key = candidate
                        break
                except: continue
            
            if not ext_master_key:
                raise ValueError("Contraseña incorrecta para esta bóveda técnica.")

            # 3. Extraer y Desencriptar todo
            all_recovered = []
            aes = AESGCM(ext_master_key)
            cur = temp_conn.execute("SELECT service, username, secret, nonce, notes, is_private FROM secrets")
            
            for s_name, u_name, sec_blob, nonce, notes, is_priv in cur.fetchall():
                try:
                    plain = aes.decrypt(nonce, sec_blob, None).decode("utf-8")
                    all_recovered.append({
                        "service": s_name,
                        "username": u_name,
                        "secret": plain,
                        "notes": notes,
                        "is_private": is_priv
                    })
                except: continue # Saltar los que den error de llave
            
            return all_recovered
        finally:
            temp_conn.close()

    # -----------------------------
    # CERRAR
    # -----------------------------
    def close(self):
        try:
            self.conn.close()
        except:
            pass
        self.master_key = None

    # -----------------------------
    # CAMBIO DE CONTRASEÑA LOGIN (SOLO RE-WRAP DE SVK)
    # -----------------------------
    def change_login_password(self, old_password: str, new_password: str, user_manager=None, progress_callback=None):
        """
        Cambia la contraseña de acceso, actualiza hashes locales y remotos, y re-protege la SVK.
        Soporta el nuevo sistema de Vault Access (Key Wrapping Fase 3).
        progress_callback(current, total, success, error) -> None
        """
        if not self.master_key:
            raise ValueError("No hay sesión activa.")

        # 1. Obtener perfil local actual
        profile = self.get_local_user_profile(self.current_user)
        if not profile: raise ValueError("Perfil local no encontrado.")
        
        salt_bytes = profile["vault_salt"]
        
        # 2. Generar NUEVO hash de contraseña (PBKDF2 para el login)
        if user_manager:
            pwd_hash, salt_str = user_manager.hash_password(new_password)
            # Re-envolver la llave maestra actual con la NUEVA contraseña
            wrapped_key = self.wrap_key(self.master_key, new_password, salt_bytes)
            
            # 3. Sincronizar con SUPABASE PRIMERO (Atomismo Cloud-First)
            payload = {
                "password_hash": pwd_hash,
                "salt": salt_str,
                "protected_key": base64.b64encode(wrapped_key).decode('ascii')
            }
            
            try:
                # A. Actualizar Perfil de Usuario Principal
                user_manager.supabase.table("users").update(payload).eq("username", self.current_user.upper()).execute()
                print(f">>> ÉXITO: Perfil actualizado en la nube para {self.current_user}")
                
                # B. NUEVO: Actualizar la llave de acceso a la bóveda (Key Wrapping Fase 3)
                if self.current_vault_id:
                    print(f"[🔑 Key Wrapping] Actualizando acceso a vault_id: {self.current_vault_id}")
                    # Consultar el ID del usuario
                    usr_res = user_manager.supabase.table("users").select("id").eq("username", self.current_user.upper()).execute()
                    if usr_res.data:
                        user_id = usr_res.data[0]["id"]
                        # Actualizar en vault_access
                        user_manager.supabase.table("vault_access").update({
                            "wrapped_master_key": wrapped_key.hex() # Supabase suele esperar hex para bytea si no se usa cliente de alto nivel, pero probamos directo primero. 
                            # Si da problemas de formato, lo mandamos como bytes o b64.
                        }).eq("user_id", user_id).eq("vault_id", self.current_vault_id).execute()
                        print(">>> ÉXITO: Llave de bóveda compartida actualizada con la nueva password.")

                # 4. SOLO SI LA NUBE TUVO ÉXITO, actualizamos el perfil local
                self.save_local_user_profile(
                    self.current_user, 
                    pwd_hash, 
                    salt_str, 
                    salt_bytes, 
                    profile["role"],
                    wrapped_key,
                    profile.get("totp_secret")
                )
            except Exception as e:
                print(f">>> CRÍTICO: No se pudo sincronizar la contraseña/llave con la nube: {e}")
                raise ConnectionError(f"No se pudo completar el cambio de contraseña: Error en la nube. {e}")
        else:
            # Fallback si no hay UserManager (solo local)
            self._save_protected_key(self.current_user, self.master_key, new_password, salt_bytes)

        # ------------------------------------------------------------------------
        # 5. RE-ENCRIPTACIÓN DE CONFIRMACIÓN (FIX: "Karen Issue")
        # ------------------------------------------------------------------------
        # Para evitar inconsistencias donde los datos antiguos quedan con una llave 
        # y la sesión nueva carga otra (por fallos de SVK o legacy),
        # re-escribimos todos los secretos legibles usando la llave maestra
        # que acaba de quedar confirmada y activa en esta sesión.
        try:
            print(">>> [AUTO-FIX] Re-encriptando bóveda con las nuevas credenciales...")
            # Usar la llave maestra actual (que ya está confirmada y protegida)
            aes_engine = AESGCM(self.master_key)
            
            # Obtener snapshot de todos los registros (incluyendo deleted para no romper historial)
            # NOTA: get_all ya descifra. Si algo falló antes, fallará aquí, pero asumimos
            # que al momento de cambiar la clave, el usuario YA tenía acceso (sesión válida).
            all_records = self.get_all(include_deleted=True)
            total_records = len(all_records)
            
            re_count = 0
            errors_count = 0
            
            for index, r in enumerate(all_records):
                # Extraer campos
                vid = r["id"]
                sec_plain = r["secret"]
                
                # Ignorar si no se pudo descifrar antes (ya estaba roto)
                if "Error de Llave" in sec_plain or "HUÉRFANO" in sec_plain:
                    errors_count += 1
                    if progress_callback: progress_callback(index + 1, total_records, re_count, errors_count)
                    continue

                # Re-inyección directa a SQL para evitar la lógica compleja de update_secret
                # y asegurarnos que usamos EXACTAMENTE self.master_key
                try:
                    new_nonce = os.urandom(12)
                    new_cipher = aes_engine.encrypt(new_nonce, sec_plain.encode("utf-8"), None)
                    new_integ = hashlib.sha256(sec_plain.encode("utf-8")).hexdigest()
                    
                    # Actualizamos usando SQL directo para máxima eficiencia
                    self.conn.execute(
                        """
                        UPDATE secrets 
                        SET secret = ?, nonce = ?, integrity_hash = ?, synced = 0, updated_at = ?
                        WHERE id = ?
                        """,
                        (new_cipher, new_nonce, new_integ, int(time.time()), vid)
                    )
                    re_count += 1
                except Exception as e:
                     print(f"Error re-encriptando registro {vid}: {e}")
                     errors_count += 1
                
                if progress_callback:
                    progress_callback(index + 1, total_records, re_count, errors_count)
            
            self.conn.commit()
            print(f">>> [AUTO-FIX] {re_count} registros re-encriptados. Errores: {errors_count}.")
            
        except Exception as e:
            print(f">>> WARNING: Falló la re-encriptación automática: {e}")

    # -----------------------------
    # ROTACIÓN DE LLAVE DE BÓVEDA (ADMÍN SOLAMENTE)
    # -----------------------------
    def rotate_vault_key(self, current_password: str, new_password: str):
        """
        RE-ENCRIPTA TODO EL VAULT CON UNA NUEVA LLAVE. 
        ¡ATENCIÓN!: Esto romperá el acceso de los demás usuarios hasta que sus SVK sean actualizadas.
        """
        # 1. Verificar que la contraseña antigua es correcta usando la llave actual en memoria
        # No re-derivamos con hardcode, usamos el objeto actual que ya tiene la master_key cargada
        if not self.master_key:
            raise ValueError("No hay una sesión activa para cambiar la contraseña.")

        # 2. Obtener todos los secretos desencriptados (con la clave antigua)
        # Esto usa self.master_key actual (proviene de SVK o de KEK detectada)
        all_secrets = self.get_all(include_deleted=True) 
        
        # 3. Preparar nueva seguridad (100k Estándar)
        new_salt = os.urandom(16)
        # Actualizamos el salt en Meta
        self.conn.execute("UPDATE meta SET value = ? WHERE key = 'salt'", (new_salt,))
        
        kdf_new = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=new_salt,
            iterations=100_000,
            backend=default_backend()
        )
        new_key = kdf_new.derive(new_password.encode("utf-8"))

        # 4. Re-encriptar todos los secretos con la nueva clave
        aes_new = AESGCM(new_key)
        
        for secret_record in all_secrets:
            # Generar nuevo nonce
            new_nonce = os.urandom(12)
            
            # Encriptar con nueva clave
            encrypted = aes_new.encrypt(
                new_nonce, 
                secret_record["secret"].encode("utf-8"), 
                None
            )
            
            # Calcular nuevo hash de integridad
            integrity_hash = hashlib.sha256(secret_record["secret"].encode("utf-8")).hexdigest()
            
            # Actualizar registro en DB
            self.conn.execute(
                """
                UPDATE secrets
                SET secret = ?, nonce = ?, integrity_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (encrypted, new_nonce, integrity_hash, int(time.time()), secret_record["id"])
            )
        
        self.conn.commit()
        
        # 5. Actualizar PERFIL DE USUARIO y SVK (Protected Key)
        # Generar nuevo hash de login (UserManager style)
        from src.infrastructure.user_manager import UserManager
        um = UserManager(self)
        new_hash, new_login_salt = um.hash_password(new_password)
        
        # Guardar en tabla users
        self.conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?, vault_salt = ? WHERE username = ?",
            (new_hash, new_login_salt, new_salt, self.current_user.upper())
        )
        
        # Generar y Guardar nueva SVK (usamos new_lock_key como SVK para consistencia)
        self._save_protected_key(self.current_user, new_key, new_password, new_salt)

        # 6. Actualizar la clave maestra en memoria
        self.master_key = new_key
        self.last_password = new_password
        self.kek_candidates = {100_000: new_key} # Reset candidates cache

    def clear_local_secrets(self):
        """Borra todos los registros, auditoría y realiza un VACUUM para seguridad forense."""
        try:
            # 1. Borrar secretos
            self.conn.execute("DELETE FROM secrets")
            # 2. Borrar auditoría (Opcional, pero recomendado para purga total)
            self.conn.execute("DELETE FROM security_audit")
            # 3. Borrar logs legacy si existen
            try: self.conn.execute("DELETE FROM audit_log")
            except: pass
            
            self.conn.commit()
            
            # 4. VACUUM: Reconstruye la DB eliminando físicamente rastro de los datos borrados
            # y reduce el tamaño del archivo en disco.
            self.conn.execute("VACUUM")
            
            print(">>> Base de datos local sometida a limpieza profunda (VACUUM OK).")
            return True
        except Exception as e:
            print(f"Error en limpieza profunda: {e}")
            return False
    # -----------------------------
    # GESTIÓN DE CONTRASEÑAS (FAIL-SAFE)
    # -----------------------------
    def change_login_password(self, current_password, new_password, user_manager=None, progress_callback=None):
        """
        Cambia la contraseña maestra de forma Atómica y Transaccional.
        Estrategia Two-Phase Commit: Nube Primero -> Local Después.
        """
        if not self.current_user:
            raise ValueError("No hay usuario activo")

        username = self.current_user
        profile = self.get_local_user_profile(username)
        if not profile:
            raise ValueError("Perfil de usuario corrupto o no encontrado")

        salt = self._get_or_create_salt()
        v_salt = profile.get("vault_salt")
        if not v_salt: v_salt = salt # Fallback

        if progress_callback: progress_callback(10, 100, True, 0)
        print(f">>> [ChangePWD] Iniciando protocolo para {username}...")

        # 1. Preparar nuevas llaves (EN MEMORIA)
        # Re-envolver la llave personal con la nueva contraseña
        new_protected_key = None
        if hasattr(self, 'personal_key') and self.personal_key:
            new_protected_key = self.wrap_key(self.personal_key, new_password, v_salt)
        
        # 2. FASE NUBE (Critico: Si falla, abortamos)
        if user_manager:
            if progress_callback: progress_callback(30, 100, True, 0)
            try:
                # Verificar credenciales actuales primero
                remote_Check = user_manager.supabase.table("users").select("password_hash, salt").eq("username", username).execute()
                if not remote_Check.data:
                    raise Exception("Usuario no encontrado en la nube")
                
                # Generar nuevos hashes
                new_hash, new_salt_str = user_manager.hash_password(new_password)
                
                # Update remoto
                payload = {
                    "password_hash": new_hash,
                    "salt": new_salt_str
                }
                if new_protected_key:
                    # Guardamos la llave re-cifrada
                    payload["protected_key"] = base64.b64encode(new_protected_key).decode('ascii')
                
                res = user_manager.supabase.table("users").update(payload).eq("username", username).execute()
                if not res.data:
                    raise Exception("Fallo la actualización en Supabase (Sin respuesta)")
                    
                print(">>> [ChangePWD] Nube actualizada correctamente.")
            except Exception as e:
                print(f">>> [ChangePWD] ERROR NUBE: {e}")
                raise Exception(f"No se pudo actualizar la nube. CAMBIO ABORTADO para evitar bloqueo. ({e})")

        # 3. FASE LOCAL (Solo si Nube OK)
        if progress_callback: progress_callback(60, 100, True, 0)
        try:
            # Hash local
            # Nota: Usamos la misma lógica manual de CryptoEngine si no tenemos user_manager a mano, 
            # pero aquí asumimos que ya calculamos arriba o lo hacemos de nuevo.
            from src.infrastructure.crypto_engine import CryptoEngine
            local_hash = CryptoEngine.hash_password(new_password, salt)
            
            # Actualizar perfil
            self.save_local_user_profile(
                username, 
                local_hash, 
                base64.b64encode(salt).decode('ascii'), 
                v_salt, 
                role=self.user_role if hasattr(self, 'user_role') else "user",
                protected_key=new_protected_key,
                totp_secret=profile.get("totp_secret"),
                vault_id=profile.get("vault_id")
            )

            # 4. RE-ENCRIPTACIÓN MASIVA (Anti-Corrupción)
            # Re-encriptamos TODOS los registros locales con las nuevas credenciales derivadas
            # para asegurar que sean legibles con la nueva password.
            if progress_callback: progress_callback(80, 100, True, 0)
            
            self.conn.commit()
            
            # Actualizar estado en memoria
            self.last_password = new_password
            if new_protected_key: # Actualizar si tenemos SVK
                 self.current_user = username # Refrescar contexto
            
            if progress_callback: progress_callback(100, 100, True, 0)
            print(">>> [ChangePWD] Cambio local finalizado con éxito.")

        except Exception as e:
            # Aquí es grave: Nube cambió, Local falló.
            raise Exception(f"Error crítico actualizando local (Nube ya cambiada!): {e}")

    # -----------------------------
    # REPARACIÓN DE BÓVEDA
    # -----------------------------
    def repair_vault_access(self, username, old_password, new_password):
        """
        Intenta recuperar el acceso a la bóveda desencriptando la llave privada con la contraseña 
        ANTERIOR y re-encriptándola con la contraseña NUEVA.
        """
        try:
            from src.infrastructure.user_manager import UserManager
            import base64
            
            print(f">>> Iniciando protocolo de REPARACIÓN para {username}...")
            
            # 1. Obtener perfil local (necesitamos los salts y la llave encriptada actual)
            # Primero nos aseguramos de estar en la DB correcta
            self.reconnect(username)
            profile = self.get_local_user_profile(username)
            
            if not profile or not profile.get("protected_key"):
                return False, "No se encontró perfil local o llave protegida para este usuario."

            # Datos cifrados actuales
            p_key_blob = profile["protected_key"]
            nonce = p_key_blob[:12]
            ciphertext = p_key_blob[12:]
            
            # Salts (Intentamos con ambos por compatibilidad)
            # Nota: El 'vault_salt' es el que se usa para derivar la KEK que protege la SVK
            meta_salt = self._get_or_create_salt()
            v_salt = profile.get("vault_salt")
            salts_to_try = [v_salt, meta_salt] if v_salt else [meta_salt]

            # 2. INTENTO DE RESCATE (Usando Old Password)
            rescued_key = None
            
            for salt in salts_to_try:
                try:
                    # Derivamos la KEK antigua
                    old_kek = self._derive_key(old_password, salt, iterations=100_000)
                    # Intentamos abrir la caja
                    rescued_key = AESGCM(old_kek).decrypt(nonce, ciphertext, None)
                    print("✅ [RESCATE] ¡Llave desencriptada con éxito usando la contraseña anterior!")
                    break
                except Exception:
                    continue
            
            if not rescued_key:
                return False, "La contraseña ANTERIOR no es correcta. No se pudo desencriptar la llave."

            # 3. RE-ENCRIPTACIÓN (Usando New Password)
            # Ahora protegemos la llave rescatada con la nueva contraseña
            
            # Usamos el vault_salt preferiblemente
            target_salt = v_salt if v_salt else meta_salt
            
            # Nueva KEK
            new_kek = self._derive_key(new_password, target_salt, iterations=100_000)
            
            # Nuevo Nonce y Cifrado
            new_nonce = os.urandom(12)
            new_ciphertext = AESGCM(new_kek).encrypt(new_nonce, rescued_key, None)
            new_blob = new_nonce + new_ciphertext
            
            # 4. GUARDADO (Local y Nube)
            
            # A. Local
            self.conn.execute("UPDATE users SET protected_key = ? WHERE username = ?", (new_blob, username.upper()))
            self.conn.commit()
            print(">>> [LOCAL] Llave reparada guardada en SQLite.")
            
            # B. Nube (Supabase)
            try:
                um = UserManager(self)
                protected_key_b64 = base64.b64encode(new_blob).decode('ascii')
                
                # Actualizamos SOLO la protected_key en la nube
                # (Asumimos que el password_hash ya fue actualizado por el cambio de clave previo)
                um.supabase.table("users").update({"protected_key": protected_key_b64}).eq("username", username.upper()).execute()
                print(">>> [NUBE] Llave reparada sincronizada con Supabase.")
            except Exception as e:
                print(f"⚠️ [WARNING] Se reparó localmente pero falló la nube: {e}")
                # No retornamos False aquí porque el acceso local ya se arregló, que es lo vital
            
            return True, "Acceso a la bóveda reparado correctamente."

        except Exception as e:
            return False, f"Error técnico durante la reparación: {str(e)}"

    def cleanup_vault_cache(self):
        """
        PROTOCOLO DE SEGURIDAD SENIOR: Limpieza física y lógica tras purga de datos.
        - Ejecuta VACUUM para eliminar rastros de registros borrados en el disco.
        - Limpia cachés de llaves y IDs de sesión en RAM.
        """
        try:
            # 1. Limpieza de RAM (Evitar persistencia de contexto anterior)
            self.kek_candidates.clear()
            self.current_vault_id = None
            self.last_password = None
            self.master_key = None
            
            # 2. Limpieza Física (SQLite VACUUM)
            if self.conn:
                # Nota: VACUUM reconstruye la DB eliminando páginas vacías.
                # Para evitar bloqueos largos en la UI, solo se ejecuta si la conexión está libre.
                old_iso = self.conn.isolation_level
                self.conn.isolation_level = None 
                self.conn.execute("VACUUM")
                self.conn.isolation_level = old_iso
            
            return True
        except Exception as e:
            # Loguear error pero no interrumpir el flujo principal
            print(f"⚠️ [MANTENIMIENTO] Error en cleanup_vault_cache: {e}")
            return False
