#!/usr/bin/env python3
"""
Test script for group-based user management system
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup
from helpers.user_group_service import UserGroupService
import database_connect as db

def test_group_system():
    """Test the group-based user management system."""
    session = db.new_session()
    
    try:
        service = UserGroupService(session)
        
        print("Testing Group-Based User Management System")
        print("=" * 50)
        
        # Test 1: Create test groups
        print("1. Creating test groups...")
        test_group = service.create_group("test_group", "Test Group", "Group for testing")
        if test_group:
            print("✓ Test group created successfully")
        else:
            print("✗ Failed to create test group")
        
        # Test 2: Create test user
        print("\n2. Creating test user...")
        test_user = User(
            username="test_user_groups",
            email="test@example.com",
            hashed_password=User.hash_password("test123")
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        print(f"✓ Test user created with ID: {test_user.id}")
        
        # Test 3: Assign user to groups
        print("\n3. Testing group assignments...")
        success1 = service.add_user_to_group(test_user.id, "user")
        success2 = service.add_user_to_group(test_user.id, "test_group")
        
        if success1 and success2:
            print("✓ User assigned to groups successfully")
        else:
            print("✗ Failed to assign user to groups")
        
        # Test 4: Check user groups
        print("\n4. Testing group membership...")
        user_groups = service.get_user_groups(test_user.id)
        print(f"User groups: {[g['name'] for g in user_groups]}")
        
        # Test 5: Test User model methods
        print("\n5. Testing User model methods...")
        session.refresh(test_user)  # Refresh to get relationships
        
        print(f"has_group('user'): {test_user.has_group('user')}")
        print(f"has_group('admin'): {test_user.has_group('admin')}")
        print(f"is_admin(): {test_user.is_admin()}")
        print(f"get_groups(): {test_user.get_groups()}")
        print(f"role property: {test_user.role}")
        
        # Test 6: Test admin user
        print("\n6. Testing admin user...")
        admin_user = session.query(User).filter(User.username == "admin").first()
        if admin_user:
            print(f"Admin user found: {admin_user.username}")
            print(f"Admin has_group('admin'): {admin_user.has_group('admin')}")
            print(f"Admin is_admin(): {admin_user.is_admin()}")
            print(f"Admin role property: {admin_user.role}")
        else:
            print("No admin user found")
        
        # Test 7: Test group users
        print("\n7. Testing group user listing...")
        admin_users = service.get_group_users("admin")
        user_users = service.get_group_users("user")
        
        print(f"Admin group has {len(admin_users)} users")
        print(f"User group has {len(user_users)} users")
        
        # Test 8: Remove user from group
        print("\n8. Testing group removal...")
        success = service.remove_user_from_group(test_user.id, "test_group")
        if success:
            print("✓ User removed from test_group successfully")
            updated_groups = service.get_user_groups(test_user.id)
            print(f"Updated user groups: {[g['name'] for g in updated_groups]}")
        else:
            print("✗ Failed to remove user from group")
        
        # Cleanup
        print("\n9. Cleaning up test data...")
        session.delete(test_user)
        if test_group:
            session.delete(test_group)
        session.commit()
        print("✓ Test cleanup completed")
        
        print("\n" + "=" * 50)
        print("Group system testing completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def test_user_creation_with_groups():
    """Test creating users with groups like the API would."""
    session = db.new_session()
    
    try:
        service = UserGroupService(session)
        
        print("\nTesting User Creation with Groups (API-style)")
        print("=" * 50)
        
        # Simulate API user creation
        user_data = {
            "username": "api_test_user",
            "email": "apitest@example.com",
            "password": "test123",
            "groups": ["user", "moderator"]
        }
        
        # Create user
        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=User.hash_password(user_data["password"])
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # Assign groups
        for group_name in user_data["groups"]:
            success = service.add_user_to_group(new_user.id, group_name)
            print(f"Assigned group '{group_name}': {'✓' if success else '✗'}")
        
        # Test user dict output
        user_dict = new_user.to_dict()
        print(f"\nUser dict output:")
        print(f"- Username: {user_dict['username']}")
        print(f"- Groups: {[g['name'] for g in user_dict['groups']]}")
        print(f"- Role (compat): {user_dict.get('role', 'N/A')}")
        
        # Cleanup
        session.delete(new_user)
        session.commit()
        print("\n✓ API-style test completed successfully!")
        
    except Exception as e:
        print(f"Error during API-style testing: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("Running Group-Based User Management Tests")
    print("This will test the new group system functionality")
    print()
    
    test_group_system()
    test_user_creation_with_groups()
    
    print("\nAll tests completed!")
    print("If you see any errors above, please check your database setup and migrations.")
