"""
Alert Rules API Endpoints

REST API for managing alert rules dynamically:
- CRUD operations (Create, Read, Update, Delete)
- Enable/disable rules
- Test rule evaluation
- View rule history and statistics
- Bulk operations

Authentication: Admin only (requires authentication and admin role)
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from monitoring.models import AlertRule, ThresholdOperator, RuleSeverity
from monitoring import RuleEvaluator
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring/rules", tags=["Monitoring - Alert Rules"])


# ============================================================================
# Pydantic Models
# ============================================================================


class AlertRuleCreate(BaseModel):
    """Schema for creating a new alert rule"""

    name: str = Field(..., min_length=1, max_length=255, description="Unique rule name")
    description: Optional[str] = Field(None, max_length=1000, description="Rule description")
    metric_name: str = Field(..., min_length=1, max_length=100, description="Metric to monitor")
    operator: ThresholdOperator = Field(..., description="Comparison operator")
    threshold_value: float = Field(..., description="Threshold value")
    duration_seconds: int = Field(default=0, ge=0, description="Duration requirement in seconds")
    cooldown_seconds: int = Field(default=300, ge=0, description="Cooldown period in seconds")
    severity: RuleSeverity = Field(default="medium", description="Alert severity level")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    alert_title_template: Optional[str] = Field(
        None, max_length=500, description="Alert title template"
    )
    alert_message_template: Optional[str] = Field(
        None, max_length=2000, description="Alert message template"
    )
    tags: Optional[List[str]] = Field(default=None, description="Rule tags")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "High API Response Time",
                "description": "Alert when API response time exceeds 2 seconds",
                "metric_name": "api_response_time_p95_ms",
                "operator": "gt",
                "threshold_value": 2000.0,
                "duration_seconds": 180,
                "cooldown_seconds": 300,
                "severity": "high",
                "enabled": True,
                "alert_title_template": "{rule_name}: Response time at {current_value}ms",
                "alert_message_template": "API response time is {current_value}ms (threshold: > {threshold_value}ms) for {duration}s",
                "tags": ["api", "performance"],
                "metadata": {"team": "backend", "priority": "high"},
            }
        }


class AlertRuleUpdate(BaseModel):
    """Schema for updating an existing alert rule"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metric_name: Optional[str] = Field(None, min_length=1, max_length=100)
    operator: Optional[ThresholdOperator] = None
    threshold_value: Optional[float] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    cooldown_seconds: Optional[int] = Field(None, ge=0)
    severity: Optional[RuleSeverity] = None
    enabled: Optional[bool] = None
    alert_title_template: Optional[str] = Field(None, max_length=500)
    alert_message_template: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class AlertRuleResponse(BaseModel):
    """Schema for alert rule response"""

    id: int
    name: str
    description: Optional[str]
    metric_name: str
    operator: str
    threshold_value: float
    duration_seconds: int
    cooldown_seconds: int
    severity: str
    enabled: bool
    alert_title_template: Optional[str]
    alert_message_template: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    trigger_count: int
    condition_display: str

    class Config:
        from_attributes = True


class RuleTestRequest(BaseModel):
    """Schema for testing a rule"""

    test_value: float = Field(..., description="Test metric value")


class RuleTestResponse(BaseModel):
    """Schema for rule test result"""

    rule_id: int
    rule_name: str
    test_value: float
    threshold_value: float
    operator: str
    violated: bool
    duration_exceeded: float
    duration_required: float
    is_duration_met: bool
    remaining_duration: float
    would_create_alert: bool
    message: str


class RuleStatsResponse(BaseModel):
    """Schema for rule statistics"""

    rule_id: int
    rule_name: str
    trigger_count: int
    last_triggered_at: Optional[datetime]
    current_violation: Optional[dict]
    in_cooldown: bool


