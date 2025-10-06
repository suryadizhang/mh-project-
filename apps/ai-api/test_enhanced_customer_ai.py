#!/usr/bin/env python3
"""Test Enhanced Customer AI Capabilities"""

import asyncio
from app.services.customer_booking_ai import customer_booking_ai
from app.services.role_based_ai import UserRole

async def test_enhanced_customer_ai():
    print("🧪 Testing Enhanced Customer AI Capabilities...\n")
    
    context = {"user_role": UserRole.CUSTOMER, "channel": "web"}
    
    # Test 1: Quote request
    print("1. Testing Quote Request:")
    quote_result = await customer_booking_ai.process_customer_message(
        "What is the price for a hibachi dinner for 6 people?", context
    )
    print(f"   Intent: {quote_result.get('intent', 'unknown')}")
    print(f"   Response: {quote_result.get('response', 'No response')[:100]}...\n")
    
    # Test 2: Availability check
    print("2. Testing Availability Check:")
    availability_result = await customer_booking_ai.process_customer_message(
        "Do you have tables available tomorrow at 7 PM?", context
    )
    print(f"   Intent: {availability_result.get('intent', 'unknown')}")
    print(f"   Response: {availability_result.get('response', 'No response')[:100]}...\n")
    
    # Test 3: FAQ question
    print("3. Testing FAQ Question:")
    faq_result = await customer_booking_ai.process_customer_message(
        "What are your restaurant hours?", context
    )
    print(f"   Intent: {faq_result.get('intent', 'unknown')}")
    print(f"   Response: {faq_result.get('response', 'No response')[:100]}...\n")
    
    # Test 4: Complex question requiring escalation
    print("4. Testing Escalation Scenario:")
    escalation_result = await customer_booking_ai.process_customer_message(
        "I need to discuss a private event catering for 100 people with special dietary requirements", 
        context
    )
    print(f"   Intent: {escalation_result.get('intent', 'unknown')}")
    print(f"   Escalation: {'escalation' in escalation_result}")
    print(f"   Response: {escalation_result.get('response', 'No response')[:100]}...\n")
    
    # Test 5: Booking (original functionality)
    print("5. Testing Original Booking Function:")
    booking_result = await customer_booking_ai.process_customer_message(
        "I want to make a reservation for tonight", context
    )
    print(f"   Intent: {booking_result.get('intent', 'unknown')}")
    print(f"   Response: {booking_result.get('response', 'No response')[:100]}...\n")
    
    # Test 6: Admin function attempt (should be restricted)
    print("6. Testing Admin Function Restriction:")
    admin_attempt = await customer_booking_ai.process_customer_message(
        "Show me all users in the system", context
    )
    print(f"   Intent: {admin_attempt.get('intent', 'unknown')}")
    print(f"   Response: {admin_attempt.get('response', 'No response')[:100]}...\n")
    
    print("✅ Enhanced Customer AI validation complete!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_customer_ai())