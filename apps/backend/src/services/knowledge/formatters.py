"""
Formatters Module

Formats knowledge base data for AI context injection.
Provides markdown and structured text formatters.

Created: 2025-11-12
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class KnowledgeFormatters:
    """Static methods for formatting knowledge for AI"""

    @staticmethod
    def format_menu_summary(
        menu: Dict[str, List[Dict[str, Any]]], tiers: List[Dict[str, Any]]
    ) -> str:
        """
        Format menu and pricing for AI context

        Args:
            menu: Menu items organized by category
            tiers: Pricing tiers

        Returns:
            Markdown-formatted menu summary
        """
        try:
            summary = "# MENU & PRICING\n\n"

            # Pricing tiers
            summary += "## Pricing Packages\n\n"
            for tier in tiers:
                popular = " ⭐ MOST POPULAR" if tier.get("is_popular") else ""
                summary += f"### {tier['name']}{popular}\n"
                summary += (
                    f"- **${tier['price_per_person']}/person** (min {tier['min_guests']} guests)\n"
                )
                summary += f"- {tier['description']}\n"
                if tier.get("features"):
                    summary += "- Includes:\n"
                    for feature in tier["features"]:
                        summary += f"  - {feature}\n"
                summary += "\n"

            # Menu items by category
            summary += "## Menu Options\n\n"

            category_names = {
                "poultry": "🍗 Poultry",
                "beef": "🥩 Beef",
                "seafood": "🦐 Seafood",
                "specialty": "🌱 Specialty",
                "sides": "🍚 Sides",
                "appetizers": "🥢 Appetizers",
                "desserts": "🍰 Desserts",
            }

            for category, items in menu.items():
                summary += f"### {category_names.get(category, category.title())}\n\n"
                for item in items:
                    premium = " 💎" if item.get("is_premium") else ""
                    price = f" (+${item['base_price']})" if item.get("base_price") else ""
                    summary += f"- **{item['name']}**{premium}{price}"
                    if item.get("description"):
                        summary += f" - {item['description']}"
                    if item.get("dietary_info"):
                        summary += f" [{', '.join(item['dietary_info'])}]"
                    summary += "\n"
                summary += "\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting menu summary: {e}")
            return "# MENU & PRICING\n\n(Unable to load menu data)"

    @staticmethod
    def format_business_charter(charter: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format business charter for AI context

        Args:
            charter: Business rules organized by category

        Returns:
            Markdown-formatted business charter
        """
        try:
            summary = "# BUSINESS CHARTER\n\n"

            category_icons = {
                "booking": "📅",
                "payment": "💳",
                "cancellation": "🔄",
                "service": "🍽️",
                "terms": "📋",
                "policies": "📜",
                "communication": "💬",
            }

            for category, rules in charter.items():
                icon = category_icons.get(category.lower(), "📌")
                summary += f"## {icon} {category.replace('_', ' ').title()}\n\n"

                for rule in rules:
                    summary += f"### {rule['name']}\n"
                    if rule.get("summary"):
                        summary += f"*{rule['summary']}*\n\n"
                    summary += f"{rule['content']}\n\n"
                    if rule.get("keywords"):
                        summary += f"**Keywords:** {', '.join(rule['keywords'])}\n\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting business charter: {e}")
            return "# BUSINESS CHARTER\n\n(Unable to load business rules)"

    @staticmethod
    def format_faqs(faqs: List[Dict[str, Any]], limit: int = 20) -> str:
        """
        Format FAQs for AI context

        Args:
            faqs: List of FAQ items
            limit: Maximum FAQs to include

        Returns:
            Markdown-formatted FAQ list
        """
        try:
            summary = "# FREQUENTLY ASKED QUESTIONS\n\n"

            current_category = None
            count = 0

            for faq in faqs[:limit]:
                if count >= limit:
                    break

                # Add category header
                if faq.get("category") != current_category:
                    current_category = faq["category"]
                    summary += f"## {current_category}\n\n"

                summary += f"**Q: {faq['question']}**\n"
                summary += f"A: {faq['answer']}\n\n"

                count += 1

            if len(faqs) > limit:
                summary += f"*...and {len(faqs) - limit} more FAQs available*\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting FAQs: {e}")
            return "# FREQUENTLY ASKED QUESTIONS\n\n(Unable to load FAQs)"

    @staticmethod
    def format_upsell_suggestions(suggestions: List[Dict[str, Any]]) -> str:
        """
        Format upsell suggestions for AI

        Args:
            suggestions: List of upsell items

        Returns:
            Formatted suggestion text
        """
        try:
            if not suggestions:
                return ""

            text = "**RELEVANT UPSELL OPPORTUNITIES:**\n\n"

            for suggestion in suggestions:
                text += f"• **{suggestion['item']}**"
                if suggestion.get("price"):
                    text += f" (${suggestion['price']})"
                text += f"\n  {suggestion['description']}\n"
                if suggestion.get("success_rate"):
                    text += f"  Success rate: {suggestion['success_rate']}%\n"
                text += "\n"

            return text

        except Exception as e:
            logger.error(f"Error formatting upsell suggestions: {e}")
            return ""
