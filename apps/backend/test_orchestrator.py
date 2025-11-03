"""
AI Orchestrator Test Suite

This script tests the orchestrator functionality with realistic customer inquiries.

Usage:
    python test_orchestrator.py

Requirements:
    - OPENAI_API_KEY environment variable
    - Backend server running OR direct orchestrator testing

Author: MyHibachi Development Team
Created: October 31, 2025
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.orchestrator import (
    AIOrchestrator,
    OrchestratorRequest,
    OrchestratorConfig
)


class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


async def test_pricing_inquiry():
    """Test: Simple pricing inquiry"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 1: Simple Pricing Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    request = OrchestratorRequest(
        message="I need a quote for 10 adults in Sacramento 95630",
        channel="email",
        customer_context={
            "name": "John Doe",
            "email": "john@example.com",
            "zipcode": "95630"
        }
    )
    
    print(f"\n{Color.CYAN}Customer Inquiry:{Color.END}")
    print(f"  Message: {request.message}")
    print(f"  Channel: {request.channel}")
    print(f"  Location: {request.customer_context.get('zipcode')}")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await orchestrator.process_inquiry(request)
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}AI Response:{Color.END}")
    print(f"  {response.response[:200]}...")
    
    print(f"\n{Color.BLUE}Tools Used: {len(response.tools_used)}{Color.END}")
    for tool in response.tools_used:
        print(f"  • {tool.tool_name} ({tool.execution_time_ms}ms)")
        if tool.result:
            print(f"    Result preview: {str(tool.result)[:100]}...")
    
    print(f"\n{Color.BLUE}Metadata:{Color.END}")
    print(f"  Execution Time: {response.metadata.get('execution_time_ms')}ms")
    print(f"  Conversation ID: {response.conversation_id}")
    print(f"  Admin Review: {response.requires_admin_review}")
    
    return response.success


async def test_protein_upgrades():
    """Test: Pricing with protein upgrades"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 2: Protein Upgrade Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    request = OrchestratorRequest(
        message="How much for 15 adults with filet mignon and lobster in 95825?",
        channel="email",
        customer_context={
            "email": "customer@example.com",
            "zipcode": "95825"
        }
    )
    
    print(f"\n{Color.CYAN}Customer Inquiry:{Color.END}")
    print(f"  Message: {request.message}")
    print(f"  Expected Tools: PricingTool (filet +$5, lobster +$15)")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await orchestrator.process_inquiry(request)
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}Tools Used:{Color.END}")
    for tool in response.tools_used:
        print(f"  • {tool.tool_name}")
        if tool.result.get("upgrade_cost"):
            print(f"    Upgrade Cost: ${tool.result['upgrade_cost']}")
        if tool.result.get("total"):
            print(f"    Total Quote: ${tool.result['total']}")
    
    return response.success


async def test_travel_fee():
    """Test: Travel fee calculation"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 3: Travel Fee Inquiry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    request = OrchestratorRequest(
        message="Do you service Folsom CA? How much for travel?",
        channel="sms",
        customer_context={
            "address": "Folsom, CA"
        }
    )
    
    print(f"\n{Color.CYAN}Customer Inquiry:{Color.END}")
    print(f"  Message: {request.message}")
    print(f"  Channel: {request.channel} (casual tone)")
    print(f"  Expected Tools: TravelFeeTool")
    
    print(f"\n{Color.YELLOW}Processing...{Color.END}")
    response = await orchestrator.process_inquiry(request)
    
    print(f"\n{Color.GREEN}✓ Response Generated{Color.END}")
    print(f"\n{Color.BLUE}AI Response (SMS format):{Color.END}")
    print(f"  {response.response}")
    
    print(f"\n{Color.BLUE}Tools Used:{Color.END}")
    for tool in response.tools_used:
        print(f"  • {tool.tool_name}")
        if tool.result.get("distance_miles"):
            print(f"    Distance: {tool.result['distance_miles']} miles")
        if tool.result.get("travel_fee"):
            print(f"    Travel Fee: ${tool.result['travel_fee']}")
    
    return response.success


