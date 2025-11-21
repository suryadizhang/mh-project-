#!/usr/bin/env python3
"""
AI Booking Assistant - Test Helper Script
Provides utilities for testing the SMS AI booking flow
"""

import os
import sys

# Add backend to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "apps", "backend", "src")
)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/mh_webapp_dev",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def check_database_setup():
    """Check if database tables exist"""
    print_header("DATABASE SETUP CHECK")

    with SessionLocal() as session:
        # Check customers table
        result = session.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers'"
            )
        )
        customers_exists = result.scalar() > 0
        print(
            f"✅ customers table: {'EXISTS' if customers_exists else '❌ MISSING'}"
        )

        # Check bookings table
        result = session.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bookings'"
            )
        )
        bookings_exists = result.scalar() > 0
        print(
            f"✅ bookings table: {'EXISTS' if bookings_exists else '❌ MISSING'}"
        )

        # Check terms_acknowledgments table
        result = session.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'terms_acknowledgments'"
            )
        )
        terms_exists = result.scalar() > 0
        print(
            f"✅ terms_acknowledgments table: {'EXISTS' if terms_exists else '❌ MISSING'}"
        )

        if customers_exists and bookings_exists and terms_exists:
            print("\n✅ ALL TABLES EXIST - Database ready for testing")
            return True
        else:
            print("\n❌ MISSING TABLES - Run migrations first")
            return False


def check_environment_variables():
    """Check if required environment variables are set"""
    print_header("ENVIRONMENT VARIABLES CHECK")

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "RINGCENTRAL_CLIENT_ID": "RingCentral SMS",
        "RINGCENTRAL_CLIENT_SECRET": "RingCentral SMS",
        "RINGCENTRAL_JWT_TOKEN": "RingCentral SMS",
        "RINGCENTRAL_PHONE_NUMBER": "SMS sender number",
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked} ({description})")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            all_set = False

    if all_set:
        print("\n✅ ALL ENVIRONMENT VARIABLES SET")
        return True
    else:
        print("\n❌ MISSING ENVIRONMENT VARIABLES - Check .env file")
        return False


def get_recent_customers(limit: int = 5):
    """Get recently created customers"""
    print_header(f"RECENT CUSTOMERS (Last {limit})")

    with SessionLocal() as session:
        result = session.execute(
            text(
                """
            SELECT id, first_name, last_name, phone, email, created_at
            FROM public.customers
            ORDER BY created_at DESC
            LIMIT :limit
        """
            ),
            {"limit": limit},
        )

        customers = result.fetchall()

        if not customers:
            print("No customers found in database")
            return

        print(f"{'ID':<6} {'Name':<30} {'Phone':<15} {'Created':<20}")
        print("-" * 80)

        for cust in customers:
            customer_id, first, last, phone, email, created = cust
            name = f"{first} {last}"
            created_str = (
                created.strftime("%Y-%m-%d %H:%M:%S") if created else "N/A"
            )
            print(
                f"{customer_id:<6} {name:<30} {phone or 'N/A':<15} {created_str:<20}"
            )


def get_recent_bookings(limit: int = 5):
    """Get recently created bookings"""
    print_header(f"RECENT BOOKINGS (Last {limit})")

    with SessionLocal() as session:
        result = session.execute(
            text(
                """
            SELECT b.id, b.customer_id, b.event_date, b.guest_count, b.status, b.created_at,
                   c.first_name, c.last_name
            FROM public.bookings b
            LEFT JOIN public.customers c ON b.customer_id = c.id
            ORDER BY b.created_at DESC
            LIMIT :limit
        """
            ),
            {"limit": limit},
        )

        bookings = result.fetchall()

        if not bookings:
            print("No bookings found in database")
            return

        print(
            f"{'ID':<6} {'Customer':<25} {'Date':<12} {'Guests':<8} {'Status':<12} {'Created':<20}"
        )
        print("-" * 100)

        for booking in bookings:
            (
                booking_id,
                cust_id,
                event_date,
                guests,
                status,
                created,
                first,
                last,
            ) = booking
            customer_name = (
                f"{first} {last}" if first and last else f"ID:{cust_id}"
            )
            event_str = (
                event_date.strftime("%Y-%m-%d") if event_date else "N/A"
            )
            created_str = (
                created.strftime("%Y-%m-%d %H:%M:%S") if created else "N/A"
            )
            print(
                f"{booking_id:<6} {customer_name:<25} {event_str:<12} {guests or 0:<8} {status or 'N/A':<12} {created_str:<20}"
            )


def get_recent_terms_acknowledgments(limit: int = 5):
    """Get recent terms acknowledgments"""
    print_header(f"RECENT TERMS ACKNOWLEDGMENTS (Last {limit})")

    with SessionLocal() as session:
        result = session.execute(
            text(
                """
            SELECT id, customer_id, booking_id, acknowledged, acknowledged_at, created_at
            FROM public.terms_acknowledgments
            ORDER BY created_at DESC
            LIMIT :limit
        """
            ),
            {"limit": limit},
        )

        terms = result.fetchall()

        if not terms:
            print("No terms acknowledgments found in database")
            return

        print(
            f"{'ID':<6} {'Cust ID':<10} {'Book ID':<10} {'Ack?':<8} {'Ack Time':<20} {'Created':<20}"
        )
        print("-" * 90)

        for term in terms:
            term_id, cust_id, book_id, acked, ack_time, created = term
            ack_str = "✅ YES" if acked else "⏳ NO"
            ack_time_str = (
                ack_time.strftime("%Y-%m-%d %H:%M:%S") if ack_time else "N/A"
            )
            created_str = (
                created.strftime("%Y-%m-%d %H:%M:%S") if created else "N/A"
            )
            print(
                f"{term_id:<6} {cust_id or 'N/A':<10} {book_id or 'N/A':<10} {ack_str:<8} {ack_time_str:<20} {created_str:<20}"
            )


