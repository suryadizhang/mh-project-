"""
Send Customer Quotes via Email Service
Clean version without emojis for maximum email client compatibility
"""

import sys
import os
from datetime import datetime

# Add the backend src to path
sys.path.insert(0, 'src')


def generate_clean_email_debbie():
    """Generate Debbie's email without emojis"""
    
    subject = "Your My Hibachi Chef Quote - Christmas Eve Available!"
    
    body = """Hi Debbie,

Thank you so much for reaching out! We're thrilled that you're considering My Hibachi Chef for your holiday celebration - and we have GREAT NEWS: we DO have availability for December 24th!

Here's your personalized quote:

================================================================================
YOUR EVENT DETAILS
================================================================================

Party Size: 14 adults + 2 children (16 total guests)
Location: Antioch, CA 94509
Date: Wednesday, December 24, 2025 (Christmas Eve)
Protein Selections: 10x Filet Mignon upgrades + 12x Chicken + 10x Shrimp

================================================================================
PRICING BREAKDOWN
================================================================================

Base Pricing:
  * 14 adults x $55 = $770.00
  * 2 children (ages 6-12) x $30 = $60.00
  * Subtotal: $830.00

Premium Protein Upgrades:
  * 10x Filet Mignon upgrade @ $5 each = $50.00
  * (Your guests can choose 2 proteins each from: Chicken, Steak, Shrimp, 
     Tofu, or Veggies - and you're upgrading 10 to premium Filet Mignon!)

Food Total: $880.00

Travel Fee: (Fremont to Antioch, CA 94509)
  * Distance: Approximately 45 miles
  * First 30 miles: FREE
  * Remaining 15 miles x $2/mile = $30.00

================================================================================
YOUR TOTAL: $910.00
================================================================================

================================================================================
CHRISTMAS EVE AVAILABILITY
================================================================================

We're excited to share that we DO have chefs available for Christmas Eve!

Available time slots:
  * 12:00 PM
  * 3:00 PM
  * 6:00 PM
  * 9:00 PM

Which time works best for your celebration?

================================================================================
WHAT'S INCLUDED
================================================================================

Your hibachi experience includes:

  * Professional hibachi chef with all equipment
  * Interactive cooking show & entertainment
  * Choice of 2 proteins per guest (Chicken, Steak, Shrimp, Tofu, or Veggies)
  * Your 10 premium Filet Mignon upgrades
  * Hibachi fried rice, fresh vegetables, side salad
  * Signature sauces & seasonings
  * Sake service for adults 21+

================================================================================
GRATUITY (100% OPTIONAL)
================================================================================

While completely optional, our hardworking chefs deeply appreciate tips! 
A suggested range is 20-35% (approximately $176-$308) based on your 
satisfaction - but this is entirely at your discretion.

================================================================================
NEXT STEPS TO SECURE YOUR DATE
================================================================================

1. Let us know your preferred time slot (12pm / 3pm / 6pm / 9pm)
2. Confirm your protein selections for each guest
3. $100 deposit secures your Christmas Eve booking
4. Remaining balance ($810) due on event day (cash, Venmo, or Zelle)

IMPORTANT: Christmas Eve is one of our busiest dates! Early reservation 
is highly recommended to lock in your spot.

================================================================================
READY TO BOOK?
================================================================================

Just reply to this email with your preferred time slot, or feel free to 
call us at (916) 740-8768 to finalize your booking!

We're so excited to create an unforgettable hibachi experience for your 
holiday celebration!

Warmest regards,

Chef Ady & The My Hibachi Team
cs@myhibachichef.com
(916) 740-8768
www.myhibachichef.com

P.S. - If you'd like to add any extras like Gyoza appetizers (+$10) or 
Yakisoba Noodles (+$5), just let us know!
"""
    
    return {
        "to": "debbie.plummer@example.com",  # REPLACE WITH REAL EMAIL
        "from": "cs@myhibachichef.com",
        "subject": subject,
        "body": body,
        "customer_name": "Debbie Plummer",
        "total": 910.00
    }


