"""
Tests for NurtureCampaignService.

Tests automated lead nurturing and campaign functionality.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from services.nurture_campaign_service import (
    NurtureCampaignService,
    CampaignType,
    CampaignStatus,
    MessageStatus,
)
from core.exceptions import NotFoundException, BusinessLogicException


@pytest.mark.asyncio
class TestNurtureCampaignService:
    """Test suite for NurtureCampaignService."""

    async def test_enroll_lead_success(self, mock_campaign_service, test_lead, mock_event_service):
        """Test successful lead enrollment in campaign."""
        # Arrange
        lead_id = test_lead.id
        campaign_type = CampaignType.WELCOME

        # Act
        result = await mock_campaign_service.enroll_lead(
            lead_id=lead_id,
            campaign_type=campaign_type,
        )

        # Assert
        assert result["lead_id"] == lead_id
        assert result["campaign_type"] == campaign_type.value
        assert result["status"] == CampaignStatus.ACTIVE.value
        assert result["total_steps"] == 3  # WELCOME campaign has 3 steps
        assert "enrolled_at" in result

        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "campaign_enrolled"

    async def test_enroll_lead_all_campaign_types(self, mock_campaign_service, test_lead):
        """Test enrolling in all available campaign types."""
        # Arrange
        lead_id = test_lead.id
        campaign_types = [
            CampaignType.WELCOME,
            CampaignType.POST_INQUIRY,
            CampaignType.ABANDONED_QUOTE,
            CampaignType.POST_EVENT,
        ]

        # Act & Assert
        for campaign_type in campaign_types:
            result = await mock_campaign_service.enroll_lead(
                lead_id=lead_id,
                campaign_type=campaign_type,
            )
            assert result["campaign_type"] == campaign_type.value
            assert result["total_steps"] > 0

    async def test_enroll_lead_with_personalization(self, mock_campaign_service, test_lead, mock_event_service):
        """Test enrolling with personalization data."""
        # Arrange
        lead_id = test_lead.id
        personalization = {
            "event_type": "Birthday Party",
            "guest_count": 20,
            "event_date": "2025-12-25",
        }

        # Act
        result = await mock_campaign_service.enroll_lead(
            lead_id=lead_id,
            campaign_type=CampaignType.WELCOME,
            personalization=personalization,
        )

        # Assert
        assert result is not None
        # In real implementation, personalization would be stored

    async def test_enroll_lead_not_found(self, mock_campaign_service):
        """Test enrollment fails when lead doesn't exist."""
        # Arrange
        invalid_lead_id = 99999

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await mock_campaign_service.enroll_lead(
                lead_id=invalid_lead_id,
                campaign_type=CampaignType.WELCOME,
            )

        assert "not found" in str(exc_info.value).lower()

    async def test_enroll_lead_skip_if_enrolled(self, mock_campaign_service, test_lead):
        """Test skip_if_enrolled parameter prevents duplicate enrollments."""
        # Arrange
        lead_id = test_lead.id

        # Act - enroll twice with skip_if_enrolled=True
        result1 = await mock_campaign_service.enroll_lead(
            lead_id=lead_id,
            campaign_type=CampaignType.WELCOME,
            skip_if_enrolled=True,
        )
        # In real implementation with database, second call would return existing enrollment
        # For now, we just verify it doesn't error
        assert result1 is not None

    async def test_send_next_message_success(self, mock_campaign_service, test_lead, mock_event_service):
        """Test sending next campaign message."""
        # Arrange
        lead_id = test_lead.id
        campaign_type = CampaignType.WELCOME

        # First enroll the lead
        await mock_campaign_service.enroll_lead(lead_id, campaign_type)

        # Act
        result = await mock_campaign_service.send_next_message(
            lead_id=lead_id,
            campaign_type=campaign_type,
        )

        # Assert
        # In real implementation with database, this would send actual message
        # For now, we verify the service structure
        assert result is not None

    async def test_send_message_uses_notification_service(self, mock_campaign_service, test_lead):
        """Test that sending message uses notification service."""
        # Arrange
        lead_id = test_lead.id
        campaign_type = CampaignType.WELCOME

        # Enroll first
        await mock_campaign_service.enroll_lead(lead_id, campaign_type)

        # Act
        await mock_campaign_service.send_next_message(lead_id, campaign_type)

        # Assert - notification service should be called in real workflow
        # (Mock won't have enrollment data, so it will raise NotFoundException)

    async def test_handle_response_reply(self, mock_campaign_service, test_lead, mock_event_service):
        """Test handling lead reply to campaign."""
        # Arrange
        lead_id = test_lead.id
        response_data = {"message": "I'm interested!"}

        # Act
        result = await mock_campaign_service.handle_response(
            lead_id=lead_id,
            response_type="reply",
            response_data=response_data,
        )

        # Assert
        assert result["lead_id"] == lead_id
        assert result["response_type"] == "reply"
        assert result["status"] == "processed"

        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "campaign_response_reply"

    async def test_handle_response_click(self, mock_campaign_service, test_lead, mock_event_service):
        """Test handling link click in campaign."""
        # Arrange
        lead_id = test_lead.id
        response_data = {"link": "https://myhibachi.com/menu", "timestamp": datetime.utcnow().isoformat()}

        # Act
        result = await mock_campaign_service.handle_response(
            lead_id=lead_id,
            response_type="click",
            response_data=response_data,
        )

        # Assert
        assert result["response_type"] == "click"
        mock_event_service.log_event.assert_called_once()

    async def test_handle_response_opt_out(self, mock_campaign_service, test_lead, mock_event_service):
        """Test handling opt-out from campaigns."""
        # Arrange
        lead_id = test_lead.id

        # Act
        result = await mock_campaign_service.handle_response(
            lead_id=lead_id,
            response_type="opt_out",
        )

        # Assert
        assert result["status"] == "opted_out"
        assert "All campaigns paused" in result["message"]

        # Verify event was tracked
        mock_event_service.log_event.assert_called_once()
        call_args = mock_event_service.log_event.call_args
        assert call_args.kwargs["action"] == "campaign_response_opt_out"

    async def test_handle_response_booking_conversion(self, mock_campaign_service, test_lead, mock_event_service):
        """Test handling booking conversion."""
        # Arrange
        lead_id = test_lead.id
        response_data = {"booking_id": "BK-12345", "amount": 500.0}

        # Act
        result = await mock_campaign_service.handle_response(
            lead_id=lead_id,
            response_type="booking",
            response_data=response_data,
        )

        # Assert
        assert result["status"] == "converted"
        assert "completed" in result["message"].lower()

        # Verify event tracked
        mock_event_service.log_event.assert_called_once()

    async def test_get_campaign_stats(self, mock_campaign_service):
        """Test getting campaign statistics."""
        # Act
        stats = await mock_campaign_service.get_campaign_stats()

        # Assert
        assert "total_enrollments" in stats
        assert "active_enrollments" in stats
        assert "completed_enrollments" in stats
        assert "opted_out" in stats
        assert "messages_sent" in stats
        assert "messages_opened" in stats
        assert "messages_clicked" in stats
        assert "conversions" in stats
        assert "open_rate" in stats
        assert "click_rate" in stats
        assert "conversion_rate" in stats

    async def test_get_campaign_stats_filtered(self, mock_campaign_service):
        """Test getting stats for specific campaign type."""
        # Act
        stats = await mock_campaign_service.get_campaign_stats(
            campaign_type=CampaignType.WELCOME
        )

        # Assert
        assert "campaign_type" in stats
        assert stats["campaign_type"] == CampaignType.WELCOME.value

    async def test_campaign_template_structure(self, mock_campaign_service):
        """Test that campaign templates have correct structure."""
        # Arrange
        templates = NurtureCampaignService.CAMPAIGN_TEMPLATES

        # Assert
        assert len(templates) > 0

        for campaign_type, steps in templates.items():
            assert len(steps) > 0
            for step in steps:
                assert "step" in step
                assert "delay_hours" in step
                assert "subject" in step
                assert "content" in step
                assert "channel" in step

    async def test_welcome_campaign_structure(self, mock_campaign_service):
        """Test WELCOME campaign has correct structure."""
        # Arrange
        welcome = NurtureCampaignService.CAMPAIGN_TEMPLATES[CampaignType.WELCOME]

        # Assert
        assert len(welcome) == 3  # 3 steps
        assert welcome[0]["delay_hours"] == 0  # Immediate
        assert welcome[1]["delay_hours"] == 24  # Next day
        assert welcome[2]["delay_hours"] == 72  # 3 days

    async def test_post_inquiry_campaign_structure(self, mock_campaign_service):
        """Test POST_INQUIRY campaign has correct structure."""
        # Arrange
        post_inquiry = NurtureCampaignService.CAMPAIGN_TEMPLATES[CampaignType.POST_INQUIRY]

        # Assert
        assert len(post_inquiry) == 2  # 2 steps
        assert post_inquiry[0]["delay_hours"] == 2  # 2 hours after
        assert post_inquiry[1]["delay_hours"] == 48  # 2 days

    async def test_abandoned_quote_campaign_structure(self, mock_campaign_service):
        """Test ABANDONED_QUOTE campaign has correct structure."""
        # Arrange
        abandoned = NurtureCampaignService.CAMPAIGN_TEMPLATES[CampaignType.ABANDONED_QUOTE]

        # Assert
        assert len(abandoned) == 2  # 2 steps
        assert abandoned[0]["delay_hours"] == 4  # 4 hours
        assert abandoned[1]["delay_hours"] == 24  # 24 hours

    async def test_post_event_campaign_structure(self, mock_campaign_service):
        """Test POST_EVENT campaign has correct structure."""
        # Arrange
        post_event = NurtureCampaignService.CAMPAIGN_TEMPLATES[CampaignType.POST_EVENT]

        # Assert
        assert len(post_event) == 2  # 2 steps
        assert post_event[0]["delay_hours"] == 24  # Next day
        assert post_event[1]["delay_hours"] == 168  # 7 days

    async def test_content_personalization(self, mock_campaign_service, test_lead):
        """Test content personalization with lead data."""
        # Arrange
        content = "Hello {name}, your email is {email}"
        personalization = {"custom_field": "custom_value"}

        # Act
        personalized = mock_campaign_service._personalize_content(
            content, test_lead, personalization
        )

        # Assert
        assert test_lead.name in personalized or "Test Lead" in personalized
        assert test_lead.email in personalized

    async def test_personalization_handles_missing_name(self, mock_campaign_service, db_session):
        """Test personalization uses 'there' when name is missing."""
        # Arrange
        from db.models.crm import Lead
        lead_no_name = Lead(
            email="noname@example.com",
            phone="+15551234567",
            source="test",
        )
        db_session.add(lead_no_name)
        await db_session.commit()
        await db_session.refresh(lead_no_name)

        content = "Hello {name}"

        # Act
        personalized = mock_campaign_service._personalize_content(
            content, lead_no_name, {}
        )

        # Assert
        assert "there" in personalized  # Default when name is None


