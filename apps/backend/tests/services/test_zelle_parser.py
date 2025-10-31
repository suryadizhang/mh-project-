"""
Test if the Zelle email parser can extract the payment details correctly
"""
import sys
sys.path.insert(0, 'src')

from services.payment_email_monitor import PaymentEmailParser

# The actual subject and note from the email
subject = "Suryadi Zhang sent you $1.00"
note_text = "2103884155 ady"  # This was in the email body

print("=" * 60)
print("Testing Zelle Email Parser")
print("=" * 60)

print(f"\nSubject: {subject}")
print(f"Note/Body: {note_text}\n")

# Test the parser - use the specific Zelle parser
parsed = PaymentEmailParser.parse_zelle_email(subject, note_text)

if parsed:
    print("✅ Successfully parsed Zelle email!")
    print("-" * 60)
    print(f"Provider: {parsed.get('provider')}")
    print(f"Amount: ${parsed.get('amount', 0):.2f}")
    print(f"Sender Name: {parsed.get('sender_name')}")
    print(f"Customer Phone: {parsed.get('customer_phone')}")
    print(f"Transaction ID: {parsed.get('transaction_id', 'N/A')}")
    print("-" * 60)
    
    if parsed.get('customer_phone') == '2103884155':
        print("\n🎯 ✅ PHONE NUMBER EXTRACTED CORRECTLY!")
        print("This payment can now be matched by phone number!")
    else:
        print(f"\n⚠️  Phone extracted: {parsed.get('customer_phone')}")
        print(f"Expected: 2103884155")
else:
    print("❌ Failed to parse email")
    print("\nThis means the email patterns need to be updated")
    print("to recognize Bank of America Zelle emails correctly.")

print("\n" + "=" * 60)
