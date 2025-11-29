"""
Unit tests for SubscriberService
Tests individual methods and business logic
UPDATED: Tests now match current implementation (returns Subscriber objects, not bools)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

# Phase 2C: Updated imports to current locations
from services.newsletter_service import SubscriberService
from db.models.newsletter import Subscriber
from db.models.crm import LeadSource


@pytest.mark.unit
class TestSubscriberServiceInitialization:
    """Test SubscriberService initialization"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, db_session: AsyncSession):
        """Test service can be initialized"""
        service = SubscriberService(db_session)
        assert service is not None
        assert service.db == db_session


@pytest.mark.unit
class TestSubscribeMethod:
    """Test SubscriberService.subscribe() method"""

    @pytest.mark.asyncio
    async def test_subscribe_with_phone_only(self, db_session: AsyncSession):
        """Test subscribing with phone only"""
        service = SubscriberService(db_session)

        # Mock the database query to return no existing subscriber
        with patch.object(
            service, "find_by_contact", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                service, "_send_welcome_message", new_callable=AsyncMock
            ) as mock_welcome:
                mock_find.return_value = None

                result = await service.subscribe(
                    phone="+15551234567", source=LeadSource.QUOTE_FORM
                )

                # Should return Subscriber object, not bool
                assert isinstance(result, Subscriber)
                assert result.phone == "+15551234567"
                assert result.subscribed is True
                assert result.sms_consent is True
                mock_find.assert_called_once()
                mock_welcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_with_phone_and_email(
        self, db_session: AsyncSession
    ):
        """Test subscribing with both phone and email"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "find_by_contact", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                service, "_send_welcome_message", new_callable=AsyncMock
            ) as mock_welcome:
                mock_find.return_value = None

                result = await service.subscribe(
                    phone="+15551234567",
                    email="test@example.com",
                    source=LeadSource.BOOKING_FORM,
                )

                assert isinstance(result, Subscriber)
                assert result.phone == "+15551234567"
                assert result.email == "test@example.com"
                assert result.sms_consent is True
                assert result.email_consent is True
                mock_welcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_without_phone_or_email_fails(
        self, db_session: AsyncSession
    ):
        """Test that subscribing without phone or email raises ValueError"""
        service = SubscriberService(db_session)

        with pytest.raises(
            ValueError, match="Either phone or email is required"
        ):
            await service.subscribe(
                phone=None, email=None, source=LeadSource.QUOTE_FORM
            )

    @pytest.mark.asyncio
    async def test_subscribe_reactivates_unsubscribed_user(
        self, db_session: AsyncSession
    ):
        """Test that subscribing an unsubscribed user reactivates them"""
        service = SubscriberService(db_session)

        # Mock finding an existing unsubscribed subscriber
        mock_subscriber = MagicMock(spec=Subscriber)
        mock_subscriber.id = "sub_123"
        mock_subscriber.phone = "+15551234567"
        mock_subscriber.unsubscribed_at = datetime.now(timezone.utc)
        mock_subscriber.subscribed = False

        with patch.object(
            service, "find_by_contact", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                service, "_send_welcome_message", new_callable=AsyncMock
            ) as mock_welcome:
                mock_find.return_value = mock_subscriber

                result = await service.subscribe(
                    phone="+15551234567", source=LeadSource.QUOTE_FORM
                )

                # Should return the reactivated subscriber
                assert result == mock_subscriber
                assert mock_subscriber.unsubscribed_at is None
                assert mock_subscriber.subscribed is True
                mock_welcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_returns_existing_active_subscriber(
        self, db_session: AsyncSession
    ):
        """Test that subscribing returns existing active subscriber"""
        service = SubscriberService(db_session)

        # Mock finding an existing active subscriber
        mock_subscriber = MagicMock(spec=Subscriber)
        mock_subscriber.id = "sub_456"
        mock_subscriber.phone = "+15551234567"
        mock_subscriber.unsubscribed_at = None
        mock_subscriber.subscribed = True

        with patch.object(
            service, "find_by_contact", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = mock_subscriber

            result = await service.subscribe(
                phone="+15551234567", source=LeadSource.QUOTE_FORM
            )

            # Should return the existing subscriber without sending welcome
            assert result == mock_subscriber


@pytest.mark.unit
class TestUnsubscribeMethod:
    """Test SubscriberService.unsubscribe() method"""

    @pytest.mark.asyncio
    async def test_unsubscribe_existing_subscriber(
        self, db_session: AsyncSession
    ):
        """Test unsubscribing an existing subscriber"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_subscriber_by_phone", new_callable=AsyncMock
        ) as mock_get:
            mock_subscriber = MagicMock()
            mock_subscriber.id = "sub_123"
            mock_subscriber.phone = "+15551234567"
            mock_subscriber.is_active = True
            mock_get.return_value = mock_subscriber

            result = await service.unsubscribe(phone="+15551234567")

            assert result is True
            assert mock_subscriber.is_active is False
            assert mock_subscriber.unsubscribed_at is not None

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_subscriber(
        self, db_session: AsyncSession
    ):
        """Test unsubscribing a phone that doesn't exist"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_subscriber_by_phone", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.unsubscribe(phone="+15559999999")

            assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_already_unsubscribed(
        self, db_session: AsyncSession
    ):
        """Test unsubscribing a subscriber who is already unsubscribed"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_subscriber_by_phone", new_callable=AsyncMock
        ) as mock_get:
            mock_subscriber = MagicMock()
            mock_subscriber.id = "sub_123"
            mock_subscriber.phone = "+15551234567"
            mock_subscriber.is_active = False  # Already unsubscribed
            mock_get.return_value = mock_subscriber

            result = await service.unsubscribe(phone="+15551234567")

            # Should still return True (idempotent)
            assert result is True


