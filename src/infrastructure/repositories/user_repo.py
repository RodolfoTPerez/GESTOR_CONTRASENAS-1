import sqlite3
import logging
from typing import Optional, Any, Dict
from src.infrastructure.database.db_manager import DBManager

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Handles persistence of user profiles and vault metadata.
    """
    def __init__(self, db_manager: DBManager) -> None:
        self.db = db_manager

    def get_meta(self, key: str) -> Optional[str]:
        try:
            cur = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,))
            row = cur.fetchone()
            if row:
                val = row[0]
                if isinstance(val, bytes): return val.decode('utf-8')
                return str(val)
            return None
        except Exception as e:
            logger.error(f"Error reading metadata for key '{key}': {e}")
            return None

    def set_meta(self, key: str, value: Any) -> None:
        try:
            val = value.encode('utf-8') if isinstance(value, str) else value
            self.db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, sqlite3.Binary(val)))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error setting metadata for key '{key}': {e}")

    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            target = str(username).upper().strip().replace(" ", "")
            cur = self.db.execute("SELECT * FROM users WHERE UPPER(username) = ?", (target,))
            row = cur.fetchone()
            if not row: return None
            return dict(zip([d[0] for d in cur.description], row))
        except Exception as e:
            logger.error(f"Error reading profile for '{username}': {e}")
            return None

    def save_profile(self, username: str, pwd_hash: str, salt: str, vault_salt: Optional[bytes], 
                     role: str = "user", protected_key: Optional[bytes] = None, 
                     totp_secret: Optional[str] = None, vault_id: Optional[str] = None, 
                     wrapped_vault_key: Optional[bytes] = None, user_id: Optional[str] = None) -> None:
        cols = ["username", "password_hash", "salt", "vault_salt", "role", "protected_key", "totp_secret", "vault_id", "wrapped_vault_key", "user_id"]
        
        # Binary data handling
        v_salt_bin = sqlite3.Binary(vault_salt) if vault_salt else None
        p_key_bin = sqlite3.Binary(protected_key) if protected_key else None
        w_vk_bin = sqlite3.Binary(wrapped_vault_key) if wrapped_vault_key else None
        totp_text = str(totp_secret) if totp_secret else None
        
        vals = [str(username).upper().strip().replace(" ", ""), pwd_hash, salt, v_salt_bin, role, p_key_bin, totp_text, vault_id, w_vk_bin, user_id]
        placeholders = ", ".join(["?"] * len(vals))
        self.db.execute(f"INSERT OR REPLACE INTO users ({', '.join(cols)}) VALUES ({placeholders})", tuple(vals))
        self.db.commit()
    def update_vault_access(self, username: str, vault_id: str, wrapped_key: bytes) -> bool:
        try:
            # [FIX] Ensure wrapped_key is bytes
            if isinstance(wrapped_key, str):
                wrapped_key = bytes.fromhex(wrapped_key)
            
            self.db.execute(
                "UPDATE users SET vault_id = ?, wrapped_vault_key = ? WHERE UPPER(username) = ?",
                (vault_id, sqlite3.Binary(wrapped_key), str(username).upper())
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating vault access for '{username}': {e}")
            return False

    def update_protected_key(self, username: str, protected_key: bytes) -> bool:
        """Saves a re-encrypted Personal Key (SVK) to the local database."""
        try:
            self.db.execute(
                "UPDATE users SET protected_key = ? WHERE UPPER(username) = ?",
                (sqlite3.Binary(protected_key), str(username).upper())
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating protected key for '{username}': {e}")
            return False
