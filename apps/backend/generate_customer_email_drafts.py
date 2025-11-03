"""
Generate Customer Email Drafts with Protein System
Malia (Sonoma) & Debbie (Antioch Christmas Eve)
"""

import sys
from datetime import datetime
from decimal import Decimal

# Add the backend src to path
sys.path.insert(0, 'src')

from api.ai.endpoints.services.protein_calculator_service import get_protein_calculator_service


def calculate_travel_fee(distance_miles, free_miles=30, rate_per_mile=2.00):
    """Calculate travel fee"""
    if distance_miles <= free_miles:
        return 0.00
    billable_miles = distance_miles - free_miles
    return billable_miles * rate_per_mile


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80 + "\n")


def generate_malia_quote():
    """Generate Malia's quote with protein breakdown"""
    
    print_section("MALIA'S QUOTE - Sonoma, CA")
    
    # Customer details
    guest_count = 9
    adults = 9
    children = 0
    adult_price = 55.00
    child_price = 30.00
    
    # Protein selections (all free proteins)
    protein_selections = {
        "steak": 9,
        "chicken": 9
    }
    
    # Calculate protein costs
    protein_calc = get_protein_calculator_service()
    protein_result = protein_calc.calculate_protein_costs(guest_count, protein_selections)
    
    # Base pricing
    adult_total = adults * adult_price
    child_total = children * child_price
    food_total = adult_total + child_total + protein_result['total_protein_cost']
    
    # Minimum check (BEFORE travel)
    party_minimum = 550.00
    meets_minimum = food_total >= party_minimum
    charged_amount = max(food_total, party_minimum)
    
    # Travel fee (ON TOP)
    distance_miles = 60.0
    travel_fee = calculate_travel_fee(distance_miles)
    
    # Grand total
    grand_total = charged_amount + travel_fee
    
    # Generate output
    print("📧 CUSTOMER: Malia")
    print("📍 LOCATION: Sonoma, CA (~60 miles)")
    print("👥 PARTY SIZE: 9 adults")
    print("📅 DATE: [To be determined]")
    print()
    
    print("💰 PRICING BREAKDOWN:")
    print(f"   Adults: {adults} × ${adult_price:.2f} = ${adult_total:.2f}")
    print(f"   Food Subtotal: ${food_total:.2f}")
    print()
    
    print("🍖 PROTEIN SELECTIONS:")
    print(f"   {protein_result['proteins_summary']}")
    print(f"   Free allowance: {protein_result['free_protein_allowance']} proteins ({guest_count} guests × 2)")
    print(f"   Total selected: {protein_result['total_proteins']} proteins")
    print(f"   Protein extras: ${protein_result['total_protein_cost']:.2f} ✅ (All FREE base proteins!)")
    print()
    
    if not meets_minimum:
        shortfall = party_minimum - food_total
        print(f"⚠️  MINIMUM ORDER:")
        print(f"   Food total: ${food_total:.2f}")
        print(f"   Party minimum: ${party_minimum:.2f}")
        print(f"   Shortfall: ${shortfall:.2f}")
        print(f"   💵 You'll be charged: ${charged_amount:.2f} (our minimum)")
        print()
        print("   💡 OPTIONAL PAID UPGRADES (Maximize your $550.00):")
        print(f"      • Add Filet Mignon upgrades (+$5.00 each)")
        print(f"      • Add Lobster Tail upgrades (+$15.00 each)")
        print(f"      • Add Gyoza appetizer ($10) or Edamame ($5)")
        print()
    
    print("🚗 TRAVEL FEE (Added on top):")
    print(f"   Distance: {distance_miles} miles")
    print(f"   Free miles: 30")
    print(f"   Billable miles: {distance_miles - 30}")
    print(f"   Rate: $2.00/mile")
    print(f"   Travel Fee: ${travel_fee:.2f}")
    print()
    
    print("💰 GRAND TOTAL:")
    print(f"   Charged: ${charged_amount:.2f}")
    print(f"   + Travel: ${travel_fee:.2f}")
    print(f"   = **${grand_total:.2f}**")
    print()
    
    print("💝 GRATUITY GUIDE (100% Optional):")
    print(f"   • Good service (20%): ${charged_amount * 0.20:.2f}")
    print(f"   • Great service (25%): ${charged_amount * 0.25:.2f}")
    print(f"   • Excellent service (30%): ${charged_amount * 0.30:.2f}")
    print(f"   • Outstanding service (35%): ${charged_amount * 0.35:.2f}")
    print()
    
    return {
        "customer": "Malia",
        "location": "Sonoma, CA",
        "adults": adults,
        "children": children,
        "food_total": food_total,
        "charged_amount": charged_amount,
        "travel_fee": travel_fee,
        "grand_total": grand_total,
        "protein_result": protein_result
    }