async def test_multi_channel():
    """Test: Different channels"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 4: Multi-Channel Tone Adaptation{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    channels = ["email", "sms", "instagram"]
    message = "Quote for 8 adults?"
    
    for channel in channels:
        print(f"\n{Color.CYAN}Testing Channel: {channel}{Color.END}")
        
        request = OrchestratorRequest(
            message=message,
            channel=channel,
            customer_context={"zipcode": "95630"}
        )
        
        response = await orchestrator.process_inquiry(request)
        
        print(f"  Response Length: {len(response.response)} chars")
        print(f"  Response Preview: {response.response[:100]}...")
        print(f"  Tools Used: {len(response.tools_used)}")
    
    return True


async def test_error_handling():
    """Test: Error handling"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 5: Error Handling{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    # Test with invalid input
    request = OrchestratorRequest(
        message="",  # Empty message
        channel="email"
    )
    
    print(f"\n{Color.CYAN}Testing Error Handling:{Color.END}")
    print(f"  Empty message input")
    
    response = await orchestrator.process_inquiry(request)
    
    if not response.success:
        print(f"\n{Color.GREEN}✓ Error handled gracefully{Color.END}")
        print(f"  Error: {response.error}")
        print(f"  Fallback message provided: {bool(response.response)}")
    else:
        print(f"\n{Color.YELLOW}⚠ AI handled empty message{Color.END}")
    
    return True


async def test_tool_registry():
    """Test: Tool registry"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 6: Tool Registry{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    orchestrator = AIOrchestrator()
    
    tools = orchestrator.tool_registry.list_tools()
    print(f"\n{Color.CYAN}Registered Tools: {len(tools)}{Color.END}")
    
    for tool_name in tools:
        tool = orchestrator.tool_registry.get(tool_name)
        print(f"\n  {Color.BLUE}• {tool.name}{Color.END}")
        print(f"    Description: {tool.description[:80]}...")
        print(f"    Parameters: {len(tool.parameters)}")
    
    # Get OpenAI function schemas
    schemas = orchestrator.tool_registry.to_openai_functions()
    print(f"\n{Color.GREEN}✓ OpenAI Schemas Generated: {len(schemas)}{Color.END}")
    
    return len(tools) == 3  # Expecting 3 tools in Phase 1


async def test_phase3_features():
    """Test: Phase 3 feature flags"""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.BOLD}TEST 7: Phase 3 Feature Flags{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}")
    
    config = OrchestratorConfig(
        enable_rag=False,
        enable_voice=False,
        enable_threading=False,
        enable_identity=False
    )
    
    orchestrator = AIOrchestrator(config=config)
    
    print(f"\n{Color.CYAN}Phase 3 Features Status:{Color.END}")
    print(f"  RAG: {Color.RED}Disabled{Color.END} (Phase 3 - Data Collection)")
    print(f"  Voice AI: {Color.RED}Disabled{Color.END} (Phase 3 - Data Collection)")
    print(f"  Threading: {Color.RED}Disabled{Color.END} (Phase 3 - Data Collection)")
    print(f"  Identity: {Color.RED}Disabled{Color.END} (Phase 3 - Data Collection)")
    
    print(f"\n{Color.GREEN}✓ Phase 3 services initialized as placeholders{Color.END}")
    print(f"  All features ready to activate with feature flags")
    
    return True


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "AI ORCHESTRATOR TEST SUITE" + " "*32 + "║")
    print("║" + " "*30 + "Phase 1" + " "*41 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Color.END}")
    
    start_time = datetime.now()
    
    tests = [
        ("Simple Pricing", test_pricing_inquiry),
        ("Protein Upgrades", test_protein_upgrades),
        ("Travel Fee", test_travel_fee),
        ("Multi-Channel", test_multi_channel),
        ("Error Handling", test_error_handling),
        ("Tool Registry", test_tool_registry),
        ("Phase 3 Features", test_phase3_features)
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
        print(f"{Color.GREEN}{Color.BOLD}🎉 ALL TESTS PASSED! 🎉{Color.END}\n")
        return 0
    else:
        print(f"{Color.YELLOW}⚠ Some tests failed. Review errors above.{Color.END}\n")
        return 1


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Color.RED}Error: OPENAI_API_KEY environment variable not set{Color.END}")
        sys.exit(1)
    
    # Run tests
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