class BulkOperationRequest(BaseModel):
    """Schema for bulk operations"""

    rule_ids: List[int] = Field(..., min_items=1, description="List of rule IDs")
    operation: str = Field(..., description="Operation: enable, disable, delete")


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation result"""

    operation: str
    total: int
    success: int
    failed: int
    errors: List[dict]


# ============================================================================
# Helper Functions
# ============================================================================


def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )


def rule_to_response(rule: AlertRule) -> AlertRuleResponse:
    """Convert AlertRule to response schema"""
    return AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        metric_name=rule.metric_name,
        operator=rule.operator,
        threshold_value=rule.threshold_value,
        duration_seconds=rule.duration_seconds,
        cooldown_seconds=rule.cooldown_seconds,
        severity=rule.severity,
        enabled=rule.enabled,
        alert_title_template=rule.alert_title_template,
        alert_message_template=rule.alert_message_template,
        tags=rule.tags,
        metadata=rule.metadata,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        last_triggered_at=rule.last_triggered_at,
        trigger_count=rule.trigger_count,
        condition_display=rule.get_condition_display(),
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/", response_model=List[AlertRuleResponse])
async def list_rules(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    severity: Optional[RuleSeverity] = Query(None, description="Filter by severity"),
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """
    List all alert rules with optional filtering.

    Query parameters:
    - enabled: Filter by enabled status (true/false)
    - severity: Filter by severity level
    - metric_name: Filter by metric name
    - skip: Pagination offset
    - limit: Maximum number of results
    """
    try:
        query = db.query(AlertRule)

        # Apply filters
        if enabled is not None:
            query = query.filter(AlertRule.enabled == enabled)

        if severity:
            query = query.filter(AlertRule.severity == severity)

        if metric_name:
            query = query.filter(AlertRule.metric_name == metric_name)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        rules = query.all()
        return [rule_to_response(rule) for rule in rules]

    except Exception as e:
        logger.error(f"Error listing rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rules: {str(e)}",
        )


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Get a specific alert rule by ID.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        return rule_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule: {str(e)}",
        )


@router.post("/", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule_data: AlertRuleCreate, db: Session = Depends(get_db)):
    """
    Create a new alert rule.
    """
    try:
        # Check for duplicate name
        existing = db.query(AlertRule).filter(AlertRule.name == rule_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule with name '{rule_data.name}' already exists",
            )

        # Create rule
        rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            metric_name=rule_data.metric_name,
            operator=rule_data.operator,
            threshold_value=rule_data.threshold_value,
            duration_seconds=rule_data.duration_seconds,
            cooldown_seconds=rule_data.cooldown_seconds,
            severity=rule_data.severity,
            enabled=rule_data.enabled,
            alert_title_template=rule_data.alert_title_template,
            alert_message_template=rule_data.alert_message_template,
            tags=rule_data.tags,
            metadata=rule_data.metadata,
            created_at=datetime.utcnow(),
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        logger.info(f"Created rule: {rule.name} (ID: {rule.id})")

        return rule_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating rule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}",
        )


@router.patch("/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(rule_id: int, rule_data: AlertRuleUpdate, db: Session = Depends(get_db)):
    """
    Update an existing alert rule.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        # Update fields
        update_data = rule_data.model_dump(exclude_unset=True)

        # Check for name conflict if name is being changed
        if "name" in update_data and update_data["name"] != rule.name:
            existing = db.query(AlertRule).filter(AlertRule.name == update_data["name"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rule with name '{update_data['name']}' already exists",
                )

        for key, value in update_data.items():
            setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(rule)

        logger.info(f"Updated rule: {rule.name} (ID: {rule.id})")

        return rule_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}",
        )


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Delete an alert rule.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        rule_name = rule.name

        # Clear any active violations and cooldowns in Redis
        redis_client = get_redis_client()
        redis_client.delete(f"rule:violation:{rule_id}")
        redis_client.delete(f"rule:cooldown:{rule_id}")

        db.delete(rule)
        db.commit()

        logger.info(f"Deleted rule: {rule_name} (ID: {rule_id})")

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}",
        )


@router.post("/{rule_id}/enable", response_model=AlertRuleResponse)
async def enable_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Enable an alert rule.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        if rule.enabled:
            return rule_to_response(rule)

        rule.enabled = True
        rule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(rule)

        logger.info(f"Enabled rule: {rule.name} (ID: {rule.id})")

        return rule_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error enabling rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable rule: {str(e)}",
        )


@router.post("/{rule_id}/disable", response_model=AlertRuleResponse)
async def disable_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Disable an alert rule.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        if not rule.enabled:
            return rule_to_response(rule)

        rule.enabled = False
        rule.updated_at = datetime.utcnow()

        # Clear any active violations and cooldowns
        redis_client = get_redis_client()
        redis_client.delete(f"rule:violation:{rule_id}")
        redis_client.delete(f"rule:cooldown:{rule_id}")

        db.commit()
        db.refresh(rule)

        logger.info(f"Disabled rule: {rule.name} (ID: {rule.id})")

        return rule_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error disabling rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable rule: {str(e)}",
        )


