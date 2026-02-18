"""
HWIDService - Hardware ID Management

Handles device fingerprinting and hardware ID validation.
Extracted from UserManager as part of SRP refactoring.
"""

import logging
from typing import Optional
from src.infrastructure.security.device_fingerprint import get_hwid

logger = logging.getLogger(__name__)


class HWIDService:
    """
    Manages hardware ID (HWID) operations for device binding.
    
    Responsibilities:
    - Generate current device HWID
    - Validate HWID against stored value
    - Link HWID to user accounts
    """
    
    def __init__(self, user_repository=None):
        """
        Initialize HWID service.
        
        Args:
            user_repository: UserRepository instance for database operations
        """
        self.users = user_repository
        self.logger = logger
    
    def get_current_hwid(self) -> str:
        """
        Get the current device's hardware ID.
        
        Returns:
            str: Hardware ID fingerprint
        """
        try:
            hwid = get_hwid()
            self.logger.debug(f"Generated HWID: {hwid[:8]}...")
            return hwid
        except Exception as e:
            self.logger.error(f"Failed to generate HWID: {e}")
            return "UNKNOWN_DEVICE"
    
    def validate_hwid(self, username: str, stored_hwid: Optional[str]) -> bool:
        """
        Validate if current device HWID matches stored HWID.
        
        Args:
            username: Username for logging
            stored_hwid: HWID stored in database
            
        Returns:
            bool: True if HWID matches or is not set, False otherwise
        """
        if not stored_hwid:
            self.logger.debug(f"No HWID stored for {username}, allowing access")
            return True
        
        current_hwid = self.get_current_hwid()
        
        if current_hwid == stored_hwid:
            self.logger.debug(f"HWID match for {username}")
            return True
        else:
            self.logger.warning(f"HWID mismatch for {username}: expected {stored_hwid[:8]}..., got {current_hwid[:8]}...")
            return False
    
    def link_hwid(self, username: str, hwid: Optional[str] = None) -> bool:
        """
        Link a hardware ID to a user account.
        
        Args:
            username: Username to link HWID to
            hwid: HWID to link (if None, uses current device)
            
        Returns:
            bool: True if successful
        """
        if not self.users:
            self.logger.error("UserRepository not available for HWID linking")
            return False
        
        try:
            hwid_to_link = hwid or self.get_current_hwid()
            
            # Update user record with HWID
            self.users.update_user_hwid(username, hwid_to_link)
            
            self.logger.info(f"HWID linked for {username}: {hwid_to_link[:8]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to link HWID for {username}: {e}")
            return False
    
    def update_hwid(self, username: str, new_hwid: str) -> bool:
        """
        Update the HWID for a user (e.g., after device change).
        
        Args:
            username: Username to update
            new_hwid: New HWID value
            
        Returns:
            bool: True if successful
        """
        return self.link_hwid(username, new_hwid)
    
    def should_update_hwid(self, username: str, stored_hwid: Optional[str]) -> bool:
        """
        Determine if HWID should be updated for this user.
        
        Args:
            username: Username to check
            stored_hwid: Currently stored HWID
            
        Returns:
            bool: True if HWID should be updated
        """
        # Update if no HWID is stored
        if not stored_hwid:
            self.logger.debug(f"No HWID stored for {username}, should update")
            return True
        
        # Update if current device doesn't match
        current_hwid = self.get_current_hwid()
        if current_hwid != stored_hwid:
            self.logger.info(f"HWID changed for {username}, should update")
            return True
        
        return False