@pytest.mark.unit
class TestResubscribeMethod:
    """Test SubscriberService.resubscribe() method"""

    @pytest.mark.asyncio
    async def test_resubscribe_unsubscribed_user(
        self, db_session: AsyncSession
    ):
        """Test resubscribing a previously unsubscribed user"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_subscriber_by_phone", new_callable=AsyncMock
        ) as mock_get:
            with patch.object(
                service, "_send_welcome_sms", new_callable=AsyncMock
            ) as mock_sms:
                mock_subscriber = MagicMock()
                mock_subscriber.id = "sub_123"
                mock_subscriber.phone = "+15551234567"
                mock_subscriber.is_active = False
                mock_subscriber.unsubscribed_at = datetime.now()
                mock_get.return_value = mock_subscriber

                result = await service.resubscribe(phone="+15551234567")

                assert result is True
                assert mock_subscriber.is_active is True
                assert mock_subscriber.unsubscribed_at is None
                mock_sms.assert_called_once_with("+15551234567")

    @pytest.mark.asyncio
    async def test_resubscribe_nonexistent_subscriber(
        self, db_session: AsyncSession
    ):
        """Test resubscribing a phone that doesn't exist"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_subscriber_by_phone", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.resubscribe(phone="+15559999999")

            assert result is False


@pytest.mark.unit
class TestPhoneNumberCleaning:
    """Test phone number cleaning logic"""

    def test_clean_phone_removes_formatting(self):
        """Test that phone formatting is removed"""
        # Phase 2B: Updated import
        from services.newsletter_service import SubscriberService

        test_cases = [
            ("(555) 123-4567", "5551234567"),
            ("555-123-4567", "5551234567"),
            ("555.123.4567", "5551234567"),
            ("+1 555 123 4567", "15551234567"),
            ("1-555-123-4567", "15551234567"),
        ]

        for input_phone, expected in test_cases:
            result = SubscriberService._clean_phone(input_phone)
            assert result == expected, f"Failed for input: {input_phone}"

    def test_clean_phone_handles_empty_input(self):
        """Test that empty phone returns None"""
        # Phase 2B: Updated import
        from services.newsletter_service import SubscriberService

        assert SubscriberService._clean_phone(None) is None
        assert SubscriberService._clean_phone("") is None
        assert SubscriberService._clean_phone("   ") is None


