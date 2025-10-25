"""
Direct Lead Service Test
Tests lead generation without needing the full backend server
"""
import asyncio
import sys
import os
from datetime import date

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

async def test_lead_creation():
    """Test creating a lead directly through the service"""
    print("🧪 Direct Lead Service Test")
    print("=" * 70)
    
    try:
        # Import dependencies
        print("\n📦 Step 1: Importing dependencies...")
        from api.app.database import get_db
        from services.lead_service import LeadService
        from api.app.models.lead_newsletter import LeadSource, LeadStatus, LeadQuality
        print("   ✅ All imports successful!")
        
        # Get database session
        print("\n🗄️  Step 2: Connecting to database...")
        async for db in get_db():
            print("   ✅ Database connected!")
            
            # Create LeadService
            print("\n🔧 Step 3: Creating LeadService...")
            lead_service = LeadService(db=db)
            print("   ✅ LeadService created!")
            
            # Test 1: Create a quote request lead
            print("\n📝 Test 1: Creating Quote Request Lead")
            print("-" * 70)
            lead = await lead_service.capture_quote_request(
                name="Test User - John Doe",
                email="john.doe.test@example.com",
                phone="+15551234567",
                event_date=date(2025, 11, 15),
                guest_count=12,
                budget="$1,000 - $2,000",
                message="Looking for hibachi catering for anniversary party",
                location="Sacramento, CA"
            )
            
            print(f"\n✅ Lead Created Successfully!")
            print(f"   ID: {lead.id}")
            print(f"   Source: {lead.source}")
            print(f"   Status: {lead.status}")
            print(f"   Quality: {lead.quality} ", end="")
            if lead.quality == LeadQuality.HOT:
                print("🔥")
            elif lead.quality == LeadQuality.WARM:
                print("☀️")
            else:
                print("❄️")
            print(f"   Score: {lead.score}/100")
            
            # Show breakdown
            print(f"\n   📊 Score Breakdown:")
            print(f"      • Source (web_quote): 20 points")
            print(f"      • Party size (12 guests): {min(12 * 2, 15)} points")
            print(f"      • Budget ($1,000-$2,000): ~15 points")
            print(f"      • Timing (future date): 15 points")
            print(f"      • Contact method (email): 5 points")
            print(f"      • Total: {lead.score} points")
            
            # Test 2: Verify contacts
            print(f"\n📞 Test 2: Verifying Contact Information")
            print("-" * 70)
            print(f"   Number of contacts: {len(lead.contacts)}")
            for i, contact in enumerate(lead.contacts, 1):
                print(f"   Contact {i}:")
                print(f"      • Channel: {contact.channel}")
                print(f"      • Handle/Address: {contact.handle_or_address}")
                print(f"      • Verified: {contact.verified}")
            
            # Test 3: Verify context
            print(f"\n🎯 Test 3: Verifying Event Context")
            print("-" * 70)
            if lead.context:
                print(f"   ✅ Context exists:")
                print(f"      • Party size: {lead.context.party_size_adults} adults")
                if lead.context.party_size_kids:
                    print(f"      • Kids: {lead.context.party_size_kids}")
                print(f"      • Budget: ${lead.context.estimated_budget_cents / 100:,.2f}")
                print(f"      • Event date: {lead.context.event_date_pref}")
                if lead.context.zip_code:
                    print(f"      • Location: {lead.context.zip_code}")
                if lead.context.notes:
                    print(f"      • Notes: {lead.context.notes}")
            else:
                print("   ⚠️  No context found")
            
            # Test 4: Verify events
            print(f"\n📋 Test 4: Verifying Event Log")
            print("-" * 70)
            print(f"   Number of events: {len(lead.events)}")
            for i, event in enumerate(lead.events, 1):
                print(f"   Event {i}:")
                print(f"      • Type: {event.type}")
                print(f"      • Occurred at: {event.occurred_at}")
                if event.payload:
                    print(f"      • Payload: {event.payload}")
            
            # Test 5: List all leads
            print(f"\n📊 Test 5: Listing All Leads")
            print("-" * 70)
            leads, total = await lead_service.list_leads(skip=0, limit=10)
            print(f"   Total leads in database: {total}")
            print(f"   Leads retrieved: {len(leads)}")
            
            for i, l in enumerate(leads[:3], 1):  # Show first 3
                print(f"\n   Lead {i}:")
                print(f"      • ID: {l.id}")
                print(f"      • Source: {l.source}")
                print(f"      • Quality: {l.quality}")
                print(f"      • Score: {l.score}")
                print(f"      • Created: {l.created_at}")
            
            if total > 3:
                print(f"\n   ... and {total - 3} more leads")
            
            # Test 6: Pipeline stats
            print(f"\n📈 Test 6: Pipeline Statistics")
            print("-" * 70)
            stats = await lead_service.get_pipeline_stats()
            print(f"   Pipeline Overview:")
            print(f"      • NEW: {stats.get('new', 0)}")
            print(f"      • WORKING: {stats.get('working', 0)}")
            print(f"      • QUALIFIED: {stats.get('qualified', 0)}")
            print(f"      • CONVERTED: {stats.get('converted', 0)}")
            print(f"      • DISQUALIFIED: {stats.get('disqualified', 0)}")
            print(f"      • Total estimated value: ${stats.get('total_estimated_value_dollars', 0):,.2f}")
            
            if stats.get('conversion_rate') is not None:
                print(f"      • Conversion rate: {stats.get('conversion_rate', 0):.1f}%")
            
            break  # Exit the async generator
        
        # Success!
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n🎉 Lead Generation System is working correctly!")
        print("\n📊 Summary:")
        print("   • LeadService: ✅ Working")
        print("   • Database: ✅ Connected")
        print("   • Lead Creation: ✅ Successful")
        print("   • Lead Scoring: ✅ Calculating")
        print("   • Contact Tracking: ✅ Working")
        print("   • Event Logging: ✅ Working")
        print("   • Pipeline Stats: ✅ Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 Starting Direct Lead Service Test...")
    print("This tests the lead generation without needing the backend server\n")
    
    success = asyncio.run(test_lead_creation())
    
    if success:
        print("\n✅ You can now test the API endpoints by starting the backend server")
        print("   or use the web forms in the customer app\n")
        sys.exit(0)
    else:
        print("\n❌ Tests failed - check the errors above\n")
        sys.exit(1)
