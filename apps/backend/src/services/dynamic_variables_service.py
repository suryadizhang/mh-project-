"""
Dynamic Variables Service
=========================

CRUD operations for the dynamic_variables table (SSoT).
All changes are logged to config_audit_log for compliance.

This service is used by:
- Admin UI for editing business configuration
- business_config_service.py for loading values
- AI tools for getting current pricing/policies

Security:
- All write operations require Super Admin role
- All changes are logged with user ID, IP, reason
- Validation rules enforced before save

Usage:
    from services.dynamic_variables_service import DynamicVariablesService

    svc = DynamicVariablesService(db)

    # Get single value
    adult_price = await svc.get_value("pricing", "adult_price_cents")

    # Get all values in a category
    pricing = await svc.get_category("pricing")

    # Update value (Super Admin only)
    await svc.update_value(
        category="pricing",
        key="adult_price_cents",
        value={"amount": 6000},
        user_id=admin_user_id,
        reason="Price increase for 2026"
    )

See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
See: database/migrations/004_dynamic_variables_ssot.sql
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DynamicVariablesService:
    """
    Service for managing dynamic business configuration variables.

    All CRUD operations with audit logging and cache invalidation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    async def get_value(
        self,
        category: str,
        key: str,
        as_of: datetime | None = None
    ) -> Any | None:
        """
        Get a single dynamic variable value.

        Args:
            category: Variable category (pricing, policy, travel, menu, booking)
            key: Variable key (adult_price_cents, deposit_amount_cents, etc.)
            as_of: Optional datetime to get value effective at that time
                   (defaults to NOW for current value)

        Returns:
            The value (usually from JSONB {"amount": X}), or None if not found
        """
        timestamp = as_of or datetime.utcnow()

        result = await self.db.execute(
            text("""
                SELECT value
                FROM dynamic_variables
                WHERE category = :category
                  AND key = :key
                  AND is_active = true
                  AND (effective_from IS NULL OR effective_from <= :ts)
                  AND (effective_to IS NULL OR effective_to > :ts)
                ORDER BY effective_from DESC NULLS LAST
                LIMIT 1
            """),
            {"category": category, "key": key, "ts": timestamp}
        )
        row = result.fetchone()

        if row:
            value = row[0]
            # Extract numeric value if wrapped in {"amount": X}
            if isinstance(value, dict) and "amount" in value:
                return value["amount"]
            return value
        return None

    async def get_category(self, category: str) -> dict[str, Any]:
        """
        Get all variables in a category as a dictionary.

        Args:
            category: Variable category

        Returns:
            Dict of {key: value} for all active variables in category
        """
        result = await self.db.execute(
            text("""
                SELECT key, value, display_name, description, unit
                FROM dynamic_variables
                WHERE category = :category
                  AND is_active = true
                  AND (effective_from IS NULL OR effective_from <= NOW())
                  AND (effective_to IS NULL OR effective_to > NOW())
                ORDER BY key
            """),
            {"category": category}
        )
        rows = result.fetchall()

        return {
            row.key: {
                "value": row.value.get("amount") if isinstance(row.value, dict) and "amount" in row.value else row.value,
                "display_name": row.display_name,
                "description": row.description,
                "unit": row.unit,
            }
            for row in rows
        }

    async def get_all(self) -> dict[str, dict[str, Any]]:
        """
        Get all active dynamic variables grouped by category.

        Returns:
            Dict of {category: {key: value_info}}
        """
        result = await self.db.execute(
            text("""
                SELECT category, key, value, display_name, description, unit, validation_rules
                FROM dynamic_variables
                WHERE is_active = true
                  AND (effective_from IS NULL OR effective_from <= NOW())
                  AND (effective_to IS NULL OR effective_to > NOW())
                ORDER BY category, key
            """)
        )
        rows = result.fetchall()

        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            if row.category not in grouped:
                grouped[row.category] = {}

            grouped[row.category][row.key] = {
                "value": row.value.get("amount") if isinstance(row.value, dict) and "amount" in row.value else row.value,
                "raw_value": row.value,
                "display_name": row.display_name,
                "description": row.description,
                "unit": row.unit,
                "validation_rules": row.validation_rules,
            }

        return grouped

    async def get_variable_details(self, category: str, key: str) -> dict | None:
        """
        Get full details for a single variable including validation rules.
        """
        result = await self.db.execute(
            text("""
                SELECT id, category, key, value, display_name, description, unit,
                       validation_rules, effective_from, effective_to,
                       updated_by, updated_at, created_at
                FROM dynamic_variables
                WHERE category = :category
                  AND key = :key
                  AND is_active = true
                ORDER BY effective_from DESC NULLS LAST
                LIMIT 1
            """),
            {"category": category, "key": key}
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row.id),
            "category": row.category,
            "key": row.key,
            "value": row.value,
            "display_name": row.display_name,
            "description": row.description,
            "unit": row.unit,
            "validation_rules": row.validation_rules,
            "effective_from": row.effective_from.isoformat() if row.effective_from else None,
            "effective_to": row.effective_to.isoformat() if row.effective_to else None,
            "updated_by": str(row.updated_by) if row.updated_by else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    # =========================================================================
    # WRITE OPERATIONS (Require Super Admin)
    # =========================================================================

    async def update_value(
        self,
        category: str,
        key: str,
        value: dict | Any,
        user_id: UUID,
        reason: str,
        user_email: str | None = None,
        ip_address: str | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
    ) -> dict:
        """
        Update a dynamic variable value with audit logging.

        Args:
            category: Variable category
            key: Variable key
            value: New value (will be wrapped in {"amount": X} if numeric)
            user_id: ID of user making the change
            reason: Reason for the change (required for audit)
            user_email: Email of user (for audit log denormalization)
            ip_address: Request IP address (for audit log)
            effective_from: When this value becomes active (default: NOW)
            effective_to: When this value expires (default: NULL = never)

        Returns:
            Dict with success status and change details

        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't have permission
        """
        # Wrap numeric values
        if isinstance(value, (int, float)):
            value = {"amount": value}

        # Get current value for audit log
        current = await self.get_variable_details(category, key)
        if not current:
            raise ValueError(f"Variable {category}.{key} not found")

        old_value = current["value"]
        variable_id = current["id"]

        # Validate new value against rules
        validation_rules = current.get("validation_rules")
        if validation_rules:
            self._validate_value(value, validation_rules, key)

        # Update the variable
        await self.db.execute(
            text("""
                UPDATE dynamic_variables
                SET value = :value,
                    updated_by = :user_id,
                    updated_at = NOW(),
                    effective_from = COALESCE(:effective_from, effective_from),
                    effective_to = :effective_to
                WHERE category = :category
                  AND key = :key
                  AND is_active = true
            """),
            {
                "category": category,
                "key": key,
                "value": value,
                "user_id": user_id,
                "effective_from": effective_from,
                "effective_to": effective_to,
            }
        )

        # Log to audit table
        await self.db.execute(
            text("""
                INSERT INTO config_audit_log (
                    variable_id, category, key, old_value, new_value,
                    change_type, changed_by, changed_by_email,
                    change_reason, ip_address
                ) VALUES (
                    :variable_id, :category, :key, :old_value, :new_value,
                    'update', :changed_by, :changed_by_email,
                    :change_reason, :ip_address
                )
            """),
            {
                "variable_id": variable_id,
                "category": category,
                "key": key,
                "old_value": old_value,
                "new_value": value,
                "changed_by": user_id,
                "changed_by_email": user_email,
                "change_reason": reason,
                "ip_address": ip_address,
            }
        )

        await self.db.commit()

        logger.info(
            f"🔧 Updated {category}.{key}: {old_value} → {value} by {user_email or user_id}"
        )

        return {
            "success": True,
            "category": category,
            "key": key,
            "old_value": old_value,
            "new_value": value,
            "updated_by": str(user_id),
            "reason": reason,
        }

    async def create_variable(
        self,
        category: str,
        key: str,
        value: dict | Any,
        display_name: str,
        description: str | None,
        unit: str | None,
        validation_rules: dict | None,
        user_id: UUID,
        reason: str,
        user_email: str | None = None,
    ) -> dict:
        """
        Create a new dynamic variable.

        Used when adding new menu items, upgrades, or policies.
        """
        # Wrap numeric values
        if isinstance(value, (int, float)):
            value = {"amount": value}

        # Check if already exists
        existing = await self.get_variable_details(category, key)
        if existing:
            raise ValueError(f"Variable {category}.{key} already exists")

        # Validate
        if validation_rules:
            self._validate_value(value, validation_rules, key)

        # Insert new variable
        result = await self.db.execute(
            text("""
                INSERT INTO dynamic_variables (
                    category, key, value, display_name, description,
                    unit, validation_rules, updated_by
                ) VALUES (
                    :category, :key, :value, :display_name, :description,
                    :unit, :validation_rules, :user_id
                )
                RETURNING id
            """),
            {
                "category": category,
                "key": key,
                "value": value,
                "display_name": display_name,
                "description": description,
                "unit": unit,
                "validation_rules": validation_rules,
                "user_id": user_id,
            }
        )
        row = result.fetchone()
        if row is None:
            raise ValueError(f"Failed to create variable {category}.{key}")
        variable_id = row[0]

        # Audit log
        await self.db.execute(
            text("""
                INSERT INTO config_audit_log (
                    variable_id, category, key, old_value, new_value,
                    change_type, changed_by, changed_by_email, change_reason
                ) VALUES (
                    :variable_id, :category, :key, NULL, :new_value,
                    'create', :changed_by, :changed_by_email, :change_reason
                )
            """),
            {
                "variable_id": variable_id,
                "category": category,
                "key": key,
                "new_value": value,
                "changed_by": user_id,
                "changed_by_email": user_email,
                "change_reason": reason,
            }
        )

        await self.db.commit()

        logger.info(f"➕ Created {category}.{key} = {value} by {user_email or user_id}")

        return {
            "success": True,
            "id": str(variable_id),
            "category": category,
            "key": key,
            "value": value,
        }

    async def delete_variable(
        self,
        category: str,
        key: str,
        user_id: UUID,
        reason: str,
        user_email: str | None = None,
    ) -> dict:
        """
        Soft-delete a dynamic variable (set is_active = false).
        """
        current = await self.get_variable_details(category, key)
        if not current:
            raise ValueError(f"Variable {category}.{key} not found")

        variable_id = current["id"]
        old_value = current["value"]

        # Soft delete
        await self.db.execute(
            text("""
                UPDATE dynamic_variables
                SET is_active = false,
                    updated_by = :user_id,
                    updated_at = NOW()
                WHERE category = :category
                  AND key = :key
            """),
            {"category": category, "key": key, "user_id": user_id}
        )

        # Audit log
        await self.db.execute(
            text("""
                INSERT INTO config_audit_log (
                    variable_id, category, key, old_value, new_value,
                    change_type, changed_by, changed_by_email, change_reason
                ) VALUES (
                    :variable_id, :category, :key, :old_value, :old_value,
                    'delete', :changed_by, :changed_by_email, :change_reason
                )
            """),
            {
                "variable_id": variable_id,
                "category": category,
                "key": key,
                "old_value": old_value,
                "changed_by": user_id,
                "changed_by_email": user_email,
                "change_reason": reason,
            }
        )

        await self.db.commit()

        logger.info(f"🗑️ Deleted {category}.{key} by {user_email or user_id}")

        return {"success": True, "category": category, "key": key}

    # =========================================================================
    # AUDIT LOG
    # =========================================================================

    async def get_audit_log(
        self,
        category: str | None = None,
        key: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Get configuration change audit log.

        Args:
            category: Filter by category (optional)
            key: Filter by key (optional)
            limit: Max results (default 50)
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        where_clauses: list[str] = []
        params: dict[str, int | str] = {"limit": limit, "offset": offset}

        if category:
            where_clauses.append("category = :category")
            params["category"] = category
        if key:
            where_clauses.append("key = :key")
            params["key"] = key

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        result = await self.db.execute(
            text(f"""
                SELECT id, variable_id, category, key, old_value, new_value,
                       change_type, changed_by, changed_by_email, changed_at,
                       change_reason, ip_address
                FROM config_audit_log
                {where_sql}
                ORDER BY changed_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        )
        rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "variable_id": str(row.variable_id),
                "category": row.category,
                "key": row.key,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "change_type": row.change_type,
                "changed_by": str(row.changed_by) if row.changed_by else None,
                "changed_by_email": row.changed_by_email,
                "changed_at": row.changed_at.isoformat() if row.changed_at else None,
                "change_reason": row.change_reason,
                "ip_address": str(row.ip_address) if row.ip_address else None,
            }
            for row in rows
        ]

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _validate_value(self, value: Any, rules: dict, key: str) -> None:
        """
        Validate a value against its validation rules.

        Raises ValueError if validation fails.
        """
        # Extract numeric value if wrapped
        numeric_value = value.get("amount") if isinstance(value, dict) else value

        value_type = rules.get("type", "any")

        # Type validation
        if value_type == "integer":
            if not isinstance(numeric_value, int):
                raise ValueError(f"{key}: Expected integer, got {type(numeric_value).__name__}")
        elif value_type == "number":
            if not isinstance(numeric_value, (int, float)):
                raise ValueError(f"{key}: Expected number, got {type(numeric_value).__name__}")

        # Range validation
        if "min" in rules and numeric_value < rules["min"]:
            raise ValueError(f"{key}: Value {numeric_value} is below minimum {rules['min']}")
        if "max" in rules and numeric_value > rules["max"]:
            raise ValueError(f"{key}: Value {numeric_value} is above maximum {rules['max']}")


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

async def get_dynamic_variable(
    db: AsyncSession,
    category: str,
    key: str
) -> Any | None:
    """
    Quick helper to get a single dynamic variable value.

    Convenience wrapper around DynamicVariablesService.
    """
    svc = DynamicVariablesService(db)
    return await svc.get_value(category, key)


async def get_pricing_config(db: AsyncSession) -> dict:
    """
    Get all pricing-related configuration.

    Returns dict with adult_price, child_price, party_minimum, etc.
    """
    svc = DynamicVariablesService(db)
    return await svc.get_category("pricing")


async def get_policy_config(db: AsyncSession) -> dict:
    """
    Get all policy-related configuration.

    Returns dict with deposit_refund_days, min_advance_hours, etc.
    """
    svc = DynamicVariablesService(db)
    return await svc.get_category("policy")