@pytest.mark.unit
class TestWelcomeMessages:
    """Test welcome message sending"""

    @pytest.mark.asyncio
    async def test_send_welcome_sms_success(self, db_session: AsyncSession):
        """Test successful SMS sending"""
        service = SubscriberService(db_session)

        with patch(
            "api.app.services.newsletter_service.send_sms",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True

            result = await service._send_welcome_sms("+15551234567")

            assert result is True
            mock_send.assert_called_once()
            args = mock_send.call_args[1]
            assert args["to_phone"] == "+15551234567"
            assert (
                "newsletter" in args["message"].lower()
                or "subscribe" in args["message"].lower()
            )

    @pytest.mark.asyncio
    async def test_send_welcome_sms_handles_failure(
        self, db_session: AsyncSession
    ):
        """Test that SMS failures are handled gracefully"""
        service = SubscriberService(db_session)

        with patch(
            "api.app.services.newsletter_service.send_sms",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.side_effect = Exception("SMS service down")

            result = await service._send_welcome_sms("+15551234567")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, db_session: AsyncSession):
        """Test successful email sending"""
        service = SubscriberService(db_session)

        with patch(
            "api.app.services.newsletter_service.send_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True

            result = await service._send_welcome_email("test@example.com")

            assert result is True
            mock_send.assert_called_once()
            args = mock_send.call_args[1]
            assert args["to_email"] == "test@example.com"
            assert "Welcome" in args["subject"]

    @pytest.mark.asyncio
    async def test_send_welcome_email_handles_failure(
        self, db_session: AsyncSession
    ):
        """Test that email failures are handled gracefully"""
        service = SubscriberService(db_session)

        with patch(
            "api.app.services.newsletter_service.send_email",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.side_effect = Exception("Email service down")

            result = await service._send_welcome_email("test@example.com")

            assert result is False


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_subscribe_continues_if_sms_fails(
        self, db_session: AsyncSession
    ):
        """Test that subscription succeeds even if SMS fails"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_or_create_subscriber", new_callable=AsyncMock
        ) as mock_get:
            with patch.object(
                service, "_send_welcome_sms", new_callable=AsyncMock
            ) as mock_sms:
                mock_subscriber = MagicMock()
                mock_subscriber.id = "sub_123"
                mock_subscriber.phone = "+15551234567"
                mock_subscriber.is_active = True
                mock_get.return_value = mock_subscriber
                mock_sms.return_value = False  # SMS fails

                result = await service.subscribe(
                    phone="+15551234567", source=LeadSource.QUOTE_FORM
                )

                # Subscription should still succeed
                assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_continues_if_email_fails(
        self, db_session: AsyncSession
    ):
        """Test that subscription succeeds even if email fails"""
        service = SubscriberService(db_session)

        with patch.object(
            service, "_get_or_create_subscriber", new_callable=AsyncMock
        ) as mock_get:
            with patch.object(
                service, "_send_welcome_sms", new_callable=AsyncMock
            ) as mock_sms:
                with patch.object(
                    service, "_send_welcome_email", new_callable=AsyncMock
                ) as mock_email:
                    mock_subscriber = MagicMock()
                    mock_subscriber.id = "sub_456"
                    mock_subscriber.phone = "+15551234567"
                    mock_subscriber.email = "test@example.com"
                    mock_subscriber.is_active = True
                    mock_get.return_value = mock_subscriber
                    mock_sms.return_value = True
                    mock_email.return_value = False  # Email fails

                    result = await service.subscribe(
                        phone="+15551234567",
                        email="test@example.com",
                        source=LeadSource.BOOKING_FORM,
                    )

                    # Subscription should still succeed
                    assert result is True


@pytest.mark.unit
class TestLeadSources:
    """Test different subscription sources"""

    @pytest.mark.asyncio
    async def test_all_subscription_sources(self, db_session: AsyncSession):
        """Test that all subscription sources work"""
        service = SubscriberService(db_session)

        sources = [
            LeadSource.QUOTE_FORM,
            LeadSource.BOOKING_FORM,
            LeadSource.CHATBOT,
            LeadSource.SMS,
            LeadSource.EMAIL,
            LeadSource.FACEBOOK,
            LeadSource.INSTAGRAM,
            LeadSource.WEBSITE,
        ]

        with patch.object(
            service, "_get_or_create_subscriber", new_callable=AsyncMock
        ) as mock_get:
            with patch.object(
                service, "_send_welcome_sms", new_callable=AsyncMock
            ) as mock_sms:
                mock_subscriber = MagicMock()
                mock_subscriber.id = "sub_123"
                mock_subscriber.phone = "+15551234567"
                mock_subscriber.is_active = True
                mock_get.return_value = mock_subscriber

                for source in sources:
                    result = await service.subscribe(
                        phone="+15551234567", source=source
                    )

                    assert result is True, f"Source {source} should work"


# Run tests with: pytest tests/test_newsletter_unit.py -v -s --tb=short
# Run specific test class: pytest tests/test_newsletter_unit.py::TestSubscribeMethod -v -s
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
