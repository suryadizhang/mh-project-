"""
Test Protein Upgrade System
Tests the new smart protein calculation with various scenarios
"""

import sys
from decimal import Decimal

# Add the backend src to path
sys.path.insert(0, 'src')

from api.ai.endpoints.services.protein_calculator_service import get_protein_calculator_service


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80 + "\n")


def test_scenario(scenario_name, guest_count, protein_selections):
    """Test a protein selection scenario"""
    print(f"📊 {scenario_name}")
    print(f"   Guests: {guest_count}")
    print(f"   Protein selections: {protein_selections}")
    print()
    
    calculator = get_protein_calculator_service()
    
    # Validate first
    is_valid, error_msg = calculator.validate_protein_selection(guest_count, protein_selections)
    if not is_valid:
        print(f"   ❌ VALIDATION ERROR: {error_msg}")
        print()
        return
    
    # Calculate costs
    result = calculator.calculate_protein_costs(guest_count, protein_selections)
    
    print(f"   💰 Cost Summary:")
    print(f"      Upgrade cost: ${result['upgrade_cost']:.2f}")
    print(f"      3rd protein cost: ${result['third_protein_cost']:.2f}")
    print(f"      Total protein extras: ${result['total_protein_cost']:.2f}")
    print()
    
    print(f"   🍖 Protein Breakdown:")
    for item in result['breakdown']:
        status = []
        if item['is_free']:
            status.append("FREE")
        if item['is_upgrade']:
            status.append(f"UPGRADE +${item['upgrade_price']}")
        if item['is_third_protein']:
            status.append("3RD PROTEIN")
        
        status_str = " | ".join(status) if status else "BASE"
        print(f"      • {item['protein_name']}: {item['quantity']}× ({status_str})")
    
    print()
    print(f"   📋 Summary: {result['proteins_summary']}")
    print()


