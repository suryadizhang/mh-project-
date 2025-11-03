"""
Test pricing service with real customer quotes
Generate quotes for Malia and Debbie with Google Maps integration
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.join(current_dir, '../..')
sys.path.insert(0, backend_src)

from api.ai.endpoints.services.pricing_service import get_pricing_service


def test_malia_quote():
    """Test Malia's quote: 9 adults, Sonoma, CA"""
    print("\n" + "="*80)
    print("MALIA'S QUOTE - 9 Adults in Sonoma, CA")
    print("="*80)
    
    pricing = get_pricing_service(db=None, station_id=None)
    
    quote = pricing.calculate_party_quote(
        adults=9,
        children=0,
        children_under_5=0,
        upgrades=None,
        addons=None,
        customer_address="Sonoma, CA",
        customer_zipcode="95476"
    )
    
    print(f"\n📋 QUOTE BREAKDOWN:")
    print(f"   Adults (9): {quote['breakdown']['adults']['count']} × ${quote['breakdown']['adults']['unit_price']:.2f} = ${quote['breakdown']['adults']['total']:.2f}")
    print(f"   Subtotal: ${quote['breakdown']['subtotal']:.2f}")
    
    if quote['breakdown'].get('travel_info'):
        travel = quote['breakdown']['travel_info']
        print(f"\n🚗 TRAVEL FEE:")
        if travel.get('status') == 'success':
            print(f"   Distance: {travel['distance_miles']} miles ({travel['drive_time']})")
            print(f"   From: {travel.get('from', 'Station')}")
            print(f"   To: {travel.get('to', 'Customer')}")
            if travel.get('breakdown'):
                br = travel['breakdown']
                print(f"   Free miles: {br['free_miles']}")
                print(f"   Billable miles: {br['billable_miles']}")
                print(f"   Rate: ${br['rate_per_mile']:.2f}/mile")
            print(f"   Travel Fee: ${travel['travel_fee']:.2f}")
            if travel.get('note'):
                print(f"   Note: {travel['note']}")
        else:
            print(f"   Status: {travel.get('status')}")
            print(f"   Message: {travel.get('message')}")
    
    print(f"\n💰 TOTAL: ${quote['total']:.2f}")
    print(f"   Minimum Required: ${quote['minimum_required']:.2f}")
    print(f"   Meets Minimum: {'✅ YES' if quote['meets_minimum'] else '❌ NO'}")
    
    if quote.get('gratuity_guidance'):
        gratuity = quote['gratuity_guidance']
        print(f"\n{gratuity['message']}")
    
    return quote


def test_debbie_quote():
    """Test Debbie's quote: 14 adults + 2 children + 10 filet, Antioch, CA 94509"""
    print("\n" + "="*80)
    print("DEBBIE'S QUOTE - 14 Adults + 2 Children + 10 Filet in Antioch, CA 94509")
    print("="*80)
    
    pricing = get_pricing_service(db=None, station_id=None)
    
    quote = pricing.calculate_party_quote(
        adults=14,
        children=2,
        children_under_5=0,
        upgrades={"filet_mignon": 10},
        addons=None,
        customer_address="Antioch, CA 94509",
        customer_zipcode="94509"
    )
    
    print(f"\n📋 QUOTE BREAKDOWN:")
    print(f"   Adults (14): {quote['breakdown']['adults']['count']} × ${quote['breakdown']['adults']['unit_price']:.2f} = ${quote['breakdown']['adults']['total']:.2f}")
    print(f"   Children (2): {quote['breakdown']['children']['count']} × ${quote['breakdown']['children']['unit_price']:.2f} = ${quote['breakdown']['children']['total']:.2f}")
    
    if quote['breakdown'].get('upgrades'):
        print(f"\n🥩 UPGRADES:")
        for name, details in quote['breakdown']['upgrades'].items():
            print(f"   {name.replace('_', ' ').title()}: {details['count']} × ${details['unit_price']:.2f} = ${details['total']:.2f}")
    
    print(f"\n   Subtotal: ${quote['breakdown']['subtotal']:.2f}")
    print(f"   Upgrade Total: ${quote['breakdown']['upgrade_total']:.2f}")
    
    if quote['breakdown'].get('travel_info'):
        travel = quote['breakdown']['travel_info']
        print(f"\n🚗 TRAVEL FEE:")
        if travel.get('status') == 'success':
            print(f"   Distance: {travel['distance_miles']} miles ({travel['drive_time']})")
            print(f"   From: {travel.get('from', 'Station')}")
            print(f"   To: {travel.get('to', 'Customer')}")
            if travel.get('breakdown'):
                br = travel['breakdown']
                print(f"   Free miles: {br['free_miles']}")
                print(f"   Billable miles: {br['billable_miles']}")
                print(f"   Rate: ${br['rate_per_mile']:.2f}/mile")
            print(f"   Travel Fee: ${travel['travel_fee']:.2f}")
            if travel.get('note'):
                print(f"   Note: {travel['note']}")
        else:
            print(f"   Status: {travel.get('status')}")
            print(f"   Message: {travel.get('message')}")
    
    print(f"\n💰 TOTAL: ${quote['total']:.2f}")
    print(f"   Minimum Required: ${quote['minimum_required']:.2f}")
    print(f"   Meets Minimum: {'✅ YES' if quote['meets_minimum'] else '❌ NO'}")
    
    if quote.get('gratuity_guidance'):
        gratuity = quote['gratuity_guidance']
        print(f"\n{gratuity['message']}")
    
    return quote


def test_zip_only_quote():
    """Test quote with ZIP code only (should give polite reminder)"""
    print("\n" + "="*80)
    print("TEST: ZIP CODE ONLY - Should show polite reminder about full address")
    print("="*80)
    
    pricing = get_pricing_service(db=None, station_id=None)
    
    quote = pricing.calculate_party_quote(
        adults=10,
        children=0,
        customer_address=None,  # No full address
        customer_zipcode="94509"  # Only ZIP
    )
    
    print(f"\n📋 QUOTE BREAKDOWN:")
    print(f"   Adults: {quote['breakdown']['adults']['count']} × ${quote['breakdown']['adults']['unit_price']:.2f} = ${quote['breakdown']['adults']['total']:.2f}")
    
    if quote['breakdown'].get('travel_info'):
        travel = quote['breakdown']['travel_info']
        print(f"\n🚗 TRAVEL FEE:")
        print(f"   Status: {travel.get('status')}")
        if travel.get('distance_miles'):
            print(f"   Distance: {travel['distance_miles']} miles")
        if travel.get('travel_fee') is not None:
            print(f"   Travel Fee: ${travel['travel_fee']:.2f}")
        if travel.get('note'):
            print(f"   📍 {travel['note']}")
    
    print(f"\n💰 TOTAL: ${quote['total']:.2f}")
    
    return quote


if __name__ == "__main__":
    print("\n🧪 TESTING PRICING SERVICE WITH REAL CUSTOMER QUOTES")
    print("=" * 80)
    
    # Test Malia's quote
    malia_quote = test_malia_quote()
    
    # Test Debbie's quote
    debbie_quote = test_debbie_quote()
    
    # Test ZIP-only (polite reminder test)
    zip_quote = test_zip_only_quote()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
