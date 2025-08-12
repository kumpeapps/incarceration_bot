"""User Group Management Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup


class UserGroupService:
    """Service for managing user group relationships."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_user_to_group(self, user_id: int, group_name: str, assigned_by_user_id: Optional[int] = None) -> bool:
        """Add a user to a group."""
        try:
            # Get group by name
            group = self.db.query(Group).filter(Group.name == group_name, Group.is_active == True).first()
            if not group:
                return False
            
            # Check if relationship already exists
            existing = self.db.query(UserGroup).filter(
                UserGroup.user_id == user_id,
                UserGroup.group_id == group.id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Create new relationship
            user_group = UserGroup(
                user_id=user_id,
                group_id=group.id,
                assigned_by=assigned_by_user_id
            )
            
            self.db.add(user_group)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error adding user to group: {e}")
            return False
    
    def remove_user_from_group(self, user_id: int, group_name: str) -> bool:
        """Remove a user from a group."""
        try:
            # Get group by name
            group = self.db.query(Group).filter(Group.name == group_name).first()
            if not group:
                return False
            
            # Find and delete the relationship
            user_group = self.db.query(UserGroup).filter(
                UserGroup.user_id == user_id,
                UserGroup.group_id == group.id
            ).first()
            
            if user_group:
                self.db.delete(user_group)
                self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error removing user from group: {e}")
            return False
    
    def get_user_groups(self, user_id: int) -> List[dict]:
        """Get all groups for a user."""
        user_groups = self.db.query(UserGroup).join(Group).filter(
            UserGroup.user_id == user_id,
            Group.is_active == True
        ).all()
        
        return [ug.group.to_dict() for ug in user_groups if ug.group]
    
    def get_group_users(self, group_name: str) -> List[dict]:
        """Get all users in a group."""
        group = self.db.query(Group).filter(Group.name == group_name, Group.is_active == True).first()
        if not group:
            return []
        
        user_groups = self.db.query(UserGroup).join(User).filter(
            UserGroup.group_id == group.id,
            User.is_active == True
        ).all()
        
        return [ug.user.to_dict() for ug in user_groups if ug.user]
    
    def create_group(self, name: str, display_name: str, description: Optional[str] = None) -> Optional[Group]:
        """Create a new group."""
        try:
            # Check if group already exists
            existing = self.db.query(Group).filter(Group.name == name).first()
            if existing:
                return existing
            
            group = Group(
                name=name,
                display_name=display_name,
                description=description
            )
            
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
            return group
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating group: {e}")
            return None
    
    def user_has_group(self, user_id: int, group_name: str) -> bool:
        """Check if a user belongs to a specific group."""
        count = self.db.query(UserGroup).join(Group).filter(
            UserGroup.user_id == user_id,
            Group.name == group_name,
            Group.is_active == True
        ).count()
        
        return count > 0
    
    def user_is_admin(self, user_id: int) -> bool:
        """Check if a user has admin privileges."""
        return self.user_has_group(user_id, "admin")
    
    def ensure_default_groups(self) -> None:
        """Ensure default groups exist."""
        default_groups = [
            {
                "name": "admin",
                "display_name": "Administrators",
                "description": "Full system access and user management"
            },
            {
                "name": "user",
                "display_name": "Regular Users", 
                "description": "Standard user access to monitor functionality"
            },
            {
                "name": "moderator",
                "display_name": "Moderators",
                "description": "Enhanced access for content moderation"
            }
        ]
        
        for group_data in default_groups:
            self.create_group(**group_data)