@router.post("/{rule_id}/test", response_model=RuleTestResponse)
async def test_rule(rule_id: int, test_data: RuleTestRequest, db: Session = Depends(get_db)):
    """
    Test a rule with a specific value to see if it would trigger an alert.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        # Create evaluator
        redis_client = get_redis_client()
        evaluator = RuleEvaluator(db, redis_client)

        # Evaluate metric
        violations = evaluator.evaluate_metric(
            rule.metric_name, test_data.test_value, datetime.utcnow().timestamp()
        )

        # Find our rule's violation
        violation = None
        for v in violations:
            if v.rule_id == rule_id:
                violation = v
                break

        if violation:
            # Check if in cooldown
            in_cooldown = redis_client.exists(f"rule:cooldown:{rule_id}")
            would_create_alert = violation.is_duration_met and not in_cooldown

            message = f"VIOLATION: Value {test_data.test_value:.2f} {violation.operator} {violation.threshold_value:.2f}"
            if not violation.is_duration_met:
                message += f" - Duration not met (need {violation.remaining_duration:.0f}s more)"
            elif in_cooldown:
                message += " - In cooldown, no alert would be created"
            else:
                message += " - Would create alert!"

            return RuleTestResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                test_value=test_data.test_value,
                threshold_value=rule.threshold_value,
                operator=rule.operator,
                violated=True,
                duration_exceeded=violation.duration_exceeded,
                duration_required=rule.duration_seconds,
                is_duration_met=violation.is_duration_met,
                remaining_duration=violation.remaining_duration,
                would_create_alert=would_create_alert,
                message=message,
            )
        else:
            return RuleTestResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                test_value=test_data.test_value,
                threshold_value=rule.threshold_value,
                operator=rule.operator,
                violated=False,
                duration_exceeded=0.0,
                duration_required=rule.duration_seconds,
                is_duration_met=False,
                remaining_duration=rule.duration_seconds,
                would_create_alert=False,
                message=f"NO VIOLATION: Value {test_data.test_value:.2f} is within threshold",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test rule: {str(e)}",
        )


@router.get("/{rule_id}/stats", response_model=RuleStatsResponse)
async def get_rule_stats(rule_id: int, db: Session = Depends(get_db)):
    """
    Get statistics for a specific rule.
    """
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
            )

        redis_client = get_redis_client()
        evaluator = RuleEvaluator(db, redis_client)

        # Get current violation status
        violations = evaluator.get_all_violations()
        current_violation = None
        for v in violations:
            if v.rule_id == rule_id:
                current_violation = v.to_dict()
                break

        # Check if in cooldown
        in_cooldown = redis_client.exists(f"rule:cooldown:{rule_id}") > 0

        return RuleStatsResponse(
            rule_id=rule.id,
            rule_name=rule.name,
            trigger_count=rule.trigger_count,
            last_triggered_at=rule.last_triggered_at,
            current_violation=current_violation,
            in_cooldown=in_cooldown,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule stats: {str(e)}",
        )


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_operation(operation_data: BulkOperationRequest, db: Session = Depends(get_db)):
    """
    Perform bulk operations on multiple rules.

    Operations:
    - enable: Enable selected rules
    - disable: Disable selected rules
    - delete: Delete selected rules
    """
    try:
        if operation_data.operation not in ["enable", "disable", "delete"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {operation_data.operation}",
            )

        total = len(operation_data.rule_ids)
        success = 0
        failed = 0
        errors = []

        redis_client = get_redis_client()

        for rule_id in operation_data.rule_ids:
            try:
                rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

                if not rule:
                    errors.append({"rule_id": rule_id, "error": "Rule not found"})
                    failed += 1
                    continue

                if operation_data.operation == "enable":
                    rule.enabled = True
                    rule.updated_at = datetime.utcnow()
                    success += 1

                elif operation_data.operation == "disable":
                    rule.enabled = False
                    rule.updated_at = datetime.utcnow()
                    redis_client.delete(f"rule:violation:{rule_id}")
                    redis_client.delete(f"rule:cooldown:{rule_id}")
                    success += 1

                elif operation_data.operation == "delete":
                    redis_client.delete(f"rule:violation:{rule_id}")
                    redis_client.delete(f"rule:cooldown:{rule_id}")
                    db.delete(rule)
                    success += 1

            except Exception as e:
                errors.append({"rule_id": rule_id, "error": str(e)})
                failed += 1

        db.commit()

        logger.info(f"Bulk operation '{operation_data.operation}': {success}/{total} success")

        return BulkOperationResponse(
            operation=operation_data.operation,
            total=total,
            success=success,
            failed=failed,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk operation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}",
        )
