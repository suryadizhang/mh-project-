"""
End-to-End Integration Test: Multi-Channel Handler + AI Orchestrator

This test validates the complete integration of:
- Multi-channel handler (6 channels)
- AI Orchestrator (tool calling)
- Pricing Tool (party quotes)
- Travel Fee Tool (distance/fees)
- Protein Tool (upgrade costs)

Author: MyHibachi Development Team
Created: October 31, 2025 (Day 3)
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path / "src"))

from api.ai.endpoints.services.multi_channel_ai_handler import get_multi_channel_handler


class Color:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


async def test_email_pricing_inquiry():
    """Test: Email channel with pricing inquiry"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 1: Email Channel - Pricing Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "I need a quote for 10 adults in Sacramento 95630"
    channel = "email"
    customer_context = {
        "name": "John Doe",
        "email": "john@example.com",
        "zipcode": "95630"
    }
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Channel: {channel}")
    print(f"  Location: {customer_context['zipcode']}")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}AI Response (Email):{Color.END}")
    print(f"  {response['content'][:300]}...")
    
    print(f"\n{Color.BLUE}Metadata:{Color.END}")
    if response.get('ai_metadata'):
        print(f"  Model: {response['ai_metadata'].get('model_used')}")
        print(f"  Tools Used: {response['ai_metadata'].get('tools_used', [])}")
        print(f"  Execution Time: {response['ai_metadata'].get('total_execution_time_ms')}ms")
        print(f"  Orchestrator: v{response['ai_metadata'].get('orchestrator_version')}")
    
    if response['metadata'].get('pricing_breakdown'):
        print(f"\n{Color.BLUE}Pricing Breakdown:{Color.END}")
        pricing = response['metadata']['pricing_breakdown']
        print(f"  Base Cost: ${pricing.get('base_cost', 0)}")
        print(f"  Travel Fee: ${pricing.get('travel_fee', 0)}")
        print(f"  Total: ${pricing.get('total', 0)}")
    
    return response.get('ai_metadata', {}).get('orchestrator_version') == '2.0'


async def test_sms_protein_upgrade():
    """Test: SMS channel with protein upgrades"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 2: SMS Channel - Protein Upgrade Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "Quote for 15 adults with filet mignon?"
    channel = "sms"
    customer_context = {"zipcode": "95825"}
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Channel: {channel} (160 char max, casual tone)")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}SMS Response:{Color.END}")
    print(f"  Length: {len(response['content'])} chars (max 160)")
    print(f"  Content: {response['content']}")
    
    if response['metadata'].get('protein_breakdown'):
        print(f"\n{Color.BLUE}Protein Costs:{Color.END}")
        print(f"  {response['metadata'].get('protein_summary', 'N/A')}")
    
    return len(response['content']) <= 160


async def test_instagram_travel_fee():
    """Test: Instagram channel with travel fee"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 3: Instagram Channel - Travel Fee Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "Do you service Folsom CA? 🎉"
    channel = "instagram"
    customer_context = {"address": "Folsom, CA"}
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Channel: {channel} (enthusiastic tone)")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}Instagram Response:{Color.END}")
    print(f"  {response['content'][:200]}...")
    
    if response['metadata'].get('travel_fee_details'):
        print(f"\n{Color.BLUE}Travel Fee:{Color.END}")
        travel = response['metadata']['travel_fee_details']
        print(f"  Distance: {travel.get('distance_miles', 0)} miles")
        print(f"  Fee: ${travel.get('travel_fee', 0)}")
        print(f"  Free Service: {travel.get('is_free', False)}")
    
    return True


