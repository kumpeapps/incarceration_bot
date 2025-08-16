#!/usr/bin/env python3
"""
Script to initialize groups and migrate existing users to group-based system
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup
from helpers.user_group_service import UserGroupService
import database_connect as db

def initialize_groups():
    """Initialize default groups and ensure existing users are migrated."""
    session = db.new_session()
    
    try:
        service = UserGroupService(session)
        
        # Ensure default groups exist
        print("Creating default groups...")
        service.ensure_default_groups()
        
        # Get all users without groups
        users_without_groups = session.query(User).outerjoin(UserGroup).filter(UserGroup.user_id.is_(None)).all()
        
        if users_without_groups:
            print(f"Found {len(users_without_groups)} users without groups. Assigning default group...")
            for user in users_without_groups:
                # Assign 'user' group as default
                success = service.add_user_to_group(user.id, "user")
                if success:
                    print(f"Assigned user '{user.username}' to 'user' group")
                else:
                    print(f"Failed to assign user '{user.username}' to 'user' group")
        else:
            print("All users already have groups assigned.")
        
        # Display group summary
        print("\n--- Group Summary ---")
        groups = session.query(Group).filter(Group.is_active == True).all()
        for group in groups:
            user_count = session.query(UserGroup).filter(UserGroup.group_id == group.id).count()
            print(f"Group '{group.name}' ({group.display_name}): {user_count} users")
        
        session.commit()
        print("\nGroup initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing groups: {e}")
        session.rollback()
    finally:
        session.close()

def migrate_role_based_users():
    """Migrate users who still have role-based assignments (if role column exists)."""
    session = db.new_session()
    
    try:
        # Check if we have any users to migrate (this would be relevant after running the migration)
        print("Checking for any additional role-based migration needs...")
        
        # Get users who might need admin privileges
        users = session.query(User).all()
        service = UserGroupService(session)
        
        print(f"Found {len(users)} total users in system")
        
        # You can add specific logic here to assign admin groups to specific users
        # For example, if you know certain usernames should be admins:
        admin_usernames = ["admin"]  # Add actual admin usernames here
        
        for username in admin_usernames:
            user = session.query(User).filter(User.username == username).first()
            if user and not service.user_has_group(user.id, "admin"):
                print(f"Assigning admin privileges to user: {username}")
                service.add_user_to_group(user.id, "admin")
        
        session.commit()
        
    except Exception as e:
        print(f"Error during role migration: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Initializing group-based user management system...")
    print("=" * 50)
    
    initialize_groups()
    migrate_role_based_users()
    
    print("\nInitialization complete!")
    print("You can now manage user permissions through groups instead of roles.")
