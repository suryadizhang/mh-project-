"""
Unit Tests for Distance Agent

Tests distance calculation, travel fee logic, and zone-based pricing.

Author: MH Backend Team
Created: 2025-11-26 (Phase 2A)
"""

import pytest
from unittest.mock import Mock, patch

from .distance_agent import DistanceAgent
from ..endpoints.services.pricing_service import PricingService


class TestDistanceAgent:
    """Test suite for Distance Agent"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def agent(self, mock_db):
        """Create Distance Agent instance"""
        return DistanceAgent(db=mock_db, station_id="test-station-123")

    def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_type == "distance"
        assert agent.temperature == 0.3  # Low for numerical accuracy
        assert agent.max_tokens == 400
        assert isinstance(agent.pricing_service, PricingService)

    def test_get_system_prompt(self, agent):
        """Test system prompt generation"""
        prompt = agent.get_system_prompt()

        # Check key elements in prompt
        assert "travel logistics specialist" in prompt.lower()
        assert "Google Maps" in prompt
        assert "30 miles" in prompt  # Free radius
        assert "$2.00 per mile" in prompt  # Per mile rate
        assert "150 miles" in prompt  # Max service radius
        assert "ONE-WAY distance only" in prompt  # Emphasize one-way calculation
        assert (
            "Fremont" in prompt or "our location" in prompt
        )  # Dynamic location (no hardcoded Sacramento)

    def test_get_tools(self, agent):
        """Test tool definitions"""
        tools = agent.get_tools()

        assert len(tools) == 3
        tool_names = [tool["function"]["name"] for tool in tools]

        assert "calculate_distance" in tool_names
        assert "check_service_area" in tool_names
        assert "get_zone_info" in tool_names

        # Verify calculate_distance tool structure
        calc_tool = next(t for t in tools if t["function"]["name"] == "calculate_distance")
        assert "destination" in calc_tool["function"]["parameters"]["properties"]
        assert "check_zone_pricing" in calc_tool["function"]["parameters"]["properties"]

    @pytest.mark.asyncio
    async def test_calculate_distance_success(self, agent):
        """Test successful distance calculation"""
        # Mock PricingService.calculate_travel_distance
        mock_result = {
            "status": "success",
            "distance_miles": 45.2,
            "distance_text": "45.2 miles",
            "drive_time": "55 min",
            "travel_fee": 30.40,  # (45.2 - 30) * 2.00
            "breakdown": {
                "total_distance": 45.2,
                "free_miles": 30,
                "billable_miles": 15.2,
                "rate_per_mile": 2.00,
            },
            "from": "Sacramento, CA",
            "to": "Folsom, CA 95630",
            "note": "First 30 miles are complimentary!",
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="calculate_distance",
                arguments={"destination": "Folsom, CA 95630"},
                context={"conversation_id": "test-123"},
            )

        assert result["success"] is True
        assert result["result"]["distance_miles"] == 45.2
        assert result["result"]["travel_fee"] == 30.40
        assert result["result"]["within_service_area"] is True  # 45.2 < 150

    @pytest.mark.asyncio
    async def test_calculate_distance_within_free_zone(self, agent):
        """Test distance within free 30-mile radius"""
        mock_result = {
            "status": "success",
            "distance_miles": 15.3,
            "distance_text": "15.3 miles",
            "drive_time": "20 min",
            "travel_fee": 0.00,  # Within 30 miles
            "breakdown": {
                "total_distance": 15.3,
                "free_miles": 30,
                "billable_miles": 0.0,
                "rate_per_mile": 2.00,
            },
            "from": "Sacramento, CA",
            "to": "Davis, CA 95616",
            "note": "First 30 miles are complimentary!",
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="calculate_distance",
                arguments={"destination": "Davis, CA"},
                context={},
            )

        assert result["success"] is True
        assert result["result"]["travel_fee"] == 0.00
        assert result["result"]["within_service_area"] is True

    @pytest.mark.asyncio
    async def test_calculate_distance_api_error(self, agent):
        """Test handling of Google Maps API errors"""
        mock_result = {
            "status": "api_error",
            "message": "Google Maps API is temporarily unavailable",
            "distance_miles": None,
            "travel_fee": None,
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="calculate_distance",
                arguments={"destination": "Test Address"},
                context={},
            )

        assert result["success"] is False
        assert "Google Maps API is temporarily unavailable" in result["error"]
        assert result["fallback_action"] == "suggest_phone_call"
        assert "note" in result  # Changed: No longer expects hardcoded phone number

    @pytest.mark.asyncio
    async def test_calculate_distance_beyond_service_area(self, agent):
        """Test location beyond 150-mile service radius"""
        mock_result = {
            "status": "success",
            "distance_miles": 175.8,  # Beyond 150-mile limit
            "distance_text": "175.8 miles",
            "drive_time": "3 hours",
            "travel_fee": 291.60,  # (175.8 - 30) * 2.00
            "breakdown": {
                "total_distance": 175.8,
                "free_miles": 30,
                "billable_miles": 145.8,
                "rate_per_mile": 2.00,
            },
            "from": "Sacramento, CA",
            "to": "Lake Tahoe, CA",
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="calculate_distance",
                arguments={"destination": "Lake Tahoe, CA"},
                context={},
            )

        assert result["success"] is True
        assert result["result"]["within_service_area"] is False  # 175.8 > 150

    @pytest.mark.asyncio
    async def test_check_service_area_within_range(self, agent):
        """Test service area validation for location within range"""
        mock_result = {
            "status": "success",
            "distance_miles": 82.5,
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="check_service_area",
                arguments={"destination": "Stockton, CA"},
                context={},
            )

        assert result["success"] is True
        assert result["result"]["within_service_area"] is True
        assert result["result"]["distance_miles"] == 82.5
        assert "within our service area" in result["result"]["message"].lower()

    @pytest.mark.asyncio
    async def test_check_service_area_out_of_range(self, agent):
        """Test service area validation for location beyond range"""
        mock_result = {
            "status": "success",
            "distance_miles": 200.0,  # Beyond 150-mile limit
        }

        with patch.object(
            agent.pricing_service, "calculate_travel_distance", return_value=mock_result
        ):
            result = await agent.process_tool_call(
                tool_name="check_service_area",
                arguments={"destination": "San Francisco, CA"},
                context={},
            )

        assert result["success"] is True
        assert result["result"]["within_service_area"] is False
        assert result["result"]["distance_miles"] == 200.0
        assert "beyond our" in result["result"]["message"].lower()
        # Changed: No longer expects hardcoded phone number - message says "call us"

    @pytest.mark.asyncio
    async def test_get_zone_info_no_database(self):
        """Test zone info when no database session available"""
        agent = DistanceAgent(db=None, station_id=None)

        result = await agent.process_tool_call(
            tool_name="get_zone_info",
            arguments={"zip_code": "95822"},
            context={},
        )

        assert result["success"] is True
        assert result["result"]["uses_default_pricing"] is True
        assert result["result"]["free_radius_miles"] == 30
        assert result["result"]["per_mile_fee"] == 2.00

    @pytest.mark.asyncio
    async def test_missing_destination(self, agent):
        """Test error handling for missing destination"""
        result = await agent.process_tool_call(
            tool_name="calculate_distance",
            arguments={},  # Missing destination
            context={},
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_tool(self, agent):
        """Test error handling for unknown tool name"""
        result = await agent.process_tool_call(
            tool_name="nonexistent_tool",
            arguments={},
            context={},
        )

        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_uses_pricing_service_not_hardcoded(self, agent):
        """
        CRITICAL: Verify agent uses PricingService (NO hardcoded values)

        Enterprise Requirement:
        - Agent MUST load pricing from database via PricingService
        - NO hardcoded $50, $2.00, or 30-mile values in agent code
        - Admin can adjust fees via UI → instant sync
        """
        # Verify PricingService is initialized
        assert agent.pricing_service is not None
        assert isinstance(agent.pricing_service, PricingService)

        # Verify agent has NO hardcoded pricing constants
        agent_code = open(__file__.replace("test_distance_agent.py", "distance_agent.py")).read()

        # These should NOT appear as hardcoded values in agent code
        # (They're OK in PricingService, but NOT in agent)
        assert "travel_fee = 50" not in agent_code.lower()
        assert "fee_per_mile = 2.00" not in agent_code.lower()
        assert "free_radius = 30" not in agent_code.lower()

        # Verify agent calls PricingService methods
        assert "self.pricing_service.calculate_travel_distance" in agent_code
        assert "TRAVEL_PRICING" in agent_code  # References PricingService config

    def test_integration_with_existing_system(self, agent):
        """
        CRITICAL: Verify integration with existing PricingService

        Enterprise Requirement:
        - Website & AI must use SAME PricingService
        - NO code duplication
        - Single source of truth for pricing
        """
        # Verify agent uses existing PricingService (not reimplemented)
        assert agent.pricing_service.__class__.__name__ == "PricingService"

        # Verify pricing config matches existing system
        assert agent.pricing_service.TRAVEL_PRICING["free_radius_miles"] == 30
        assert agent.pricing_service.TRAVEL_PRICING["per_mile_after"] == 2.00

        # Verify PricingService has calculate_travel_distance method (existing)
        assert hasattr(agent.pricing_service, "calculate_travel_distance")
        assert callable(agent.pricing_service.calculate_travel_distance)
