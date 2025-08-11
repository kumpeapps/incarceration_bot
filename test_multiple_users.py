#!/usr/bin/env python3
"""
Test script to verify notification system handles multiple users with same monitors
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token for admin user"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def create_test_user(token, username, password):
    """Create a test user"""
    headers = {"Authorization": f"Bearer {token}"}
    user_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to create user {username}: {response.text}")
        return None

def create_monitor_for_user(token, user_id, monitor_name):
    """Create a monitor and assign it to a specific user"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create monitor
    monitor_data = {
        "name": monitor_name,
        "notify_address": f"user{user_id}@test.com",
        "notify_method": "email",
        "enable_notifications": 1
    }
    
    response = requests.post(f"{BASE_URL}/monitors", json=monitor_data, headers=headers)
    if response.status_code == 200:
        monitor = response.json()
        monitor_id = monitor['id']
        
        # Assign to user
        assign_response = requests.put(f"{BASE_URL}/monitors/{monitor_id}/assign/{user_id}", headers=headers)
        if assign_response.status_code == 200:
            print(f"✅ Created monitor '{monitor_name}' (ID: {monitor_id}) for user ID {user_id}")
            return monitor
        else:
            print(f"❌ Failed to assign monitor to user: {assign_response.text}")
    else:
        print(f"❌ Failed to create monitor: {response.text}")
    return None

def get_all_monitors(token):
    """Get all monitors in the system"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/monitors?limit=100", headers=headers)
    if response.status_code == 200:
        return response.json()['items']
    return []

def test_multiple_user_notifications():
    """Test that multiple users with same monitor name get notified"""
    print("🧪 Testing Multiple User Notification System...")
    
    # Get admin token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    # Create test users
    print("\n1️⃣ Creating test users...")
    user1 = create_test_user(token, "testuser1", "password123")
    user2 = create_test_user(token, "testuser2", "password123")
    
    if not user1 or not user2:
        print("❌ Failed to create test users")
        return
    
    print(f"   Created User 1: {user1['username']} (ID: {user1['id']})")
    print(f"   Created User 2: {user2['username']} (ID: {user2['id']})")
    
    # Create monitors for same person but different users
    print("\n2️⃣ Creating monitors for same person...")
    monitor_name = "SMITH, JOHN DOE"  # Same name for both users
    
    monitor1 = create_monitor_for_user(token, user1['id'], monitor_name)
    monitor2 = create_monitor_for_user(token, user2['id'], monitor_name)
    
    if not monitor1 or not monitor2:
        print("❌ Failed to create monitors")
        return
    
    # Verify monitors were created
    print("\n3️⃣ Verifying monitor configuration...")
    all_monitors = get_all_monitors(token)
    same_name_monitors = [m for m in all_monitors if m['name'] == monitor_name]
    
    print(f"   Found {len(same_name_monitors)} monitors with name '{monitor_name}':")
    for i, monitor in enumerate(same_name_monitors, 1):
        print(f"   Monitor {i}: ID {monitor['id']}, User ID: {monitor.get('user_id', 'Unknown')}, Notify: {monitor['notify_address']}")
    
    if len(same_name_monitors) >= 2:
        print("✅ Multiple user notification test setup completed!")
        print("\n📋 Summary:")
        print(f"   - Created 2 test users")
        print(f"   - Created 2 monitors with identical name: '{monitor_name}'")
        print(f"   - Each monitor assigned to different user")
        print(f"   - When processing runs, BOTH users should get notifications")
        print("\n🔍 To verify fix is working:")
        print("   1. Run the jail scraping process")
        print("   2. Check logs for multiple notifications for same inmate")
        print("   3. Look for 'Monitor ID' and 'User ID' in log messages")
    else:
        print("❌ Test setup incomplete - need at least 2 monitors with same name")

if __name__ == "__main__":
    test_multiple_user_notifications()
