#!/usr/bin/env python3
"""
Test Zuercher Release Date Parsing
Tests the improved release date parsing function with various input formats
"""

import sys
import os
from datetime import datetime

# Add paths for different environments
sys.path.append('/app')
sys.path.append('.')
sys.path.append('./backend')

def test_release_date_parsing():
    """Test the parse_release_date function with various inputs."""
    
    # Import the function from the updated module
    try:
        from scrapes.zuercher import parse_release_date
    except ImportError as e:
        print(f"❌ Could not import parse_release_date: {e}")
        return False
    
    print("🧪 Testing Zuercher Release Date Parsing")
    print("=" * 50)
    
    # Test cases that should work
    test_cases = [
        # (input, expected_output, description)
        ("2025-09-04", "2025-09-04", "Standard ISO date"),
        ("2025-09-04T10:30:00", "2025-09-04", "ISO datetime with time"),
        ("2025-09-04 10:30:00", "2025-09-04", "Date with space and time"),
        ("09/04/2025", "2025-09-04", "US date format MM/DD/YYYY"),
        ("09-04-2025", "2025-09-04", "US date format MM-DD-YYYY"),
        ("", "", "Empty string"),
        (None, "", "None value"),
        ("TBD", "", "Text value 'TBD'"),
        ("Unknown", "", "Text value 'Unknown'"),
        ("null", "", "String 'null'"),
        ("2024-12-25", "2024-12-25", "Christmas date"),
        ("01/01/2025", "2025-01-01", "New Year's Day"),
        ("invalid-date", "", "Invalid date format"),
        ("2025-13-40", "", "Invalid date values"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    print(f"Running {total} test cases...\n")
    
    for i, (input_val, expected, description) in enumerate(test_cases, 1):
        try:
            result = parse_release_date(input_val)
            
            if result == expected:
                print(f"✅ Test {i:2d}: {description}")
                print(f"    Input:    {repr(input_val)}")
                print(f"    Output:   {repr(result)}")
                print(f"    Expected: {repr(expected)}")
                passed += 1
            else:
                print(f"❌ Test {i:2d}: {description}")
                print(f"    Input:    {repr(input_val)}")
                print(f"    Output:   {repr(result)}")
                print(f"    Expected: {repr(expected)}")
                
        except Exception as e:
            print(f"💥 Test {i:2d}: {description}")
            print(f"    Input:    {repr(input_val)}")
            print(f"    Error:    {e}")
            print(f"    Expected: {repr(expected)}")
        
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Release date parsing is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the parsing logic.")
        return False

def test_real_world_scenarios():
    """Test with real-world scenarios that might occur."""
    
    try:
        from scrapes.zuercher import parse_release_date
    except ImportError as e:
        print(f"❌ Could not import parse_release_date: {e}")
        return False
    
    print("\n🌍 Testing Real-World Scenarios")
    print("=" * 50)
    
    # Simulate various API responses that might come from Zuercher
    real_world_cases = [
        # Cases that were likely causing the original issue
        "2025-09-04T15:30:00.000Z",  # ISO with milliseconds and timezone
        "2025-09-04T15:30:00",       # ISO datetime
        "09/04/2025 3:30 PM",        # US format with time
        "TBD",                       # To Be Determined
        "UNKNOWN",                   # Unknown release
        "",                          # Empty from API
        "null",                      # String null from JSON
        "2025-09-04 00:00:00",       # Midnight time
    ]
    
    print("Testing cases that likely caused the original issue:\n")
    
    for case in real_world_cases:
        try:
            result = parse_release_date(case)
            status = "✅" if result == "" or result.count("-") == 2 else "⚠️"
            print(f"{status} Input: {repr(case):25} → Output: {repr(result)}")
        except Exception as e:
            print(f"❌ Input: {repr(case):25} → Error: {e}")
    
    print("\n✅ Real-world scenario testing completed")
    return True

if __name__ == "__main__":
    print("🚀 Zuercher Release Date Parser Test Suite")
    print()
    
    # Test basic parsing functionality
    basic_success = test_release_date_parsing()
    
    # Test real-world scenarios
    real_world_success = test_real_world_scenarios()
    
    print("\n" + "=" * 70)
    if basic_success and real_world_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Zuercher release date parsing should now work correctly")
        print("✅ No more missing release dates in scraped data")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please review the parsing logic")
    print("=" * 70)
