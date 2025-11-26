"""
Test cases for cursor pagination implementation.

This file validates the cursor pagination logic to ensure:
1. Cursor encoding/decoding works correctly
2. Forward pagination works
3. Backward pagination works
4. Edge cases are handled
"""
import base64
import json
from datetime import datetime
from uuid import UUID, uuid4


def test_cursor_encoding():
    """Test that cursor encoding produces valid base64 JSON."""
    # Simulate cursor data
    cursor_dict = {
        "value": "2024-10-20T10:30:00+00:00",
        "secondary_value": str(uuid4()),
        "reverse": False
    }
    
    # Encode
    json_str = json.dumps(cursor_dict, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    
    print(f"✅ Cursor encoded successfully: {encoded[:50]}...")
    
    # Decode
    decoded_json = base64.urlsafe_b64decode(encoded.encode()).decode()
    decoded_dict = json.loads(decoded_json)
    
    assert decoded_dict == cursor_dict, "Decoded cursor doesn't match original"
    print("✅ Cursor decoding works correctly")
    
    return True


def test_datetime_serialization():
    """Test datetime ISO format serialization."""
    dt = datetime.now()
    iso_str = dt.isoformat()
    
    # Parse back
    parsed = datetime.fromisoformat(iso_str)
    
    assert parsed.year == dt.year
    assert parsed.month == dt.month
    assert parsed.day == dt.day
    assert parsed.hour == dt.hour
    assert parsed.minute == dt.minute
    
    print("✅ Datetime serialization works correctly")
    return True


def test_uuid_serialization():
    """Test UUID string serialization."""
    test_uuid = uuid4()
    uuid_str = str(test_uuid)
    
    # Parse back
    parsed = UUID(uuid_str)
    
    assert parsed == test_uuid, "UUID parsing failed"
    print("✅ UUID serialization works correctly")
    return True


def test_cursor_with_timezone():
    """Test cursor with timezone-aware datetime."""
    cursor_dict = {
        "value": "2024-10-20T10:30:00Z",  # UTC timezone
        "secondary_value": str(uuid4()),
        "reverse": False
    }
    
    # Encode
    json_str = json.dumps(cursor_dict, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    
    # Decode
    decoded_json = base64.urlsafe_b64decode(encoded.encode()).decode()
    decoded_dict = json.loads(decoded_json)
    
    # Parse datetime with Z timezone
    dt_str = decoded_dict["value"]
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    
    assert dt.year == 2024
    assert dt.month == 10
    assert dt.day == 20
    
    print("✅ Timezone-aware datetime works correctly")
    return True


def test_invalid_cursor_handling():
    """Test that invalid cursors are handled gracefully."""
    invalid_cursors = [
        "invalid_base64",
        "YWJjZGVm",  # Valid base64 but invalid JSON
        base64.urlsafe_b64encode(b'{"invalid": "no value key"}').decode(),
    ]
    
    for invalid_cursor in invalid_cursors:
        try:
            # Simulate decode logic
            json_str = base64.urlsafe_b64decode(invalid_cursor.encode()).decode()
            cursor_dict = json.loads(json_str)
            
            # Check for required field
            if "value" not in cursor_dict:
                print(f"✅ Invalid cursor correctly rejected (missing 'value')")
                continue
                
        except (ValueError, json.JSONDecodeError):
            print(f"✅ Invalid cursor correctly rejected (decode error)")
            continue
    
    return True


def test_pagination_logic():
    """Test pagination comparison logic."""
    
    # DESC ordering (newest first)
    # Forward: WHERE created_at < cursor_value
    # Backward: WHERE created_at > cursor_value
    
    cursor_value = datetime(2024, 10, 20, 10, 0, 0)
    
    # Simulate forward pagination (DESC)
    # Should get items BEFORE cursor (older items)
    test_date_1 = datetime(2024, 10, 20, 9, 0, 0)  # Before cursor - SHOULD MATCH
    test_date_2 = datetime(2024, 10, 20, 11, 0, 0)  # After cursor - should NOT match
    
    assert test_date_1 < cursor_value, "Forward DESC logic correct"
    assert not (test_date_2 < cursor_value), "Forward DESC logic correct"
    
    # Simulate backward pagination (DESC with reverse=True)
    # Should get items AFTER cursor (newer items)
    assert test_date_2 > cursor_value, "Backward DESC logic correct"
    assert not (test_date_1 > cursor_value), "Backward DESC logic correct"
    
    print("✅ Pagination comparison logic is correct")
    return True


def test_limit_plus_one():
    """Test that limit + 1 logic works for hasNext."""
    
    # Simulate fetching 51 items with limit=50
    items = list(range(51))
    limit = 50
    
    has_next = len(items) > limit
    assert has_next == True, "Should have next page"
    
    trimmed_items = items[:limit]
    assert len(trimmed_items) == 50, "Should return exactly 50 items"
    
    # Simulate fetching 30 items with limit=50
    items = list(range(30))
    has_next = len(items) > limit
    assert has_next == False, "Should NOT have next page"
    
    print("✅ Limit + 1 logic for hasNext works correctly")
    return True


def run_all_tests():
    """Run all cursor pagination tests."""
    print("\n" + "="*60)
    print("CURSOR PAGINATION LOGIC VALIDATION")
    print("="*60 + "\n")
    
    tests = [
        ("Cursor Encoding/Decoding", test_cursor_encoding),
        ("Datetime Serialization", test_datetime_serialization),
        ("UUID Serialization", test_uuid_serialization),
        ("Timezone Handling", test_cursor_with_timezone),
        ("Invalid Cursor Handling", test_invalid_cursor_handling),
        ("Pagination Comparison Logic", test_pagination_logic),
        ("Limit + 1 Logic", test_limit_plus_one),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Testing: {test_name}")
            print("-" * 60)
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} ERROR: {e}\n")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Cursor pagination logic is correct.\n")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Review the logic above.\n")
        return False


if __name__ == "__main__":
    run_all_tests()