def generate_debbie_quote():
    """Generate Debbie's quote with Christmas Eve availability"""
    
    print_section("DEBBIE'S QUOTE - Antioch, CA (Christmas Eve)")
    
    # Customer details
    adults = 14
    children = 2
    guest_count = adults + children
    adult_price = 55.00
    child_price = 30.00
    
    # Protein selections (10 Filet upgrades + free proteins)
    protein_selections = {
        "filet_mignon": 10,
        "chicken": 12,
        "shrimp": 10
    }
    
    # Calculate protein costs
    protein_calc = get_protein_calculator_service()
    protein_result = protein_calc.calculate_protein_costs(guest_count, protein_selections)
    
    # Base pricing
    adult_total = adults * adult_price
    child_total = children * child_price
    food_total = adult_total + child_total + protein_result['total_protein_cost']
    
    # Minimum check (BEFORE travel)
    party_minimum = 550.00
    meets_minimum = food_total >= party_minimum
    charged_amount = max(food_total, party_minimum)
    
    # Travel fee (ON TOP)
    distance_miles = 45.0
    travel_fee = calculate_travel_fee(distance_miles)
    
    # Grand total
    grand_total = charged_amount + travel_fee
    
    # Generate output
    print("📧 CUSTOMER: Debbie")
    print("📍 LOCATION: Antioch, CA 94509 (~45 miles)")
    print("👥 PARTY SIZE: 14 adults + 2 children (16 total)")
    print("📅 DATE: December 24, 2025 (Christmas Eve) 🎄")
    print("🎅 AVAILABILITY: ✅ AVAILABLE (2 chefs, 4 time slots)")
    print()
    
    print("💰 PRICING BREAKDOWN:")
    print(f"   Adults: {adults} × ${adult_price:.2f} = ${adult_total:.2f}")
    print(f"   Children (6-12): {children} × ${child_price:.2f} = ${child_total:.2f}")
    print(f"   Food Subtotal: ${adult_total + child_total:.2f}")
    print()
    
    print("🍖 PROTEIN SELECTIONS:")
    print(f"   {protein_result['proteins_summary']}")
    print(f"   Free allowance: {protein_result['free_protein_allowance']} proteins ({guest_count} guests × 2)")
    print(f"   Total selected: {protein_result['total_proteins']} proteins")
    print()
    print(f"   💎 Protein Upgrades:")
    print(f"      • {protein_result['upgrade_cost']:.2f} in premium protein upgrades")
    print(f"        (10× Filet Mignon @ $5.00 each)")
    print(f"      • ${protein_result['third_protein_cost']:.2f} for 3rd protein charges")
    print(f"   **Total protein extras: ${protein_result['total_protein_cost']:.2f}**")
    print()
    
    print(f"📊 FOOD TOTAL: ${food_total:.2f}")
    print(f"   Status: {'✅ MEETS MINIMUM' if meets_minimum else '❌ BELOW MINIMUM'}")
    if meets_minimum:
        surplus = food_total - party_minimum
        print(f"   (${surplus:.2f} above ${party_minimum:.2f} minimum)")
    print()
    
    print("🚗 TRAVEL FEE (Added on top):")
    print(f"   Distance: {distance_miles} miles")
    print(f"   Free miles: 30")
    print(f"   Billable miles: {distance_miles - 30}")
    print(f"   Rate: $2.00/mile")
    print(f"   Travel Fee: ${travel_fee:.2f}")
    print()
    
    print("💰 GRAND TOTAL:")
    print(f"   Food: ${food_total:.2f}")
    print(f"   + Travel: ${travel_fee:.2f}")
    print(f"   = **${grand_total:.2f}**")
    print()
    
    print("🎄 CHRISTMAS EVE AVAILABILITY:")
    print("   Date: Wednesday, December 24, 2025")
    print("   Status: ✅ AVAILABLE")
    print("   Time Slots: 12pm / 3pm / 6pm / 9pm")
    print("   Note: 2 chefs available (internal only)")
    print()
    
    print("💝 GRATUITY GUIDE (100% Optional):")
    print(f"   • Good service (20%): ${food_total * 0.20:.2f}")
    print(f"   • Great service (25%): ${food_total * 0.25:.2f}")
    print(f"   • Excellent service (30%): ${food_total * 0.30:.2f}")
    print(f"   • Outstanding service (35%): ${food_total * 0.35:.2f}")
    print()
    
    return {
        "customer": "Debbie",
        "location": "Antioch, CA 94509",
        "adults": adults,
        "children": children,
        "food_total": food_total,
        "charged_amount": charged_amount,
        "travel_fee": travel_fee,
        "grand_total": grand_total,
        "protein_result": protein_result,
        "christmas_eve": True
    }


