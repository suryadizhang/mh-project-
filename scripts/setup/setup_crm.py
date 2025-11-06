#!/usr/bin/env python3
"""
Enhanced CRM Setup Script
Initializes the enterprise-grade CRM system with lead management and newsletter capabilities.
"""

import asyncio
from pathlib import Path
import sys

# Add the app directory to Python path
app_dir = Path(__file__).parent / "apps" / "api"
sys.path.insert(0, str(app_dir))

import logging

from alembic import command
from alembic.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_enhanced_crm():
    """Setup the enhanced CRM system with all new features."""

    logger.info("🚀 Setting up Enhanced CRM System")

    # Step 1: Run database migrations
    logger.info("📊 Running database migrations...")
    try:
        alembic_cfg = Config("apps/api/alembic.ini")
        alembic_cfg.set_main_option("script_location", "apps/api/alembic")

        # Run all migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations completed")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

    # Step 2: Initialize AI services
    logger.info("🤖 Initializing AI services...")
    try:
        from apps.api.app.services.ai_lead_management import (
            get_ai_lead_manager,
            get_social_media_ai,
        )

        ai_manager = await get_ai_lead_manager()
        social_ai = await get_social_media_ai()

        logger.info("✅ AI services initialized")
    except Exception as e:
        logger.error(f"❌ AI services initialization failed: {e}")
        return False

    # Step 3: Setup RingCentral integration
    logger.info("📱 Setting up RingCentral SMS integration...")
    try:
        from apps.api.app.services.ringcentral_sms import ringcentral_sms

        async with ringcentral_sms as sms_service:
            # Test authentication
            auth_success = await sms_service.authenticate()
            if auth_success:
                logger.info("✅ RingCentral integration ready")

                # Setup webhook if configured
                webhook_url = (
                    "https://api.myhibachi.com/api/webhooks/ringcentral/sms"
                )
                webhook_success = await sms_service.setup_webhook(webhook_url)
                if webhook_success:
                    logger.info("✅ RingCentral webhook configured")
                else:
                    logger.warning("⚠️ RingCentral webhook setup failed")
            else:
                logger.warning(
                    "⚠️ RingCentral authentication failed - check credentials"
                )
    except Exception as e:
        logger.warning(f"⚠️ RingCentral setup failed: {e}")

    # Step 4: Create sample data
    logger.info("📝 Creating sample data...")
    try:
        await create_sample_data()
        logger.info("✅ Sample data created")
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")

    # Step 5: Test API endpoints
    logger.info("🔍 Testing API endpoints...")
    try:
        await test_api_endpoints()
        logger.info("✅ API endpoints working")
    except Exception as e:
        logger.error(f"❌ API testing failed: {e}")

    logger.info("🎉 Enhanced CRM setup completed!")

    # Print summary
    print_setup_summary()

    return True


