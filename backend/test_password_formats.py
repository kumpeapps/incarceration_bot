#!/usr/bin/env python3
"""
Test script to verify password format handling in Incarceration Bot

This script tests the password verification for different formats that 
aMember might use, ensuring our implementation handles them correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.User import User
import hashlib

def test_password_formats():
    """Test different password formats that aMember might provide."""
    
    test_password = "testpass123"
    user = User()
    
    print("Testing password format verification...")
    print(f"Test password: {test_password}")
    print("-" * 50)
    
    # Test 1: bcrypt format (what we normally use)
    print("1. Testing bcrypt format...")
    bcrypt_hash = User.hash_password(test_password)
    user.hashed_password = bcrypt_hash
    user.password_format = "bcrypt"
    result = user.verify_password_with_format(test_password, "bcrypt")
    print(f"   Hash: {bcrypt_hash}")
    print(f"   Verification: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test 2: MD5 format (simple hash) - DEPRECATED AND INSECURE
    print("\n2. Testing MD5 format (DEPRECATED - INSECURE)...")
    print("   ⚠️  WARNING: MD5 is cryptographically broken and should not be used for passwords!")
    print("   ⚠️  This test is for legacy compatibility only.")
    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    user.hashed_password = md5_hash
    user.password_format = "md5"
    result = user.verify_password_with_format(test_password, "md5")
    print(f"   Hash: {md5_hash}")
    print(f"   Verification: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test 3: SHA1 format - DEPRECATED AND INSECURE
    print("\n3. Testing SHA1 format (DEPRECATED - INSECURE)...")
    print("   ⚠️  WARNING: SHA1 is cryptographically broken and should not be used for passwords!")
    print("   ⚠️  This test is for legacy compatibility only.")
    sha1_hash = hashlib.sha1(test_password.encode()).hexdigest()
    user.hashed_password = sha1_hash
    user.password_format = "sha1"
    result = user.verify_password_with_format(test_password, "sha1")
    print(f"   Hash: {sha1_hash}")
    print(f"   Verification: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test 4: phpass format (simulated - would need actual phpass hash)
    print("\n4. Testing phpass format detection...")
    phpass_like_hash = "$P$B12345678901234567890123456789"  # Simulated
    detected_format = detect_password_format(phpass_like_hash)
    print(f"   Hash: {phpass_like_hash}")
    print(f"   Detected format: {detected_format}")
    print(f"   Detection: {'✅ PASS' if detected_format == 'phpass' else '❌ FAIL'}")
    
    # Test 5: bcrypt format detection
    print("\n5. Testing bcrypt format detection...")
    bcrypt_like_hash = "$2y$10$abcdefghijklmnopqrstuvwxyz1234567890"  # Simulated
    detected_format = detect_password_format(bcrypt_like_hash)
    print(f"   Hash: {bcrypt_like_hash}")
    print(f"   Detected format: {detected_format}")
    print(f"   Detection: {'✅ PASS' if detected_format == 'bcrypt' else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    print("Password format testing completed!")

def detect_password_format(password_hash):
    """Mirror the detection logic from our aMember plugin."""
    if not password_hash:
        return 'plain'
    
    # Detect aMember/WordPress phpass format
    if password_hash.startswith('$P$') or password_hash.startswith('$H$'):
        return 'phpass'
    
    # Detect PHP password_hash() bcrypt format
    if password_hash.startswith(('$2a$', '$2b$', '$2x$', '$2y$')):
        return 'bcrypt'
    
    # Detect argon2i format
    if password_hash.startswith('$argon2i$'):
        return 'argon2i'
    
    # Detect argon2id format
    if password_hash.startswith('$argon2id$'):
        return 'argon2id'
    
    # Detect Unix MD5 crypt format
    if password_hash.startswith('$1$'):
        return 'crypt'
    
    # Detect simple MD5 hash (32 hex characters)
    if len(password_hash) == 32 and all(c in '0123456789abcdefABCDEF' for c in password_hash):
        return 'md5'
    
    # Detect simple SHA1 hash (40 hex characters)
    if len(password_hash) == 40 and all(c in '0123456789abcdefABCDEF' for c in password_hash):
        return 'sha1'
    
    # Default to phpass for aMember
    return 'phpass'

if __name__ == "__main__":
    print("Incarceration Bot - Password Format Testing")
    print("==========================================")
    
    try:
        test_password_formats()
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you're running this from the backend directory.")
    except Exception as e:
        print(f"Test failed with error: {e}")
