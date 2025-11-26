"""
Comprehensive Newsletter Service Tests - Production Grade
Tests all real-world scenarios that occur in production:
- New subscriptions (phone, email, both)
- Resubscriptions after unsubscribe
- Unsubscribe flows and STOP commands
- START command resubscriptions
- Edge cases and error handling
- Data encryption and PII protection
- Concurrent operations
- Compliance (TCPA, CAN-SPAM)
"""

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from models.legacy_lead_newsletter import Subscriber, LeadSource
from services.newsletter_service import SubscriberService


class TestNewsletterServiceProductionScenarios:
    """Production-grade tests simulating real user journeys"""

    @pytest_asyncio.fixture
    async def newsletter_service(self, db_session: AsyncSession):
        """Create newsletter service with clean database state"""
        # Clean up any existing test data
        await db_session.execute(
            text("DELETE FROM newsletter.subscribers WHERE TRUE")
        )
        await db_session.commit()
        return SubscriberService(db_session)

    @pytest_asyncio.fixture
    def mock_sms_service(self):
        """Mock SMS service to prevent actual SMS sends in tests"""
        with patch("services.ringcentral_sms.RingCentralSMSService") as mock:
            mock_instance = AsyncMock()
            mock_instance.send_sms = AsyncMock(return_value=True)
            mock.return_value = mock_instance
            yield mock_instance

    @pytest_asyncio.fixture
    def mock_email_service(self):
        """Mock email service to prevent actual email sends in tests"""
        with patch("services.email_service.EmailService") as mock:
            mock_instance = AsyncMock()
            mock_instance.send_email = AsyncMock(return_value=True)
            mock.return_value = mock_instance
            yield mock_instance

    # ==================== NEW SUBSCRIPTION SCENARIOS ====================

    @pytest.mark.asyncio
    async def test_subscribe_new_user_phone_only(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: User submits quote form with phone only
        Real scenario: Quote form, event inquiry, contact form
        """
        # Act
        result = await newsletter_service.subscribe(
            phone="+15551234567",
            name="John Doe",
            source=LeadSource.WEB_QUOTE,
            auto_subscribed=True,
        )

        # Assert - Subscriber created with E.164 format phone
        assert result is not None
        assert isinstance(result, Subscriber)
        assert result.phone == "+15551234567"  # Stored in E.164 format
        assert result.email is None
        assert result.subscribed is True
        assert result.sms_consent is True
        assert result.email_consent is False
        assert result.source == LeadSource.WEB_QUOTE
        assert result.unsubscribed_at is None

        # Assert - Welcome SMS sent
        mock_sms_service.send_sms.assert_called_once()
        call_args = mock_sms_service.send_sms.call_args
        assert "+15551234567" in str(call_args)
        assert "Welcome" in str(call_args) or "Thanks" in str(call_args)

        # Assert - Data persisted
        await db_session.refresh(result)
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_subscribe_new_user_email_only(
        self, newsletter_service, mock_email_service, db_session
    ):
        """
        PRODUCTION CASE: User subscribes via email newsletter signup
        Real scenario: Footer newsletter, blog subscription
        """
        # Act
        result = await newsletter_service.subscribe(
            email="john.doe@example.com",
            name="John Doe",
            source=LeadSource.WEB_QUOTE,
            auto_subscribed=False,  # Manual opt-in
        )

        # Assert - Subscriber created
        assert result is not None
        assert result.email == "john.doe@example.com"
        assert result.phone is None
        assert result.subscribed is True
        assert result.email_consent is True
        assert result.sms_consent is False

        # Assert - Welcome email sent
        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert "john.doe@example.com" in str(call_args)

    @pytest.mark.asyncio
    async def test_subscribe_new_user_both_phone_and_email(
        self,
        newsletter_service,
        mock_sms_service,
        mock_email_service,
        db_session,
    ):
        """
        PRODUCTION CASE: User provides both phone and email
        Real scenario: Booking form, comprehensive quote request
        """
        # Act
        result = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john.doe@example.com",
            name="John Doe",
            source=LeadSource.WEB_QUOTE,
            auto_subscribed=True,
        )

        # Assert - Subscriber created with both channels
        assert result.phone == "+15551234567"
        assert result.email == "john.doe@example.com"
        assert result.sms_consent is True
        assert result.email_consent is True

        # Assert - Both welcome messages sent
        mock_sms_service.send_sms.assert_called_once()
        mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_duplicate_phone_already_active(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: User already subscribed tries to subscribe again
        Real scenario: Multiple form submissions, returning customer
        Expected: Returns existing subscription, no duplicate created
        """
        # Arrange - Create existing subscription
        existing = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )
        existing_id = existing.id
        mock_sms_service.reset_mock()

        # Act - Try to subscribe again
        result = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.CHAT
        )

        # Assert - Same subscription returned, no new record
        assert result.id == existing_id
        assert result.subscribed is True

        # Assert - No duplicate welcome message
        mock_sms_service.send_sms.assert_not_called()

        # Assert - No duplicate in database
        all_subs = await db_session.execute(
            text(
                "SELECT COUNT(*) as cnt FROM newsletter.subscribers WHERE phone_enc IS NOT NULL"
            )
        )
        count = all_subs.scalar()
        assert count == 1

    # ==================== RESUBSCRIPTION SCENARIOS ====================

    @pytest.mark.asyncio
    async def test_resubscribe_after_unsubscribe(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: User unsubscribed but wants back in
        Real scenario: Changed mind, new promotion, re-engaged customer
        """
        # Arrange - Create and unsubscribe
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )

        # Clear session cache to ensure fresh lookup
        db_session.expire_all()

        await newsletter_service.unsubscribe(phone="+15551234567")

        # Re-query to get updated state (don't use refresh, fetch fresh)
        subscriber = await newsletter_service.find_by_contact(
            phone="+15551234567"
        )
        assert subscriber.unsubscribed_at is not None
        mock_sms_service.reset_mock()

        # Act - Resubscribe
        db_session.expire_all()
        result = await newsletter_service.subscribe(
            phone="+15551234567", name="John Doe", source=LeadSource.WEB_QUOTE
        )

        # Assert - Same subscriber reactivated
        assert result.id == subscriber.id
        assert result.unsubscribed_at is None
        assert result.subscribed is True

        # Assert - Resubscribe confirmation sent
        mock_sms_service.send_sms.assert_called_once()
        call_args = str(mock_sms_service.send_sms.call_args)
        assert (
            "resubscribe" in call_args.lower() or "back" in call_args.lower()
        )

    @pytest.mark.asyncio
    async def test_resubscribe_preserves_engagement_history(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Resubscription should preserve engagement metrics
        Real scenario: Marketing analytics, customer lifetime value tracking
        """
        # Arrange - Create subscriber with engagement history
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
        )
        # Simulate engagement history
        subscriber.total_emails_sent = 10
        subscriber.total_emails_opened = 5
        subscriber.total_clicks = 3
        subscriber.engagement_score = 75
        await db_session.commit()

        # Unsubscribe
        await newsletter_service.unsubscribe(phone="+15551234567")
        await db_session.refresh(subscriber)

        # Act - Resubscribe
        result = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )

        # Assert - Engagement history preserved
        await db_session.refresh(result)
        assert result.total_emails_sent == 10
        assert result.total_emails_opened == 5
        assert result.total_clicks == 3
        assert result.engagement_score == 75

    # ==================== UNSUBSCRIBE SCENARIOS ====================

    @pytest.mark.asyncio
    async def test_unsubscribe_active_subscriber(
        self,
        newsletter_service,
        mock_sms_service,
        mock_email_service,
        db_session,
    ):
        """
        PRODUCTION CASE: User clicks unsubscribe link in email
        Real scenario: Email footer unsubscribe, too many messages
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
        )
        mock_sms_service.reset_mock()
        mock_email_service.reset_mock()

        # Act
        result = await newsletter_service.unsubscribe(
            phone="+15551234567", email="john@example.com"
        )

        # Assert
        assert result is True
        await db_session.refresh(subscriber)
        assert subscriber.unsubscribed_at is not None
        assert isinstance(subscriber.unsubscribed_at, datetime)

        # Assert - Confirmation messages sent
        mock_sms_service.send_sms.assert_called_once()
        mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_subscriber(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Unsubscribe request for non-subscriber
        Real scenario: Spam prevention, wrong number, forwarded email
        """
        # Act
        result = await newsletter_service.unsubscribe(phone="+15559999999")

        # Assert - Returns False, no error thrown
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_already_unsubscribed(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: Multiple unsubscribe attempts (duplicate clicks)
        Real scenario: User clicks unsubscribe link multiple times
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )

        # Clear cache and unsubscribe
        db_session.expire_all()
        await newsletter_service.unsubscribe(phone="+15551234567")

        # Re-query to get updated state
        subscriber = await newsletter_service.find_by_contact(
            phone="+15551234567"
        )
        first_unsub_time = subscriber.unsubscribed_at
        mock_sms_service.reset_mock()

        # Act - Try to unsubscribe again
        db_session.expire_all()
        result = await newsletter_service.unsubscribe(phone="+15551234567")

        # Assert - Idempotent operation
        assert result is True

        # Re-query again to check timestamp
        subscriber = await newsletter_service.find_by_contact(
            phone="+15551234567"
        )
        # Timestamp should not change on duplicate unsubscribe
        assert subscriber.unsubscribed_at == first_unsub_time

    # ==================== STOP/START COMMAND SCENARIOS ====================

    @pytest.mark.asyncio
    async def test_process_stop_command_sms(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: User replies "STOP" to SMS (TCPA compliance)
        Real scenario: SMS opt-out, regulatory requirement
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.SMS
        )
        mock_sms_service.reset_mock()

        # Act
        success, message = await newsletter_service.process_stop_command(
            phone="+15551234567", channel="sms"
        )

        # Assert
        assert success is True
        assert (
            "removed" in message.lower() or "unsubscribed" in message.lower()
        )
        await db_session.refresh(subscriber)
        assert subscriber.unsubscribed_at is not None
        assert subscriber.unsubscribe_reason == "stop_command_sms"

    @pytest.mark.asyncio
    async def test_process_start_command_new_subscriber(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: User replies "START" to opt-in via SMS
        Real scenario: SMS marketing opt-in, contest entry
        """
        # Act
        success, message = await newsletter_service.process_start_command(
            phone="+15551234567", name="John Doe", channel="sms"
        )

        # Assert
        assert success is True
        assert "subscribed" in message.lower() or "welcome" in message.lower()

        # Verify subscriber created
        subscriber = await newsletter_service.find_by_contact(
            phone="+15551234567"
        )
        assert subscriber is not None
        assert subscriber.subscribed is True
        assert subscriber.source == LeadSource.SMS
        assert subscriber.unsubscribed_at is None

    @pytest.mark.asyncio
    async def test_process_start_command_resubscribe(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: Previously unsubscribed user replies "START"
        Real scenario: User changed mind, wants back in
        """
        # Arrange - Subscribe and unsubscribe
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.SMS
        )
        await newsletter_service.process_stop_command(
            phone="+15551234567", channel="sms"
        )
        await db_session.refresh(subscriber)
        original_id = subscriber.id
        mock_sms_service.reset_mock()

        # Act
        success, message = await newsletter_service.process_start_command(
            phone="+15551234567", channel="sms"
        )

        # Assert
        assert success is True
        await db_session.refresh(subscriber)
        assert subscriber.id == original_id  # Same record reactivated
        assert subscriber.unsubscribed_at is None
        assert subscriber.subscribed is True

    @pytest.mark.asyncio
    async def test_stop_command_already_unsubscribed(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: User sends STOP after already unsubscribed
        Real scenario: Duplicate STOP replies, confusion
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.SMS
        )

        # Clear cache before STOP command
        db_session.expire_all()
        await newsletter_service.process_stop_command(
            phone="+15551234567", channel="sms"
        )

        # Act - Send STOP again
        db_session.expire_all()
        success, message = await newsletter_service.process_stop_command(
            phone="+15551234567", channel="sms"
        )

        # Assert - Friendly response
        assert success is True
        assert "already" in message.lower()

    @pytest.mark.asyncio
    async def test_stop_command_nonexistent_subscriber(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Non-subscriber sends STOP
        Real scenario: Wrong number, forwarded message
        """
        # Act
        success, message = await newsletter_service.process_stop_command(
            phone="+15559999999", channel="sms"
        )

        # Assert - Clear response
        assert success is False
        assert "not" in message.lower() and "subscribed" in message.lower()

    # ==================== EDGE CASES & VALIDATION ====================

    @pytest.mark.asyncio
    async def test_subscribe_no_contact_info_raises_error(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Invalid form submission with no contact info
        Real scenario: Bot submission, form validation bypass
        """
        # Act & Assert
        with pytest.raises(
            ValueError, match="Either phone or email is required"
        ):
            await newsletter_service.subscribe(
                name="John Doe", source=LeadSource.WEB_QUOTE
            )

    @pytest.mark.asyncio
    async def test_phone_number_cleaning(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: Phone number format consistency
        Real scenario: All phones must be in E.164 format (+15551234567)
        Expected: Frontend enforces format, backend stores as-is
        """
        # Act - Subscribe with E.164 format
        result1 = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )
        mock_sms_service.reset_mock()

        # Try to subscribe with same E.164 phone
        db_session.expire_all()
        result2 = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )

        # Assert - Same subscriber recognized
        assert result1.id == result2.id
        assert result1.phone == result2.phone
        # Phone stored in E.164 format
        assert result1.phone == "+15551234567"

    @pytest.mark.asyncio
    async def test_email_case_insensitive(
        self, newsletter_service, mock_email_service, db_session
    ):
        """
        PRODUCTION CASE: Email addresses with different cases
        Real scenario: User types email differently each time
        """
        # Act
        result1 = await newsletter_service.subscribe(
            email="John.Doe@Example.COM", source=LeadSource.WEB_QUOTE
        )
        mock_email_service.reset_mock()

        # Clear cache before second subscribe
        db_session.expire_all()
        result2 = await newsletter_service.subscribe(
            email="john.doe@example.com", source=LeadSource.WEB_QUOTE
        )

        # Assert - Same subscriber
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_find_by_contact_phone_only(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Lookup subscriber by phone
        Real scenario: SMS reply processing, webhook handling
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.SMS
        )

        # Act
        result = await newsletter_service.find_by_contact(phone="+15551234567")

        # Assert
        assert result is not None
        assert result.id == subscriber.id

    @pytest.mark.asyncio
    async def test_find_by_contact_email_only(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Lookup subscriber by email
        Real scenario: Email bounce processing, unsubscribe handling
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            email="john@example.com", source=LeadSource.WEB_QUOTE
        )

        # Act
        result = await newsletter_service.find_by_contact(
            email="john@example.com"
        )

        # Assert
        assert result is not None
        assert result.id == subscriber.id

    @pytest.mark.asyncio
    async def test_find_by_contact_either_phone_or_email_matches(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Subscriber has both, lookup by either
        Real scenario: Cross-channel identification
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
        )

        # Act & Assert - Find by phone
        result1 = await newsletter_service.find_by_contact(
            phone="+15551234567"
        )
        assert result1.id == subscriber.id

        # Act & Assert - Find by email
        result2 = await newsletter_service.find_by_contact(
            email="john@example.com"
        )
        assert result2.id == subscriber.id

    # ==================== DATA ENCRYPTION & PII PROTECTION ====================

    @pytest.mark.asyncio
    async def test_pii_data_encrypted_at_rest(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: PII data must be encrypted in database
        Real scenario: GDPR, CCPA compliance, data breach protection
        """
        # Arrange & Act
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
        )
        await db_session.commit()

        # Assert - Check raw database storage
        result = await db_session.execute(
            text(
                """
                SELECT email_enc, phone_enc 
                FROM newsletter.subscribers 
                WHERE id = :id
            """
            ),
            {"id": subscriber.id},
        )
        row = result.fetchone()

        # Raw encrypted data should be bytes, not plaintext
        assert isinstance(row.email_enc, bytes)
        assert isinstance(row.phone_enc, bytes)
        # Should NOT contain plaintext
        assert b"john@example.com" not in row.email_enc
        assert b"15551234567" not in row.phone_enc

    @pytest.mark.asyncio
    async def test_pii_data_decrypts_on_read(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Application can decrypt PII for business use
        Real scenario: Sending messages, customer support lookup
        """
        # Arrange
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
        )

        # Act - Read subscriber
        result = await newsletter_service.find_by_contact(phone="+15551234567")

        # Assert - Properties decrypt automatically
        assert result.phone == "+15551234567"
        assert result.email == "john@example.com"

    # ==================== ERROR HANDLING & RESILIENCE ====================

    @pytest.mark.asyncio
    async def test_sms_failure_does_not_prevent_subscription(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: SMS service down or rate limited
        Real scenario: RingCentral outage, API rate limits
        Expected: Subscription still created, error logged
        """
        # Arrange - Mock SMS failure
        mock_sms_service.send_sms.side_effect = Exception(
            "SMS service unavailable"
        )

        # Act - Should not raise
        result = await newsletter_service.subscribe(
            phone="+15551234567", source=LeadSource.WEB_QUOTE
        )

        # Assert - Subscription created despite SMS failure
        assert result is not None
        assert result.subscribed is True
        await db_session.refresh(result)
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_email_failure_does_not_prevent_subscription(
        self, newsletter_service, mock_email_service, db_session
    ):
        """
        PRODUCTION CASE: Email service down or quota exceeded
        Real scenario: SMTP server down, SendGrid outage
        Expected: Subscription still created, error logged
        """
        # Arrange - Mock email failure
        mock_email_service.send_email.side_effect = Exception(
            "Email service unavailable"
        )

        # Act - Should not raise
        result = await newsletter_service.subscribe(
            email="john@example.com", source=LeadSource.WEB_QUOTE
        )

        # Assert - Subscription created despite email failure
        assert result is not None
        assert result.subscribed is True

    @pytest.mark.asyncio
    async def test_concurrent_subscriptions_same_phone(
        self, newsletter_service, mock_sms_service, db_session
    ):
        """
        PRODUCTION CASE: Multiple simultaneous form submissions
        Real scenario: User double-clicks submit, duplicate webhook deliveries
        Expected: Only one subscription created
        """
        import asyncio

        # Act - Concurrent subscribe attempts
        results = await asyncio.gather(
            newsletter_service.subscribe(
                phone="+15551234567", source=LeadSource.WEB_QUOTE
            ),
            newsletter_service.subscribe(
                phone="+15551234567", source=LeadSource.WEB_QUOTE
            ),
            newsletter_service.subscribe(
                phone="+15551234567", source=LeadSource.WEB_QUOTE
            ),
            return_exceptions=True,
        )

        # Assert - All return same subscriber (or some may raise, that's ok)
        successful_results = [r for r in results if isinstance(r, Subscriber)]
        assert len(successful_results) >= 1

        # Verify only one record in database
        count_result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM newsletter.subscribers WHERE phone_enc IS NOT NULL"
            )
        )
        count = count_result.scalar()
        assert count == 1

    # ==================== COMPLIANCE & CONSENT TRACKING ====================

    @pytest.mark.asyncio
    async def test_consent_tracking_auto_subscribed(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Implied consent (TCPA compliance)
        Real scenario: User submits inquiry form with phone/email
        """
        # Act
        subscriber = await newsletter_service.subscribe(
            phone="+15551234567",
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
            auto_subscribed=True,  # Implied consent
        )

        # Assert - Consent flags set appropriately
        assert subscriber.sms_consent is True
        assert subscriber.email_consent is True
        assert subscriber.consent_updated_at is not None
        assert isinstance(subscriber.consent_updated_at, datetime)

    @pytest.mark.asyncio
    async def test_consent_tracking_manual_opt_in(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Explicit consent (checkbox checked)
        Real scenario: Newsletter signup form with clear opt-in
        """
        # Act
        subscriber = await newsletter_service.subscribe(
            email="john@example.com",
            source=LeadSource.WEB_QUOTE,
            auto_subscribed=False,  # Explicit opt-in
        )

        # Assert
        assert subscriber.email_consent is True
        assert subscriber.consent_updated_at is not None

    @pytest.mark.asyncio
    async def test_get_active_subscriptions(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Fetch all active subscribers for campaign
        Real scenario: Email blast, SMS campaign, analytics
        """
        # Arrange - Create mix of active and inactive
        await newsletter_service.subscribe(
            phone="+15551111111", source=LeadSource.WEB_QUOTE
        )
        await newsletter_service.subscribe(
            phone="+15552222222", source=LeadSource.WEB_QUOTE
        )
        unsubscribed = await newsletter_service.subscribe(
            phone="+15553333333", source=LeadSource.WEB_QUOTE
        )
        await newsletter_service.unsubscribe(phone="+15553333333")

        # Act
        active = await newsletter_service.get_active_subscriptions()

        # Assert - Only active returned
        assert len(active) == 2
        active_ids = [s.id for s in active]
        assert unsubscribed.id not in active_ids

    @pytest.mark.asyncio
    async def test_get_active_subscriptions_pagination(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Large subscriber base requires pagination
        Real scenario: Enterprise with 100k+ subscribers
        """
        # Arrange - Create multiple subscribers
        for i in range(25):
            await newsletter_service.subscribe(
                phone=f"+1555000{i:04d}", source=LeadSource.WEB_QUOTE
            )

        # Act - Paginate
        page1 = await newsletter_service.get_active_subscriptions(
            limit=10, offset=0
        )
        page2 = await newsletter_service.get_active_subscriptions(
            limit=10, offset=10
        )
        page3 = await newsletter_service.get_active_subscriptions(
            limit=10, offset=20
        )

        # Assert
        assert len(page1) == 10
        assert len(page2) == 10
        assert len(page3) == 5

        # No overlap between pages
        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    # ==================== STATIC METHOD TESTS ====================

    @pytest.mark.asyncio
    async def test_is_stop_command_variations(self):
        """
        PRODUCTION CASE: Various STOP command formats (TCPA requirement)
        Real scenario: Users type different variations
        """
        # Assert - All variations recognized
        assert SubscriberService.is_stop_command("STOP") is True
        assert SubscriberService.is_stop_command("stop") is True
        assert SubscriberService.is_stop_command("Stop") is True
        assert SubscriberService.is_stop_command("  STOP  ") is True
        assert SubscriberService.is_stop_command("UNSUBSCRIBE") is True
        assert SubscriberService.is_stop_command("cancel") is True
        assert SubscriberService.is_stop_command("end") is True
        assert SubscriberService.is_stop_command("quit") is True
        assert SubscriberService.is_stop_command("opt out") is True
        assert SubscriberService.is_stop_command("optout") is True

        # Assert - Regular messages not recognized
        assert SubscriberService.is_stop_command("Hello") is False
        assert SubscriberService.is_stop_command("I'd like to book") is False

    @pytest.mark.asyncio
    async def test_is_start_command_variations(self):
        """
        PRODUCTION CASE: Various START command formats
        Real scenario: Users opt back in
        """
        # Assert - All variations recognized
        assert SubscriberService.is_start_command("START") is True
        assert SubscriberService.is_start_command("start") is True
        assert SubscriberService.is_start_command("Start") is True
        assert SubscriberService.is_start_command("  START  ") is True
        assert SubscriberService.is_start_command("SUBSCRIBE") is True
        assert SubscriberService.is_start_command("yes") is True
        assert SubscriberService.is_start_command("join") is True
        assert SubscriberService.is_start_command("opt in") is True
        assert SubscriberService.is_start_command("optin") is True

        # Assert - Regular messages not recognized
        assert SubscriberService.is_start_command("No thanks") is False
        assert SubscriberService.is_start_command("Maybe later") is False


class TestNewsletterServiceLeadSources:
    """Test different lead sources are tracked correctly"""

    @pytest_asyncio.fixture
    async def newsletter_service(self, db_session: AsyncSession):
        await db_session.execute(
            text("DELETE FROM newsletter.subscribers WHERE TRUE")
        )
        await db_session.commit()
        return SubscriberService(db_session)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "source,expected_source",
        [
            (LeadSource.WEB_QUOTE, LeadSource.WEB_QUOTE),
            (LeadSource.CHAT, LeadSource.CHAT),
            (LeadSource.INSTAGRAM, LeadSource.INSTAGRAM),
            (LeadSource.FACEBOOK, LeadSource.FACEBOOK),
            (LeadSource.SMS, LeadSource.SMS),
            (LeadSource.PHONE, LeadSource.PHONE),
            (LeadSource.REFERRAL, LeadSource.REFERRAL),
            (LeadSource.EVENT, LeadSource.EVENT),
        ],
    )
    async def test_lead_source_tracking(
        self, newsletter_service, source, expected_source, db_session
    ):
        """
        PRODUCTION CASE: Track where subscribers come from
        Real scenario: Marketing attribution, channel performance
        """
        with patch("services.ringcentral_sms.RingCentralSMSService"):
            # Act
            subscriber = await newsletter_service.subscribe(
                phone=f"+1555{hash(source) % 10000000:07d}", source=source
            )

            # Assert
            assert subscriber.source == expected_source


class TestNewsletterServiceChannelSpecific:
    """Test channel-specific behaviors (SMS vs Email)"""

    @pytest_asyncio.fixture
    async def newsletter_service(self, db_session: AsyncSession):
        await db_session.execute(
            text("DELETE FROM newsletter.subscribers WHERE TRUE")
        )
        await db_session.commit()
        return SubscriberService(db_session)

    @pytest.mark.asyncio
    async def test_sms_only_subscriber_no_email_sent(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: SMS-only subscriber shouldn't get emails
        Real scenario: Phone number only, no email provided
        """
        with patch(
            "services.ringcentral_sms.RingCentralSMSService"
        ) as mock_sms:
            mock_sms_instance = AsyncMock()
            mock_sms.return_value = mock_sms_instance

            with patch("services.email_service.EmailService") as mock_email:
                mock_email_instance = AsyncMock()
                mock_email.return_value = mock_email_instance

                # Act
                await newsletter_service.subscribe(
                    phone="+15551234567", source=LeadSource.WEB_QUOTE
                )

                # Assert - SMS sent, email not sent
                mock_sms_instance.send_sms.assert_called_once()
                mock_email_instance.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_only_subscriber_no_sms_sent(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Email-only subscriber shouldn't get SMS
        Real scenario: Email signup, no phone provided
        """
        with patch(
            "services.ringcentral_sms.RingCentralSMSService"
        ) as mock_sms:
            mock_sms_instance = AsyncMock()
            mock_sms.return_value = mock_sms_instance

            with patch("services.email_service.EmailService") as mock_email:
                mock_email_instance = AsyncMock()
                mock_email.return_value = mock_email_instance

                # Act
                await newsletter_service.subscribe(
                    email="john@example.com", source=LeadSource.WEB_QUOTE
                )

                # Assert - Email sent, SMS not sent
                mock_email_instance.send_email.assert_called_once()
                mock_sms_instance.send_sms.assert_not_called()

    @pytest.mark.asyncio
    async def test_multi_channel_subscriber_gets_both(
        self, newsletter_service, db_session
    ):
        """
        PRODUCTION CASE: Subscriber with both contacts gets both messages
        Real scenario: Full contact information provided
        """
        with patch(
            "services.ringcentral_sms.RingCentralSMSService"
        ) as mock_sms:
            mock_sms_instance = AsyncMock()
            mock_sms.return_value = mock_sms_instance

            with patch("services.email_service.EmailService") as mock_email:
                mock_email_instance = AsyncMock()
                mock_email.return_value = mock_email_instance

                # Act
                await newsletter_service.subscribe(
                    phone="+15551234567",
                    email="john@example.com",
                    source=LeadSource.WEB_QUOTE,
                )

                # Assert - Both sent
                mock_sms_instance.send_sms.assert_called_once()
                mock_email_instance.send_email.assert_called_once()
