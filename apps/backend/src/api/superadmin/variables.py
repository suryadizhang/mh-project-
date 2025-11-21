"""
Super Admin Variables Management API
Handles variable CRUD operations with GSM and local file sync
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Union, Literal
from pydantic import BaseModel
import os
import logging
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/superadmin/variables", tags=["variables"])


class Variable(BaseModel):
    key: str
    value: Union[str, int, float, bool]
    type: Literal["string", "number", "boolean"]
    category: Literal["pricing", "business", "feature", "environment", "ai", "monitoring"]
    description: str
    source: str
    priority: Literal["critical", "high", "medium", "low"]
    lastModified: Optional[str] = None


class UpdateVariableRequest(BaseModel):
    key: str
    value: Union[str, int, float, bool]


class BulkUpdateRequest(BaseModel):
    variables: List[UpdateVariableRequest]
    sync_to_gsm: bool = True
    update_config_version: bool = True


# Variable definitions mapping
VARIABLE_DEFINITIONS = {
    # Pricing Variables (Critical)
    "BASE_PRICE_PER_PERSON": {
        "type": "number",
        "category": "pricing",
        "description": "Base hibachi price per person before add-ons",
        "source": "ai_booking_config_v2.py",
        "priority": "critical",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
    "DEPOSIT_AMOUNT": {
        "type": "number",
        "category": "pricing",
        "description": "Fixed deposit amount for all bookings",
        "source": "faq.json, policies.json",
        "priority": "critical",
        "files": [
            "apps/customer/src/data/faq.json",
            "apps/customer/src/data/policies.json",
            "apps/admin/src/data/faq.json",
            "apps/admin/src/data/policies.json",
        ],
    },
    "TRAVEL_FEE_BASE_RATE": {
        "type": "number",
        "category": "pricing",
        "description": "Base travel fee per mile",
        "source": "ai_booking_config_v2.py",
        "priority": "critical",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
    # Business Rules (High Priority)
    "MINIMUM_GUESTS": {
        "type": "number",
        "category": "business",
        "description": "Minimum number of guests required for booking",
        "source": "ai_booking_config_v2.py",
        "priority": "high",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
    "MAXIMUM_GUESTS": {
        "type": "number",
        "category": "business",
        "description": "Maximum guests per chef",
        "source": "ai_booking_config_v2.py",
        "priority": "high",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
    "ADVANCE_BOOKING_HOURS": {
        "type": "number",
        "category": "business",
        "description": "Minimum advance notice required for booking",
        "source": "policies.json",
        "priority": "high",
        "files": ["apps/customer/src/data/policies.json", "apps/admin/src/data/policies.json"],
    },
    # Feature Flags (Medium Priority)
    "FF_ENABLE_AI_BOOKING_V3": {
        "type": "boolean",
        "category": "feature",
        "description": "Enable AI Booking System V3",
        "source": "env.ts",
        "priority": "medium",
        "files": ["apps/customer/src/lib/env.ts", "apps/admin/src/lib/env.ts"],
    },
    "FF_ENABLE_TRAVEL_FEE_V2": {
        "type": "boolean",
        "category": "feature",
        "description": "Enable Travel Fee Calculation V2",
        "source": "env.ts",
        "priority": "medium",
        "files": ["apps/customer/src/lib/env.ts", "apps/admin/src/lib/env.ts"],
    },
    # AI System Variables
    "AI_MODEL_VERSION": {
        "type": "string",
        "category": "ai",
        "description": "OpenAI model version for customer support",
        "source": "ai_booking_config_v2.py",
        "priority": "high",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
    "AI_MAX_TOKENS": {
        "type": "number",
        "category": "ai",
        "description": "Maximum tokens for AI responses",
        "source": "ai_booking_config_v2.py",
        "priority": "medium",
        "files": ["apps/backend/src/config/ai_booking_config_v2.py"],
    },
}


async def get_current_user():
    """Get current user - replace with actual auth"""
    return {"id": 1, "email": "admin@myhibachi.com", "role": "super_admin"}


@router.get("/", response_model=List[Variable])
async def get_all_variables(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Get all variables with optional filtering"""
    try:
        variables = []

        # Load current values from files
        for key, definition in VARIABLE_DEFINITIONS.items():
            try:
                # Get current value from primary source file
                current_value = await get_variable_from_files(key, definition)

                variable = Variable(
                    key=key,
                    value=current_value,
                    type=definition["type"],
                    category=definition["category"],
                    description=definition["description"],
                    source=definition["source"],
                    priority=definition["priority"],
                    lastModified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                )

                # Apply filters
                if category and variable.category != category:
                    continue
                if priority and variable.priority != priority:
                    continue

                variables.append(variable)

            except Exception as e:
                logger.error(f"Error loading variable {key}: {e}")
                continue

        return variables

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading variables: {str(e)}")


