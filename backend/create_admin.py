#!/usr/bin/env python3
"""
Script to create initial admin user in the database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup
import database_connect as db

def create_admin_user():
    """Create the initial admin user"""
    session = db.new_session()
    
    try:
        # Check if admin user already exists
        existing_admin = session.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists")
            return
        
        # Ensure admin group exists
        admin_group = session.query(Group).filter(Group.name == "admin").first()
        if not admin_group:
            admin_group = Group(
                name="admin",
                description="Administrator group with full access",
                is_active=True
            )
            session.add(admin_group)
            session.commit()
            print("Created admin group")
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=User.hash_password("admin123"),
            password_format="bcrypt",
            is_active=True
        )
        
        session.add(admin_user)
        session.commit()
        
        # Add user to admin group
        user_group = UserGroup(
            user_id=admin_user.id,
            group_id=admin_group.id
        )
        session.add(user_group)
        session.commit()
        
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        
        # Ensure user group exists
        user_group_obj = session.query(Group).filter(Group.name == "user").first()
        if not user_group_obj:
            user_group_obj = Group(
                name="user",
                description="Regular user group",
                is_active=True
            )
            session.add(user_group_obj)
            session.commit()
            print("Created user group")
        
        # Create test user
        existing_user = session.query(User).filter(User.username == "user").first()
        if not existing_user:
            test_user = User(
                username="user",
                email="user@example.com",
                hashed_password=User.hash_password("user123"),
                password_format="bcrypt",
                is_active=True
            )
            session.add(test_user)
            session.commit()
            
            # Add test user to user group
            test_user_group = UserGroup(
                user_id=test_user.id,
                group_id=user_group_obj.id
            )
            session.add(test_user_group)
            session.commit()
            
            print("Test user created successfully")
            print("Username: user")
            print("Password: user123")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_admin_user()
