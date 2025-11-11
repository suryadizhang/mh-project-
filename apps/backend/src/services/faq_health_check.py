"""
FAQ Health Check & Error Detection System
Monitors FAQ sync between database and AI responses
"""

from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.faq_service import FAQService

logger = logging.getLogger(__name__)


class FAQHealthCheck:
    """
    Detects when FAQ updates fail to propagate to AI

    Use Cases:
    1. Verify FAQ data is being fetched from DB
    2. Alert if stale data is being used
    3. Validate pricing matches website
    """

    @staticmethod
    async def check_faq_freshness(db: AsyncSession) -> dict:
        """
        Check if FAQ data is fresh and being used correctly

        Returns:
            {
                "status": "healthy" | "warning" | "error",
                "last_update": datetime,
                "age_minutes": int,
                "is_stale": bool,
                "message": str
            }
        """
        faq_settings = await FAQService.get_active_faq_settings(db)

        if not faq_settings:
            return {
                "status": "error",
                "last_update": None,
                "age_minutes": None,
                "is_stale": True,
                "message": "⚠️ No active FAQ settings found! AI is using fallback data.",
            }

        # Calculate how old the data is
        now = datetime.utcnow()
        age = now - faq_settings.updated_at
        age_minutes = int(age.total_seconds() / 60)

        # Flag as stale if not updated in 7+ days
        is_stale = age > timedelta(days=7)

        if is_stale:
            return {
                "status": "warning",
                "last_update": faq_settings.updated_at,
                "age_minutes": age_minutes,
                "is_stale": True,
                "message": f"⚠️ FAQ data hasn't been updated in {age.days} days. Consider reviewing for accuracy.",
            }

        return {
            "status": "healthy",
            "last_update": faq_settings.updated_at,
            "age_minutes": age_minutes,
            "is_stale": False,
            "message": f"✅ FAQ data is fresh (last updated {age_minutes} minutes ago)",
        }

    @staticmethod
    async def validate_pricing_consistency(db: AsyncSession) -> dict:
        """
        Validate that pricing in FAQ matches expected business logic

        Checks:
        1. Adult price is set
        2. Child price is less than adult
        3. Deposit is $100
        4. Party minimum is $550

        Returns:
            {
                "valid": bool,
                "errors": list[str],
                "warnings": list[str]
            }
        """
        faq_data = await FAQService.get_faq_for_ai_prompt(db)

        errors = []
        warnings = []

        # Check deposit amount
        if faq_data["deposit_amount"] != 100:
            errors.append(f"Deposit should be $100, but is set to ${faq_data['deposit_amount']}")

        # Check pricing structure exists
        pricing = faq_data.get("pricing_info", {})

        if not pricing:
            errors.append("Pricing info is missing!")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check base pricing
        base_pricing = pricing.get("base_pricing", {})

        if not base_pricing:
            errors.append("Base pricing structure is missing!")
        else:
            adult_price = base_pricing.get("adult_13_plus", {}).get("price_per_person")
            child_price = base_pricing.get("child_6_to_12", {}).get("price_per_person")

            if not adult_price:
                errors.append("Adult pricing is missing!")
            elif adult_price != 55.0:
                warnings.append(f"Adult price is ${adult_price}, expected $55")

            if not child_price:
                errors.append("Child pricing is missing!")
            elif child_price != 30.0:
                warnings.append(f"Child price is ${child_price}, expected $30")

            if adult_price and child_price and child_price >= adult_price:
                errors.append("Child price should be less than adult price!")

        # Check party minimum
        party_min = pricing.get("party_minimum", {}).get("amount")
        if not party_min:
            errors.append("Party minimum is missing!")
        elif party_min != 550.0:
            warnings.append(f"Party minimum is ${party_min}, expected $550")

        # Check travel fee
        travel_fee = pricing.get("travel_fee", {})
        if not travel_fee.get("after_30_miles"):
            warnings.append("Travel fee pricing is missing")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    async def compare_faq_with_source(db: AsyncSession, source_data: dict) -> dict:
        """
        Compare FAQ database with source of truth (e.g., faqsData.ts)

        Args:
            source_data: Expected FAQ data from website/CMS

        Returns:
            {
                "matches": bool,
                "differences": list[str]
            }
        """
        faq_data = await FAQService.get_faq_for_ai_prompt(db)

        differences = []

        # Compare deposit
        if faq_data["deposit_amount"] != source_data.get("deposit_amount", 100):
            differences.append(
                f"Deposit: DB=${faq_data['deposit_amount']}, "
                f"Source=${source_data.get('deposit_amount')}"
            )

        # Compare adult pricing
        db_adult_price = faq_data["pricing_info"]["base_pricing"]["adult_13_plus"][
            "price_per_person"
        ]
        source_adult_price = source_data.get("adult_price", 55.0)

        if db_adult_price != source_adult_price:
            differences.append(f"Adult Price: DB=${db_adult_price}, Source=${source_adult_price}")

        # Compare service area
        if faq_data["service_area"] != source_data.get("service_area"):
            differences.append(
                f"Service Area: DB='{faq_data['service_area'][:50]}...', "
                f"Source='{source_data.get('service_area', '')[:50]}...'"
            )

        return {"matches": len(differences) == 0, "differences": differences}

    @staticmethod
    async def run_full_health_check(db: AsyncSession) -> dict:
        """
        Run all health checks and return comprehensive report

        Returns:
            {
                "overall_status": "healthy" | "warning" | "error",
                "freshness": {...},
                "pricing_validation": {...},
                "recommendations": list[str]
            }
        """
        freshness = await FAQHealthCheck.check_faq_freshness(db)
        pricing_validation = await FAQHealthCheck.validate_pricing_consistency(db)

        recommendations = []

        # Generate recommendations based on findings
        if freshness["is_stale"]:
            recommendations.append("Review and update FAQ data to ensure accuracy")

        if pricing_validation["errors"]:
            recommendations.append("Fix pricing errors immediately - AI may give incorrect quotes")

        if pricing_validation["warnings"]:
            recommendations.append("Review pricing warnings to ensure consistency with website")

        if (
            not pricing_validation["errors"]
            and not pricing_validation["warnings"]
            and not freshness["is_stale"]
        ):
            recommendations.append("All systems healthy! ✅")

        # Determine overall status
        if pricing_validation["errors"] or freshness["status"] == "error":
            overall_status = "error"
        elif pricing_validation["warnings"] or freshness["status"] == "warning":
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "freshness": freshness,
            "pricing_validation": pricing_validation,
            "recommendations": recommendations,
        }
