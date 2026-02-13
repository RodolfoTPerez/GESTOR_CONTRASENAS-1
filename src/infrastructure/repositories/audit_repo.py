import time
import socket
import logging
from typing import List, Dict, Any, Optional
from src.infrastructure.database.db_manager import DBManager

logger = logging.getLogger(__name__)

class AuditRepository:
    """
    Handles persistence of security audit logs.
    """
    def __init__(self, db_manager: DBManager) -> None:
        self.db = db_manager

    def log_event(self, user_name: str, user_id: Optional[str], action: str, 
                  service: str = "-", status: str = "SUCCESS", details: str = "-", **kwargs: Any) -> None:
        try:
            device = socket.gethostname()
            final_details = details
            target = kwargs.get("target_user", "-")
            if target != "-":
                final_details = f"{details} | Target: {target}"
            
            self.db.execute(
                "INSERT INTO security_audit (timestamp, user_name, action, service, status, details, device_info, synced, user_id) VALUES (?,?,?,?,?,?,?,0,?)",
                (int(time.time()), user_name, action, service, status, final_details, device, user_id)
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging event '{action}' for user '{user_name}': {e}")

    def get_logs(self, user_name: str, role: str, limit: int = 500) -> List[Dict[str, Any]]:
        try:
            if str(role).lower() == "admin":
                query = "SELECT * FROM security_audit ORDER BY timestamp DESC LIMIT ?"
                params: tuple = (limit,)
            else:
                query = "SELECT * FROM security_audit WHERE UPPER(user_name) = ? ORDER BY timestamp DESC LIMIT ?"
                params = (str(user_name).upper(), limit)
                
            cursor = self.db.execute(query, params)
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor]
        except Exception as e:
            logger.error(f"Error reading logs for user '{user_name}': {e}")
            return []

    def get_count(self) -> int:
        try:
            cursor = self.db.execute("SELECT COUNT(*) FROM security_audit")
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            logger.debug(f"Error getting audit count: {e}")
            return 0

    def get_pending_logs(self) -> List[tuple]:
        try:
            cursor = self.db.execute("SELECT * FROM security_audit WHERE synced = 0")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching pending audit logs: {e}")
            return []

    def mark_as_synced(self) -> None:
        try:
            self.db.execute("UPDATE security_audit SET synced = 1 WHERE synced = 0")
            self.db.commit()
        except Exception as e:
            logger.error(f"Error marking audit logs as synced: {e}")
