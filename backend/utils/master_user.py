"""Master User module for API key authentication"""

from typing import List


class MasterUser:
    """
    Virtual user class for master API key authentication.
    
    Provides admin-level access for external integrations using the master API key.
    This class mimics the User model interface to maintain compatibility with
    existing authorization logic.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize MasterUser with admin privileges.
        
        Args:
            api_key (str): The master API key used for authentication
        """
        self.id = 0
        self.username = "api_integration"
        self.email = "api@system.local"
        self.is_active = True
        self.api_key = api_key

    def is_admin(self) -> bool:
        """Check if user has admin privileges (always True for master user)."""
        return True

    def has_group(self, group_name: str) -> bool:
        """Check if user belongs to a specific group (always True for master user)."""
        # Master user has access to all groups
        return True

    def get_groups(self) -> List[str]:
        """Get list of groups user belongs to (admin for master user)."""
        return ["admin"]

    @property
    def role(self) -> str:
        """Get user role (always admin for master user)."""
        return "admin"

    def to_dict(self) -> dict:
        """
        Convert the master user to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the master user
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "role": self.role,
            "groups": [{"name": "admin", "display_name": "Administrators"}],
        }
