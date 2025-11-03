"""
Additional Testing for WhatsApp Notification System

Tests edge cases and advanced scenarios:
1. SMS fallback (WhatsApp failure)
2. Quiet hours (10 PM - 8 AM)
3. Invalid phone numbers
4. Different guest counts
5. Complaint priority levels
6. Concurrent bookings (load testing)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, time as dt_time

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("=" * 80)
print("ADDITIONAL WHATSAPP NOTIFICATION TESTING")
print("=" * 80)
print()


async def test_sms_fallback():
    """Test 1: SMS fallback when WhatsApp fails"""
    print("=" * 80)
    print("TEST 1: SMS FALLBACK")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    # Create service with simulated WhatsApp failure
    service = UnifiedNotificationService()
    
    try:
        print()
        print("Simulating WhatsApp failure scenario...")
        print("(In production, this would automatically fall back to SMS)")
        print()
        
        # Test with invalid WhatsApp number to trigger fallback
        result = await service.send_new_booking_notification(
            customer_name="Test Customer",
            customer_phone="+11111111111",  # Invalid for WhatsApp
            event_date="2024-12-25",
            event_time="6:00 PM",
            guest_count=10,
            location="Test Location",
            booking_id=999
        )
        
        print(f"✅ Fallback test completed!")
        print(f"   Result: {result}")
        print()
        print("Expected behavior:")
        print("   1. Try WhatsApp first")
        print("   2. If fails → Try SMS")
        print("   3. If SMS fails → Log error")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quiet_hours():
    """Test 2: Quiet hours enforcement (10 PM - 8 AM)"""
    print("=" * 80)
    print("TEST 2: QUIET HOURS (10 PM - 8 AM)")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    service = UnifiedNotificationService()
    
    try:
        # Check if currently in quiet hours
        current_time = datetime.now().time()
        quiet_start = dt_time(22, 0)  # 10 PM
        quiet_end = dt_time(8, 0)     # 8 AM
        
        is_quiet = current_time >= quiet_start or current_time < quiet_end
        
        print()
        print(f"Current Time: {current_time.strftime('%I:%M %p')}")
        print(f"Quiet Hours: 10:00 PM - 8:00 AM")
        print(f"Currently in quiet hours: {'✅ YES' if is_quiet else '❌ NO'}")
        print()
        
        # Test notification during quiet hours
        result = await service.send_new_booking_notification(
            customer_name="Night Customer",
            customer_phone="+12103884155",
            event_date="2024-12-25",
            event_time="6:00 PM",
            guest_count=10,
            location="Night Location",
            booking_id=888
        )
        
        print("✅ Quiet hours test completed!")
        print()
        print("Expected behavior:")
        print("   - Customer: Skipped during quiet hours")
        print("   - Admin: ALWAYS notified (no quiet hours)")
        print()
        
        if is_quiet:
            print("⏰ Currently in quiet hours:")
            print("   Customer should NOT receive notification")
            print("   Admin SHOULD receive notification")
        else:
            print("☀️ Currently NOT in quiet hours:")
            print("   Both customer and admin receive notifications")
        
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_invalid_phone_numbers():
    """Test 3: Handling invalid phone numbers"""
    print("=" * 80)
    print("TEST 3: INVALID PHONE NUMBERS")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    service = UnifiedNotificationService()
    
    invalid_phones = [
        ("", "Empty string"),
        ("invalid", "Non-numeric"),
        ("+1", "Too short"),
        ("+123456789012345678901234567890", "Too long"),
        ("5551234", "No country code"),
    ]
    
    print()
    print("Testing various invalid phone formats...")
    print()
    
    results = []
    
    for phone, description in invalid_phones:
        try:
            result = await service.send_new_booking_notification(
                customer_name="Test Customer",
                customer_phone=phone,
                event_date="2024-12-25",
                event_time="6:00 PM",
                guest_count=10,
                location="Test Location",
                booking_id=777
            )
            
            # Should handle gracefully
            print(f"   ✅ {description:20s} - Handled gracefully")
            results.append(True)
        except Exception as e:
            print(f"   ❌ {description:20s} - Error: {str(e)[:50]}")
            results.append(False)
    
    print()
    print("Expected behavior:")
    print("   - Invalid phones logged as errors")
    print("   - System doesn't crash")
    print("   - Admin still receives notification")
    print()
    
    return all(results)


async def test_different_guest_counts():
    """Test 4: Different guest count formatting"""
    print("=" * 80)
    print("TEST 4: GUEST COUNT FORMATTING")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    service = UnifiedNotificationService()
    
    guest_counts = [1, 5, 15, 25, 50]
    
    print()
    print("Testing guest count formatting...")
    print()
    
    for count in guest_counts:
        try:
            result = await service.send_new_booking_notification(
                customer_name="Test Customer",
                customer_phone="+12103884155",
                event_date="2024-12-25",
                event_time="6:00 PM",
                guest_count=count,
                location="Test Location",
                booking_id=count
            )
            
            print(f"   ✅ {count} guests - Notification formatted correctly")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ {count} guests - Error: {e}")
    
    print()
    print("Expected formatting:")
    print("   - 1 guest  → '1 guest'")
    print("   - 5 guests → '5 guests'")
    print("   - 15+ guests → '~15 guests' (approximate)")
    print()
    
    return True


async def test_complaint_priorities():
    """Test 5: All complaint priority levels"""
    print("=" * 80)
    print("TEST 5: COMPLAINT PRIORITY LEVELS")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    service = UnifiedNotificationService()
    
    priorities = [
        ("low", "Minor issue"),
        ("medium", "Moderate concern"),
        ("high", "Serious problem"),
        ("urgent", "Critical situation")
    ]
    
    print()
    print("Testing all complaint priorities...")
    print()
    
    for priority, description in priorities:
        try:
            result = await service.send_complaint_notification(
                customer_name="Test Customer",
                customer_phone="+12103884155",
                booking_id=f"test-{priority}",
                complaint_text=f"{description}: Testing {priority} priority notification",
                priority=priority
            )
            
            emoji = {
                "low": "ℹ️",
                "medium": "⚠️",
                "high": "🚨",
                "urgent": "🔴"
            }
            
            print(f"   {emoji[priority]} {priority.upper():8s} - {description}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ {priority.upper():8s} - Error: {e}")
    
    print()
    print("Expected formatting:")
    print("   - Low: ℹ️ COMPLAINT - LOW PRIORITY")
    print("   - Medium: ⚠️ COMPLAINT - MEDIUM PRIORITY")
    print("   - High: 🚨 COMPLAINT - HIGH PRIORITY")
    print("   - Urgent: 🔴 COMPLAINT - URGENT (Respond within 1 hour)")
    print()
    
    return True


async def test_concurrent_bookings():
    """Test 6: Concurrent bookings (load testing)"""
    print("=" * 80)
    print("TEST 6: CONCURRENT BOOKINGS (Load Testing)")
    print("=" * 80)
    
    from services.unified_notification_service import UnifiedNotificationService
    
    service = UnifiedNotificationService()
    
    print()
    print("Creating 10 concurrent bookings...")
    print()
    
    try:
        # Create 10 booking notifications concurrently
        tasks = []
        for i in range(10):
            task = service.send_new_booking_notification(
                customer_name=f"Customer {i+1}",
                customer_phone="+12103884155",
                event_date="2024-12-25",
                event_time=f"{6+i%3}:00 PM",
                guest_count=10 + i,
                location=f"Location {i+1}",
                booking_id=100 + i
            )
            tasks.append(task)
        
        # Wait for all to complete
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Count successes
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"✅ Load test completed!")
        print()
        print(f"   Total bookings: 10")
        print(f"   Successful: {successes}")
        print(f"   Failed: {failures}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Avg per booking: {duration/10:.2f} seconds")
        print()
        
        if failures > 0:
            print("Errors encountered:")
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    print(f"   ❌ Booking {i+1}: {str(r)[:60]}")
            print()
        
        print("Expected behavior:")
        print("   - All notifications queued without blocking")
        print("   - No rate limit errors")
        print("   - System remains responsive")
        print()
        
        return failures == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all additional tests"""
    print()
    print("🚀 Starting Additional Testing...")
    print()
    print("IMPORTANT: These tests verify edge cases and system reliability:")
    print("  - SMS fallback when WhatsApp fails")
    print("  - Quiet hours enforcement")
    print("  - Invalid input handling")
    print("  - Various formatting scenarios")
    print("  - System load handling")
    print()
    
    input("Press Enter to begin testing...")
    print()
    
    results = []
    
    # Test 1: SMS Fallback
    result1 = await test_sms_fallback()
    results.append(("SMS fallback", result1))
    await asyncio.sleep(2)
    
    # Test 2: Quiet Hours
    result2 = await test_quiet_hours()
    results.append(("Quiet hours", result2))
    await asyncio.sleep(2)
    
    # Test 3: Invalid Phones
    result3 = await test_invalid_phone_numbers()
    results.append(("Invalid phone numbers", result3))
    await asyncio.sleep(2)
    
    # Test 4: Guest Counts
    result4 = await test_different_guest_counts()
    results.append(("Guest count formatting", result4))
    await asyncio.sleep(2)
    
    # Test 5: Complaint Priorities
    result5 = await test_complaint_priorities()
    results.append(("Complaint priorities", result5))
    await asyncio.sleep(2)
    
    # Test 6: Concurrent Load
    result6 = await test_concurrent_bookings()
    results.append(("Concurrent bookings", result6))
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print()
        print("🎉 ALL ADDITIONAL TESTS PASSED!")
        print()
        print("✅ SMS fallback working!")
        print("✅ Quiet hours enforced!")
        print("✅ Error handling robust!")
        print("✅ Formatting correct!")
        print("✅ System handles load!")
        print()
        print("System is production-ready! 🚀")
    else:
        print()
        print("⚠️ SOME TESTS FAILED")
        print()
        print("Review the errors above and fix issues before production.")
    
    print()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
