"""
Seed Mock Data for Testing
Creates realistic test data for all tables
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import get_settings

# Import all models
from models import (
    Customer, CustomerStatus,
    Booking, BookingStatus,
    Lead,
    Campaign,
    SocialAccount, SocialIdentity, SocialThread, SocialMessage,
    Review,
    BusinessRule, FAQItem, MenuItem,
)
from models.enums import SocialPlatform, ThreadStatus, ReviewSource

settings = get_settings()


async def seed_database():
    """Seed comprehensive mock data"""
    print("=" * 80)
    print("🌱 SEEDING MOCK DATA FOR TESTING")
    print("=" * 80)
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        
        # ====================================================================
        # 1. CUSTOMERS (10 customers)
        # ====================================================================
        print("\n📋 Creating customers...")
        customers = []
        customer_data = [
            ("John", "Doe", "+19165551001", "john.doe@gmail.com"),
            ("Jane", "Smith", "+19165551002", "jane.smith@yahoo.com"),
            ("Mike", "Johnson", "+19165551003", "mike.j@outlook.com"),
            ("Sarah", "Williams", "+19165551004", "sarah.w@gmail.com"),
            ("David", "Brown", "+19165551005", "david.brown@email.com"),
            ("Emily", "Davis", "+19165551006", "emily.d@gmail.com"),
            ("Chris", "Miller", "+19165551007", "chris.m@yahoo.com"),
            ("Amanda", "Wilson", "+19165551008", "amanda.w@gmail.com"),
            ("Robert", "Moore", "+19165551009", "robert.m@email.com"),
            ("Lisa", "Taylor", "+19165551010", "lisa.t@gmail.com"),
        ]
        
        for first, last, phone, email in customer_data:
            customer = Customer(
                id=uuid4(),
                name=f"{first} {last}",
                phone=phone,
                email=email,
                status=CustomerStatus.ACTIVE,
                total_bookings=0,
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            )
            session.add(customer)
            customers.append(customer)
            print(f"  ✓ Customer: {customer.name} ({phone})")
        
        await session.flush()
        
        # ====================================================================
        # 2. BOOKINGS (15 bookings - past, current, future)
        # ====================================================================
        print("\n📋 Creating bookings...")
        for i in range(15):
            customer = customers[i % len(customers)]
            event_date = datetime.now(timezone.utc) + timedelta(days=i-5)  # Some past, some future
            
            booking = Booking(
                id=uuid4(),
                customer_id=customer.id,
                event_date=event_date.date(),
                event_time=f"{12 + (i % 8)}:00:00",
                guests=10 + (i % 20),
                status=BookingStatus.CONFIRMED if i % 3 == 0 else BookingStatus.PENDING,
                total_amount=Decimal(str(500 + (i * 50))),
                deposit_amount=Decimal(str(100 + (i * 10))),
                created_at=datetime.now(timezone.utc) - timedelta(days=20-i)
            )
            session.add(booking)
            print(f"  ✓ Booking: {customer.name} - {event_date.date()} - ${booking.total_amount}")
        
        await session.flush()
        
        # ====================================================================
        # 3. LEADS (20 leads - various sources)
        # ====================================================================
        print("\n📋 Creating leads...")
        sources = ["website", "instagram", "facebook", "referral", "google"]
        for i in range(20):
            lead = Lead(
                id=uuid4(),
                phone=f"+1916555{2000+i:04d}",
                name=f"Lead {i+1}",
                email=f"lead{i+1}@example.com" if i % 2 == 0 else None,
                source=sources[i % len(sources)],
                message=f"Interested in booking for {10+i} guests",
                created_at=datetime.now(timezone.utc) - timedelta(days=15-i)
            )
            session.add(lead)
            if i % 5 == 0:
                print(f"  ✓ Lead: {lead.name} from {lead.source}")
        
        print(f"  ✓ Created {20} leads")
        await session.flush()
        
        # ====================================================================
        # 4. SOCIAL ACCOUNTS (3 business accounts)
        # ====================================================================
        print("\n📋 Creating social accounts...")
        social_accounts = []
        
        # Instagram account
        instagram = SocialAccount(
            id=uuid4(),
            platform=SocialPlatform.INSTAGRAM,
            page_id="myhibachichef_ig",
            page_name="My Hibachi Chef",
            handle="myhibachichef",
            profile_url="https://instagram.com/myhibachichef",
            connected_by=uuid4(),  # Dummy user ID
            connected_at=datetime.now(timezone.utc) - timedelta(days=90),
            is_active=True,
            webhook_verified=True
        )
        session.add(instagram)
        social_accounts.append(instagram)
        print(f"  ✓ Instagram: @{instagram.handle}")
        
        # Facebook account
        facebook = SocialAccount(
            id=uuid4(),
            platform=SocialPlatform.FACEBOOK,
            page_id="myhibachichef_fb",
            page_name="My Hibachi Chef",
            profile_url="https://facebook.com/myhibachichef",
            connected_by=uuid4(),
            connected_at=datetime.now(timezone.utc) - timedelta(days=90),
            is_active=True,
            webhook_verified=True
        )
        session.add(facebook)
        social_accounts.append(facebook)
        print(f"  ✓ Facebook: {facebook.page_name}")
        
        # Google account
        google = SocialAccount(
            id=uuid4(),
            platform=SocialPlatform.GOOGLE,
            page_id="myhibachichef_google",
            page_name="My Hibachi Chef - Sacramento",
            profile_url="https://g.page/myhibachichef",
            connected_by=uuid4(),
            connected_at=datetime.now(timezone.utc) - timedelta(days=60),
            is_active=True,
            webhook_verified=False
        )
        session.add(google)
        social_accounts.append(google)
        print(f"  ✓ Google: {google.page_name}")
        
        await session.flush()
        
        # ====================================================================
        # 5. SOCIAL IDENTITIES (customer social handles)
        # ====================================================================
        print("\n📋 Creating social identities...")
        for i, customer in enumerate(customers[:5]):  # First 5 customers
            identity = SocialIdentity(
                id=uuid4(),
                platform=SocialPlatform.INSTAGRAM if i % 2 == 0 else SocialPlatform.FACEBOOK,
                handle=f"{customer.name.lower().replace(' ', '')}{i}",
                display_name=customer.name,
                customer_id=customer.id,
                confidence_score=0.95,
                verification_status="verified",
                first_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
                last_active_at=datetime.now(timezone.utc) - timedelta(days=i)
            )
            session.add(identity)
            print(f"  ✓ Identity: @{identity.handle} → {customer.name}")
        
        await session.flush()
        
        # ====================================================================
        # 6. SOCIAL THREADS & MESSAGES (10 conversations)
        # ====================================================================
        print("\n📋 Creating social threads and messages...")
        for i in range(10):
            customer = customers[i % len(customers)]
            account = social_accounts[i % len(social_accounts)]
            
            thread = SocialThread(
                id=uuid4(),
                platform=account.platform,
                account_id=account.id,
                thread_ref=f"thread_{account.platform.value}_{i}",
                customer_id=customer.id if i % 2 == 0 else None,  # 50% linked to customers
                status=ThreadStatus.OPEN if i % 3 == 0 else ThreadStatus.CLOSED,
                subject=f"Inquiry about catering - {i+1}",
                message_count=2 + (i % 3),
                last_message_at=datetime.now(timezone.utc) - timedelta(hours=i),
                created_at=datetime.now(timezone.utc) - timedelta(days=i)
            )
            session.add(thread)
            
            # Add 2-4 messages per thread
            for j in range(2 + (i % 3)):
                message = SocialMessage(
                    id=uuid4(),
                    thread_id=thread.id,
                    platform_message_id=f"msg_{i}_{j}",
                    author_name=customer.name if j % 2 == 0 else "My Hibachi Chef",
                    content=f"Sample message {j+1} in thread {i+1}",
                    sent_at=datetime.now(timezone.utc) - timedelta(days=i, hours=j),
                    direction="in" if j % 2 == 0 else "out",
                    kind="dm"
                )
                session.add(message)
            
            if i % 3 == 0:
                print(f"  ✓ Thread: {account.platform.value} - {thread.subject}")
        
        print(f"  ✓ Created 10 threads with ~30 messages")
        await session.flush()
        
        # ====================================================================
        # 7. REVIEWS (15 reviews across platforms)
        # ====================================================================
        print("\n📋 Creating reviews...")
        review_texts = [
            "Amazing service! The chef was fantastic and the food was delicious!",
            "Great experience for our party. Highly recommend!",
            "Food was okay but service could be better",
            "Best hibachi catering in Sacramento!",
            "Kids loved it! Will book again",
        ]
        
        for i in range(15):
            customer = customers[i % len(customers)]
            account = social_accounts[i % len(social_accounts)]
            
            review = Review(
                id=uuid4(),
                customer_id=customer.id if i % 3 == 0 else None,
                account_id=account.id,
                source=account.platform.value,
                rating=3 + (i % 3),  # Ratings 3-5
                content=review_texts[i % len(review_texts)],
                author_name=customer.name,
                status="new" if i % 4 == 0 else "responded",
                created_at=datetime.now(timezone.utc) - timedelta(days=20-i)
            )
            session.add(review)
            if i % 5 == 0:
                print(f"  ✓ Review: {review.rating}⭐ on {account.platform.value}")
        
        print(f"  ✓ Created 15 reviews")
        await session.flush()
        
        # ====================================================================
        # 8. KNOWLEDGE BASE (FAQ, Business Rules, Menu Items)
        # ====================================================================
        print("\n📋 Creating knowledge base...")
        
        # FAQs
        faqs = [
            ("What is your service area?", "We serve Sacramento and surrounding areas within 50 miles"),
            ("How many guests minimum?", "Minimum 10 guests for catering service"),
            ("Do you provide tables and chairs?", "Tables and chairs rental available for $5/person"),
            ("What's included in the price?", "Chef, ingredients, cooking equipment, and cleanup"),
            ("How far in advance should I book?", "We recommend booking 2-4 weeks in advance"),
        ]
        for question, answer in faqs:
            faq = FAQItem(
                id=uuid4(),
                question=question,
                answer=answer,
                category="general",
                is_active=True
            )
            session.add(faq)
        print(f"  ✓ Created {len(faqs)} FAQ items")
        
        # Business Rules
        rules = [
            ("Minimum guests required", "10 guests minimum for all bookings"),
            ("Deposit required", "25% deposit required to confirm booking"),
            ("Cancellation policy", "Full refund if cancelled 7+ days before event"),
            ("Travel fee calculation", "Base rate $50, plus $1 per mile over 20 miles"),
        ]
        for title, description in rules:
            rule = BusinessRule(
                id=uuid4(),
                title=title,
                description=description,
                category="booking",
                is_active=True
            )
            session.add(rule)
        print(f"  ✓ Created {len(rules)} business rules")
        
        # Menu Items
        menu_items = [
            ("Hibachi Chicken", "Grilled chicken with vegetables and fried rice", Decimal("25.00")),
            ("Hibachi Steak", "Premium steak with vegetables and fried rice", Decimal("35.00")),
            ("Hibachi Shrimp", "Jumbo shrimp with vegetables and fried rice", Decimal("30.00")),
            ("Vegetarian Hibachi", "Assorted vegetables with tofu and fried rice", Decimal("22.00")),
            ("Kids Hibachi", "Smaller portions perfect for children", Decimal("18.00")),
        ]
        for name, description, price in menu_items:
            item = MenuItem(
                id=uuid4(),
                name=name,
                description=description,
                base_price=price,
                category="entree",
                is_available=True
            )
            session.add(item)
        print(f"  ✓ Created {len(menu_items)} menu items")
        
        await session.flush()
        
        # ====================================================================
        # COMMIT ALL CHANGES
        # ====================================================================
        print("\n📋 Committing all changes...")
        await session.commit()
        
        print("\n" + "=" * 80)
        print("✅ MOCK DATA SEEDED SUCCESSFULLY")
        print("=" * 80)
        print("\n📊 Summary:")
        print(f"  • Customers: {len(customers)}")
        print(f"  • Bookings: 15")
        print(f"  • Leads: 20")
        print(f"  • Social Accounts: {len(social_accounts)}")
        print(f"  • Social Identities: 5")
        print(f"  • Social Threads: 10 (with ~30 messages)")
        print(f"  • Reviews: 15")
        print(f"  • FAQs: {len(faqs)}")
        print(f"  • Business Rules: {len(rules)}")
        print(f"  • Menu Items: {len(menu_items)}")
        print("=" * 80)
    
    await engine.dispose()


if __name__ == "__main__":
    print("\n⏳ Starting database seeding...")
    asyncio.run(seed_database())
