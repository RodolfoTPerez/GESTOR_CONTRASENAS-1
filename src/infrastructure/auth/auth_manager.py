"""
AuthManager - Authentication and Authorization

Handles user authentication, password verification, and 2FA.
Extracted from UserManager as part of SRP refactoring.
"""

import pyotp
import logging
import hashlib
from typing import Optional, Dict, Any, Tuple
from supabase import Client
from config.config import AUTH_MAX_ATTEMPTS, AUTH_WINDOW_SECONDS
from src.infrastructure.crypto_engine import CryptoEngine, rate_limit
from src.infrastructure.security.device_fingerprint import get_hwid

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages authentication and authorization operations.
    
    Responsibilities:
    - Password hashing and verification
    - User authentication (local and cloud)
    - 2FA (TOTP) management
    - Credential normalization
    """
    
    def __init__(self, db_manager, supabase_client: Client, security_service=None):
        """
        Initialize authentication manager.
        
        Args:
            db_manager: DBManager instance
            supabase_client: Supabase client for cloud auth
            security_service: SecurityService for crypto operations
        """
        self.db = db_manager
        self.supabase = supabase_client
        self.security = security_service
        self.logger = logger
        self.crypto = CryptoEngine()
    
    # ===== PASSWORD OPERATIONS =====
    
    def hash_password(self, password: str, salt: Any = None) -> Tuple[str, str]:
        """
        Generate a secure password hash using best available algorithm.
        
        - New users: Argon2id (if enabled)
        - Legacy: PBKDF2-SHA256
        
        Args:
            password: Plain text password
            salt: Optional salt (only used for PBKDF2)
            
        Returns:
            Tuple[str, str]: (hash, salt_hex)
                             For Argon2: salt_hex is empty string
                             For PBKDF2: salt_hex contains hex salt
        """
        hash_result, salt_bytes = self.crypto.hash_user_password_auto(password, salt)
        
        # For Argon2, salt is embedded in hash, return empty string
        # For PBKDF2, return hex-encoded salt
        salt_hex = salt_bytes.hex() if salt_bytes else ""
        
        return hash_result, salt_hex
    
    def verify_password(self, password: str, salt: Any, stored_hash: str) -> bool:
        """
        Verifica una contraseña contra un hash almacenado.
        Soporta tanto PBKDF2 como Argon2 mediante auto-detección.
        
        Args:
            password: Contraseña en texto plano
            salt: Salt del usuario (puede ser None para Argon2)
            stored_hash: Hash almacenado
            
        Returns:
            bool: True si la contraseña es válida
        """
        try:
            # Debug logging
            self.logger.debug(f"[AuthManager] verify_password called:")
            self.logger.debug(f"  - stored_hash type: {type(stored_hash)}, starts with: {stored_hash[:20] if stored_hash else 'None'}")
            self.logger.debug(f"  - salt type: {type(salt)}, value: {salt if isinstance(salt, str) else (salt.hex() if salt else 'None')}")
            
            # Use auto-detection method from CryptoEngine
            result = self.crypto.verify_user_password_auto(password, salt, stored_hash)
            
            self.logger.debug(f"[AuthManager] verify_user_password_auto result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    # ===== 2FA (TOTP) OPERATIONS =====
    
    def generate_totp_secret(self) -> str:
        """
        Generate a new TOTP secret for 2FA.
        
        Returns:
            str: Base32 encoded TOTP secret
        """
        return pyotp.random_base32()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """
        Verify a TOTP token.
        
        Args:
            secret: TOTP secret (base32)
            token: 6-digit TOTP code
            
        Returns:
            bool: True if token is valid
        """
        try:
            if not secret or not token:
                return False
            
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=1)
            
            if is_valid:
                self.logger.debug("2FA token verified successfully")
            else:
                self.logger.warning("2FA token verification failed")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"2FA verification error: {e}")
            return False
    
    def get_totp_secret(self, username: str) -> Optional[str]:
        """
        Retrieve TOTP secret for a user.
        
        Args:
            username: Username
            
        Returns:
            Optional[str]: TOTP secret or None
        """
        try:
            response = self.supabase.table("users").select("totp_secret").eq("username", username.upper()).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("totp_secret")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving TOTP secret: {e}")
            return None
    
    # ===== AUTHENTICATION =====
    
    from config.config import AUTH_MAX_ATTEMPTS, AUTH_WINDOW_SECONDS
    @rate_limit(max_attempts=AUTH_MAX_ATTEMPTS, window=AUTH_WINDOW_SECONDS)
    def check_local_login(self, username: str, password: str) -> bool:
        """
        Validate login using local database only.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            bool: True if authentication successful
        """
        try:
            username = username.upper().strip()
            
            # Query local database
            cursor = self.db.conn.execute(
                "SELECT password_hash, vault_salt FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if not row:
                self.logger.warning(f"User {username} not found in local DB")
                return False
            
            stored_hash, salt = row
            
            # Verify password
            if self.verify_password(password, salt, stored_hash):
                self.logger.info(f"Local authentication successful for {username}")
                return True
            else:
                self.logger.warning(f"Password mismatch for {username}")
                return False
                
        except Exception as e:
            self.logger.error(f"Local login error: {e}")
            return False
    
    def validate_user_access(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Validate user access via Supabase (cloud authentication).
        
        Performs:
        1. User existence and active status check
        2. HWID binding validation
        3. Vault access retrieval
        
        Args:
            username: Username to validate
            
        Returns:
            Optional[Dict]: User profile with keys and metadata, or None
        """
        try:
            username_clean = username.upper().strip()
            
            # Query Supabase for user
            response = self.supabase.table("users").select("*").ilike("username", username_clean).execute()
            
            if not response.data or len(response.data) == 0:
                self.logger.warning(f"User {username_clean} not found in Supabase")
                return None
            
            user = response.data[0]
            
            # Check if user is active
            if not user.get("active", True):
                self.logger.warning(f"User {username_clean} is deactivated")
                return None
            
            # HWID validation
            stored_hwid = user.get("linked_hwid")
            if stored_hwid:
                current_hwid = get_hwid()
                if current_hwid != stored_hwid:
                    self.logger.warning(f"HWID mismatch for {username_clean}")
                    # Update HWID if needed
                    try:
                        self.supabase.table("users").update({"linked_hwid": current_hwid}).eq("username", username_clean).execute()
                        self.logger.info(f"HWID updated for {username_clean}")
                    except Exception as e:
                        self.logger.error(f"Failed to update HWID: {e}")
            
            # Get vault access
            u_id = user.get("id")
            v_id = user.get("vault_id")
            
            if u_id and v_id:
                try:
                    va_res = self.supabase.table("vault_access").select("wrapped_master_key").eq("user_id", u_id).eq("vault_id", v_id).execute()
                    
                    if va_res.data and len(va_res.data) > 0:
                        user["wrapped_vault_key"] = va_res.data[0].get("wrapped_master_key")
                        self.logger.info(f"[Auth] Found Team Key in vault_access for {username_clean}")
                except Exception as e:
                    self.logger.debug(f"No vault_access entry: {e}")
            
            # Get vault name
            if v_id:
                try:
                    v_res = self.supabase.table("vaults").select("name").eq("id", v_id).execute()
                    if v_res.data and len(v_res.data) > 0:
                        vault_name = v_res.data[0].get("name", "UNKNOWN")
                        user["vault_name"] = vault_name
                        self.logger.info(f"Vault name synchronized: {vault_name}")
                except Exception as e:
                    self.logger.debug(f"Could not fetch vault name: {e}")
            
            self.logger.info(f"[Auth] Normalized credentials for {username_clean} (Professional Sync)")
            return user
            
        except Exception as e:
            self.logger.error(f"Cloud validation error for {username}: {e}")
            return None
    
    # ===== CREDENTIAL NORMALIZATION =====
    
    def _normalize_credentials(self, username: str, password: str) -> Tuple[str, str]:
        """
        Normalize username and password for consistent authentication.
        
        Args:
            username: Raw username
            password: Raw password
            
        Returns:
            Tuple[str, str]: (normalized_username, normalized_password)
        """
        # Username: uppercase, no spaces
        username_clean = username.upper().strip().replace(" ", "")
        
        # Password: strip whitespace only
        password_clean = password.strip()
        
        return username_clean, password_clean