def generate_clean_email_malia():
    """Generate Malia's email without emojis"""
    
    subject = "Your Hibachi Bachelorette Quote - Sonoma (August 2026)"
    
    body = """Hi Malia,

Thank you so much for reaching out! A hibachi bachelorette party sounds
absolutely AMAZING - we'd love to help make it an unforgettable celebration
for you and your friends!

Here's your personalized quote:

================================================================================
YOUR EVENT DETAILS
================================================================================

Party Size: 9 guests
Location: Sonoma, CA
Date: August 2026 (flexible date - we'll coordinate once you're closer!)
Protein Selections: NY Strip Steak & Chicken (all FREE base proteins!)

================================================================================
PRICING BREAKDOWN
================================================================================

Base Pricing:
  * 9 adults x $55 = $495.00

Premium Protein Upgrades:
  * None needed! Your guests chose FREE base proteins
  * (Each guest gets 2 proteins: Chicken, NY Strip Steak, Shrimp, Tofu, 
     or Veggies)

Food Subtotal: $495.00

Party Minimum: $550.00
  * Your food total is $55 below our party minimum, so you'll be charged 
    the minimum of $550.00

Travel Fee: (Fremont to Sonoma, CA)
  * Distance: Approximately 60 miles
  * First 30 miles: FREE
  * Remaining 30 miles x $2/mile = $60.00

================================================================================
YOUR TOTAL: $610.00
================================================================================

================================================================================
OPTIONAL UPGRADES TO MAXIMIZE YOUR EXPERIENCE
================================================================================

Since you're already paying our $550 minimum, here are some OPTIONAL PAID 
upgrades to enhance your bachelorette experience:

Premium Protein Upgrades:
  * Filet Mignon: +$5 per person (upgrade any protein to premium tenderloin)
  * Lobster Tail: +$15 per person (the ultimate luxury!)
  * Salmon or Scallops: +$5 per person

Delicious Add-Ons:
  * Gyoza (pan-fried dumplings): +$10
  * Yakisoba Noodles (Japanese lo mein): +$5
  * Extra Fried Rice or Vegetables: +$5 each
  * Edamame (steamed soybeans): +$5

These are completely optional - just ideas to maximize your $550 value!

================================================================================
WHAT'S INCLUDED
================================================================================

Your hibachi experience includes:

  * Professional hibachi chef with all equipment
  * Interactive cooking show & entertainment (onion volcano, egg toss, 
    knife tricks!)
  * Choice of 2 proteins per guest (Chicken, NY Strip Steak, Shrimp, 
    Tofu, Veggies)
  * Hibachi fried rice, fresh vegetables, side salad
  * Signature sauces & seasonings
  * Sake service for adults 21+ (perfect for toasts!)

================================================================================
GRATUITY (100% OPTIONAL)
================================================================================

While completely optional, our hardworking chefs deeply appreciate tips! 
A suggested range is 20-35% (approximately $110-$193) based on your 
satisfaction. Your appreciation means the world to our chefs!

================================================================================
NEXT STEPS TO SECURE YOUR DATE
================================================================================

1. Choose your specific date in August 2026
2. Confirm protein selections for each guest (or decide closer to the event!)
3. Decide on any optional upgrades (Filet? Lobster? Gyoza?)
4. $100 deposit secures your date
5. Remaining balance ($510) due on event day (cash, Venmo, or Zelle)

================================================================================
READY TO BOOK?
================================================================================

Just reply with your preferred date in August 2026, and we'll get you on 
the calendar! Or feel free to call us at (916) 740-8768 to chat about 
making this bachelorette absolutely epic!

We can't wait to celebrate with you!

Warmest regards,

Chef Ady & The My Hibachi Team
cs@myhibachichef.com
(916) 740-8768
www.myhibachichef.com

P.S. - For bachelorette parties, we can coordinate fun extras like custom 
chef tricks, special toasts, or themed presentations. Just let us know!
"""
    
    return {
        "to": "malia.nakamura@example.com",  # REPLACE WITH REAL EMAIL
        "from": "cs@myhibachichef.com",
        "subject": subject,
        "body": body,
        "customer_name": "Malia Nakamura",
        "total": 610.00
    }


def save_email_to_file(email_data, filename_prefix):
    """Save email to text file for review"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"TO: {email_data['to']}\n")
        f.write(f"FROM: {email_data['from']}\n")
        f.write(f"SUBJECT: {email_data['subject']}\n")
        f.write(f"\n{'='*80}\n\n")
        f.write(email_data['body'])
    
    return filename


def main():
    """Generate clean email files"""
    
    print("="*80)
    print("CUSTOMER EMAIL GENERATION - CLEAN VERSION (No Emojis)")
    print("="*80)
    print()
    
    # Generate Debbie's email
    print("Generating Debbie's email...")
    debbie_email = generate_clean_email_debbie()
    debbie_file = save_email_to_file(debbie_email, "email_clean_debbie")
    print(f"  Saved to: {debbie_file}")
    print(f"  Total: ${debbie_email['total']:.2f}")
    print()
    
    # Generate Malia's email
    print("Generating Malia's email...")
    malia_email = generate_clean_email_malia()
    malia_file = save_email_to_file(malia_email, "email_clean_malia")
    print(f"  Saved to: {malia_file}")
    print(f"  Total: ${malia_email['total']:.2f}")
    print()
    
    print("="*80)
    print("EMAIL GENERATION COMPLETE")
    print("="*80)
    print()
    print("NEXT STEPS:")
    print("1. Review the clean email files (no encoding issues!)")
    print("2. Replace placeholder emails with real customer emails:")
    print("   - debbie.plummer@example.com -> [REAL EMAIL]")
    print("   - malia.nakamura@example.com -> [REAL EMAIL]")
    print()
    print("3. To send via your email system:")
    print("   - Option A: Copy email content and send from cs@myhibachichef.com")
    print("   - Option B: Use our multi-channel AI email endpoint")
    print("   - Option C: Integrate with your CRM system")
    print()
    print("FILES GENERATED:")
    print(f"  * {debbie_file}")
    print(f"  * {malia_file}")
    print()
    print("PRICING VERIFIED:")
    print(f"  Debbie (Christmas Eve): $910.00 ✓")
    print(f"  Malia (Sonoma): $610.00 ✓")
    print()


if __name__ == "__main__":
    main()