def generate_email_template(quote_data):
    """Generate professional email template"""
    
    print_section(f"EMAIL DRAFT FOR {quote_data['customer'].upper()}")
    
    is_christmas = quote_data.get('christmas_eve', False)
    
    print("Subject: Your My Hibachi Chef Quote" + (" - Christmas Eve Available! 🎄" if is_christmas else ""))
    print()
    print("---")
    print()
    
    print(f"Hi {quote_data['customer']},")
    print()
    print("Thank you for your interest in My Hibachi Chef! We're excited to bring an unforgettable")
    print("hibachi experience to your celebration. Here's your personalized quote:")
    print()
    print("═══════════════════════════════════════════════════════════════════")
    print("📋 YOUR QUOTE SUMMARY")
    print("═══════════════════════════════════════════════════════════════════")
    print()
    print(f"📍 Location: {quote_data['location']}")
    print(f"👥 Party Size: {quote_data['adults']} adults" + (f" + {quote_data['children']} children" if quote_data['children'] > 0 else ""))
    if is_christmas:
        print(f"📅 Date: December 24, 2025 (Christmas Eve) 🎄")
    print()
    
    print("💰 PRICING BREAKDOWN:")
    print(f"   Food & Protein Selections: ${quote_data['food_total']:.2f}")
    print(f"   Travel Fee: ${quote_data['travel_fee']:.2f}")
    print(f"   ──────────────────────────")
    print(f"   **TOTAL: ${quote_data['grand_total']:.2f}**")
    print()
    
    print("🍖 YOUR PROTEIN SELECTIONS:")
    print(f"   {quote_data['protein_result']['proteins_summary']}")
    print()
    
    protein_upgrade_cost = quote_data['protein_result']['upgrade_cost']
    if protein_upgrade_cost > 0:
        print(f"   ✨ Includes ${protein_upgrade_cost:.2f} in premium protein upgrades!")
        print()
    
    if is_christmas:
        print("🎄 CHRISTMAS EVE AVAILABILITY:")
        print("   ✅ Great news - we have availability for Christmas Eve!")
        print("   Available time slots: 12pm / 3pm / 6pm / 9pm")
        print("   Please let us know your preferred time!")
        print()
    
    print("💝 GRATUITY (100% Optional):")
    print("   While completely optional, our chefs deeply appreciate tips!")
    print(f"   Suggested range: ${quote_data['food_total'] * 0.20:.2f} - ${quote_data['food_total'] * 0.35:.2f} (20-35%)")
    print()
    
    print("🎯 WHAT'S INCLUDED:")
    print("   • Professional hibachi chef with all equipment")
    print("   • Interactive cooking show & entertainment")
    print("   • Choice of 2 proteins per guest (from our premium selection)")
    print("   • Hibachi fried rice, fresh vegetables, side salad")
    print("   • Signature sauces & seasonings")
    print("   • Sake service for adults 21+")
    print()
    
    print("📅 NEXT STEPS:")
    print(f"   1. Review this quote and let us know if you have any questions")
    print(f"   2. Choose your preferred date" + (" and time slot" if is_christmas else ""))
    print(f"   3. Confirm your protein selections for each guest")
    print(f"   4. We'll send a booking confirmation with payment details")
    print()
    
    print("💬 QUESTIONS? READY TO BOOK?")
    print("   📧 Email: cs@myhibachichef.com")
    print("   📞 Phone: (916) 740-8768")
    print("   🌐 Website: www.myhibachichef.com")
    print()
    
    print("We're thrilled to create an unforgettable hibachi experience for you!")
    print()
    print("Warmest regards,")
    print("My Hibachi Chef Team")
    print("🔥 Bringing the Hibachi Experience to You! 🔥")
    print()
    print("---")
    print()


def main():
    """Generate all customer quotes and email drafts"""
    
    print("=" * 80)
    print("CUSTOMER QUOTE GENERATION WITH PROTEIN SYSTEM")
    print("=" * 80)
    
    # Generate Malia's quote
    malia_quote = generate_malia_quote()
    generate_email_template(malia_quote)
    
    # Generate Debbie's quote
    debbie_quote = generate_debbie_quote()
    generate_email_template(debbie_quote)
    
    print_section("✅ QUOTE GENERATION COMPLETE")
    
    print("📊 SUMMARY:")
    print(f"   Malia (Sonoma): ${malia_quote['grand_total']:.2f}")
    print(f"   Debbie (Antioch, Christmas Eve): ${debbie_quote['grand_total']:.2f}")
    print()
    print("📝 NEXT STEPS:")
    print("   1. Review email drafts above")
    print("   2. Make any necessary adjustments")
    print("   3. Get approval from business owner")
    print("   4. Send emails to customers")
    print()


if __name__ == "__main__":
    main()
