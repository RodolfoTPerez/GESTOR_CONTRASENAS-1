import uuid
import logging
import threading
from typing import Optional, Any

logger = logging.getLogger(__name__)

class SessionService:
    """
    Manages the active user context and security keys in RAM.
    Implements Zeroing memory logic for keys.
    Thread-safe implementation using RLock and operation tracking.
    """
    def __init__(self) -> None:
        # Thread synchronization
        self._lock = threading.RLock()
        self._active_ops = 0  # Counter for background operations
        
        # User context
        self.current_user: Optional[str] = None
        self.current_user_id: Optional[str] = None
        self.user_role: str = "user"
        self.current_vault_id: Optional[str] = None
        self.session_id: str = str(uuid.uuid4())
        
        # RAM Keys (Sensitive) - Protected by lock
        self._personal_key: Optional[bytearray] = None
        self._vault_key: Optional[bytearray] = None
        self._master_key: Optional[bytearray] = None
        self.kek_candidates: dict[str, Any] = {}

    def start_operation(self):
        """Signals that a sensitive operation (like sync) is starting."""
        with self._lock:
            self._active_ops += 1

    def end_operation(self):
        """Signals that a sensitive operation has finished."""
        with self._lock:
            self._active_ops = max(0, self._active_ops - 1)

    # Thread-safe properties for sensitive keys
    @property
    def personal_key(self) -> Optional[bytearray]:
        with self._lock:
            return self._personal_key
    
    @personal_key.setter
    def personal_key(self, value: Optional[bytearray]) -> None:
        with self._lock:
            self._personal_key = value
    
    @property
    def vault_key(self) -> Optional[bytearray]:
        with self._lock:
            return self._vault_key
    
    @vault_key.setter
    def vault_key(self, value: Optional[bytearray]) -> None:
        with self._lock:
            self._vault_key = value
    
    @property
    def master_key(self) -> Optional[bytearray]:
        with self._lock:
            return self._master_key
    
    @master_key.setter
    def master_key(self, value: Optional[bytearray]) -> None:
        with self._lock:
            self._master_key = value

    def set_user(self, username: str, user_id: str, role: str, vault_id: Optional[str]) -> None:
        with self._lock:
            self.current_user = str(username).upper().strip()
            self.current_user_id = user_id
            self.user_role = str(role).lower()
            self.current_vault_id = vault_id
            self.session_id = str(uuid.uuid4())

    def clear(self) -> None:
        """
        Purges session and zeroes keys in memory.
        If background operations are active, it defers key zeroing to prevent crashes.
        """
        with self._lock:
            if self._active_ops > 0:
                logger.warning(f"Session clear requested while {self._active_ops} ops active. Postponing full zeroing.")
                self.current_user = None # Mark as logged out but keep keys for active ops
                return

            # Security: Zeroing out sensitive keys in memory
            for key_attr in ["_master_key", "_personal_key", "_vault_key"]:
                key_obj = getattr(self, key_attr, None)
                if isinstance(key_obj, bytearray):
                    for i in range(len(key_obj)):
                        key_obj[i] = 0
                    setattr(self, key_attr, None)
            
            if self.kek_candidates:
                self.kek_candidates = {}

            self.current_user = None
            self.current_user_id = None
            self.session_id = str(uuid.uuid4())
            logger.info("Session context purged and zeroed.")