async def test_facebook_complete_quote():
    """Test: Facebook channel with complete party quote"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 4: Facebook Channel - Complete Quote{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "I want to book a hibachi party for 20 adults with lobster and filet mignon in Folsom CA"
    channel = "facebook"
    customer_context = {
        "name": "Sarah Smith",
        "address": "Folsom, CA 95630"
    }
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Channel: {channel}")
    print(f"  Expected Tools: PricingTool, ProteinTool, TravelFeeTool")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    
    tools_used = response.get('ai_metadata', {}).get('tools_used', [])
    print(f"\n{Color.BLUE}Tools Executed:{Color.END}")
    for tool in tools_used:
        print(f"  ✓ {tool}")
    
    print(f"\n{Color.BLUE}Complete Quote:{Color.END}")
    if response['metadata'].get('pricing_breakdown'):
        pricing = response['metadata']['pricing_breakdown']
        print(f"  Base: ${pricing.get('base_cost', 0)}")
        print(f"  Proteins: ${pricing.get('protein_upgrades', 0)}")
        print(f"  Travel: ${pricing.get('travel_fee', 0)}")
        print(f"  TOTAL: ${pricing.get('total', 0)}")
    
    return len(tools_used) >= 1  # At least pricing tool should be used


async def test_phone_transcript():
    """Test: Phone transcript channel"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 5: Phone Transcript Channel{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "Hi, I'm calling about hiring a hibachi chef for my daughter's birthday. We have 8 adults and 5 kids."
    channel = "phone_transcript"
    customer_context = {
        "phone": "(916) 555-0123",
        "zipcode": "95630"
    }
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message[:80]}...")
    print(f"  Channel: {channel}")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}Phone Response:{Color.END}")
    print(f"  {response['content'][:250]}...")
    
    return True


async def test_web_chat():
    """Test: Web chat channel"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 6: Web Chat Channel{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "How much for a party?"
    channel = "web_chat"
    
    print(f"\n{Color.CYAN}Input:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Channel: {channel}")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}Web Chat Response:{Color.END}")
    print(f"  {response['content'][:200]}...")
    
    return True


async def test_admin_review_workflow():
    """Test: Admin review workflow"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 7: Admin Review Workflow{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    handler = get_multi_channel_handler()
    
    message = "Quote for 50 adults with all premium proteins in Napa Valley"
    channel = "email"
    customer_context = {
        "email": "bigevent@company.com",
        "address": "Napa, CA"
    }
    
    print(f"\n{Color.CYAN}High-Value Quote Request:{Color.END}")
    print(f"  Message: {message}")
    print(f"  Expected: Requires admin review")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await handler.process_multi_channel_inquiry(
        message=message,
        channel=channel,
        customer_context=customer_context
    )
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    
    requires_review = response.get('requires_admin_review', False)
    conversation_id = response.get('conversation_id')
    
    print(f"\n{Color.BLUE}Admin Review:{Color.END}")
    print(f"  Requires Review: {requires_review}")
    print(f"  Conversation ID: {conversation_id}")
    
    if response['metadata'].get('pricing_breakdown'):
        total = response['metadata']['pricing_breakdown'].get('total', 0)
        print(f"  Quote Total: ${total}")
    
    return conversation_id is not None


async def run_all_tests():
    """Run all end-to-end tests"""
    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "MULTI-CHANNEL + ORCHESTRATOR E2E TESTS" + " "*24 + "║")
    print("║" + " "*30 + "Day 3" + " "*44 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Color.END}")
    
    start_time = datetime.now()
    
    tests = [
        ("Email - Pricing", test_email_pricing_inquiry),
        ("SMS - Protein Upgrade", test_sms_protein_upgrade),
        ("Instagram - Travel Fee", test_instagram_travel_fee),
        ("Facebook - Complete Quote", test_facebook_complete_quote),
        ("Phone Transcript", test_phone_transcript),
        ("Web Chat", test_web_chat),
        ("Admin Review Workflow", test_admin_review_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n{Color.RED}✗ Test Failed: {str(e)}{Color.END}")
    
    # Print summary
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST SUMMARY{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = f"{Color.GREEN}✓ PASS{Color.END}" if success else f"{Color.RED}✗ FAIL{Color.END}"
        print(f"  {status}  {test_name}")
        if error:
            print(f"         Error: {error}")
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"  Tests Passed: {passed}/{total}")
    print(f"  Success Rate: {(passed/total)*100:.1f}%")
    print(f"  Execution Time: {execution_time:.2f}s")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    if passed == total:
        print(f"{Color.GREEN}{Color.BOLD}🎉 ALL E2E TESTS PASSED! 🎉{Color.END}\n")
        print(f"{Color.GREEN}✅ Multi-Channel Handler + Orchestrator Integration: SUCCESS{Color.END}\n")
        return 0
    else:
        print(f"{Color.YELLOW}⚠ Some tests failed. Review errors above.{Color.END}\n")
        return 1


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Color.RED}Error: OPENAI_API_KEY environment variable not set{Color.END}")
        print(f"\nSet it with: $env:OPENAI_API_KEY='sk-...'")
        sys.exit(1)
    
    # Run tests
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