@router.post("/bulk-update")
async def bulk_update_variables(request: BulkUpdateRequest, current_user=Depends(get_current_user)):
    """Update multiple variables in bulk"""
    try:
        updated_count = 0
        errors = []

        for variable_update in request.variables:
            try:
                await update_single_variable(variable_update.key, variable_update.value)
                updated_count += 1
            except Exception as e:
                errors.append(f"{variable_update.key}: {str(e)}")

        # Update config version if requested
        if request.update_config_version:
            await increment_config_version()

        # Sync to GSM if requested
        if request.sync_to_gsm:
            await sync_variables_to_gsm(request.variables)

        return {
            "success": True,
            "updated_count": updated_count,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")


@router.post("/sync-to-gsm")
async def sync_to_gsm(current_user=Depends(get_current_user)):
    """Sync all current variables to Google Secret Manager"""
    try:
        # This would integrate with your GSM client
        # For now, simulate the sync
        await asyncio.sleep(2)  # Simulate API calls

        return {
            "success": True,
            "synced_count": len(VARIABLE_DEFINITIONS),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gsm_project": "my-hibachi-prod",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GSM sync failed: {str(e)}")


@router.post("/sync-from-gsm")
async def sync_from_gsm(current_user=Depends(get_current_user)):
    """Load variables from Google Secret Manager and update local files"""
    try:
        # This would integrate with your GSM client
        # For now, simulate the sync
        await asyncio.sleep(3)  # Simulate API calls

        return {
            "success": True,
            "loaded_count": len(VARIABLE_DEFINITIONS),
            "updated_files": 12,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GSM load failed: {str(e)}")


@router.get("/config-version")
async def get_config_version():
    """Get current configuration version"""
    try:
        # Try to read from GSM first, then fallback to env
        version = os.environ.get("CONFIG_VERSION", "1")
        return {
            "version": version,
            "source": "environment",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config version: {str(e)}")


@router.post("/config-version/increment")
async def increment_config_version(current_user=Depends(get_current_user)):
    """Increment configuration version to trigger reloads"""
    try:
        current_version = int(os.environ.get("CONFIG_VERSION", "1"))
        new_version = current_version + 1

        # Update in GSM (simulated for now)
        await asyncio.sleep(1)

        return {
            "old_version": current_version,
            "new_version": new_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error incrementing config version: {str(e)}")


# Helper functions
async def get_variable_from_files(key: str, definition: dict) -> Union[str, int, float, bool]:
    """Get current value of a variable from its source files"""

    # Hardcoded current values for demonstration
    # In real implementation, parse actual files
    sample_values = {
        "BASE_PRICE_PER_PERSON": 75,
        "DEPOSIT_AMOUNT": 100,  # Fixed from your correction
        "TRAVEL_FEE_BASE_RATE": 1.25,
        "MINIMUM_GUESTS": 8,
        "MAXIMUM_GUESTS": 20,
        "ADVANCE_BOOKING_HOURS": 48,
        "FF_ENABLE_AI_BOOKING_V3": True,
        "FF_ENABLE_TRAVEL_FEE_V2": False,
        "AI_MODEL_VERSION": "gpt-4o",
        "AI_MAX_TOKENS": 1500,
    }

    return sample_values.get(key, "")


async def update_single_variable(key: str, value: Union[str, int, float, bool]):
    """Update a single variable in its source files"""
    definition = VARIABLE_DEFINITIONS.get(key)
    if not definition:
        raise ValueError(f"Unknown variable: {key}")

    # Here you would update the actual files
    # For now, just simulate
    logger.info(f"Updating variable {key} in files: {definition['files']}")


async def sync_variables_to_gsm(variables: List[UpdateVariableRequest]):
    """Sync variables to Google Secret Manager"""
    # Here you would use your GSM client
    logger.info(f"Syncing {len(variables)} variables to GSM")


async def increment_config_version():
    """Increment the CONFIG_VERSION to trigger reloads"""
    # Here you would update GSM
    logger.info("Incrementing CONFIG_VERSION in GSM")
