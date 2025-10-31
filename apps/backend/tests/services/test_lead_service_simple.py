"""
Direct test of LeadService without API
"""
import asyncio
import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

from datetime import date
from api.app.database import get_db_context
from api.app.services.lead_service import LeadService

async def test_lead_creation():
    print("🧪 Testing LeadService directly...")
    
    try:
        async with get_db_context() as db:
            # Create service
            lead_service = LeadService(db=db)
            print("✅ LeadService created")
            
            # Test capture_quote_request
            lead = await lead_service.capture_quote_request(
                name="Test User",
                phone="5551234567",  # Required
                email="test@example.com",  # Optional
                event_date=date(2025, 11, 15),
                guest_count=25,
                budget="$1000-2000",
                message="Test quote request",
                location="90210"
            )
            
            # Refresh with all relationships before accessing
            await db.refresh(lead, ['contacts', 'context'])
            
            print(f"✅ Lead created successfully!")
            print(f"   Lead ID: {lead.id}")
            print(f"   Source: {lead.source}")
            print(f"   Status: {lead.status}")
            print(f"   Quality: {lead.quality}")
            print(f"   Score: {lead.score}")
            if lead.contacts:
                print(f"   Contacts: {len(lead.contacts)} contact(s)")
                for contact in lead.contacts:
                    print(f"     - {contact.channel}: {contact.handle_or_address}")
            if lead.context:
                print(f"   Party Size: {lead.context.party_size_adults} adults")
                print(f"   Event Date: {lead.context.event_date_pref}")
                print(f"   Budget: ${lead.context.estimated_budget_cents / 100:.2f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lead_creation())