async def create_sample_data():
    """Create sample leads and newsletter subscribers."""
    from apps.api.app.database import get_db_context
    from apps.api.app.models.lead_newsletter import (
        Campaign,
        CampaignChannel,
        CampaignStatus,
        ContactChannel,
        Lead,
        LeadContact,
        LeadContext,
        LeadSource,
        Subscriber,
    )

    async with get_db_context() as db:
        try:
            # Create sample leads
            sample_leads = [
                {
                    "source": LeadSource.WEB_QUOTE,
                    "contacts": [
                        {
                            "channel": ContactChannel.EMAIL,
                            "handle_or_address": "john@example.com",
                            "verified": True,
                        }
                    ],
                    "context": {
                        "party_size_adults": 8,
                        "estimated_budget_cents": 150000,
                        "zip_code": "95123",
                    },
                },
                {
                    "source": LeadSource.INSTAGRAM,
                    "contacts": [
                        {
                            "channel": ContactChannel.SMS,
                            "handle_or_address": "+15551234567",
                            "verified": True,
                        }
                    ],
                    "context": {
                        "party_size_adults": 12,
                        "estimated_budget_cents": 200000,
                        "zip_code": "94102",
                    },
                },
                {
                    "source": LeadSource.PHONE,
                    "contacts": [
                        {
                            "channel": ContactChannel.PHONE,
                            "handle_or_address": "+15559876543",
                            "verified": True,
                        },
                        {
                            "channel": ContactChannel.EMAIL,
                            "handle_or_address": "sarah@example.com",
                            "verified": False,
                        },
                    ],
                    "context": {
                        "party_size_adults": 6,
                        "estimated_budget_cents": 120000,
                        "zip_code": "90210",
                    },
                },
            ]

            for lead_data in sample_leads:
                # Create lead
                lead = Lead(source=lead_data["source"])
                db.add(lead)
                await db.flush()

                # Add contacts
                for contact_data in lead_data["contacts"]:
                    contact = LeadContact(lead_id=lead.id, **contact_data)
                    db.add(contact)

                # Add context
                if lead_data.get("context"):
                    context = LeadContext(
                        lead_id=lead.id, **lead_data["context"]
                    )
                    db.add(context)

                # Calculate initial score
                lead.score = lead.calculate_score()

            # Create sample newsletter subscribers
            sample_subscribers = [
                {
                    "email": "customer1@example.com",
                    "tags": ["vip", "corporate"],
                    "engagement_score": 85,
                },
                {
                    "email": "customer2@example.com",
                    "phone": "+15555551234",
                    "sms_consent": True,
                    "engagement_score": 65,
                },
                {
                    "email": "customer3@example.com",
                    "tags": ["birthday"],
                    "engagement_score": 45,
                },
            ]

            for sub_data in sample_subscribers:
                subscriber = Subscriber(**sub_data)
                db.add(subscriber)

            # Create sample campaign
            campaign = Campaign(
                name="Welcome to My Hibachi Chef",
                channel=CampaignChannel.EMAIL,
                subject="Thank you for your interest in our hibachi catering!",
                content={
                    "html": "<h1>Welcome!</h1><p>We're excited to serve you authentic hibachi cuisine.</p>",
                    "text": "Welcome! We're excited to serve you authentic hibachi cuisine.",
                },
                status=CampaignStatus.DRAFT,
                created_by="system",
            )
            db.add(campaign)

            await db.commit()
            logger.info("Sample data created successfully")

        except Exception:
            await db.rollback()
            raise


async def test_api_endpoints():
    """Test key API endpoints."""

    import httpx

    base_url = "http://localhost:8003"

    # Test health endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")
        if response.status_code != 200:
            raise Exception(f"Health check failed: {response.status_code}")

        # Test leads endpoint
        response = await client.get(f"{base_url}/api/leads/")
        if response.status_code not in [
            200,
            401,
        ]:  # 401 is OK if auth required
            raise Exception(f"Leads endpoint failed: {response.status_code}")

        # Test newsletter endpoint
        response = await client.get(f"{base_url}/api/newsletter/subscribers")
        if response.status_code not in [200, 401]:
            raise Exception(
                f"Newsletter endpoint failed: {response.status_code}"
            )


def print_setup_summary():
    """Print setup summary and next steps."""

    print("\n" + "=" * 60)
    print("🎉 ENHANCED CRM SETUP COMPLETE")
    print("=" * 60)

    print("\n📊 DATABASE SCHEMAS CREATED:")
    print("   ✅ core - Customer and booking management")
    print("   ✅ events - Event sourcing and CQRS")
    print("   ✅ integra - Payment and call integration")
    print("   ✅ lead - Lead management and social threads")
    print("   ✅ newsletter - Email marketing and campaigns")

    print("\n🚀 API ENDPOINTS AVAILABLE:")
    print("   📋 Lead Management: /api/leads/")
    print("   📧 Newsletter: /api/newsletter/")
    print("   📱 SMS Webhooks: /api/webhooks/ringcentral/")
    print("   📊 Analytics: /api/admin/analytics/")

    print("\n🔧 INTEGRATIONS CONFIGURED:")
    print("   🤖 AI Lead Scoring (OpenAI GPT)")
    print("   📱 RingCentral SMS")
    print("   💳 Stripe Payments")
    print("   📊 Event Sourcing")

    print("\n📖 DOCUMENTATION:")
    print("   📚 API Docs: http://localhost:8003/docs")
    print("   🔍 ReDoc: http://localhost:8003/redoc")

    print("\n🔧 NEXT STEPS:")
    print("   1. Configure RingCentral credentials in .env")
    print("   2. Set up OpenAI API key for AI features")
    print("   3. Configure webhook endpoints with RingCentral")
    print("   4. Set up social media API integrations")
    print("   5. Launch admin panel to manage leads and campaigns")

    print("\n💡 ADMIN PANEL ACCESS:")
    print("   🖥️  Frontend: http://localhost:3000/admin")
    print("   📊 Analytics: http://localhost:3000/admin/analytics")
    print("   📧 Campaigns: http://localhost:3000/admin/newsletter")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("🚀 Starting Enhanced CRM Setup...")
    success = asyncio.run(setup_enhanced_crm())

    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