def search_customer_by_phone(phone: str):
    """Search for customer by phone number"""
    print_header(f"SEARCH CUSTOMER BY PHONE: {phone}")

    # Normalize phone (remove non-digits)
    phone_digits = "".join(filter(str.isdigit, phone))

    with SessionLocal() as session:
        result = session.execute(
            text(
                """
            SELECT id, first_name, last_name, phone, email, status, created_at, updated_at
            FROM public.customers
            WHERE regexp_replace(phone, '[^0-9]', '', 'g') = :phone_digits
        """
            ),
            {"phone_digits": phone_digits},
        )

        customer = result.fetchone()

        if customer:
            cust_id, first, last, phone, email, status, created, updated = (
                customer
            )
            print("✅ CUSTOMER FOUND")
            print(f"  ID: {cust_id}")
            print(f"  Name: {first} {last}")
            print(f"  Phone: {phone}")
            print(f"  Email: {email}")
            print(f"  Status: {status}")
            print(f"  Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Updated: {updated.strftime('%Y-%m-%d %H:%M:%S')}")

            # Get their bookings
            result = session.execute(
                text(
                    """
                SELECT id, event_date, guest_count, status
                FROM public.bookings
                WHERE customer_id = :cust_id
                ORDER BY created_at DESC
            """
                ),
                {"cust_id": cust_id},
            )

            bookings = result.fetchall()
            if bookings:
                print(f"\n  📅 BOOKINGS ({len(bookings)}):")
                for booking in bookings:
                    b_id, event_date, guests, b_status = booking
                    event_str = (
                        event_date.strftime("%Y-%m-%d")
                        if event_date
                        else "N/A"
                    )
                    print(
                        f"    - #{b_id}: {event_str}, {guests} guests, {b_status}"
                    )
            else:
                print("\n  No bookings found")
        else:
            print(f"❌ NO CUSTOMER FOUND with phone: {phone}")


def test_ai_import():
    """Test if AI service can be imported"""
    print_header("AI SERVICE IMPORT TEST")

    try:
        from services.ai_booking_assistant_service import (
            AIBookingAssistant,
            BookingIntent,
            BookingStage,
        )

        print("✅ Successfully imported AIBookingAssistant")
        print(
            f"✅ BookingIntent enum: {', '.join([intent.value for intent in BookingIntent])}"
        )
        print(
            f"✅ BookingStage enum: {', '.join([stage.value for stage in BookingStage])}"
        )
        return True
    except ImportError as e:
        print(f"❌ Failed to import AI service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing AI service: {e}")
        return False


def run_all_checks():
    """Run all pre-test checks"""
    print("\n")
    print("🧪" * 40)
    print("  AI BOOKING ASSISTANT - PRE-TEST CHECKS")
    print("🧪" * 40)

    checks_passed = []

    # Check 1: Database setup
    checks_passed.append(check_database_setup())

    # Check 2: Environment variables
    checks_passed.append(check_environment_variables())

    # Check 3: AI service import
    checks_passed.append(test_ai_import())

    # Show recent data
    get_recent_customers(5)
    get_recent_bookings(5)
    get_recent_terms_acknowledgments(5)

    # Final assessment
    print_header("FINAL ASSESSMENT")

    if all(checks_passed):
        print("✅ ✅ ✅ ALL CHECKS PASSED ✅ ✅ ✅")
        print("\n🚀 READY TO TEST!")
        print(
            "\nNext step: Send SMS to +19167408768 with: 'How much for 20 people?'"
        )
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print("\n⚠️  FIX ISSUES BEFORE TESTING")
        return False


def interactive_menu():
    """Interactive testing menu"""
    while True:
        print("\n" + "=" * 80)
        print("  AI BOOKING ASSISTANT - TEST HELPER")
        print("=" * 80)
        print("\n1. Run all pre-test checks")
        print("2. View recent customers")
        print("3. View recent bookings")
        print("4. View recent terms acknowledgments")
        print("5. Search customer by phone")
        print("6. Test AI service import")
        print("7. Check environment variables")
        print("8. Check database setup")
        print("9. Exit")

        choice = input("\nEnter choice (1-9): ").strip()

        if choice == "1":
            run_all_checks()
        elif choice == "2":
            limit = input("How many customers? (default 5): ").strip() or "5"
            get_recent_customers(int(limit))
        elif choice == "3":
            limit = input("How many bookings? (default 5): ").strip() or "5"
            get_recent_bookings(int(limit))
        elif choice == "4":
            limit = input("How many terms? (default 5): ").strip() or "5"
            get_recent_terms_acknowledgments(int(limit))
        elif choice == "5":
            phone = input("Enter phone number: ").strip()
            if phone:
                search_customer_by_phone(phone)
        elif choice == "6":
            test_ai_import()
        elif choice == "7":
            check_environment_variables()
        elif choice == "8":
            check_database_setup()
        elif choice == "9":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-9.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command-line mode
        command = sys.argv[1].lower()

        if command == "check":
            run_all_checks()
        elif command == "customers":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            get_recent_customers(limit)
        elif command == "bookings":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            get_recent_bookings(limit)
        elif command == "terms":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            get_recent_terms_acknowledgments(limit)
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: python test_ai_booking.py search <phone_number>")
            else:
                search_customer_by_phone(sys.argv[2])
        else:
            print(
                "Unknown command. Available: check, customers, bookings, terms, search"
            )
    else:
        # Interactive mode
        interactive_menu()
