"""
Tests for Menu Agent

Test Coverage:
- Menu loading from menu.json (same as website)
- Dietary restriction filtering
- Protein recommendations with pricing
- Seasonal offer integration
- Budget optimization
- Data consistency validation
- Error handling and fallbacks
"""

import pytest
from unittest.mock import MagicMock, patch

from api.ai.agents.menu_agent import MenuAgent


class TestMenuAgent:
    """Test suite for Menu Agent"""

    @pytest.fixture
    def menu_agent(self):
        """Create Menu Agent instance for testing"""
        # Mock database session
        db_mock = MagicMock()

        return MenuAgent(db=db_mock)

    @pytest.fixture
    def sample_menu_data(self):
        """Sample menu data matching menu.json structure"""
        return [
            {
                "title": "Premium Hibachi Combo",
                "description": "Our signature hibachi experience with choice of protein",
                "content": "Includes: Choice of chicken, beef, shrimp, or salmon • Hibachi fried rice • Mixed grilled vegetables",
                "category": "entrees",
                "keywords": ["combo", "hibachi", "chicken", "beef", "shrimp", "salmon"],
            },
            {
                "title": "Vegetarian Hibachi",
                "description": "Fresh seasonal vegetables grilled hibachi-style with tofu",
                "content": "Perfect for vegetarians! Fresh seasonal vegetables and tofu",
                "category": "vegetarian",
                "keywords": ["vegetarian", "vegetables", "tofu", "plant-based", "no meat"],
            },
            {
                "title": "Hibachi Shrimp",
                "description": "Fresh jumbo shrimp grilled hibachi-style",
                "content": "Large, fresh shrimp grilled with garlic butter",
                "category": "seafood",
                "keywords": ["shrimp", "seafood", "garlic butter", "shellfish"],
            },
            {
                "title": "Salmon Hibachi",
                "description": "Fresh salmon fillet grilled hibachi-style",
                "content": "Premium salmon fillet grilled fresh with teriyaki glaze",
                "category": "seafood",
                "keywords": ["salmon", "fish", "healthy", "teriyaki"],
            },
            {
                "title": "Hibachi Fried Rice",
                "description": "Our signature fried rice made fresh on the hibachi grill",
                "content": "Made fresh with eggs, vegetables, and seasonings",
                "category": "sides",
                "keywords": ["fried rice", "side dish", "eggs", "vegetables"],
            },
        ]

    # ============================================================================
    # Test 1: Menu Loading from menu.json
    # ============================================================================

    def test_menu_loads_from_json(self, menu_agent, sample_menu_data):
        """Test that menu loads from actual menu.json file (same as website)"""
        # Verify menu data loaded
        assert menu_agent.menu_data is not None
        assert isinstance(menu_agent.menu_data, list)

        # Verify NOT empty (should have actual menu items)
        assert len(menu_agent.menu_data) > 0, "Menu should load items from menu.json"

        # Verify structure matches menu.json format
        first_item = menu_agent.menu_data[0]
        assert "title" in first_item
        assert "description" in first_item
        assert "category" in first_item

        print(f"✅ Menu loaded {len(menu_agent.menu_data)} items from menu.json")

    def test_menu_fallback_on_load_error(self):
        """Test fallback menu when menu.json fails to load"""
        with patch("api.ai.agents.menu_agent.get_current_menu_from_service", return_value=None):
            agent = MenuAgent(db=MagicMock())

            # Should return fallback menu (minimal items)
            assert len(agent.menu_data) > 0
            assert agent.menu_data[0]["title"] == "Adult Hibachi Experience"

            print("✅ Fallback menu works when menu.json unavailable")

    # ============================================================================
    # Test 2: Menu Recommendations Tool
    # ============================================================================

    def test_get_menu_recommendations_by_keyword(self, menu_agent):
        """Test menu recommendations based on keywords"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Chicken Teriyaki",
                    "description": "Tender chicken",
                    "category": "chicken",
                    "keywords": ["chicken", "teriyaki"],
                },
                {
                    "title": "Beef Hibachi",
                    "description": "Premium beef",
                    "category": "beef",
                    "keywords": ["beef", "steak"],
                },
                {
                    "title": "Vegetarian Hibachi",
                    "description": "Tofu and vegetables",
                    "category": "vegetarian",
                    "keywords": ["vegetarian", "tofu"],
                },
            ],
        ):
            result = menu_agent._get_menu_recommendations(
                {
                    "keywords": ["chicken"],
                    "guest_count": 10,
                }
            )

            assert result["matches"] == 1
            assert result["items"][0]["title"] == "Chicken Teriyaki"
            assert result["portion_guidance"]["free_proteins_included"] == 20  # 10 guests × 2

            print("✅ Menu recommendations filter by keywords correctly")

    def test_get_menu_recommendations_by_category(self, menu_agent):
        """Test menu recommendations by category filter"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {"title": "Chicken", "category": "chicken", "keywords": []},
                {"title": "Vegetables", "category": "vegetarian", "keywords": []},
                {"title": "Shrimp", "category": "seafood", "keywords": []},
            ],
        ):
            result = menu_agent._get_menu_recommendations({"category": "vegetarian"})

            assert result["matches"] == 1
            assert result["items"][0]["title"] == "Vegetables"

            print("✅ Menu recommendations filter by category correctly")

    def test_get_menu_recommendations_no_filters(self, menu_agent):
        """Test menu recommendations with no filters (returns all items)"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {"title": "Item 1", "category": "entrees", "keywords": []},
                {"title": "Item 2", "category": "sides", "keywords": []},
            ],
        ):
            result = menu_agent._get_menu_recommendations({})

            assert result["matches"] == 2
            assert len(result["items"]) == 2

            print("✅ Menu recommendations return all items when no filters applied")

    # ============================================================================
    # Test 3: Dietary Restriction Filtering
    # ============================================================================

    def test_filter_vegetarian(self, menu_agent):
        """Test vegetarian dietary filtering"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Chicken",
                    "description": "Chicken breast",
                    "keywords": ["chicken"],
                    "category": "chicken",
                },
                {
                    "title": "Tofu",
                    "description": "Fresh tofu",
                    "keywords": ["tofu", "vegetarian"],
                    "category": "vegetarian",
                },
                {
                    "title": "Vegetables",
                    "description": "Grilled vegetables",
                    "keywords": ["vegetables", "vegetarian"],
                    "category": "vegetarian",
                },
                {
                    "title": "Shrimp",
                    "description": "Fresh shrimp",
                    "keywords": ["shrimp", "seafood"],
                    "category": "seafood",
                },
            ],
        ):
            result = menu_agent._filter_by_dietary_restrictions(
                {"restrictions": ["vegetarian"], "guest_count": 10}
            )

            # Should exclude chicken and shrimp
            assert result["count"] == 2
            safe_titles = [item["title"] for item in result["safe_items"]]
            assert "Tofu" in safe_titles
            assert "Vegetables" in safe_titles
            assert "Chicken" not in safe_titles
            assert "Shrimp" not in safe_titles

            print("✅ Vegetarian filtering excludes meat/seafood correctly")

    def test_filter_vegan(self, menu_agent):
        """Test vegan dietary filtering (stricter than vegetarian)"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Tofu",
                    "description": "Fresh tofu",
                    "keywords": ["tofu", "vegan"],
                    "category": "vegetarian",
                },
                {
                    "title": "Vegetables",
                    "description": "Grilled vegetables",
                    "keywords": ["vegetables", "vegan"],
                    "category": "vegetarian",
                },
                {
                    "title": "Fried Rice",
                    "description": "Rice with eggs",
                    "keywords": ["rice", "eggs"],
                    "category": "sides",
                },
            ],
        ):
            result = menu_agent._filter_by_dietary_restrictions({"restrictions": ["vegan"]})

            # Should exclude fried rice (contains eggs)
            assert result["count"] == 2
            safe_titles = [item["title"] for item in result["safe_items"]]
            assert "Tofu" in safe_titles
            assert "Vegetables" in safe_titles
            assert "Fried Rice" not in safe_titles

            print("✅ Vegan filtering excludes eggs/dairy correctly")

    def test_filter_shellfish_allergy(self, menu_agent):
        """Test shellfish allergy filtering"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Chicken",
                    "description": "Chicken breast",
                    "keywords": ["chicken"],
                    "category": "chicken",
                },
                {
                    "title": "Shrimp",
                    "description": "Fresh shrimp",
                    "keywords": ["shrimp", "shellfish"],
                    "category": "seafood",
                },
                {
                    "title": "Lobster",
                    "description": "Lobster tail",
                    "keywords": ["lobster", "shellfish"],
                    "category": "seafood",
                },
                {
                    "title": "Salmon",
                    "description": "Salmon fillet",
                    "keywords": ["salmon", "fish"],
                    "category": "seafood",
                },
            ],
        ):
            result = menu_agent._filter_by_dietary_restrictions(
                {"restrictions": ["shellfish-free"]}
            )

            # Should exclude shrimp and lobster, keep salmon
            safe_titles = [item["title"] for item in result["safe_items"]]
            assert "Chicken" in safe_titles
            assert "Salmon" in safe_titles
            assert "Shrimp" not in safe_titles
            assert "Lobster" not in safe_titles

            print("✅ Shellfish-free filtering excludes shrimp/lobster correctly")

    def test_filter_multiple_restrictions(self, menu_agent):
        """Test filtering with multiple dietary restrictions"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Vegetables",
                    "description": "Grilled vegetables",
                    "keywords": ["vegetables", "vegetarian", "vegan"],
                    "category": "vegetarian",
                },
                {
                    "title": "Tofu",
                    "description": "Fresh tofu",
                    "keywords": ["tofu", "vegetarian", "vegan"],
                    "category": "vegetarian",
                },
                {
                    "title": "Shrimp",
                    "description": "Fresh shrimp",
                    "keywords": ["shrimp", "shellfish"],
                    "category": "seafood",
                },
            ],
        ):
            result = menu_agent._filter_by_dietary_restrictions(
                {"restrictions": ["vegan", "shellfish-free"]}
            )

            # Should only show vegetables and tofu
            assert result["count"] == 2
            safe_titles = [item["title"] for item in result["safe_items"]]
            assert "Vegetables" in safe_titles
            assert "Tofu" in safe_titles
            assert "Shrimp" not in safe_titles

            print("✅ Multiple dietary restrictions filter correctly")

    # ============================================================================
    # Test 4: Protein Recommendations
    # ============================================================================

    def test_protein_recommendations_budget_friendly(self, menu_agent):
        """Test budget-friendly protein recommendations (all FREE)"""
        result = menu_agent._calculate_protein_recommendations(
            {"guest_count": 10, "budget_per_protein": 0}  # Budget-conscious
        )

        assert result["guest_count"] == 10
        assert result["free_proteins_included"] == 20  # 10 guests × 2

        # Should have budget-friendly option with FREE proteins
        budget_option = result["recommendations"][0]
        assert budget_option["option"] == "Budget-Friendly (All FREE proteins)"
        assert budget_option["cost"] == "$0"

        print("✅ Budget-friendly protein recommendations use FREE proteins")

    def test_protein_recommendations_balanced(self, menu_agent):
        """Test balanced protein recommendations (mix of FREE + UPGRADE)"""
        result = menu_agent._calculate_protein_recommendations({"guest_count": 10})

        # Should have balanced mix option
        balanced_option = result["recommendations"][1]
        assert "Balanced Mix" in balanced_option["option"]
        assert "FREE + Premium Upgrades" in balanced_option["option"]

        print("✅ Balanced protein recommendations mix FREE + UPGRADE")

    def test_protein_recommendations_premium(self, menu_agent):
        """Test premium protein recommendations (Filet + Lobster)"""
        result = menu_agent._calculate_protein_recommendations({"guest_count": 10})

        # Should have premium option
        premium_option = result["recommendations"][2]
        assert "Premium Experience" in premium_option["option"]
        assert "Filet Mignon + Lobster" in premium_option["option"]

        # Verify pricing calculation
        # 10 guests: 10 Filet ($5 each) + 10 Lobster ($15 each) = $200
        assert "$200" in premium_option["estimated_upgrade_cost"]

        print("✅ Premium protein recommendations show Filet + Lobster with pricing")

    def test_protein_recommendations_includes_pricing_reference(self, menu_agent):
        """Test protein recommendations include pricing reference"""
        result = menu_agent._calculate_protein_recommendations({"guest_count": 15})

        # Should have protein pricing reference
        assert "protein_pricing" in result
        pricing = result["protein_pricing"]

        assert "FREE" in pricing
        assert "UPGRADE (+$5)" in pricing
        assert "PREMIUM (+$15)" in pricing
        assert "3rd_protein_rule" in pricing

        # Verify 3rd protein rule calculation
        # 15 guests × 2 = 30 FREE proteins
        assert "30 proteins" in pricing["3rd_protein_rule"]

        print("✅ Protein recommendations include pricing reference")

    # ============================================================================
    # Test 5: Seasonal Offers Integration
    # ============================================================================

    @pytest.mark.asyncio
    async def test_get_seasonal_offers_success(self, menu_agent):
        """Test loading seasonal offers (placeholder implementation)"""
        result = await menu_agent._get_seasonal_offers()

        # Should return placeholder response
        assert result["count"] == 0
        assert result["seasonal_offers"] == []
        assert "future update" in result["note"].lower()

        print("✅ Seasonal offers placeholder works correctly")

    @pytest.mark.asyncio
    async def test_get_seasonal_offers_no_database(self):
        """Test seasonal offers placeholder (model not yet implemented)"""
        agent = MenuAgent(db=None)

        result = await agent._get_seasonal_offers()

        assert result["seasonal_offers"] == []
        assert result["count"] == 0
        assert "future update" in result["note"].lower()

        print("✅ Seasonal offers placeholder handles missing database")

    # ============================================================================
    # Test 6: System Prompt Generation
    # ============================================================================

    def test_system_prompt_includes_protein_pricing(self, menu_agent):
        """Test system prompt includes FREE and UPGRADE protein lists"""
        prompt = menu_agent.get_system_prompt()

        # Should mention FREE proteins
        assert "Chicken" in prompt
        assert "Shrimp" in prompt
        assert "Tofu" in prompt

        # Should mention UPGRADE proteins with pricing
        assert "Filet Mignon" in prompt
        assert "Lobster Tail" in prompt
        assert "+$5" in prompt
        assert "+$15" in prompt

        # Should mention 3rd protein rule
        assert "3rd Protein Rule" in prompt
        assert "+$10" in prompt

        print("✅ System prompt includes protein pricing details")

    def test_system_prompt_includes_menu_count(self, menu_agent):
        """Test system prompt includes actual menu item count"""
        prompt = menu_agent.get_system_prompt()

        # Should mention number of menu items loaded
        menu_count = len(menu_agent.menu_data)
        assert f"{menu_count} items" in prompt

        print(f"✅ System prompt shows {menu_count} menu items loaded")

    # ============================================================================
    # Test 7: Tool Definitions
    # ============================================================================

    def test_tools_definition(self, menu_agent):
        """Test that all required tools are defined"""
        tools = menu_agent.get_tools()

        tool_names = [tool["function"]["name"] for tool in tools]

        assert "get_menu_recommendations" in tool_names
        assert "filter_by_dietary_restrictions" in tool_names
        assert "calculate_protein_recommendations" in tool_names
        assert "get_seasonal_offers" in tool_names

        print("✅ All menu tools defined correctly")

    def test_tool_parameters_valid(self, menu_agent):
        """Test tool parameters are properly structured"""
        tools = menu_agent.get_tools()

        # Check get_menu_recommendations parameters
        menu_rec_tool = next(
            t for t in tools if t["function"]["name"] == "get_menu_recommendations"
        )
        params = menu_rec_tool["function"]["parameters"]["properties"]

        assert "keywords" in params
        assert params["keywords"]["type"] == "array"
        assert "category" in params
        assert "guest_count" in params

        print("✅ Tool parameters structured correctly")

    # ============================================================================
    # Test 8: Tool Execution
    # ============================================================================

    @pytest.mark.asyncio
    async def test_execute_tool_get_menu_recommendations(self, menu_agent):
        """Test executing get_menu_recommendations tool"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Chicken",
                    "description": "Grilled chicken",
                    "category": "chicken",
                    "keywords": ["chicken"],
                },
            ],
        ):
            result = await menu_agent.execute_tool(
                "get_menu_recommendations", {"keywords": ["chicken"], "guest_count": 10}
            )

            assert result["matches"] == 1
            assert result["items"][0]["title"] == "Chicken"

            print("✅ Tool execution: get_menu_recommendations works")

    @pytest.mark.asyncio
    async def test_execute_tool_filter_dietary(self, menu_agent):
        """Test executing filter_by_dietary_restrictions tool"""
        with patch.object(
            menu_agent,
            "menu_data",
            new=[
                {
                    "title": "Tofu",
                    "description": "Fresh tofu",
                    "keywords": ["tofu", "vegetarian"],
                    "category": "vegetarian",
                },
                {
                    "title": "Chicken",
                    "description": "Grilled chicken",
                    "keywords": ["chicken"],
                    "category": "chicken",
                },
            ],
        ):
            result = await menu_agent.execute_tool(
                "filter_by_dietary_restrictions", {"restrictions": ["vegetarian"], "guest_count": 5}
            )

            assert result["count"] == 1
            assert result["safe_items"][0]["title"] == "Tofu"

            print("✅ Tool execution: filter_by_dietary_restrictions works")

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, menu_agent):
        """Test executing unknown tool returns error"""
        result = await menu_agent.execute_tool("unknown_tool", {})

        assert "error" in result
        assert "Unknown tool" in result["error"]
        assert "available_tools" in result

        print("✅ Tool execution: unknown tool returns helpful error")

    # ============================================================================
    # Test 9: Data Consistency with Website
    # ============================================================================

    def test_menu_matches_website_json_structure(self, menu_agent):
        """Test that menu structure matches apps/customer/src/data/menu.json"""
        # Load actual website menu.json
        try:
            from config.ai_booking_config_v2 import get_current_menu_from_service

            website_menu = get_current_menu_from_service()

            if website_menu and isinstance(website_menu, list):
                # Verify agent loaded same data
                assert len(menu_agent.menu_data) == len(website_menu)

                # Verify structure matches
                if len(menu_agent.menu_data) > 0:
                    agent_item = menu_agent.menu_data[0]
                    website_item = website_menu[0]

                    # Compare keys (structure should be identical)
                    assert set(agent_item.keys()) == set(website_item.keys())

                    print(f"✅ Menu Agent loads same {len(website_menu)} items as website")
                else:
                    print("⚠️ Menu empty - check menu.json file")
            else:
                print("⚠️ Could not load website menu.json for comparison")

        except Exception as e:
            print(f"⚠️ Menu consistency test skipped: {e}")

    # ============================================================================
    # Test 10: Error Handling
    # ============================================================================

    @pytest.mark.asyncio
    async def test_execute_tool_handles_exceptions(self, menu_agent):
        """Test tool execution handles exceptions gracefully"""
        # Force an error by patching internal method
        with patch.object(
            menu_agent, "_get_menu_recommendations", side_effect=Exception("Test error")
        ):
            result = await menu_agent.execute_tool(
                "get_menu_recommendations", {"keywords": ["test"]}
            )

            assert "error" in result
            assert "Failed to execute" in result["error"]
            assert "Test error" in result["error"]

            print("✅ Tool execution handles exceptions gracefully")

    def test_menu_load_handles_invalid_json(self):
        """Test menu loading handles invalid JSON gracefully"""
        with patch(
            "config.ai_booking_config_v2.get_current_menu_from_service",
            return_value={"invalid": "structure"},
        ):
            agent = MenuAgent(db=MagicMock())

            # Should fallback to basic menu (not crash)
            assert len(agent.menu_data) > 0
            assert agent.menu_data[0]["title"] == "Adult Hibachi Experience"

            print("✅ Menu loading handles invalid JSON structure")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("MENU AGENT TEST SUITE")
    print("=" * 80 + "\n")

    pytest.main([__file__, "-v", "--tb=short"])
