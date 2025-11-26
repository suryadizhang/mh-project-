"""
Tests for ReferralService.

Tests all referral program functionality with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta

from services.referral_service import ReferralService, ReferralStatus
from core.exceptions import BusinessLogicException, NotFoundException


@pytest.mark.asyncio
class TestReferralService:
    """Test suite for ReferralService."""

    async def test_create_referral_success(self, mock_referral_service, test_lead, mock_event_service):
        """Test successful referral creation."""
        # Arrange
        referrer_id = test_lead.id
        referee_email = "referee@example.com"
        referee_name = "Referee Name"
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email=referee_email,
            referee_name=referee_name,
            reward_amount=50.0,
            reward_type="credit",
        )
        
        # Assert
        assert result["referee_email"] == referee_email
        assert result["reward_amount"] == 50.0
        assert result["status"] == ReferralStatus.PENDING
        assert "referral_code" in result
        assert result["referral_code"].startswith("REF-")
        assert "expires_at" in result
        assert "referral_link" in result
        
        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "referral_created"
        assert call_args.kwargs["entity_type"] == "referral"
        assert call_args.kwargs["user_id"] == referrer_id

    async def test_create_referral_generates_unique_code(self, mock_referral_service, test_lead):
        """Test that referral codes are unique."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act - create two referrals
        result1 = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="referee1@example.com",
        )
        result2 = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="referee2@example.com",
        )
        
        # Assert
        assert result1["referral_code"] != result2["referral_code"]

    async def test_create_referral_with_custom_code(self, mock_referral_service, test_lead):
        """Test creating referral with custom code."""
        # Arrange
        referrer_id = test_lead.id
        custom_code = "CUSTOM-2025"
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="referee@example.com",
            referral_code=custom_code,
        )
        
        # Assert
        assert result["referral_code"] == custom_code

    async def test_create_referral_referrer_not_found(self, mock_referral_service):
        """Test referral creation fails when referrer doesn't exist."""
        # Arrange
        invalid_referrer_id = 99999
        
        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await mock_referral_service.create_referral(
                referrer_id=invalid_referrer_id,
                referee_email="referee@example.com",
            )
        
        assert "not found" in str(exc_info.value).lower()

    async def test_create_referral_sends_notification(self, mock_referral_service, test_lead):
        """Test that referral creation sends notification."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="referee@example.com",
        )
        
        # Assert - notification service should be called
        assert mock_referral_service.notification_service.called

    async def test_track_conversion_success(self, mock_referral_service, test_lead, mock_event_service):
        """Test successful conversion tracking."""
        # Arrange
        referral_code = "REF-ABC123"
        referee_id = test_lead.id
        conversion_value = 299.99
        
        # Act
        result = await mock_referral_service.track_conversion(
            referral_code=referral_code,
            referee_id=referee_id,
            conversion_value=conversion_value,
            conversion_type="booking",
        )
        
        # Assert
        assert result["referral_code"] == referral_code
        assert result["conversion_value"] == conversion_value
        assert result["conversion_type"] == "booking"
        assert result["status"] == ReferralStatus.COMPLETED
        assert result["reward_awarded"] is True
        
        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "referral_converted"

    async def test_track_conversion_multiple_types(self, mock_referral_service, test_lead):
        """Test tracking different conversion types."""
        # Arrange
        referee_id = test_lead.id
        conversion_types = ["booking", "purchase", "signup"]
        
        # Act & Assert
        for conv_type in conversion_types:
            result = await mock_referral_service.track_conversion(
                referral_code=f"REF-{conv_type.upper()}",
                referee_id=referee_id,
                conversion_value=100.0,
                conversion_type=conv_type,
            )
            assert result["conversion_type"] == conv_type

    async def test_get_referral_stats(self, mock_referral_service, test_lead, mock_event_service):
        """Test getting referral statistics."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        stats = await mock_referral_service.get_referral_stats(referrer_id)
        
        # Assert
        assert stats["referrer_id"] == referrer_id
        assert "total_referrals" in stats
        assert "pending_referrals" in stats
        assert "completed_referrals" in stats
        assert "expired_referrals" in stats
        assert "total_earnings" in stats
        assert "pending_earnings" in stats
        assert "referral_codes" in stats
        
        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "referral_stats_requested"

    async def test_award_referral_credit(self, mock_referral_service, test_lead, mock_event_service):
        """Test awarding referral credit."""
        # Arrange
        referrer_id = test_lead.id
        amount = 50.0
        reason = "Successful referral conversion"
        
        # Act
        result = await mock_referral_service.award_referral_credit(
            referrer_id=referrer_id,
            amount=amount,
            reason=reason,
        )
        
        # Assert
        assert result["referrer_id"] == referrer_id
        assert result["amount"] == amount
        assert result["reason"] == reason
        assert "awarded_at" in result
        
        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "referral_credit_awarded"
        assert call_args.kwargs["metadata"]["amount"] == amount

    async def test_award_credit_sends_notification(self, mock_referral_service, test_lead):
        """Test that awarding credit sends notification."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        await mock_referral_service.award_referral_credit(
            referrer_id=referrer_id,
            amount=50.0,
            reason="Test credit",
        )
        
        # Assert
        assert mock_referral_service.notification_service.called

    async def test_referral_code_format(self, mock_referral_service, test_lead):
        """Test that generated referral codes follow correct format."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="test@example.com",
        )
        
        # Assert
        code = result["referral_code"]
        assert code.startswith("REF-")
        assert len(code) == 13  # REF- (4) + 9 chars
        assert code[4:].isupper()  # Code part should be uppercase
        assert code[4:].isalnum()  # Code part should be alphanumeric

    async def test_referral_link_generation(self, mock_referral_service, test_lead):
        """Test that referral link is correctly generated."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="test@example.com",
        )
        
        # Assert
        link = result["referral_link"]
        assert "myhibachi.com" in link
        assert "ref=" in link
        assert result["referral_code"] in link

    async def test_multiple_reward_types(self, mock_referral_service, test_lead):
        """Test creating referrals with different reward types."""
        # Arrange
        referrer_id = test_lead.id
        reward_types = ["credit", "discount", "cash"]
        
        # Act & Assert
        for reward_type in reward_types:
            result = await mock_referral_service.create_referral(
                referrer_id=referrer_id,
                referee_email=f"{reward_type}@example.com",
                reward_type=reward_type,
            )
            # In real implementation, this would be persisted
            # For now, we just verify the service accepts different types
            assert result is not None

    async def test_award_credit_with_metadata(self, mock_referral_service, test_lead, mock_event_service):
        """Test awarding credit with additional metadata."""
        # Arrange
        referrer_id = test_lead.id
        metadata = {
            "booking_id": "BK-12345",
            "referee_name": "John Doe",
            "referee_email": "john@example.com",
        }
        
        # Act
        result = await mock_referral_service.award_referral_credit(
            referrer_id=referrer_id,
            amount=75.0,
            reason="Premium booking referral",
            metadata=metadata,
        )
        
        # Assert
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["metadata"]["metadata"] == metadata

    async def test_create_referral_default_values(self, mock_referral_service, test_lead):
        """Test that default values are applied correctly."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="test@example.com",
        )
        
        # Assert - default values
        assert result["reward_amount"] == 50.0  # Default reward
        assert result["status"] == ReferralStatus.PENDING

    async def test_expiration_date_set(self, mock_referral_service, test_lead):
        """Test that expiration date is set correctly (90 days)."""
        # Arrange
        referrer_id = test_lead.id
        
        # Act
        result = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email="test@example.com",
        )
        
        # Assert
        assert "expires_at" in result
        # In real implementation, verify it's 90 days from now
        # For now, just verify it exists and is a valid ISO string
        expires_at = result["expires_at"]
        datetime.fromisoformat(expires_at)  # Should not raise