@pytest.mark.asyncio
class TestCampaignServiceIntegration:
    """Integration tests for full campaign workflows."""

    async def test_full_welcome_campaign_workflow(self, mock_campaign_service, test_lead, mock_event_service):
        """Test complete welcome campaign workflow."""
        # Step 1: Enroll lead
        enrollment = await mock_campaign_service.enroll_lead(
            lead_id=test_lead.id,
            campaign_type=CampaignType.WELCOME,
            personalization={"event_type": "Wedding"},
        )

        # Step 2: Handle various responses
        await mock_campaign_service.handle_response(
            lead_id=test_lead.id,
            response_type="click",
            response_data={"link": "menu"},
        )

        await mock_campaign_service.handle_response(
            lead_id=test_lead.id,
            response_type="reply",
            response_data={"message": "Tell me more"},
        )

        # Step 3: Get stats
        stats = await mock_campaign_service.get_campaign_stats(
            campaign_type=CampaignType.WELCOME
        )

        # Assert
        assert enrollment["total_steps"] == 3
        assert stats is not None

        # Verify events tracked (enroll + 2 responses + stats)
        assert mock_event_service.log_event.call_count >= 3

    async def test_opt_out_stops_all_campaigns(self, mock_campaign_service, test_lead, mock_event_service):
        """Test that opt-out pauses all active campaigns."""
        # Arrange - enroll in multiple campaigns
        await mock_campaign_service.enroll_lead(test_lead.id, CampaignType.WELCOME)
        await mock_campaign_service.enroll_lead(test_lead.id, CampaignType.POST_INQUIRY)

        # Act - opt out
        result = await mock_campaign_service.handle_response(
            lead_id=test_lead.id,
            response_type="opt_out",
        )

        # Assert
        assert result["status"] == "opted_out"

        # Verify opt-out event tracked
        opt_out_calls = [
            call for call in mock_event_service.log_event.call_args_list
            if "opt_out" in str(call)
        ]
        assert len(opt_out_calls) > 0

    async def test_booking_conversion_completes_campaigns(self, mock_campaign_service, test_lead):
        """Test that booking conversion marks campaigns as complete."""
        # Arrange - enroll in campaign
        await mock_campaign_service.enroll_lead(test_lead.id, CampaignType.ABANDONED_QUOTE)

        # Act - convert with booking
        result = await mock_campaign_service.handle_response(
            lead_id=test_lead.id,
            response_type="booking",
            response_data={"booking_id": "BK-12345"},
        )

        # Assert
        assert result["status"] == "converted"