def main():
    """Run all protein system tests"""
    
    print_section("🍖 PROTEIN UPGRADE SYSTEM TEST SUITE")
    
    # Scenario 1: Simple case - 10 guests, all free proteins
    print_section("SCENARIO 1: Basic Free Proteins Only")
    print("Customer: 10 guests with 20 proteins (all free options)")
    print("Expected: $0 extra (all within free allowance)")
    test_scenario(
        "10 guests, 11 Steak + 9 Chicken",
        guest_count=10,
        protein_selections={
            "steak": 11,
            "chicken": 9
        }
    )
    
    # Scenario 2: Filet Mignon upgrade
    print_section("SCENARIO 2: Filet Mignon Upgrade")
    print("Customer: 10 guests, upgrade some proteins to Filet Mignon")
    print("Expected: $5 per Filet Mignon")
    test_scenario(
        "10 guests, 11 Filet + 9 Chicken",
        guest_count=10,
        protein_selections={
            "filet_mignon": 11,
            "chicken": 9
        }
    )
    
    # Scenario 3: Lobster + 3rd protein
    print_section("SCENARIO 3: Lobster Upgrade + 3rd Protein")
    print("Customer: 10 guests, 21 proteins (1 is Lobster)")
    print("Expected: $10 (3rd protein) + $15 (Lobster) = $25")
    test_scenario(
        "10 guests, 11 Steak + 9 Chicken + 1 Lobster",
        guest_count=10,
        protein_selections={
            "steak": 11,
            "chicken": 9,
            "lobster_tail": 1
        }
    )
    
    # Scenario 4: Multiple 3rd proteins
    print_section("SCENARIO 4: Multiple 3rd Proteins")
    print("Customer: 10 guests, 22 proteins (2 extra beyond free allowance)")
    print("Expected: $10 × 2 = $20 for 3rd proteins (each 3rd protein is +$10)")
    test_scenario(
        "10 guests, 11 Steak + 11 Chicken (22 proteins total)",
        guest_count=10,
        protein_selections={
            "steak": 11,
            "chicken": 11
        }
    )
    
    # Scenario 5: Complex mix
    print_section("SCENARIO 5: Complex Mix - Multiple Upgrades + 3rd Proteins")
    print("Customer: 10 guests, mixed premium proteins + 3rd proteins")
    print("Expected: Filet upgrades + Scallop upgrades + 3rd protein charges")
    test_scenario(
        "10 guests, 8 Filet + 8 Chicken + 5 Scallops (21 proteins)",
        guest_count=10,
        protein_selections={
            "filet_mignon": 8,
            "chicken": 8,
            "scallops": 5
        }
    )
    
    # Scenario 6: Malia's actual quote (9 guests)
    print_section("SCENARIO 6: Malia's Quote - 9 Adults, All Free Proteins")
    print("Customer: Malia from Sonoma, CA")
    print("Expected: $0 extra (18 free proteins = 9 guests × 2)")
    test_scenario(
        "9 guests, 9 Steak + 9 Chicken",
        guest_count=9,
        protein_selections={
            "steak": 9,
            "chicken": 9
        }
    )
    
    # Scenario 7: Debbie's actual quote (14 adults + 2 children with Filet)
    print_section("SCENARIO 7: Debbie's Quote - 16 Total Guests, 10 Filet Upgrades")
    print("Customer: Debbie - Christmas Eve in Antioch, CA")
    print("Expected: $5 × 10 = $50 for Filet upgrades")
    test_scenario(
        "16 guests, 10 Filet + 12 Chicken + 10 Shrimp (32 proteins = 16×2)",
        guest_count=16,
        protein_selections={
            "filet_mignon": 10,
            "chicken": 12,
            "shrimp": 10
        }
    )
    
    # Scenario 8: Error case - Not enough proteins
    print_section("SCENARIO 8: Minimum Order Value Enforcement")
    print("Customer: 10 guests but only 5 proteins selected")
    print("Expected: Validation error - need minimum 1 protein per guest")
    print("Note: If food total < $550, customer is charged $550 minimum")
    print("      We suggest OPTIONAL PAID upgrades to maximize their $550 value")
    test_scenario(
        "10 guests, only 5 proteins (ERROR - not enough proteins)",
        guest_count=10,
        protein_selections={
            "chicken": 5
        }
    )
    
    # Scenario 9: All premium proteins
    print_section("SCENARIO 9: Luxury Party - All Premium Proteins")
    print("Customer: 10 guests, all Lobster Tail")
    print("Expected: $15 × 20 = $300 for premium upgrades")
    test_scenario(
        "10 guests, 20 Lobster Tail",
        guest_count=10,
        protein_selections={
            "lobster_tail": 20
        }
    )
    
    # Scenario 10: Show available proteins
    print_section("AVAILABLE PROTEINS & PRICING")
    calculator = get_protein_calculator_service()
    available = calculator.get_available_proteins()
    
    print("🆓 FREE BASE PROTEINS (Included in base price):")
    for protein in available['free_proteins']:
        if not protein['key'].endswith('_'): # Skip duplicates
            print(f"   • {protein['name']}: Included (2 per guest)")
    
    print()
    print("💎 PREMIUM UPGRADE PROTEINS:")
    for protein in available['premium_upgrades']:
        if not protein['key'].endswith('_'):  # Skip duplicates
            print(f"   • {protein['name']}: +${protein['price']:.2f} per protein")
    
    print()
    print(f"🔢 3RD PROTEIN: +${available['third_protein_price']:.2f} per person")
    print(f"   (Each guest gets {available['protein_allowance_per_guest']} free protein choices)")
    
    print_section("✅ ALL TESTS COMPLETE")
    
    print("\n📝 KEY TAKEAWAYS:")
    print("   1. Each guest gets 2 FREE protein choices")
    print("   2. FREE proteins: Chicken, NY Strip Steak, Shrimp, Tofu, Vegetables")
    print("   3. UPGRADE proteins: Salmon (+$5), Scallops (+$5), Filet (+$5), Lobster (+$15)")
    print("   4. If total proteins > (guests × 2): Each extra protein is +$10 (3rd protein charge)")
    print("   5. If 3rd protein is premium: +$10 (3rd) + premium price")
    print("   6. Minimum order value: $550 per event (checked BEFORE travel fee)")
    print("   7. If food total < $550: Customer pays $550 minimum + travel fee")
    print("   8. Suggest OPTIONAL PAID upgrades to maximize customer's $550 value (NOT free!)")
    print()


if __name__ == "__main__":
    main()
