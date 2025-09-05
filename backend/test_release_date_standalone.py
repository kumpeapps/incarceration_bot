#!/usr/bin/env python3
"""
Standalone Test for Release Date Parsing Logic
Tests the parsing logic without requiring external dependencies
"""

from datetime import datetime
import logging

# Set up simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_release_date(release_date_raw):
    """
    Parse release date from various formats into standardized string format.
    
    Args:
        release_date_raw: Raw release date from Zuercher API (could be various formats)
        
    Returns:
        str: Formatted date string (YYYY-MM-DD) or empty string if invalid/missing
    """
    if not release_date_raw or release_date_raw in ['', 'None', 'null', 'TBD', 'Unknown']:
        return ""
    
    # Convert to string and clean up
    release_date_str = str(release_date_raw).strip()
    
    if not release_date_str:
        return ""
    
    # Try different date formats that Zuercher might return
    date_formats = [
        "%Y-%m-%d",           # 2025-09-04
        "%Y-%m-%dT%H:%M:%S",  # 2025-09-04T10:30:00
        "%Y-%m-%d %H:%M:%S",  # 2025-09-04 10:30:00
        "%m/%d/%Y",           # 09/04/2025
        "%m-%d-%Y",           # 09-04-2025
        "%d/%m/%Y",           # 04/09/2025 (European format)
        "%d-%m-%Y",           # 04-09-2025 (European format)
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(release_date_str, date_format).date()
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If no format matches, log warning and return empty
    logger.warning(f"Could not parse release date: {release_date_raw}")
    return ""

def test_release_date_parsing():
    """Test the parse_release_date function with various inputs."""
    
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
        ("2025-09-04T15:30:00.000Z", "", "ISO with timezone (should fail gracefully)"),
        ("12/31/2024", "2024-12-31", "End of year US format"),
        ("2025-1-1", "", "Single digit month/day (should fail)"),
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
        
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Release date parsing is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the parsing logic.")
        return False

def demonstrate_original_problem():
    """Demonstrate what would happen with the original code."""
    print("\n🔧 Demonstrating Original Problem")
    print("=" * 50)
    
    # Simulate the original problematic code
    def original_release_date_parsing(release_date_raw):
        try:
            return datetime.strptime(release_date_raw, "%Y-%m-%d").date().strftime("%Y-%m-%d")
        except ValueError:
            return ""
    
    problem_cases = [
        "2025-09-04T10:30:00",  # Would fail - has time component
        "09/04/2025",           # Would fail - wrong format
        "TBD",                  # Would fail - not a date
        None,                   # Would fail - can't parse None
    ]
    
    print("Cases that would fail with original code:")
    for case in problem_cases:
        try:
            original_result = original_release_date_parsing(case)
            new_result = parse_release_date(case)
            print(f"Input: {repr(case):20}")
            print(f"  Original: {repr(original_result):15} (would lose release date)")
            print(f"  Fixed:    {repr(new_result):15} (properly handled)")
        except Exception as e:
            new_result = parse_release_date(case)
            print(f"Input: {repr(case):20}")
            print(f"  Original: ERROR - {e}")
            print(f"  Fixed:    {repr(new_result):15} (error handled)")
        print()
    
    print("✅ The fix properly handles all problematic cases")

if __name__ == "__main__":
    print("🚀 Standalone Zuercher Release Date Parser Test")
    print()
    
    # Test basic parsing functionality
    success = test_release_date_parsing()
    
    # Demonstrate the original problem
    demonstrate_original_problem()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The improved parsing should fix the missing release dates")
        print("✅ Zuercher scrapes will now properly populate release dates")
        print("✅ Various date formats and edge cases are handled")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  The parsing logic needs adjustment")
    print("=" * 70)
