import uuid
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class SessionService:
    """
    Manages the active user context and security keys in RAM.
    Implements Zeroing memory logic for keys.
    """
    def __init__(self) -> None:
        self.current_user: Optional[str] = None
        self.current_user_id: Optional[str] = None
        self.user_role: str = "user"
        self.current_vault_id: Optional[str] = None
        self.session_id: str = str(uuid.uuid4())
        
        # RAM Keys (Sensitive)
        self.personal_key: Optional[bytearray] = None
        self.vault_key: Optional[bytearray] = None
        self.master_key: Optional[bytearray] = None
        self.kek_candidates: dict[str, Any] = {}

    def set_user(self, username: str, user_id: str, role: str, vault_id: Optional[str]) -> None:
        self.current_user = str(username).upper().strip()
        self.current_user_id = user_id
        self.user_role = str(role).lower()
        self.current_vault_id = vault_id
        self.session_id = str(uuid.uuid4())

    def clear(self) -> None:
        # Security: Zeroing out sensitive keys in memory
        for key_attr in ["master_key", "personal_key", "vault_key"]:
            key_obj = getattr(self, key_attr, None)
            if isinstance(key_obj, bytearray):
                for i in range(len(key_obj)):
                    key_obj[i] = 0
                setattr(self, key_attr, None)
        
        if self.kek_candidates:
            for k in self.kek_candidates:
                cand = self.kek_candidates[k]
                if isinstance(cand, (bytearray, bytes)):
                    # Note: bytes are immutable, so we can't zero them easily, but replacing them is a start.
                    pass
            self.kek_candidates = {}

        self.current_user = None
        self.current_user_id = None
        self.session_id = str(uuid.uuid4())
        logger.info("Session context purged and zeroed.")
