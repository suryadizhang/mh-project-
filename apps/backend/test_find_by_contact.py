import sys
sys.path.insert(0, "src")

import asyncio
from services.newsletter_service import SubscriberService
from models.legacy_lead_newsletter import LeadSource
from core.database import get_db_session

async def test():
    async for session in get_db_session():
        svc = SubscriberService(session)
        
        # Create subscriber
        subscriber = await svc.subscribe(phone="+15551234567", source=LeadSource.WEB_QUOTE)
        print(f"Created subscriber: {subscriber.id}")
        print(f"Subscriber phone (decrypted): {subscriber.phone}")
        print(f"Subscriber phone_enc (encrypted): {subscriber.phone_enc[:50] if subscriber.phone_enc else None}...")
        
        # Clear session cache
        session.expire_all()
        
        # Try to find
        found = await svc.find_by_contact(phone="+15551234567")
        print(f"\nFound by phone: {found}")
        if found:
            print(f"Found phone (decrypted): {found.phone}")
        else:
            print("NOT FOUND - Let's check all subscribers:")
            from sqlalchemy import select
            from models.legacy_lead_newsletter import Subscriber
            result = await session.execute(select(Subscriber))
            all_subs = list(result.scalars().all())
            print(f"Total subscribers: {len(all_subs)}")
            for sub in all_subs:
                print(f"  - ID: {sub.id}, phone_enc exists: {sub.phone_enc is not None}, phone decrypted: {sub.phone}")
        
        break

asyncio.run(test())
