import pyotp
from typing import Any, Optional, Tuple, Dict
from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from src.infrastructure.security.device_fingerprint import get_hwid
from src.infrastructure.crypto_engine import CryptoEngine, rate_limit
import base64, secrets, hashlib, re, logging
from src.domain.messages import MESSAGES

class UserManager:
    def __init__(self, secrets_manager=None):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.sm = secrets_manager
        self.logger = logging.getLogger(__name__)

    def sync_vault_name(self, vault_id, name):
        """Sincroniza el nombre de la bóveda con la nube."""
        if not vault_id or not name: return False
        try:
            # Upsert (Insertar o Actualizar)
            # Sincronizar en la tabla que usa UUIDs (vaults)
            self.supabase.table("vaults").upsert({"id": vault_id, "name": name}).execute()
            
            # Intento secundario en vault_groups (Opcional)
            try:
                self.supabase.table("vault_groups").upsert({"vault_name": name}).execute()
            except Exception as e:
                self.logger.warning(f"No se pudo actualizar vault_groups (Opcional): {e}")

            self.logger.info(f"Nombre '{name}' sincronizado en tablas de boveda.")
            return True
        except Exception as e:
            self.logger.error(f"Error sincronizando nombre: {e}")
            return False

    def prepare_for_user(self, username):
        """Prepara el entorno para un usuario específico (cambio de DB local).
        [FIX] Solo reconecta si la base de datos ya existe, evitando crear basura en logins fallidos.
        """
        if not self.sm:
            from src.infrastructure.secrets_manager import SecretsManager
            self.sm = SecretsManager()
            
        from src.infrastructure.config.path_manager import PathManager
        db_path = PathManager.get_user_db(username)
        
        # Solo reconectamos si la base de datos existe localmente.
        # En logins de usuarios nuevos (nube -> local), el sync_user_to_local 
        # o set_active_user se encargarán de la reconexión final.
        if db_path.exists():
            self.sm.reconnect(username)
        else:
            self.logger.debug(f"Postponing DB creation for {username} until successful auth/sync.")

    # ------------------------------------------------------------------
    #  TOTP (2FA)
    # ------------------------------------------------------------------
    def generate_totp_secret(self) -> str:
        """Genera un nuevo secreto aleatorio para 2FA."""
        return pyotp.random_base32()
    
    # ------------------------------------------------------------------
    #  AUTENTICACIÓN Y HASHING (UNIFICADO)
    # ------------------------------------------------------------------
    def _normalize_to_bytes(self, val: Any) -> Optional[bytes]:
        """
        Normaliza cualquier dato (hex string, base64, bytes) a bytes puros.
        Especialmente útil para datos que vienen 'doblemente encodeados' de Supabase.
        """
        if not val: return None
        if isinstance(val, (bytes, bytearray)): return bytes(val)
        
        s = str(val).strip()
        # Caso: Supabase devuelve hex string (\x...)
        if s.startswith("\\x") or s.startswith("\\\\x"):
            hex_data = s[3:] if s.startswith("\\\\x") else s[2:]
            try:
                raw = bytes.fromhex(hex_data)
                # Heurística Senior: ¿Es este binario en realidad un string Base64?
                # Algunos procesos legacy guardan Base64 dentro de un bytea.
                if len(raw) > 0:
                    try:
                        b64_candidate = raw.decode('ascii')
                        if 16 <= len(base64.b64decode(b64_candidate)) <= 64:
                            return base64.b64decode(b64_candidate)
                    except: pass
                return raw
            except: pass

        # Caso: Es Base64 directo
        if re.match(r'^[A-Za-z0-9+/=]+$', s) and len(s) >= 32 and (len(s) % 4 == 0):
            try: return base64.b64decode(s)
            except: pass
        
        return s.encode('utf-8')

    def _normalize_hex(self, val: Any) -> Optional[str]:
        """Limpia prefijos \\x y asegura que el valor sea un string hex puro."""
        if not val: return None
        if isinstance(val, bytes): return val.hex()
        s = str(val).strip()
        if s.startswith("\\x"): s = s[2:]
        if s.startswith("\\\\x"): s = s[3:]
        return s

    def _normalize_salt(self, salt: Any) -> bytes:
        """
        Normaliza el salt a la especificación profesional (16 bytes binarios).
        Soporta: bytes, sqlite3.Binary, hex string, double-escaped hex string.
        """
        if not salt:
            return None # CryptoEngine generará uno nuevo
            
        if isinstance(salt, (bytes, bytearray)):
            return bytes(salt)
            
        s = str(salt).strip()
        # Limpieza de prefijos de Postgres/Supabase (\x)
        if s.startswith("\\x"): s = s[2:]
        if s.startswith("\\\\x"): s = s[3:]
        
        try:
            # Si es un hex string de 32 chars, lo tratamos como bytes de salt (16 bytes)
            # Esto es lo más profesional: el salt REAL son los bytes, no el ASCII del hex.
            if len(s) == 32:
                return bytes.fromhex(s)
            # Fallback seguro para otros formatos
            return s.encode('utf-8')[:16].ljust(16, b'\0')
        except Exception:
            return s.encode('utf-8')[:16].ljust(16, b'\0')

    def hash_password(self, password: str, salt: Any = None):
        """
        Genera un hash seguro delegando en CryptoEngine.
        Mantiene el retorno (hash, salt_hex) para compatibilidad con la capa de datos.
        """
        salt_bin = self._normalize_salt(salt)
        pwd_hash, salt_out = CryptoEngine.hash_user_password(password, salt_bin)
        return pwd_hash, salt_out.hex()

    @rate_limit(max_attempts=5, window=60)
    def verify_password(self, password: str, salt: Any, stored_hash: str) -> bool:
        """Verifica una contraseña delegando en el motor centralizado CryptoEngine."""
        if not salt or not stored_hash:
            return False
            
        salt_bin = self._normalize_salt(salt)
        result = CryptoEngine.verify_user_password(password, salt_bin, stored_hash)
        
        self.logger.info(f"[Auth] verify_password (Unified): Result={result}")
        return result

    def sync_user_to_local(self, username, cloud_profile):
        """
        Persiste el perfil de usuario de la nube al almacenamiento SQLite local.
        
        Realiza un 'Upsert' inteligente que garantiza que las llaves de protección
        y los salts locales no se pierdan, manteniendo la capacidad de login offline.
        
        Args:
            username: Nombre del usuario a sincronizar.
            cloud_profile: Diccionario con los datos provenientes de Supabase.
            
        Returns:
            bool: True si la persistencia fue exitosa.
        """
        if not username:
            self.logger.warning("Aborting sync: username is None")
            return False
            
        username_clean = username.upper().replace(" ", "")
        if not self.sm: return False

        # [CRITICAL FIX] Ensure we write to the specific User DB, not Global DB
        # This prevents 'Phantom Salt' bug where profile is saved to vultrax.db and lost.
        try:
             current_db = self.sm.db_path.name if self.sm.db_path else ""
             target_db = f"vault_{username_clean.lower()}.db"
             
             # If we are in global DB or wrong DB, switch immediately
             # Note: 'vultrax.db' is only for pre-login, users need their own vault DB.
             if current_db == "vultrax.db" or (current_db != target_db and "vault_" in current_db):
                 self.logger.info(f"Switching DB context to {target_db} before saving profile...")
                 self.sm.reconnect(username_clean)
        except Exception as e:
             self.logger.warning(f"Could not verify DB context: {e}")
        
        # [DOUBLE-BUFFERED SYNC] Logic to prevent stale cloud keys from overwriting local resets
        # 1. Always stage cloud credentials in vault_access if different or new
        # Initialize these variables here, as they are used before the new logic.
        vault_salt_bytes = None
        protected_key_bytes = None
        wrapped_v_bytes = None

        # Obtener el perfil local una sola vez para las comparaciones de preservación
        local_profile = self.sm.get_local_user_profile(username_clean)
        
        # [HEALING DETECTION] 
        # Check if the current session for THIS user is broken (unwrap failed)
        session_is_broken = (self.sm.session.current_user == username_clean and self.sm.vault_key is None)
        if session_is_broken:
             self.logger.info(f"Healing Mode: Local broken session detected for {username_clean}. Preferring Cloud Credentials.")

        # 1. Manejar Vault Salt (UNIFICADO)
        vault_salt_bytes = self._normalize_to_bytes(cloud_profile.get("vault_salt"))
        
        if not vault_salt_bytes:
            # Si en la nube no hay salt, intentamos REUTILIZAR el local existente para no romper las llaves
            if local_profile and local_profile.get("vault_salt"):
                vault_salt_bytes = self.sm._ensure_bytes(local_profile["vault_salt"])
                self.logger.info(f"Preservando Salt local existente para {username_clean}.")
            else:
                # Si sigue siendo None (usuario nuevo sin salt en ningún lado), generamos uno
                vault_salt_bytes = secrets.token_bytes(16)
                self.logger.info(f"Generando Salt nuevo para {username_clean}.")

        # 2. Manejar Protected Key (SVK) - [PRESERVACIÓN CRÍTICA UNIFICADA]
        protected_key_bytes = self._normalize_to_bytes(cloud_profile.get("protected_key"))
        
        # [PRESERVACIÓN CRÍTICA] Si la nube no mandó protected_key, mantenemos la local
        # [HEALING] Unless we are in healing mode and cloud DOES have a key
        if not protected_key_bytes and local_profile and local_profile.get("protected_key"):
            protected_key_bytes = self.sm._ensure_bytes(local_profile["protected_key"])
            self.logger.info("Preservando Protected Key local.")
        elif session_is_broken and protected_key_bytes:
             self.logger.info("Healing: Applying Cloud Protected Key (Bypassing local preservation).")
        
        # 3. Manejar Wrapped Vault Key (Equipo) - [PRESERVACIÓN CRÍTICA]
        wrapped_v_key = cloud_profile.get("wrapped_vault_key")
        
        if wrapped_v_key:
            # Puede venir en 3 formatos:
            # 1. Bytes puros (desde vault_access ya decodificado)
            # 2. Hex con prefijo \\x (desde columna bytea de users)
            # 3. Base64 (desde columna bytea de users)
            if isinstance(wrapped_v_key, bytes):
                # Ya es bytes, perfecto
                wrapped_v_bytes = wrapped_v_key
            elif isinstance(wrapped_v_key, str):
                if wrapped_v_key.startswith('\\x'):
                    try:
                        # Postgres bytea may be hex: \\xdeadbeef
                        hex_str = wrapped_v_key[2:]
                        wrapped_v_bytes = bytes.fromhex(hex_str)
                    except Exception:
                        try:
                            # Or it might be hex containing B64: \\x(B64_IN_HEX)
                            ascii_b64 = bytes.fromhex(wrapped_v_key[2:]).decode('ascii')
                            wrapped_v_bytes = base64.b64decode(ascii_b64)
                        except Exception as e:
                            self.logger.error(f"Error decoding wrapped_vault_key bytea: {e}")
                            wrapped_v_bytes = None
                else:
                    # Generic string format
                    try: wrapped_v_bytes = base64.b64decode(wrapped_v_key)
                    except:
                        try: wrapped_v_bytes = bytes.fromhex(wrapped_v_key)
                        except: wrapped_v_bytes = wrapped_v_key.encode('utf-8')
            else:
                wrapped_v_bytes = wrapped_v_key
        
        # [PRESERVACIÓN CRÍTICA] Si la nube no mandó wrapped_vault_key, mantenemos la local
        # [HEALING] Si la sesión está rota, NO preservamos la local si hay una esperanza en la nube.
        if not wrapped_v_bytes and local_profile and local_profile.get("wrapped_vault_key"):
            if not session_is_broken:
                wrapped_v_bytes = self.sm._ensure_bytes(local_profile["wrapped_vault_key"])
                self.logger.info("Preservando Wrapped Vault Key local.")
            else:
                self.logger.warning("Session broken: Skipping preservation of corrupt local vault key.")

        # [DOUBLE-BUFFERED SYNC] Logic to prevent stale cloud keys from overwriting local resets
        # 1. Always stage cloud credentials in vault_access if different or new
        if wrapped_v_bytes and cloud_profile.get("vault_id"):
            # We save this as a fallback in the vault_access table
            self.logger.info(f"[Sync] Staging cloud vault key for {cloud_profile.get('vault_id')} in vault_access table.")
            self.sm.users.save_vault_access(cloud_profile.get("vault_id"), wrapped_v_bytes)

        # 2. DECISION: Do we trust the local primary credentials?
        # If we have a local key/salt pair, we keep them in the 'users' table (Primary).
        # This allows local resets to work immediately. set_active_user will handle fallbacks.
        if not session_is_broken and local_profile and local_profile.get("wrapped_vault_key") and local_profile.get("vault_salt"):
            local_v_bytes = self.sm._ensure_bytes(local_profile["wrapped_vault_key"])
            local_s_bytes = self.sm._ensure_bytes(local_profile["vault_salt"])
            
            if wrapped_v_bytes and local_v_bytes != wrapped_v_bytes:
                self.logger.info("Preserving local Primary Vault Key (Cloud key staged in vault_access).")
                wrapped_v_bytes = local_v_bytes
                vault_salt_bytes = local_s_bytes # Salt must match the key
        elif session_is_broken:
            self.logger.info("Healing: Trusting Cloud Vault Key/Salt (Bypassing primary preservation).")
        elif not wrapped_v_bytes and local_profile and local_profile.get("wrapped_vault_key"):
            wrapped_v_bytes = self.sm._ensure_bytes(local_profile["wrapped_vault_key"])
            vault_salt_bytes = self.sm._ensure_bytes(local_profile.get("vault_salt"))
            self.logger.info("Preserving local Vault Key (Cloud sent nothing).")
            
        # 4. Manejar TOTP Secret - [DESCIFRADO ROBUSTO CON SYSTEM KEY]
        totp_raw = cloud_profile.get("totp_secret")
        totp_clean = None
        
        if totp_raw:
            # 1. Normalización de formato hexadecimal (PostgREST bytea)
            if isinstance(totp_raw, str) and totp_raw.startswith("\\x"):
                try:
                    totp_bytes = bytes.fromhex(totp_raw[2:])
                    # Intentar ver si es texto plano (Base32) o binario cifrado
                    try:
                        candidate = totp_bytes.decode('utf-8')
                        if 16 <= len(candidate.strip()) <= 64 and re.fullmatch(r'[A-Z2-7]+=*', candidate.upper().strip()):
                            totp_raw = candidate.strip()
                        else:
                            # Es binario cifrado, lo pasamos a Base64 para el siguiente bloque
                            totp_raw = base64.b64encode(totp_bytes).decode('ascii')
                    except:
                        # Error de decodificación -> es binario cifrado
                        totp_raw = base64.b64encode(totp_bytes).decode('ascii')
                except: pass

            # 2. Detectar si el secreto está en texto plano o cifrado
            is_plaintext = False
            if isinstance(totp_raw, str):
                # Limpieza agresiva de espacios y saltos de línea
                totp_raw = totp_raw.strip()
                target = totp_raw.upper().replace(" ", "")
                # Si parece Base32 puro, está en texto plano
                if re.fullmatch(r'[A-Z2-7]+=*', target) and 16 <= len(target) <= 64:
                    is_plaintext = True
                    totp_raw = target # Normalizar a mayúsculas sin espacios
            
            if is_plaintext:
                # Usar directamente
                totp_clean = totp_raw
            else:
                # Intentar descifrar con System Key
                try:
                    from config.config import TOTP_SYSTEM_KEY
                    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                    import hashlib
                    
                    key = hashlib.sha256(TOTP_SYSTEM_KEY.encode()).digest()
                    cipher = AESGCM(key)
                    
                    payload = base64.b64decode(totp_raw)
                    nonce = payload[:12]
                    ciphertext = payload[12:]
                    
                    decrypted = cipher.decrypt(nonce, ciphertext, None)
                    totp_clean = decrypted.decode('utf-8')
                except Exception as decrypt_err:
                    # Si falla, usar como texto plano (compatibilidad con datos viejos)
                    self.logger.debug(f"TOTP Decrypt: Using raw value or discarding: {decrypt_err}")
                    totp_clean = totp_raw if is_plaintext else None
        
        # --- [BLINDAJE DE SEGURIDAD SENIOR] ---
        # Si la nube no tiene el token (común tras un reset) pero nosotros sí,
        # lo preservamos a toda costa para no dejar al usuario bloqueado.
        local_prof = self.sm.get_local_user_profile(username_clean)
        if local_prof and not totp_clean:
            totp_clean = local_prof.get("totp_secret")

        # [DEBUG] Logging antes de guardar
        self.logger.debug(f"Saving profile for {username_clean}:")
        self.logger.debug(f"    protected_key: {type(protected_key_bytes).__name__} ({len(protected_key_bytes) if protected_key_bytes else 0} bytes)")
        self.logger.debug(f"    wrapped_vault_key: {type(wrapped_v_bytes).__name__} ({len(wrapped_v_bytes) if wrapped_v_bytes else 0} bytes)")
        self.logger.debug(f"    vault_salt: {type(vault_salt_bytes).__name__} ({len(vault_salt_bytes) if vault_salt_bytes else 0} bytes)")

        self.sm.save_local_user_profile(
            username_clean,
            cloud_profile.get("password_hash"),
            cloud_profile.get("salt"),
            vault_salt_bytes,
            cloud_profile.get("role", "user"),
            protected_key_bytes,
            totp_clean, # Usamos el secreto limpio
            cloud_profile.get("vault_id"),
            wrapped_v_bytes,
            user_id=cloud_profile.get("id")
        )
        self.sm.conn.commit()
        return vault_salt_bytes

    @rate_limit(max_attempts=5, window=60)
    def check_local_login(self, username, password):
        """Intenta validar el login usando solo la base de datos local."""
        username_clean = username.upper().replace(" ", "")
        if not self.sm: return None
        
        profile = self.sm.get_local_user_profile(username_clean)
        if not profile: return None # No existe localmente
        
        if not profile.get("password_hash"):
            return {"exists": True, "active": True, "status": "needs_setup", "profile": profile}

        is_valid = self.verify_password(password, profile["salt"], profile["password_hash"])
        if is_valid:
            # Normalizar perfil para que sea idéntico al de la nube
            return {
                "id": profile.get("user_id"),
                "exists": True,
                "active": True, # Si está en la DB local y llegamos aquí, asumimos activo
                "role": profile.get("role", "user"),
                "password_hash": profile.get("password_hash"),
                "salt": profile.get("salt"),
                "vault_salt": profile.get("vault_salt"),
                "protected_key": profile.get("protected_key"),
                "totp_secret": profile.get("totp_secret"),
                "vault_id": profile.get("vault_id"),
                "wrapped_vault_key": profile.get("wrapped_vault_key"),
                "is_offline": True # Flag de control
            }
        return {"exists": True, "active": True, "status": "error"}

    def verify_totp(self, secret: str, token: str) -> bool:
            """Verificación 2FA limpia y directa (patrón profesional recomendado)."""
            try:
                if not secret or not token: return False
                
                # 1. Limpiar espacios y normalizar a mayúsculas
                secreto_limpio = str(secret).strip().replace(" ", "").upper()
                if not secreto_limpio: return False
                
                # 2. Añadir padding si falta (Base32 requiere múltiplos de 8)
                import re
                b32 = re.sub(r'[^A-Z2-7]', '', secreto_limpio)
                mod = len(b32) % 8
                if mod != 0: b32 += '=' * (8 - mod)
                
                # 3. Validar con ventana de tiempo (90 segundos de tolerancia)
                totp = pyotp.TOTP(b32)
                return totp.verify(str(token).strip(), valid_window=1)
            except Exception as e:
                self.logger.error(f"2FA Verification Error: {e}")
                return False
                
    def validate_user_access(self, username: str):
        """
        Consulta en Supabase si el usuario existe y está activo.
        
        Realiza una validación completa que incluye:
        1. Verificación de existencia y estado activo.
        2. Vinculación de Hardware (HWID Binding).
        3. Recuperación de la Vault Key empaquetada (Wrapped Team Key).
        4. Sincronización del nombre de la instancia.
        
        Args:
            username: Nombre de usuario (será normalizado a uppercase).
            
        Returns:
            dict: Perfil del usuario con llaves y metadatos, o None si hay error fatal.
        """
        username_clean = username.upper().replace(" ", "")
        try:
            # Consultamos la tabla public.users (Case-Insensitive)
            response = self.supabase.table("users").select("*").ilike("username", username_clean).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                
                # [FIX CRITICAL] Fetch Wrapped Vault Key from 'vault_access'
                # This is essential for local persistence of the Team Key.
                wrapped_vault_key = None
                try:
                    v_id = user_data.get("vault_id")
                    u_id = user_data.get("id")
                    if v_id and u_id:
                        va_res = self.supabase.table("vault_access").select("wrapped_master_key").eq("user_id", u_id).eq("vault_id", v_id).execute()
                        if va_res.data:
                            wmk_raw = va_res.data[0].get("wrapped_master_key")
                            # vault_access guarda la llave como HEX puro (no Base64)
                            if wmk_raw:
                                if isinstance(wmk_raw, str):
                                    # Es hex puro (120 chars = 60 bytes)
                                    wrapped_vault_key = bytes.fromhex(wmk_raw)
                                else:
                                    wrapped_vault_key = wmk_raw
                            self.logger.info(f"[Auth] Found Team Key in vault_access for {username_clean}")
                except Exception as ve:
                    self.logger.warning(f"Could not fetch vault_access: {ve}")

                # --- [SEGURIDAD DE HARDWARE (HWID)] ---
                current_hwid = get_hwid()
                stored_hwid = user_data.get("linked_hwid")

                # Escenario A: Usuario nuevo o migrado sin HWID vinculado
                if not stored_hwid:
                    self.logger.info(f"[HWID Bind] Vinculando cuenta {username_clean} a este dispositivo...")
                    try:
                        self.supabase.table("users").update({"linked_hwid": current_hwid}).eq("username", username_clean).execute()
                        stored_hwid = current_hwid
                    except Exception as e:
                        self.logger.error(f"No se pudo vincular hardware: {e}")

                # Escenario B: Validación de Identidad Física
                if stored_hwid and stored_hwid != current_hwid:
                    self.logger.warning(f"[ACCESO DENEGADO] Intento de entrada desde hardware no autorizado: {current_hwid}")
                    return {
                        "exists": True,
                        "active": False,
                        "role": "blocked",
                        "error": "DEVICE_MISMATCH" # Flag para la UI
                    }

                # --- [SYNC NOMBRE DE BÓVEDA] ---
                vault_name = None
                try:
                    v_id = user_data.get("vault_id")
                    if v_id:
                        # Buscamos en vaults (que usa UUID y campo 'name')
                        v_res = self.supabase.table("vaults").select("name").eq("id", v_id).execute()
                        if v_res.data:
                            vault_name = v_res.data[0].get("name")
                            # Guardar localmente para persistencia offline
                            if self.sm:
                                self.sm.set_meta("instance_name", vault_name)
                                self.logger.info(f"Vault name synchronized: {vault_name}")
                except Exception as ve:
                    self.logger.warning(f"Could not fetch vault name: {ve}")

                # --- [NORMALIZACIÓN DE DATOS PARA LOGIN] ---
                pwd_hash_clean = self._normalize_hex(user_data.get("password_hash"))
                salt_clean = self._normalize_hex(user_data.get("salt"))
                
                self.logger.info(f"[Auth] Normalized credentials for {username_clean} (Professional Sync)")

                return {
                    "id": user_data.get("id"),
                    "exists": True,
                    "active": user_data.get("active", False),
                    "role": user_data.get("role") or "user",
                    "password_hash": pwd_hash_clean,
                    "salt": salt_clean,
                    "vault_salt": user_data.get("vault_salt"),
                    "protected_key": user_data.get("protected_key"),
                    "totp_secret": user_data.get("totp_secret"),
                    "vault_id": user_data.get("vault_id"),
                    "vault_name": vault_name,
                    "wrapped_vault_key": wrapped_vault_key
                }
            
            return {"exists": False, "active": False, "role": None}
        except Exception as e:
            self.logger.critical(f"Error fatal validando usuario en Supabase: {e}")
            return None

    def get_all_users(self):
        """Obtiene la lista de todos los usuarios registrados con fallback offline."""
        try:
            r = self.supabase.table("users").select("*").execute()
            return r.data or []
        except Exception as e:
            # [OFFLINE FALLBACK] Si falla la conexión a Supabase, usar datos locales
            err_str = str(e).lower()
            if "getaddrinfo" in err_str or "connection" in err_str or "network" in err_str or "timeout" in err_str:
                self.logger.warning(f"Network unavailable, using local user cache: {e}")
                return self._get_local_users()
            self.logger.error(f"Error listing users: {e}")
            return []
    
    def _get_local_users(self):
        """Obtiene usuarios desde la base de datos local SQLite."""
        if not self.sm or not self.sm.conn:
            self.logger.warning("No local database connection available")
            return []
        
        try:
            cursor = self.sm.conn.execute("""
                SELECT username, role, 1 as active, totp_secret, user_id 
                FROM users 
                WHERE username IS NOT NULL
            """)
            rows = cursor.fetchall()
            
            # Convertir a formato compatible con Supabase response
            users = []
            for row in rows:
                users.append({
                    "username": row[0],
                    "role": row[1] or "user",
                    "active": bool(row[2]),
                    "totp_secret": row[3],
                    "id": row[4] or f"local_{row[0]}"  # Fallback ID
                })
            
            self.logger.info(f"Retrieved {len(users)} users from local cache")
            return users
        except Exception as e:
            self.logger.error(f"Error reading local users: {e}")
            return []

    def get_user_count(self):
        """Devuelve el número actual de usuarios."""
        try:
            all_users = self.get_all_users()
            return len(all_users)
        except:
            return 0

    def get_user_totp_secret(self, username: str):
        """Recupera el secreto TOTP de un usuario (si existe)."""
        username_clean = username.upper().replace(" ", "")
        try:
            r = self.supabase.table("users").select("totp_secret").eq("username", username_clean).execute()
            if r.data:
                return r.data[0].get("totp_secret")
            return None
        except Exception:
            return None

    def save_totp_secret(self, username: str, secret: str, password: str = None, salt: bytes = None):
        """Guarda el secreto TOTP CIFRADO con System Key en Supabase.
        
        ARQUITECTURA DE SEGURIDAD:
        - El secreto se cifra con TOTP_SYSTEM_KEY (no con la contraseña del usuario)
        - Esto protege contra lectura no autorizada de la DB
        - Pero permite descifrar durante el login sin bucle circular
        """
        username_clean = username.upper().replace(" ", "")
        try:
            check_response = self.supabase.table("users").select("username,id").eq("username", username_clean).execute()
            if not check_response.data: return False
            
            # Cifrar con System Key usando AES-GCM
            from config.config import TOTP_SYSTEM_KEY
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            import hashlib
            
            # Derivar clave de 32 bytes desde el pepper
            key = hashlib.sha256(TOTP_SYSTEM_KEY.encode()).digest()
            cipher = AESGCM(key)
            nonce = secrets.token_bytes(12)
            
            encrypted = cipher.encrypt(nonce, secret.encode('utf-8'), None)
            # [SENIOR FIX] Guardar como hex compatible con bytea (\x prefix)
            # Esto evita doble codificación y misterios de longitud.
            binary_payload = nonce + encrypted
            payload = "\\x" + binary_payload.hex()
            
            self.supabase.table("users").update({"totp_secret": payload}).eq("username", username_clean).execute()
            return True
        except Exception as e:
            self.logger.error(f"TOTP Sync Error: {e}")
            return False


    def add_new_user(self, username: str, role: str, password: str = None):
        """Crea un nuevo usuario con gestión profesional de llaves."""
        username_clean = username.upper().replace(" ", "")
        
        try:
            # 1. Validación de existencia y límites
            valid, msg = self._validate_new_user(username_clean)
            if not valid: return False, msg

            # 2. Generación de llaves E2EE
            keys = self._generate_user_keys(username_clean, role, password)
            
            # 3. Preparar payload para Cloud
            payload = self._build_user_payload(username_clean, role, keys, password)

            # 4. Inserción en Supabase
            res = self.supabase.table("users").insert(payload).execute()
            if not res.data: return False, "Error al crear perfil en la nube."

            # 5. Registrar acceso a bóveda y estabilizar localmente
            user_data = res.data[0]
            if keys.get('protected'):
                # Sincronizar acceso a bóveda localmente antes de terminar
                if self.sm:
                    # Guardar en local vault_access para que el usuario pueda loguearse offline de inmediato
                    self.sm.users.save_vault_access(keys['vault_id'], keys['protected'], synced=1)
                
                # Sincronizar en la nube
                self._register_vault_access(user_data['id'], keys['vault_id'], keys['protected'])

            self.sync_user_to_local(username_clean, user_data)
            if password:
                self.sm.set_active_user(username_clean, password)

            return True, f"Usuario {username_clean} configurado correctamente."
        except Exception as e:
            # [OFFLINE DETECTION] Detectar errores de red y dar mensaje claro
            err_str = str(e).lower()
            if "getaddrinfo" in err_str or "connection" in err_str or "network" in err_str or "timeout" in err_str:
                self.logger.error(f"Network unavailable during user creation: {e}")
                fallback_msg = MESSAGES.COMMON.ERR_OFFLINE if hasattr(MESSAGES, 'COMMON') and hasattr(MESSAGES.COMMON, 'ERR_OFFLINE') else "No hay conexión a internet."
                return False, fallback_msg
            return self._handle_add_user_error(e, username_clean)


    def _validate_new_user(self, username: str) -> Tuple[bool, str]:
        """Realiza comprobaciones de negocio antes de crear el usuario."""
        check = self.validate_user_access(username)
        if check and check.get("exists"):
            return False, f"El usuario '{username}' ya está registrado en el sistema."
        if self.get_user_count() >= 5:
            return False, "Límite de usuarios alcanzado (Máx 5)."
        return True, ""

    def _generate_user_keys(self, username: str, role: str, password: str) -> Dict[str, Any]:
        """Genera salts y envuelve la llave maestra según el rol del usuario."""
        v_salt = secrets.token_bytes(16)
        protected = None
        is_first = (role == "admin" and self.get_user_count() == 0)
        
        # Resolución de Vault Context
        vault_id = getattr(self.sm, 'current_vault_id', None) or self.get_master_vault_id()
        if self.sm: self.sm.current_vault_id = vault_id

        if is_first:
            new_master = secrets.token_bytes(32)
            if self.sm: self.sm.master_key = new_master # En memoria temporal
            protected = self.sm.wrap_key(new_master, password, v_salt)
            self.logger.info("Primer admin - Llave maestra generada.")
        else:
            # Intentar obtener la llave del admin si está disponible
            target_key = None
            if self.sm and self.sm.master_key:
                target_key = self.sm.master_key
            elif self.sm and self.sm.vault_key:
                target_key = self.sm.vault_key
            elif self.sm and vault_id:
                # Fallback: intentar recuperar de vault_access local si el admin la tiene
                va = self.sm.users.get_vault_access(vault_id)
                if va and va.get("wrapped_master_key"):
                    # Necesitamos la password del admin para esto... 
                    # Pero el admin ya debería haberla desencriptado en su sesión.
                    pass 

            if target_key and password:
                protected = self.sm.wrap_key(target_key, password, v_salt)
                self.logger.info(f"Usuario secundario - Llave {'Maestra' if target_key == self.sm.master_key else 'de Bóveda'} enlazada.")
            else:
                self.logger.warning("No se pudo enlazar llave: Admin no tiene llave activa en memoria.")
            
        return {"vault_id": vault_id, "v_salt": v_salt, "protected": protected}

    def _build_user_payload(self, username: str, role: str, keys: dict, password: str) -> dict:
        """Construye el objeto de datos para la inserción en Supabase."""
        pwd_hash, salt = self.hash_password(password) if password else (None, None)
        return {
            "username": username,
            "role": role,
            "active": True,
            "vault_id": keys["vault_id"],
            "password_hash": pwd_hash,
            "salt": salt,
            "vault_salt": base64.b64encode(keys["v_salt"]).decode('ascii'),
            "protected_key": base64.b64encode(keys["protected"]).decode('ascii') if keys["protected"] else None
        }

    def _register_vault_access(self, user_id, vault_id, protected_key):
        """Persiste el registro de acceso a la bóveda con fallback cromático."""
        try:
            payload = {
                "user_id": user_id,
                "vault_id": vault_id,
                "wrapped_master_key": protected_key.hex()
            }
            self.supabase.table("vault_access").upsert(payload).execute()
        except Exception as e:
            if "wrapped_master_key" in str(e).lower():
                payload["wrapped_vault_key"] = payload.pop("wrapped_master_key")
                self.supabase.table("vault_access").upsert(payload).execute()
            else:
                self.logger.error(f"Error registrando acceso a bóveda: {e}")

    def _handle_add_user_error(self, e, username):
        """Centraliza la gestión de errores durante la creación de usuarios."""
        err_str = str(e)
        if "23505" in err_str or "already exists" in err_str.lower():
            return False, f"El usuario '{username}' ya existe."
        self.logger.error(f"Error in add_new_user: {e}")
        return False, f"Fallo de Protocolo: {err_str}"

    def get_master_vault_id(self):
        """
        Resuelve el ID de la bóveda maestra de forma dinámica.
        Prioriza la caché de sesión, luego busca en Supabase el primer registro disponible.
        """
        if self.sm and self.sm.current_vault_id:
            return self.sm.current_vault_id
            
        try:
            # Buscamos la primera bóveda creada (la maestra histórica)
            res = self.supabase.table("vaults").select("id").limit(1).execute()
            if res.data:
                v_id = res.data[0]["id"]
                if self.sm: self.sm.current_vault_id = v_id
                return v_id
        except Exception as e:
            self.logger.warning(f"Could not resolve Master Vault ID from cloud: {e}")
            
        # Fallback histórico para compatibilidad con instalaciones antiguas v2.0
        return "0637ae0d-7446-4c94-bc06-18c918ce596e"

    # ------------------------------------------------------------------
    #  SISTEMA DE INVITACIONES (AUTO-ONBOARDING)
    # ------------------------------------------------------------------

    def create_invitation(self, role: str, created_by: str):
        """Genera un código de invitación único que vincula al nuevo usuario a la bóveda actual."""
        try:
            part1 = secrets.token_hex(2).upper()
            part2 = secrets.token_hex(2).upper()
            code = f"PG-{part1}-{part2}"
            
            payload = {
                "code": code,
                "role": role,
                "created_by": str(created_by or "SYSTEM").upper(),
                "used": False
            }

            # PUENTE DE LLAVES (SaaS Elite): 
            if self.sm and self.sm.master_key:
                try:
                    # Usamos el código de invitación como llave temporal (KEK)
                    v_salt = code.encode('utf-8')[:16].ljust(16, b'\0')
                    wrapped_key = self.sm.wrap_key(self.sm.master_key, code, v_salt)
                    
                    payload["wrapped_vault_key"] = base64.b64encode(wrapped_key).decode('ascii')
                    # Intentar obtener el vault_id actual si existe
                    payload["vault_id"] = self.sm.current_vault_id
                except Exception as e:
                    self.logger.error(f"create_invitation: Key wrapping failed: {e}")

            # Intento 1: Insertar con todos los campos (incluyendo vault_id y created_by si existen)
            try:
                self.supabase.table("invitations").insert(payload).execute()
            except Exception as e:
                err_str = str(e)
                # Manejar esquemas legacy que no tienen ciertas columnas
                if "column" in err_str.lower() or "could not find" in err_str.lower():
                    self.logger.warning("Legacy schema detected in 'invitations'. Adapting payload...")
                    # Remover campos que pueden no existir
                    payload.pop("vault_id", None)
                    payload.pop("wrapped_vault_key", None)
                    payload.pop("created_by", None)
                    # Reintentar con payload mínimo
                    self.supabase.table("invitations").insert(payload).execute()
                else:
                    raise e
            
            if self.sm:
                self.sm.log_event("INVITACION_GENERADA", "SISTEMA", details=f"Código: {code}, Rol: {role}")
            
            return True, code
        except Exception as e:
            err_msg = str(e)
            if "invitations" in err_msg and ("not found" in err_msg or "does not exist" in err_msg):
                return False, "⚠️ ERROR CRÍTICO: La tabla 'invitations' no existe en Supabase."
            return False, f"Error al crear invitación: {err_msg}"

    def get_invitations(self):
        """Lista todas las invitaciones."""
        try:
            r = self.supabase.table("invitations").select("*").order("created_at", desc=True).execute()
            return r.data or []
        except Exception:
            return []

    def register_with_invitation(self, code: str, username: str, password: str):
        """Registra un nuevo usuario heredando las llaves de bóveda compartidas."""
        try:
            # 1. Validar invitación
            code = code.strip().upper()
            r = self.supabase.table("invitations").select("*").eq("code", code).eq("used", False).execute()
            
            if not r.data:
                return False, "Código de invitación no válido o ya utilizado."
            
            invitation = r.data[0]
            
            # --- VALIDACIÓN DE EXPIRACIÓN (24H) ---
            from datetime import datetime, timedelta, timezone
            try:
                created_at_str = invitation.get("created_at")
                if created_at_str:
                    # Supabase devuelve UTC ISO8601 (ej: 2024-01-01T12:00:00+00:00)
                    # Python 3.11+ maneja 'Z', pero versiones anteriores necesitan patch
                    created_at_str = created_at_str.replace('Z', '+00:00')
                    created_dt = datetime.fromisoformat(created_at_str)
                    
                    # Convertir a UTC consciente para comparar
                    now_utc = datetime.now(timezone.utc)
                    
                    if (now_utc - created_dt) > timedelta(hours=24):
                        return False, "Este código de invitación ha expirado (Límite: 24h)."
            except Exception as e:
                self.logger.warning(f"Warning validating invitation date: {e}")
                # Si falla el parseo, permitimos el paso 'fail-open' o 'fail-close'
                # Para seguridad estricta deberíamos fallar, pero por ahora logueamos.

            role = invitation.get("role", "user")
            wrapped_vault_key_b64 = invitation.get("wrapped_vault_key")
            vault_id = invitation.get("vault_id")

            # 2. Verificar que el usuario no exista
            check = self.validate_user_access(username)
            if check and check["exists"]:
                return False, "El nombre de usuario ya está ocupado."

            # 3. Recuperar Master Key heredada (SaaS Elite Bridge)
            inherited_master_key = None
            if wrapped_vault_key_b64:
                try:
                    # Usamos el código de invitación como KEK temporal para des-envolver la llave maestra
                    v_salt_inv = code.encode('utf-8')[:16].ljust(16, b'\0')
                    wrapped_data = base64.b64decode(wrapped_vault_key_b64)
                    
                    # Usamos una instancia temporal de SecretsManager para el unwrap
                    from src.infrastructure.secrets_manager import SecretsManager
                    tmp_sm = SecretsManager()
                    inherited_master_key = tmp_sm.unwrap_key(wrapped_data, code, v_salt_inv)
                    self.logger.info(f"register_with_invitation: Inherited key successfully ({len(inherited_master_key)} bytes)")
                except Exception as e:
                    self.logger.error(f"register_with_invitation: Error inheriting key: {e}")

            # 4. Inyectar llave heredada para que add_new_user la enclave con el nuevo password
            if inherited_master_key:
                if not self.sm:
                    from src.infrastructure.secrets_manager import SecretsManager
                    self.sm = SecretsManager()
                self.sm.master_key = inherited_master_key
            
            success, msg = self.add_new_user(username, role, password)
            if not success:
                return False, msg

            # 5. Marcar invitación como usada (Resilient Flow)
            username_clean = str(username or "UNKNOWN").upper().replace(" ", "")
            try:
                self.supabase.table("invitations").update({
                    "used": True,
                    "claimed_by": username_clean
                }).eq("code", code).execute()
            except Exception as e:
                err_str = str(e)
                if "column" in err_str.lower() or "could not find" in err_str.lower():
                    self.logger.warning(f"register_with_invitation: Legacy schema in 'invitations'. Skipping 'claimed_by'.")
                    # Reintento sin el campo conflictivo
                    self.supabase.table("invitations").update({"used": True}).eq("code", code).execute()
                else:
                    raise e

            # 6. Vincular vault_id en el perfil del usuario si existe
            if vault_id:
                try:
                    self.supabase.table("users").update({"vault_id": vault_id}).eq("username", username_clean).execute()
                except Exception as e:
                    self.logger.error(f"register_with_invitation: Error linking vault_id: {e}")

            # Auditoría
            if self.sm:
                self.sm.log_event("REGISTRO_INVITACION", "SISTEMA", details=f"Código usado: {code}")

            return True, "Registro completado exitosamente con herencia de llaves."
        except Exception as e:
            return False, f"Error en el registro: {str(e)}"

    def get_cloud_vault_accesses(self, user_id: str) -> list:
        """Recupera todos los registros de acceso a bvedas desde la nube."""
        try:
            r = self.supabase.table("vault_access").select("*").eq("user_id", user_id).execute()
            return r.data or []
        except Exception as e:
            self.logger.error(f"Error fetching cloud vault accesses: {e}")
            return []

    def update_user_password(self, username, password, new_protected_key=None, new_vault_salt=None):
        """Actualiza la contraseña y salts del usuario en la nube."""
        username_clean = username.upper().replace(" ", "")
        try:
            pwd_hash, salt = self.hash_password(password)
            
            # Si nos pasan la sal de bóveda ya generada (B64), usarla. Si no, generar nueva.
            if new_vault_salt:
                vault_salt_b64 = new_vault_salt
            else:
                vault_salt_bytes = secrets.token_bytes(16)
                vault_salt_b64 = base64.b64encode(vault_salt_bytes).decode('ascii')
            
            payload = {
                "password_hash": pwd_hash,
                "salt": salt,
                "vault_salt": vault_salt_b64
            }

            # Si nos pasan la protected_key externa (Admin Reset Flow), usarla
            if new_protected_key:
                payload["protected_key"] = new_protected_key
            else:
                # Flujo normal: el usuario se cambia su propia clave y tiene la master_key en memoria
                if self.sm and self.sm.master_key:
                     # Decodificamos la sal para usarla en el wrapping
                     v_salt_decoded = base64.b64decode(vault_salt_b64)
                     protected_key = self.sm.wrap_key(self.sm.master_key, password, v_salt_decoded)
                     payload["protected_key"] = base64.b64encode(protected_key).decode('ascii')
            
            try:
                res = self.supabase.table("users").update(payload).eq("username", username_clean).execute()
            except Exception as e:
                # Fallback por compatibilidad
                if "protected_key" in str(e):
                    payload.pop("protected_key", None)
                    res = self.supabase.table("users").update(payload).eq("username", username_clean).execute()
                else:
                    raise e
            
            if not res.data:
                 return False, "Usuario no encontrado"
            
            if self.sm:
                self.sm.log_event("CAMBIO_PASSWORD", details=f"Perfil de {username_clean} actualizado")
            
            return True, None
        except Exception as e:
            self.logger.error(f"Error in update_user_password: {e}")
            return False, str(e)

    def update_bulk_vault_access(self, user_id: str, vault_key_map: list) -> bool:
        """
        Updates multiple vault access records in Supabase.
        vault_key_map: List of tuples/dicts [(vault_id, wrapped_key_hex), ...]
        """
        try:
            for v_id, w_key_hex in vault_key_map:
                self.supabase.table("vault_access")\
                    .update({"wrapped_master_key": w_key_hex})\
                    .eq("user_id", user_id)\
                    .eq("vault_id", v_id).execute()
            return True
        except Exception as e:
            self.logger.error(f"Error in update_bulk_vault_access: {e}")
            return False

    def toggle_user_status(self, user_id: int, current_status: bool):
        """Activa o desactiva un usuario en Supabase."""
        try:
            user_data = self.supabase.table("users").select("role").eq("id", user_id).execute()
            if user_data.data and user_data.data[0].get("role") == "admin":
                return False, "No se puede suspender a un administrador."

            self.supabase.table("users").update({"active": not current_status}).eq("id", user_id).execute()
            status_msg = "ACTIVADO" if not current_status else "SUSPENDIDO"
            return True, (f"Usuario {status_msg} correctamente.\n\n"
                          f"ⓘ NOTA TÉCNICA: El cambio se ha registrado en la nube.\n"
                          f"Debido a los ciclos de refresco, la desactivación total en sesiones activas puede tardar hasta 2 minutos.")
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_user(self, user_id: int, force: bool = False):
        """
        Elimina un usuario y gestiona sus secretos para evitar huerfanos:
        - Borra registros PRIVADOS.
        - Los registros PUBLICOS son adoptados por el administrador actual.
        """
        try:
            # 1. Obtener datos del usuario a eliminar
            user_res = self.supabase.table("users").select("username, role").eq("id", user_id).execute()
            if not user_res.data:
                return False, "Usuario no encontrado."
            
            target_username = str(user_res.data[0].get("username") or "").upper().replace(" ", "")
            target_role = user_res.data[0]["role"]
            
            if target_role == "admin":
                return False, "No se puede eliminar a un administrador."

            # --- BLOQUEO DE SEGURIDAD ÉTICO: SESIÓN ACTIVA ---
            if not force:
                import time
                limit_time = int(time.time()) - 300 # 5 minutos de ventana de actividad
                
                # Buscamos actividad RECIENTE que NO sea de desconexión
                active_res = self.supabase.table("security_audit")\
                    .select("id, action, status")\
                    .eq("user_name", target_username)\
                    .gt("timestamp", limit_time)\
                    .order("timestamp", desc=True)\
                    .limit(1).execute()
                
                # Solo bloqueamos si el ÚLTIMO evento es de actividad real
                if active_res.data:
                    last_event = active_res.data[0]
                    is_really_active = (
                        last_event.get("action") not in ("LOGOUT", "ADMIN_REVOKE") and 
                        last_event.get("status") != "REVOKED"
                    )
                    
                    if is_really_active:
                        return False, (f"⚠️ PROTOCOLO ACTIVO: {target_username} está conectado.\n\n"
                                       f"Por ética y seguridad de datos, no se puede eliminar una cuenta en uso.\n"
                                       f"PASO 1: Vaya a 'Admin Panel' -> 'Sesiones' y use TERMINAR.\n"
                                       f"PASO 2: Intente eliminar nuevamente.")


            # 2. Gestionar SECRETOS del usuario (Para evitar huerfanos)
            # A. REGISTROS PRIVADOS: Se eliminan tanto en Nube como en Local
            priv_res = self.supabase.table("secrets").select("id").eq("owner_name", target_username).eq("is_private", 1).execute()
            count_private = len(priv_res.data)
            if count_private > 0:
                # Nube
                self.supabase.table("secrets").delete().eq("owner_name", target_username).eq("is_private", 1).execute()
                # Local
                if self.sm:
                    self.sm.conn.execute("DELETE FROM secrets WHERE owner_name = ? AND is_private = 1", (target_username,))
                    self.sm.conn.commit()

            # B. REGISTROS PUBLICOS: Los adopta el administrador (Nube y Local)
            admin_raw = (self.sm.current_user if self.sm else None) or "ADMIN"
            admin_name = str(admin_raw).upper().replace(" ", "")
            pub_res = self.supabase.table("secrets").select("id").eq("owner_name", target_username).eq("is_private", 0).execute()
            count_public = len(pub_res.data)
            if count_public > 0:
                # 1. Obtener ID de Bóveda del Admin para evitar orfandad
                admin_vault_id = self.sm.current_vault_id if (self.sm and hasattr(self.sm, 'current_vault_id')) else None
                if not admin_vault_id:
                     # Fallback a nube si local no lo tiene cargado
                     vres = self.supabase.table("users").select("vault_id").eq("username", admin_name).execute()
                     if vres.data: admin_vault_id = vres.data[0].get("vault_id")

                # 2. Actualizar en Nube (Adopción + Reubicación de Bóveda)
                cloud_update = {"owner_name": admin_name, "username": admin_name}
                if admin_vault_id: cloud_update["vault_id"] = admin_vault_id
                
                self.supabase.table("secrets").update(cloud_update).eq("owner_name", target_username).eq("is_private", 0).execute()
                
                # 3. Actualizar Localmente
                if self.sm:
                    if admin_vault_id:
                        self.sm.conn.execute(
                            "UPDATE secrets SET owner_name = ?, username = ?, vault_id = ? WHERE owner_name = ? AND is_private = 0", 
                            (admin_name, admin_name, admin_vault_id, target_username)
                        )
                    else:
                        self.sm.conn.execute(
                            "UPDATE secrets SET owner_name = ?, username = ? WHERE owner_name = ? AND is_private = 0", 
                            (admin_name, admin_name, target_username)
                        )
                    self.sm.conn.commit()
            
            # 3. Limpiar vault_access y usuario final
            self.supabase.table("vault_access").delete().eq("user_id", user_id).execute()
            self.supabase.table("users").delete().eq("id", user_id).execute()

            transfer_note = ""
            if count_public > 0:
                transfer_note = f"\n⚠️ IMPORTANTE: {count_public} registros de equipo (Públicos) han sido TRANSFERIDOS a su propiedad ({admin_name})."
            else:
                transfer_note = "\n(No se encontraron registros de equipo para transferir)"

            success_msg = (
                f"PROTOCOLO DE ELIMINACION COMPLETADO:\n\n"
                f"👤 Usuario eliminado: {target_username}\n"
                f"🗑️ Registros Privados borrados: {count_private}\n"
                f"{transfer_note}\n\n"
                f"El usuario ha sido purgado del sistema."
            )
            
            # MANTENIMIENTO POS-ELIMINACIÓN (Cleanup de caché y RAM)
            self.cleanup_vault_cache()
            
            return True, success_msg
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"

    def repair_orphans(self, admin_username):
        """Asigna el vault_id del admin a todos los secretos huérfanos que le pertenecen."""
        admin_clean = admin_username.upper().replace(" ", "")
        try:
            # 1. Obtener datos correctos (Vault ID y User ID)
            user_res = self.supabase.table("users").select("id, vault_id").eq("username", admin_clean).execute()
            if not user_res.data or not user_res.data[0].get("vault_id"):
                return False, "No se encontró un vault_id válido para el admin."
            
            vid = user_res.data[0]["vault_id"]
            uid = user_res.data[0]["id"]
            
            # 2. Update masivo en Nube (Asignar Vault + Unificar Username) utilizando ID de usuario
            res = self.supabase.table("secrets").update({
                "vault_id": vid,
                "username": admin_clean  # Para el dashboard
            })\
                .eq("owner_name", admin_clean)\
                .is_("vault_id", "null").execute()
            
            # También unificar registros que ya tengan vault_id pero username incorrecto
            self.supabase.table("secrets").update({"username": admin_clean})\
                .eq("owner_name", admin_clean)\
                .eq("is_private", 0).execute()

            # 3. Update masivo Local
            if self.sm:
                # Caso A: Reparar Vaults nulos
                self.sm.conn.execute(
                    "UPDATE secrets SET vault_id = ?, username = ? WHERE owner_name = ? AND vault_id IS NULL", 
                    (vid, admin_clean, admin_clean)
                )
                # Caso B: Unificar nombres de usuario para todos los registros del Admin (públicos)
                self.sm.conn.execute(
                    "UPDATE secrets SET username = ? WHERE owner_name = ? AND is_private = 0", 
                    (admin_clean, admin_clean)
                )
                self.sm.conn.commit()
                
            updated_count = len(res.data) if res.data else 0
            return True, f"Se repararon {updated_count} registros huérfanos asociados a la bóveda {vid}."
        except Exception as e:
            return False, f"Error en reparación: {e}"

    def cleanup_vault_cache(self):
        """
        Limpia cualquier rastro del usuario o IDs de bóveda en la RAM 
        y delega el mantenimiento físico al SecretsManager.
        """
        try:
            if self.sm:
                # El SecretsManager se encarga del VACUUM y limpieza de sesión
                return self.sm.cleanup_vault_cache()
            return True
        except Exception as e:
            self.logger.error(f"Error in UserManager.cleanup_vault_cache: {e}")
            return False

if __name__ == "__main__":
    import pyotp, time, logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    secret = pyotp.random_base32()
    logger.info(f"Generated test TOTP secret: {secret}")
    while True:
        tok = pyotp.TOTP(secret).now()
        logger.info(f"Current Token: {tok} (Remaining: {int(30 - time.time() % 30)}s)")
        time.sleep(1)
