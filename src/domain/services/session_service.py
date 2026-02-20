import uuid
import logging
import threading
from typing import Optional, Any, Dict
from src.infrastructure.secure_memory import SecureBytes

logger = logging.getLogger(__name__)

class SessionService:
    """
    Manages the active user context and security keys in RAM.
    Implements Military-Grade Zeroing memory logic for keys via SecureBytes.
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
        
        # Security Containers
        self._personal_key: Optional[SecureBytes] = None
        self._vault_key: Optional[SecureBytes] = None
        self._master_key: Optional[SecureBytes] = None
        self.kek_candidates: Dict[str, SecureBytes] = {}

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
            return self._personal_key.get_raw() if self._personal_key else None
    
    @personal_key.setter
    def personal_key(self, value: Any) -> None:
        with self._lock:
            if self._personal_key: self._personal_key.clear()
            self._personal_key = SecureBytes(value) if value else None
    
    @property
    def vault_key(self) -> Optional[bytearray]:
        with self._lock:
            return self._vault_key.get_raw() if self._vault_key else None
    
    @vault_key.setter
    def vault_key(self, value: Any) -> None:
        with self._lock:
            if self._vault_key: self._vault_key.clear()
            self._vault_key = SecureBytes(value) if value else None
    
    @property
    def master_key(self) -> Optional[bytearray]:
        with self._lock:
            return self._master_key.get_raw() if self._master_key else None
    
    @master_key.setter
    def master_key(self, value: Any) -> None:
        with self._lock:
            if self._master_key: self._master_key.clear()
            self._master_key = SecureBytes(value) if value else None

    def set_user(self, username: str, user_id: str, role: str, vault_id: Optional[str]) -> None:
        with self._lock:
            self.current_user = str(username).upper().strip()
            self.current_user_id = user_id
            self.user_role = str(role).lower()
            self.current_vault_id = vault_id
            self.session_id = str(uuid.uuid4())

    def clear(self) -> None:
        """Purges session and physically zeroes keys using SecureBytes."""
        with self._lock:
            if self._active_ops > 0:
                logger.warning(f"Session clear requested while {self._active_ops} ops active. Postponing full zeroing.")
                self.current_user = None
                return

            # Zeroing containers
            if self._master_key: self._master_key.clear(); self._master_key = None
            if self._personal_key: self._personal_key.clear(); self._personal_key = None
            if self._vault_key: self._vault_key.clear(); self._vault_key = None
            
            for k in self.kek_candidates.values():
                if hasattr(k, 'clear'):
                    k.clear()
            self.kek_candidates = {}

            self.current_user = None
            self.current_user_id = None
            self.session_id = str(uuid.uuid4())
            
            import gc; gc.collect()
            logger.info("[Security] Session context purged and zeroed securely.")
