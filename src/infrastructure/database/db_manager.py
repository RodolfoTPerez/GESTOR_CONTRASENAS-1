import sqlite3
import re
import logging
import hashlib
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class DBManager:
    """
    Handles SQLite physical connections and schema structure.
    Isolated from security logic.
    """
    def __init__(self, app_data_name: str = "vultrax") -> None:
        self.conn: Optional[sqlite3.Connection] = None
        self.db_path: Optional[Path] = None
        self._initialize_db(app_data_name)

    def _initialize_db(self, name: str) -> None:
        if self.conn:
            try: self.conn.close()
            except Exception as e:
                logger.debug(f"Error closing previous connection: {e}")
        
        from src.infrastructure.config.path_manager import PathManager
        
        data_dir = PathManager.DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', str(name).lower().strip())
        filename = f"vault_{safe_name}.db" if safe_name != "vultrax" else PathManager.GLOBAL_DB.name
        
        self.db_path = data_dir / filename
        self.conn = sqlite3.connect(str(self.db_path), timeout=30, check_same_thread=False)
        self._check_schema()
    
    def _check_schema(self) -> None:
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_access (
                    vault_id TEXT PRIMARY KEY,
                    wrapped_master_key BLOB,
                    access_level TEXT DEFAULT 'member',
                    updated_at INTEGER,
                    synced INTEGER DEFAULT 1
                )
            """)
            self.conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value BLOB)")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, password_hash TEXT, salt TEXT, vault_salt BLOB, 
                    role TEXT, active BOOLEAN DEFAULT 1, protected_key BLOB, totp_secret BLOB, 
                    vault_id TEXT, wrapped_vault_key BLOB, user_id TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS secrets (
                    id INTEGER PRIMARY KEY, service TEXT, username TEXT, secret BLOB, nonce BLOB, 
                    integrity_hash TEXT, notes TEXT, updated_at INTEGER, deleted INTEGER DEFAULT 0, owner_name TEXT, 
                    synced INTEGER DEFAULT 0, is_private INTEGER DEFAULT 0, vault_id TEXT, key_type TEXT,
                    cloud_id TEXT, owner_id TEXT, version TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS security_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER, user_name TEXT, 
                    action TEXT, service TEXT, status TEXT DEFAULT 'SUCCESS', details TEXT, 
                    device_info TEXT, synced INTEGER DEFAULT 0, user_id TEXT
                )
            """)
            
            # Table to track deletions made offline that need to be synced to cloud
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_deletes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cloud_id TEXT NOT NULL,
                    deleted_at INTEGER NOT NULL
                )
            """)
            
            self.conn.execute("DROP INDEX IF EXISTS idx_unique_service")
            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_record 
                ON secrets (service, username, owner_name)
            """)
            self.conn.commit()
            
            # Hotfix migrations logic (simplified but equivalent)
            migrations = [
                ("users", "user_id", "TEXT"),
                ("users", "synced", "INTEGER DEFAULT 1"),  # Track offline user creation sync
                ("secrets", "owner_id", "TEXT"),
                ("security_audit", "user_id", "TEXT"),
                ("secrets", "cloud_id", "TEXT"),
                ("secrets", "version", "TEXT")
            ]
            for t, c, tp in migrations:
                try:
                    self.conn.execute(f"ALTER TABLE {t} ADD COLUMN {c} {tp}")
                except Exception as e: 
                    logger.debug(f"Migration for {t}.{c} skipped or failed (likely exists): {e}")
            
            self.conn.commit()
            
            # Normalización estructural de datos legacy (Professional Data Clean-up)
            self.conn.execute("UPDATE secrets SET is_private = 0 WHERE is_private IS NULL")
            self.conn.execute("UPDATE secrets SET synced = 0 WHERE synced IS NULL")
            self.conn.execute("UPDATE secrets SET deleted = 0 WHERE deleted IS NULL")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error checking or updating schema: {e}")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        if not self.conn:
            raise RuntimeError("Database connection not initialized")
        return self.conn.execute(query, params)

    def commit(self) -> None:
        if self.conn:
            self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def vacuum(self) -> None:
        try:
            if self.conn:
                self.conn.execute("VACUUM")
        except Exception as e:
            logger.debug(f"Vacuum failed: {e}")
