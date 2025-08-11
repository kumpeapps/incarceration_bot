#!/usr/bin/env python3
"""
Script to create initial admin user in the database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from models.User import User
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
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=User.hash_password("admin123"),
            role="admin"
        )
        
        session.add(admin_user)
        session.commit()
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        
        # Create test user
        existing_user = session.query(User).filter(User.username == "user").first()
        if not existing_user:
            test_user = User(
                username="user",
                email="user@example.com",
                hashed_password=User.hash_password("user123"),
                role="user"
            )
            session.add(test_user)
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
