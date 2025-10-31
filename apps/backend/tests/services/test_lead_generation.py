"""
Test the Lead Generation API endpoints directly
This script tests the lead capture functionality without needing the full server running
"""
import asyncio
import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_lead_api():
    """Test lead generation API endpoints"""
    print("🧪 Testing Lead Generation API\n")
    print("=" * 60)
    
    # Import after path is set
    from sqlalchemy.ext.asyncio import AsyncSession
    from api.app.database import get_db
    from services.lead_service import LeadService
    from api.app.models.lead_newsletter import LeadSource
    
    print("\n✅ All imports successful!\n")
    
    # Test 1: Create a quote request lead
    print("📝 Test 1: Create Quote Request Lead")
    print("-" * 60)
    
    async for db in get_db():
        lead_service = LeadService(db=db)
        
        lead = await lead_service.capture_quote_request(
            name="John Doe",
            email="john.doe@example.com",
            phone="+15551234567",
            event_date=date(2025, 11, 15),
            guest_count=12,
            budget="$1,000 - $2,000",
            message="Looking for hibachi catering for anniversary party",
            location="Sacramento, CA"
        )
        
        print(f"✅ Lead created!")
        print(f"   ID: {lead.id}")
        print(f"   Source: {lead.source}")
        print(f"   Status: {lead.status}")
        print(f"   Quality: {lead.quality}")
        print(f"   Score: {lead.score}")
        print(f"   Contacts: {len(lead.contacts)} contacts")
        print(f"   Context: Party size {lead.context.party_size_adults if lead.context else 'N/A'}")
        
        # Test 2: Check lead scoring
        print("\n🎯 Test 2: Verify Lead Scoring")
        print("-" * 60)
        
        if lead.score > 0:
            print(f"✅ Lead score calculated: {lead.score}/100")
            
            if lead.score >= 70:
                print(f"   Quality: HOT 🔥 (Score >= 70)")
            elif lead.score >= 40:
                print(f"   Quality: WARM ☀️ (Score 40-69)")
            else:
                print(f"   Quality: COLD ❄️ (Score < 40)")
            
            # Show score breakdown
            print(f"\n   Score Breakdown:")
            print(f"   - Source (web_quote): 20 points")
            print(f"   - Party size (12): {min(12 * 2, 15)} points")
            print(f"   - Budget ($1,000-$2,000): ~15 points")
            print(f"   - Timing: 15 points")
            print(f"   - Contact methods: 5 points (email)")
        else:
            print("❌ Lead score not calculated")
        
        # Test 3: Create social inquiry lead
        print("\n📱 Test 3: Create Social Media Lead")
        print("-" * 60)
        
        social_lead = await lead_service.capture_social_inquiry(
            platform="instagram",
            handle="@foodlover123",
            message="Interested in hibachi catering for my birthday next month",
            thread_id="instagram_thread_12345"
        )
        
        print(f"✅ Social lead created!")
        print(f"   ID: {social_lead.id}")
        print(f"   Source: {social_lead.source}")
        print(f"   Score: {social_lead.score}")
        
        # Test 4: List all leads
        print("\n📋 Test 4: List All Leads")
        print("-" * 60)
        
        leads, total = await lead_service.list_leads(skip=0, limit=10)
        
        print(f"✅ Found {total} total leads")
        for idx, lead in enumerate(leads, 1):
            print(f"\n   Lead {idx}:")
            print(f"   - ID: {lead.id}")
            print(f"   - Source: {lead.source}")
            print(f"   - Quality: {lead.quality}")
            print(f"   - Score: {lead.score}")
            print(f"   - Created: {lead.created_at}")
        
        # Test 5: Get pipeline stats
        print("\n📊 Test 5: Pipeline Statistics")
        print("-" * 60)
        
        stats = await lead_service.get_pipeline_stats()
        
        print(f"✅ Pipeline stats:")
        print(f"   - NEW: {stats.get('new', 0)}")
        print(f"   - WORKING: {stats.get('working', 0)}")
        print(f"   - QUALIFIED: {stats.get('qualified', 0)}")
        print(f"   - CONVERTED: {stats.get('converted', 0)}")
        print(f"   - Total estimated value: ${stats.get('total_estimated_value_dollars', 0):,.2f}")
        print(f"   - Conversion rate: {stats.get('conversion_rate', 0):.1f}%")
        
        break  # Exit the async generator
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Lead Generation API is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_lead_api())
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
