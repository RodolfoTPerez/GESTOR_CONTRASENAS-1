import os
import shutil
import sqlite3
import logging
import time
import secrets
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.infrastructure.config.path_manager import PathManager
from src.infrastructure.crypto_engine import CryptoEngine

logger = logging.getLogger(__name__)

class MaintenanceService:
    """
    Provides administrative and emergency recovery tools.
    Integrates functionality from previous external scripts (nuke_local, repair_vault).
    """
    
    @staticmethod
    def nuke_local_state() -> int:
        """
        [NUCLEAR OPERATION] Removes all local databases to force a clean cloud sync.
        Returns the count of deleted files.
        """
        logger.warning("[Maintenance] STARTING NUCLEAR RESET (Local State Only)")
        data_dir = PathManager.DATA_DIR
        count = 0
        
        if not data_dir.exists():
            return 0
            
        for pattern in ["*.db", "*.db-journal", "*.db-wal"]:
            for f in data_dir.glob(pattern):
                try:
                    # Create final backup before nuking
                    backup_name = f"{f.name}.{int(time.time())}.nuclear.bak"
                    shutil.copy2(f, data_dir / backup_name)
                    
                    logger.info(f"[Maintenance] Nuking local file: {f.name}")
                    f.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"[Maintenance] Failed to nuke {f.name}: {e}")
        
        return count

    @staticmethod
    def repair_vault_key(username: str, password: str, db_manager) -> bool:
        """
        [REPAIR OPERATION] Regenerates a vault master key and updates local access.
        Useful when the local vault key is corrupt or lost.
        """
        username_upper = username.upper()
        logger.warning(f"[Maintenance] REPAIRING VAULT KEY for {username_upper}")
        
        try:
            # 1. Fetch User Profile
            cur = db_manager.execute("SELECT * FROM users WHERE UPPER(username) = ?", (username_upper,))
            user = cur.fetchone()
            if not user:
                logger.error(f"[Maintenance] User {username_upper} not found in database.")
                return False
            
            # Use column indices/names depending on row_factory
            profile = dict(zip([d[0] for d in cur.description], user)) if not isinstance(user, dict) else user
            vault_id = profile.get("vault_id")
            
            # 2. Derive Salt
            vault_salt = profile.get("vault_salt")
            if not vault_salt:
                vault_salt = secrets.token_bytes(16)
            
            # 3. Generate NEW Vault Master Key (VMK)
            new_vmk = secrets.token_bytes(32)
            
            # 4. Wrap with password (Uses current KDF settings)
            wrapped_key = CryptoEngine.wrap_vault_key(new_vmk, password, vault_salt)
            
            # 5. Update Database
            db_manager.execute(
                "UPDATE users SET wrapped_vault_key = ?, vault_salt = ? WHERE UPPER(username) = ?",
                (sqlite3.Binary(wrapped_key), sqlite3.Binary(vault_salt), username_upper)
            )
            
            if vault_id:
                db_manager.execute("""
                    INSERT OR REPLACE INTO vault_access 
                    (vault_id, wrapped_master_key, access_level, updated_at, synced) 
                    VALUES (?, ?, ?, ?, 0)
                """, (vault_id, sqlite3.Binary(wrapped_key), 'admin', int(time.time()), 0))
            
            db_manager.commit()
            logger.info(f"[Maintenance] Vault key for {username_upper} repaired successfully.")
            return True
            
        except Exception as e:
            logger.error(f"[Maintenance] Repair failed: {e}")
            return False
