import sqlite3
import time
import logging
from typing import List, Dict, Any, Optional
from src.infrastructure.database.db_manager import DBManager

logger = logging.getLogger(__name__)

class SecretRepository:
    """
    Handles persistence of encrypted secrets.
    """
    def __init__(self, db_manager: DBManager) -> None:
        self.db = db_manager

    def add_secret(self, service: str, username: str, encrypted_secret: bytes, 
                   nonce: bytes, integrity: str, notes: Optional[str], 
                   is_private: int, owner_name: str, owner_id: Optional[str], 
                   vault_id: Optional[str], version: Optional[str] = None) -> Optional[int]:
        try:
            cursor = self.db.execute(
                """INSERT OR REPLACE INTO secrets 
                (service, username, secret, nonce, updated_at, deleted, owner_name, owner_id, integrity_hash, notes, is_private, vault_id, version) 
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)""",
                (service, username, sqlite3.Binary(encrypted_secret), sqlite3.Binary(nonce), int(time.time()), 
                owner_name, owner_id, integrity, notes, int(is_private), vault_id, version)
            )
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding secret for service '{service}': {e}")
            return None

    def batch_add_secrets(self, records_data: List[tuple]) -> bool:
        """
        Inserta múltiples registros en una sola transacción para máximo rendimiento.
        records_data: Lista de tuplas (service, username, secret_blob, nonce_blob, updated_at, owner_name, owner_id, integrity, notes, is_private, vault_id)
        """
        try:
            self.db.execute("BEGIN TRANSACTION")
            self.db.conn.executemany(
                """INSERT OR REPLACE INTO secrets 
                (service, username, secret, nonce, updated_at, deleted, owner_name, owner_id, integrity_hash, notes, is_private, vault_id, version) 
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)""",
                records_data
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error in batch_add_secrets: {e}")
            try: self.db.execute("ROLLBACK")
            except: pass
            return False

    def update_secret(self, sid: int, service: str, username: str, 
                      encrypted_secret: bytes, nonce: bytes, integrity: str, 
                      notes: Optional[str], is_private: int, version: Optional[str] = None) -> None:
        try:
            self.db.execute(
                """UPDATE secrets SET 
                service=?, username=?, secret=?, nonce=?, updated_at=?, integrity_hash=?, notes=?, is_private=?, synced=0, version=? 
                WHERE id=?""",
                (service, username, sqlite3.Binary(encrypted_secret), sqlite3.Binary(nonce), int(time.time()), integrity, notes, int(is_private), version, sid)
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Error updating secret ID {sid}: {e}")

    def get_all(self, current_user: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        try:
            user_target = str(current_user).upper()
            query = "SELECT * FROM secrets WHERE (is_private = 0 OR UPPER(owner_name) = ?)"
            params = [user_target]
            if not include_deleted: 
                query += " AND deleted = 0"
            
            cursor = self.db.execute(query, tuple(params))
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor]
        except Exception as e:
            logger.error(f"Error fetching secrets for user '{current_user}': {e}")
            return []

    def delete_secret(self, sid: int) -> None:
        try:
            self.db.execute("UPDATE secrets SET deleted=1, synced=0 WHERE id=?", (sid,))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error marking secret ID {sid} as deleted: {e}")

    def hard_delete(self, sid: int) -> None:
        try:
            self.db.execute("DELETE FROM secrets WHERE id=?", (sid,))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error permanently deleting secret ID {sid}: {e}")

    def restore_secret(self, sid: int) -> None:
        try:
            self.db.execute("UPDATE secrets SET deleted=0, synced=0 WHERE id=?", (sid,))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error restoring secret ID {sid}: {e}")

    def get_service_name_by_id(self, sid: int) -> str:
        try:
            ctx = self.db.execute("SELECT service FROM secrets WHERE id=?", (sid,)).fetchone()
            return ctx[0] if ctx else "Unknown"
        except Exception as e:
            logger.debug(f"Error getting service name for secret ID {sid}: {e}")
            return "Unknown"

    def check_exists(self, service_name: str) -> bool:
        try:
            target = str(service_name).strip().lower()
            query = """
                SELECT 1 FROM secrets 
                WHERE LOWER(TRIM(service)) = ? 
                AND deleted = 0
                LIMIT 1
            """
            cur = self.db.execute(query, (target,))
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking existence for service '{service_name}': {e}")
            return False

    def get_all_encrypted(self, current_user: str, only_mine: bool = False) -> List[Dict[str, Any]]:
        try:
            user_clean = str(current_user).upper()
            if only_mine:
                cursor = self.db.execute("SELECT * FROM secrets WHERE UPPER(owner_name) = ?", (user_clean,))
            else:
                cursor = self.db.execute("SELECT * FROM secrets WHERE is_private = 0 OR UPPER(owner_name) = ?", (user_clean,))
            
            cols = [d[0] for d in cursor.description]
            res = []
            for row in cursor:
                res.append(dict(zip(cols, row)))
            return res
        except Exception as e:
            logger.error(f"Error fetching encrypted secrets for user '{current_user}': {e}")
            return []

    def add_encrypted_direct(self, data_dict: Dict[str, Any]) -> None:
        try:
            cols = ", ".join(data_dict.keys())
            placeholders = ", ".join(["?"] * len(data_dict))
            vals = []
            for v in data_dict.values():
                if isinstance(v, (bytes, bytearray)):
                    vals.append(sqlite3.Binary(v))
                else:
                    vals.append(v)
            
            self.db.execute(f"INSERT OR REPLACE INTO secrets ({cols}) VALUES ({placeholders})", tuple(vals))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error in direct encrypted insertion: {e}")

    def get_existing_keys(self, current_user: str) -> set:
        """
        Retorna un set de tuplas (service, username) en minúsculas para validación rápida.
        No desencripta nada, es puramente estructural.
        """
        try:
            user_target = str(current_user).upper()
            query = "SELECT service, username FROM secrets WHERE (is_private = 0 OR UPPER(owner_name) = ?) AND deleted = 0"
            cursor = self.db.execute(query, (user_target,))
            return {(str(row[0]).strip().lower(), str(row[1]).strip().lower()) for row in cursor}
        except Exception as e:
            logger.error(f"Error fetching existing keys: {e}")
            return set()
