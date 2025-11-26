#!/usr/bin/env python3
"""
Test Google Maps Distance Matrix API and Travel Fee Calculator
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def calculate_travel_fee(distance_miles):
    """Calculate travel fee based on distance"""
    free_miles = int(os.getenv('TRAVEL_FREE_DISTANCE_MILES', 30))
    fee_per_mile_cents = int(os.getenv('TRAVEL_FEE_PER_MILE_CENTS', 200))
    fee_per_mile = fee_per_mile_cents / 100
    
    if distance_miles <= free_miles:
        return 0.0, free_miles, 0.0
    
    billable_miles = distance_miles - free_miles
    total_fee = billable_miles * fee_per_mile
    return total_fee, free_miles, billable_miles

def test_distance_api(destination_address):
    """Test Google Maps Distance Matrix API"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    business_address = os.getenv('BUSINESS_ADDRESS')
    
    # Use coordinates for origin
    origin = f"{os.getenv('BUSINESS_LATITUDE')},{os.getenv('BUSINESS_LONGITUDE')}"
    
    # Build API URL
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': origin,
        'destinations': destination_address,
        'key': api_key
    }
    
    print("\n" + "=" * 70)
    print("🚗 GOOGLE MAPS API TEST - TRAVEL FEE CALCULATOR")
    print("=" * 70)
    print(f"From: {business_address}")
    print(f"To: {destination_address}\n")
    
    # Make API request
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('status') == 'OK':
        element = data['rows'][0]['elements'][0]
        
        if element.get('status') == 'OK':
            # Extract distance and duration
            distance_meters = element['distance']['value']
            distance_miles = distance_meters / 1609.34
            duration_text = element['duration']['text']
            
            print(f"📍 Distance: {distance_miles:.1f} miles")
            print(f"⏱️  Drive Time: {duration_text}\n")
            
            # Calculate travel fee
            total_fee, free_miles, billable_miles = calculate_travel_fee(distance_miles)
            
            print("💰 TRAVEL FEE CALCULATION:")
            print("-" * 70)
            if total_fee == 0:
                print(f"   ✅ FREE DELIVERY (within {free_miles} miles)")
                print(f"   Travel Fee: $0.00")
            else:
                fee_per_mile = int(os.getenv('TRAVEL_FEE_PER_MILE_CENTS')) / 100
                print(f"   Total distance: {distance_miles:.1f} miles")
                print(f"   Free distance: {free_miles} miles")
                print(f"   Billable miles: {billable_miles:.1f} miles")
                print(f"   Rate: ${fee_per_mile:.2f} per mile")
                print(f"   ")
                print(f"   💵 TOTAL TRAVEL FEE: ${total_fee:.2f}")
            
            print("=" * 70)
            return True
        else:
            print(f"❌ Routing Error: {element.get('status')}")
            return False
    else:
        print(f"❌ API Error: {data.get('status')}")
        print(f"Error Message: {data.get('error_message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    # Test with multiple destinations
    test_destinations = [
        "1600 Amphitheatre Parkway, Mountain View, CA",  # Google HQ - ~20 miles
        "Sacramento, CA",  # Sacramento - ~90 miles
        "San Francisco, CA",  # SF - ~40 miles
        "47300 Warm Springs Blvd, Fremont, CA"  # Close address - ~3 miles
    ]
    
    print("\n" + "🧪 TESTING GOOGLE MAPS DISTANCE MATRIX API" + "\n")
    
    for destination in test_destinations:
        test_distance_api(destination)
        print("\n")
