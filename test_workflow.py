#!/usr/bin/env python3
"""
Test complete monitor-inmate link functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def test_complete_workflow():
    """Test complete monitor-inmate link workflow"""
    print("🚀 Testing complete monitor-inmate link workflow...")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Search for inmates
    print("\n1️⃣ Searching for inmates with 'smith'...")
    response = requests.get(f"{BASE_URL}/inmates/search?q=smith", headers=headers)
    if response.status_code == 200:
        inmates = response.json()
        print(f"   Found {len(inmates)} inmates")
        if inmates:
            inmate = inmates[0]  # Use first result
            print(f"   Selected: {inmate['name']} (ID: {inmate['id']})")
        else:
            print("❌ No inmates found")
            return
    else:
        print(f"❌ Search failed: {response.text}")
        return
    
    # 2. Create a monitor-inmate link
    print("\n2️⃣ Creating monitor-inmate link...")
    link_data = {
        "inmate_id": inmate['id'],
        "is_excluded": False,
        "link_reason": "API test - matching name pattern"
    }
    
    response = requests.post(f"{BASE_URL}/monitors/1/inmate-links", json=link_data, headers=headers)
    if response.status_code == 200:
        link = response.json()
        print(f"   ✅ Created link: Monitor 1 -> Inmate {inmate['name']}")
        print(f"   Link ID: {link['id']}, Reason: {link['link_reason']}")
    else:
        print(f"❌ Link creation failed: {response.text}")
        return
    
    # 3. Get monitor links to verify
    print("\n3️⃣ Retrieving monitor links...")
    response = requests.get(f"{BASE_URL}/monitors/1/inmate-links", headers=headers)
    if response.status_code == 200:
        links = response.json()
        print(f"   ✅ Monitor 1 now has {len(links)} inmate links")
        for link in links:
            # Print the link structure for debugging
            print(f"   - Link ID {link['id']}: {link.get('inmate_name', 'Unknown')} ({'excluded' if link['is_excluded'] else 'included'})")
    else:
        print(f"❌ Failed to get links: {response.text}")
        return
    
    # 4. Update the link to excluded
    print("\n4️⃣ Updating link to excluded...")
    update_data = {
        "is_excluded": True,
        "link_reason": "API test - marking as false positive"
    }
    
    response = requests.put(f"{BASE_URL}/monitors/1/inmate-links/{link['id']}", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_link = response.json()
        print(f"   ✅ Updated link: now {'excluded' if updated_link['is_excluded'] else 'included'}")
    else:
        print(f"❌ Link update failed: {response.text}")
        return
    
    print("\n🎉 Complete workflow test successful!")
    print("   ✅ Search inmates")
    print("   ✅ Create monitor-inmate link")
    print("   ✅ Retrieve links")
    print("   ✅ Update link status")

if __name__ == "__main__":
    test_complete_workflow()
