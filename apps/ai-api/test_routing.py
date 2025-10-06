#!/usr/bin/env python3
"""Test AI routing functionality"""

import asyncio
from app.services.role_based_ai import UserRole
from app.services.customer_booking_ai import customer_booking_ai
from app.services.admin_management_ai import admin_management_ai

async def test_routing():
    print("Testing customer AI...")
    customer_context = {"user_role": UserRole.CUSTOMER}
    customer_result = await customer_booking_ai.process_customer_message("I want to book a table", customer_context)
    print(f"Customer result: {customer_result}")
    
    print("\nTesting admin AI...")
    admin_context = {"user_role": UserRole.ADMIN}
    admin_result = await admin_management_ai.process_admin_message("Show me all users", admin_context)
    print(f"Admin result keys: {list(admin_result.keys())}")
    print(f"Admin function: {admin_result.get('function', 'No function key')}")
    print(f"Admin response length: {len(admin_result.get('response', ''))}")

if __name__ == "__main__":
    try:
        asyncio.run(test_routing())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()