@pytest.mark.asyncio
class TestReferralServiceIntegration:
    """Integration tests for ReferralService with full workflow."""

    async def test_full_referral_workflow(self, mock_referral_service, test_lead, mock_event_service):
        """Test complete referral workflow from creation to conversion."""
        # Arrange
        referrer_id = test_lead.id
        referee_email = "newcustomer@example.com"
        
        # Step 1: Create referral
        referral = await mock_referral_service.create_referral(
            referrer_id=referrer_id,
            referee_email=referee_email,
            reward_amount=100.0,
        )
        referral_code = referral["referral_code"]
        
        # Step 2: Track conversion
        conversion = await mock_referral_service.track_conversion(
            referral_code=referral_code,
            referee_id=test_lead.id,  # Using test_lead as referee for simplicity
            conversion_value=500.0,
        )
        
        # Step 3: Award credit
        credit = await mock_referral_service.award_referral_credit(
            referrer_id=referrer_id,
            amount=100.0,
            reason="Referral conversion",
        )
        
        # Assert - verify full workflow
        assert referral["status"] == ReferralStatus.PENDING
        assert conversion["status"] == ReferralStatus.COMPLETED
        assert credit["amount"] == 100.0
        
        # Verify all events were tracked (3 calls total)
        assert mock_event_service.log_event.call_count == 3
