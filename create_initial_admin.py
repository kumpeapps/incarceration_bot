#!/usr/bin/env python3
"""
Create initial admin user and API key for aMember integration
This script should be run once to bootstrap the system before aMember sync
"""

import sys
import os
import secrets
import string
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/justinkumpe/Documents/incarceration_bot/backend')

from database_connect import new_session
from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup

def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_initial_admin():
    """Create initial admin user and API key"""
    try:
        # Get database session
        session = new_session()
        
        # Check if admin group exists
        admin_group = session.query(Group).filter_by(name='admin').first()
        if not admin_group:
            print("Creating admin group...")
            admin_group = Group(
                name='admin',
                display_name='Administrator',
                description='System administrators with full access'
            )
            session.add(admin_group)
            session.commit()
            print(f"✓ Created admin group (ID: {admin_group.id})")
        
        # Check if initial admin user exists
        admin_user = session.query(User).filter_by(username='initial_admin').first()
        if admin_user:
            print("Initial admin user already exists")
            print(f"Username: {admin_user.username}")
            print(f"API Key: {admin_user.api_key}")
            return admin_user.api_key
        
        # Generate API key
        new_api_key = generate_api_key()
        
        # Create initial admin user
        print("Creating initial admin user...")
        admin_user = User(
            username='initial_admin',
            email='admin@system.local',
            password_hash='AMEMBER_MANAGED',  # Password managed by aMember
            api_key=new_api_key,
            is_active=True,
            created_at=datetime.utcnow(),
            amember_user_id=None  # Will be set when aMember creates the real admin
        )
        
        session.add(admin_user)
        session.commit()
        print(f"✓ Created initial admin user (ID: {admin_user.id})")
        
        # Assign admin to admin group
        user_group = UserGroup(
            user_id=admin_user.id,
            group_id=admin_group.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.utcnow()
        )
        session.add(user_group)
        session.commit()
        print("✓ Assigned user to admin group")
        
        session.close()
        
        print("\n" + "="*50)
        print("INITIAL ADMIN CREATED SUCCESSFULLY!")
        print("="*50)
        print("Username: initial_admin")
        print("Email: admin@system.local")
        print(f"API Key: {new_api_key}")
        print("\nUse this API key in your aMember plugin configuration.")
        print("This user will be replaced/updated when aMember syncs real admin users.")
        print("="*50)
        
        return new_api_key
        
    except Exception as e:
        print(f"Error creating initial admin: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return None

if __name__ == "__main__":
    print("Creating initial admin user for aMember integration...")
    result_api_key = create_initial_admin()
    if result_api_key:
        print(f"\nSuccess! API Key: {result_api_key}")
    else:
        print("Failed to create initial admin user")
        sys.exit(1)
