"""
AI Cost Monitoring API Test Script
Tests all 6 endpoints of the cost monitoring dashboard
"""

import httpx
import asyncio
from datetime import datetime, timedelta
import json


BASE_URL = "http://localhost:8000/api/v1"


async def test_cost_summary():
    """Test GET /ai/costs/summary"""
    print("\n🔍 Testing Cost Summary Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/ai/costs/summary")
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            print(f"Current Month Spend: ${data['current_month']['spend']:.2f}")
            print(f"Projected Spend: ${data['current_month']['projected']:.2f}")
            print(f"Budget: ${data['current_month']['threshold']:.2f}")
            print(f"Budget Used: {data['current_month']['threshold_percent']:.1f}%")
            print(f"\nToday's Stats:")
            print(f"  - Spend: ${data['today']['spend']:.2f}")
            print(f"  - API Calls: {data['today']['calls']}")
            print(f"  - Tokens: {data['today']['tokens']:,}")
            
            if data['breakdown']:
                print(f"\nModel Breakdown:")
                for model, stats in data['breakdown'].items():
                    print(f"  {model}:")
                    print(f"    - Cost: ${stats['cost_usd']:.2f}")
                    print(f"    - Calls: {stats['call_count']}")
                    print(f"    - Tokens: {stats['total_tokens']:,}")
            
            if data['recommendations']['llama3_upgrade']['recommended']:
                print(f"\n💡 Recommendation:")
                print(f"  {data['recommendations']['llama3_upgrade']['reason']}")
                print(f"  Potential Savings: ${data['recommendations']['llama3_upgrade']['potential_savings']:.2f}/month")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def test_cost_trend():
    """Test GET /ai/costs/trend"""
    print("\n🔍 Testing Cost Trend Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test with 7 days
            response = await client.get(f"{BASE_URL}/ai/costs/trend?days=7")
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            print(f"Days analyzed: {len(data['dates'])}")
            
            if data['dates']:
                print(f"\nLast 3 days:")
                for i in range(min(3, len(data['dates']))):
                    idx = -(i+1)
                    print(f"  {data['dates'][idx]}: ${data['costs'][idx]:.2f} ({data['calls'][idx]} calls)")
            
            # Calculate total
            total_cost = sum(data['costs'])
            total_calls = sum(data['calls'])
            avg_cost_per_call = total_cost / total_calls if total_calls > 0 else 0
            
            print(f"\n7-Day Summary:")
            print(f"  - Total Cost: ${total_cost:.2f}")
            print(f"  - Total Calls: {total_calls}")
            print(f"  - Avg Cost/Call: ${avg_cost_per_call:.4f}")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def test_hourly_costs():
    """Test GET /ai/costs/hourly"""
    print("\n🔍 Testing Hourly Costs Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test today's hourly breakdown
            response = await client.get(f"{BASE_URL}/ai/costs/hourly")
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            print(f"Hours with activity: {len(data)}")
            
            if data:
                print(f"\nTop 5 most expensive hours:")
                sorted_hours = sorted(data, key=lambda x: x['cost'], reverse=True)[:5]
                for hour_data in sorted_hours:
                    print(f"  {hour_data['hour']}: ${hour_data['cost']:.2f} ({hour_data['calls']} calls)")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def test_cost_alerts():
    """Test GET /ai/costs/alerts"""
    print("\n🔍 Testing Cost Alerts Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/ai/costs/alerts")
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            
            if data['has_alerts']:
                print(f"⚠️  {data['alert_count']} alert(s) found:")
                for alert in data['alerts']:
                    icon = "🚨" if alert['severity'] == 'critical' else "⚠️"
                    print(f"\n{icon} {alert['type'].upper()}")
                    print(f"   {alert['message']}")
            else:
                print("✅ No alerts - all costs within thresholds")
            
            print(f"\nChecked at: {data['checked_at']}")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def test_top_expensive():
    """Test GET /ai/costs/top-expensive"""
    print("\n🔍 Testing Top Expensive Queries Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/ai/costs/top-expensive?limit=5")
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            print(f"Found {len(data)} expensive queries")
            
            if data:
                print(f"\nTop 5 most expensive API calls:")
                for i, query in enumerate(data, 1):
                    print(f"\n{i}. ${query['cost_usd']:.3f} - {query['model']}")
                    print(f"   Tokens: {query['total_tokens']:,} (in: {query['input_tokens']}, out: {query['output_tokens']})")
                    print(f"   Response time: {query['response_time_ms']}ms")
                    print(f"   Created: {query['created_at']}")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def test_set_budget():
    """Test POST /ai/costs/set-budget"""
    print("\n🔍 Testing Set Budget Endpoint...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Get current summary first
            summary_response = await client.get(f"{BASE_URL}/ai/costs/summary")
            current_budget = summary_response.json()['current_month']['threshold']
            
            # Set new budget (same as current for testing)
            new_budget = current_budget
            response = await client.post(
                f"{BASE_URL}/ai/costs/set-budget",
                params={"budget_usd": new_budget}
            )
            response.raise_for_status()
            
            data = response.json()
            print("✅ Success!")
            print(f"Budget updated: ${data['new_budget']:.2f}")
            print(f"Message: {data['message']}")
            
            return True
            
        except httpx.HTTPError as e:
            print(f"❌ Failed: {e}")
            return False


async def run_all_tests():
    """Run all cost monitoring API tests"""
    print("\n" + "=" * 60)
    print("🧪 AI COST MONITORING API TEST SUITE")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Cost Summary", test_cost_summary),
        ("Cost Trend", test_cost_trend),
        ("Hourly Costs", test_hourly_costs),
        ("Cost Alerts", test_cost_alerts),
        ("Top Expensive Queries", test_top_expensive),
        ("Set Budget", test_set_budget),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Cost monitoring API is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
