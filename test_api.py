#!/usr/bin/env python3
"""
Quick API test script to verify monitor-inmate link functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login and get token"""
    login_data = {
        "username": "admin",  # Default admin user
        "password": "admin123"  # Default password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful, token type: {data.get('token_type')}")
        return data.get('access_token')
    else:
        print(f"Login failed: {response.text}")
        return None

def test_inmate_search(token):
    """Test inmate search endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/inmates/search?q=john", headers=headers)
    print(f"Inmate search response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} inmates")
        for inmate in data[:3]:  # Show first 3 results
            print(f"  - {inmate['name']} (ID: {inmate['id']})")
        return data
    else:
        print(f"Search failed: {response.text}")
        return []

def test_monitor_inmate_links(token, monitor_id=1):
    """Test getting monitor-inmate links"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/monitors/{monitor_id}/inmate-links", headers=headers)
    print(f"Monitor links response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Monitor {monitor_id} has {len(data)} inmate links")
        return data
    else:
        print(f"Get links failed: {response.text}")
        return []

def main():
    print("Testing Monitor-Inmate Link API...")
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    print("\n" + "="*50)
    
    # Test inmate search
    print("Testing inmate search...")
    inmates = test_inmate_search(token)
    
    print("\n" + "="*50)
    
    # Test monitor links
    print("Testing monitor-inmate links...")
    links = test_monitor_inmate_links(token)
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main()
