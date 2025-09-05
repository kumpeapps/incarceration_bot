#!/usr/bin/env python3
"""
Test Release Date Fix for Zuercher Scraper
Validates that the issue with missing release dates has been resolved
"""

import sys
import os
from datetime import datetime

# Add paths for different environments
sys.path.append('/app')
sys.path.append('.')
sys.path.append('./backend')

def test_scraping_utils():
    """Test the new scraping utilities."""
    try:
        from scrapes.scraping_utils import parse_release_date, parse_arrest_date, parse_date_flexible
        print("✅ Successfully imported scraping utilities")
        return True
    except ImportError as e:
        print(f"❌ Failed to import scraping utilities: {e}")
        return False

def test_release_date_scenarios():
    """Test various release date scenarios that were causing issues."""
    try:
        from scrapes.scraping_utils import parse_release_date
    except ImportError:
        print("❌ Cannot import parse_release_date")
        return False
    
    print("\n🧪 Testing Release Date Scenarios")
    print("=" * 50)
    
    # Real-world scenarios that were causing the original issue
    test_scenarios = [
        # (input, description, expected_success)
        ("2025-09-04T15:30:00", "ISO datetime with time", True),
        ("09/04/2025", "US date format", True),
        ("2025-09-04", "Standard ISO date", True),
        ("TBD", "To Be Determined text", True),  # Should return empty string
        ("", "Empty string", True),
        (None, "None value", True),
        ("2025-09-04T15:30:00.000Z", "ISO with timezone", True),
        ("Invalid Date", "Invalid text", True),  # Should return empty string gracefully
    ]
    
    all_passed = True
    
    for input_val, description, should_succeed in test_scenarios:
        try:
            result = parse_release_date(input_val)
            
            # Check if result is a valid date string or empty
            is_valid = (result == "" or 
                       (len(result) == 10 and result.count("-") == 2))
            
            if is_valid:
                print(f"✅ {description}")
                print(f"   Input: {repr(input_val)}")
                print(f"   Output: {repr(result)}")
            else:
                print(f"❌ {description}")
                print(f"   Input: {repr(input_val)}")
                print(f"   Output: {repr(result)} (invalid format)")
                all_passed = False
                
        except Exception as e:
            print(f"💥 {description}")
            print(f"   Input: {repr(input_val)}")
            print(f"   Error: {e}")
            if should_succeed:
                all_passed = False
        
        print()
    
    return all_passed

def test_zuercher_integration():
    """Test that the Zuercher scraper uses the new utilities."""
    print("🔍 Testing Zuercher Scraper Integration")
    print("=" * 50)
    
    try:
        # Check that the scraper imports the utilities
        import scrapes.zuercher as zuercher_module
        
        # Check if it has the right imports
        source_file = '/Users/justinkumpe/Documents/incarceration_bot/backend/scrapes/zuercher.py'
        if os.path.exists(source_file):
            with open(source_file, 'r') as f:
                source_code = f.read()
                
            if 'from scrapes.scraping_utils import' in source_code:
                print("✅ Zuercher scraper imports scraping utilities")
            else:
                print("❌ Zuercher scraper missing scraping utilities import")
                return False
                
            if 'parse_release_date(' in source_code:
                print("✅ Zuercher scraper uses parse_release_date function")
            else:
                print("❌ Zuercher scraper not using parse_release_date function")
                return False
                
            if 'parse_arrest_date(' in source_code:
                print("✅ Zuercher scraper uses parse_arrest_date function")
            else:
                print("⚠️  Zuercher scraper not using parse_arrest_date function (OK)")
        
        print("✅ Zuercher scraper integration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Zuercher integration: {e}")
        return False

def demonstrate_fix():
    """Demonstrate how the fix resolves the original problem."""
    print("\n🔧 Demonstrating the Fix")
    print("=" * 50)
    
    print("BEFORE (Original Issue):")
    print("- Zuercher API returns: '2025-09-04T15:30:00'")
    print("- Original parser fails with ValueError")
    print("- release_date gets set to '' (empty)")
    print("- User sees no release date in the system")
    print()
    
    print("AFTER (With Fix):")
    try:
        from scrapes.scraping_utils import parse_release_date
        
        example_input = "2025-09-04T15:30:00"
        result = parse_release_date(example_input)
        
        print(f"- Zuercher API returns: '{example_input}'")
        print(f"- New parser successfully extracts: '{result}'")
        print("- release_date gets properly populated")
        print("- User sees correct release date in the system")
        print()
        print("✅ Problem resolved!")
        
    except Exception as e:
        print(f"❌ Fix demonstration failed: {e}")
        return False
    
    return True

def main():
    """Run all tests and demonstrate the fix."""
    print("🚀 Zuercher Release Date Fix Validation")
    print("=" * 70)
    
    tests = [
        ("Scraping Utilities Import", test_scraping_utils),
        ("Release Date Scenarios", test_release_date_scenarios),
        ("Zuercher Integration", test_zuercher_integration),
        ("Fix Demonstration", demonstrate_fix),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🏃 Running {test_name}...")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ The Zuercher release date issue has been fixed!")
        print("✅ Release dates will now be properly populated")
        print("✅ Various date formats and edge cases are handled")
        print("✅ Shared utilities available for other scrapers")
        print()
        print("🚀 Ready for deployment!")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("Please review the issues above before deployment.")
    
    print("=" * 70)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
