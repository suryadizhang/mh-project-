"""
Security Dashboard API Endpoints (SUPER_ADMIN only)

Provides endpoints for:
- Viewing security alerts
- Managing alert status
- Security event logs
- Blocked IPs management
- Account security actions
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from core.config import get_settings
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================
# Pydantic Models
# ============================================


class AlertStatusUpdate(BaseModel):
    """Request to update alert status"""

    status: str = Field(..., pattern="^(acknowledged|resolved|dismissed)$")


class BlockIPRequest(BaseModel):
    """Request to block an IP address"""

    ip_address: str
    reason: str
    expires_hours: Optional[int] = None  # None = permanent


class UnblockIPRequest(BaseModel):
    """Request to unblock an IP address"""

    ip_address: str


class RestoreAccountRequest(BaseModel):
    """Request to restore a security-disabled account"""

    user_id: str
    reset_pin: bool = True  # Also reset their PIN


class SecurityStats(BaseModel):
    """Security dashboard statistics"""

    new_alerts: int = 0
    critical_alerts: int = 0
    events_24h: int = 0
    lockouts_24h: int = 0
    failed_mfa_24h: int = 0
    suspicious_ips_1h: int = 0
    blocked_ips: int = 0


# ============================================
# Authorization Helper
# ============================================


def require_super_admin(current_user: dict):
    """Ensure current user is Super Admin"""
    role = current_user.get("role", "").lower()
    if role != "super_admin":
        raise HTTPException(status_code=403, detail="This endpoint requires Super Admin privileges")


# ============================================
# Dashboard Stats
# ============================================


@router.get("/stats", response_model=SecurityStats, tags=["Security Dashboard"])
async def get_security_stats(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get security dashboard statistics (SUPER_ADMIN only).

    Returns counts of alerts, events, lockouts, etc.
    """
    require_super_admin(current_user)

    try:
        # Try to use the view if it exists
        query = text("SELECT * FROM security.dashboard_stats LIMIT 1")
        result = await db.execute(query)
        row = result.fetchone()

        if row:
            return SecurityStats(
                new_alerts=row.new_alerts or 0,
                critical_alerts=row.critical_alerts or 0,
                events_24h=row.events_24h or 0,
                lockouts_24h=row.lockouts_24h or 0,
                failed_mfa_24h=row.failed_mfa_24h or 0,
                suspicious_ips_1h=row.suspicious_ips_1h or 0,
                blocked_ips=row.blocked_ips or 0,
            )
    except Exception as e:
        logger.warning(f"Security stats view not available: {e}")

    # Fallback: manual queries
    stats = SecurityStats()

    try:
        # New alerts
        result = await db.execute(
            text("SELECT COUNT(*) FROM security.admin_alerts WHERE status = 'new'")
        )
        stats.new_alerts = result.scalar() or 0

        # Critical alerts
        result = await db.execute(
            text(
                "SELECT COUNT(*) FROM security.admin_alerts WHERE status = 'new' AND severity = 'critical'"
            )
        )
        stats.critical_alerts = result.scalar() or 0

    except Exception as e:
        logger.warning(f"Could not get alert stats: {e}")

    return stats


# ============================================
# Alerts Management
# ============================================


@router.get("/alerts", tags=["Security Dashboard"])
async def get_alerts(
    status: Optional[str] = Query(None, pattern="^(new|acknowledged|resolved|dismissed)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get security alerts (SUPER_ADMIN only).

    Filters:
    - status: new, acknowledged, resolved, dismissed
    - severity: low, medium, high, critical
    """
    require_super_admin(current_user)

    # Build query
    conditions = []
    params = {"limit": limit, "offset": offset}

    if status:
        conditions.append("a.status = :status")
        params["status"] = status
    else:
        conditions.append("a.status IN ('new', 'acknowledged')")

    if severity:
        conditions.append("a.severity = :severity")
        params["severity"] = severity

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = text(
        f"""
        SELECT a.id, a.title, a.message, a.severity, a.event_type,
               a.user_id, a.email, a.ip_address, a.requires_action,
               a.action_url, a.status, a.created_at, a.resolved_at,
               u.email as resolved_by_email
        FROM security.admin_alerts a
        LEFT JOIN identity.users u ON a.resolved_by = u.id
        WHERE {where_clause}
        ORDER BY
            CASE a.severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
            END,
            a.created_at DESC
        LIMIT :limit OFFSET :offset
    """
    )

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        alerts = []
        for row in rows:
            alerts.append(
                {
                    "id": str(row.id),
                    "title": row.title,
                    "message": row.message,
                    "severity": row.severity,
                    "event_type": row.event_type,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "requires_action": row.requires_action,
                    "action_url": row.action_url,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
                    "resolved_by": row.resolved_by_email,
                }
            )

        # Get total count (remove alias prefix for simple count)
        count_where = where_clause.replace("a.", "")
        count_query = text(f"SELECT COUNT(*) FROM security.admin_alerts WHERE {count_where}")
        count_result = await db.execute(count_query, params)
        total = count_result.scalar() or 0

        return {
            "alerts": alerts,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.patch("/alerts/{alert_id}", tags=["Security Dashboard"])
async def update_alert_status(
    alert_id: str,
    request: AlertStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update alert status (SUPER_ADMIN only).

    Valid statuses: acknowledged, resolved, dismissed
    """
    require_super_admin(current_user)

    user_id = current_user.get("sub") or current_user.get("id")

    query = text(
        """
        UPDATE security.admin_alerts
        SET status = :status,
            resolved_by = CASE WHEN :status IN ('resolved', 'dismissed') THEN :user_id::uuid ELSE resolved_by END,
            resolved_at = CASE WHEN :status IN ('resolved', 'dismissed') THEN NOW() ELSE resolved_at END,
            updated_at = NOW()
        WHERE id = :alert_id::uuid
        RETURNING id
    """
    )

    try:
        result = await db.execute(
            query,
            {
                "alert_id": alert_id,
                "status": request.status,
                "user_id": user_id,
            },
        )
        await db.commit()

        if not result.scalar():
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": f"Alert status updated to {request.status}", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update alert")


# ============================================
# Security Events Log
# ============================================


@router.get("/events", tags=["Security Dashboard"])
async def get_security_events(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),  # Max 7 days
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get security event log (SUPER_ADMIN only).

    Filters:
    - event_type: login_failed, mfa_failed, account_locked, etc.
    - user_id: Filter by specific user
    - ip_address: Filter by IP
    - hours: How far back to look (default 24, max 168)
    """
    require_super_admin(current_user)

    conditions = ["created_at > NOW() - INTERVAL ':hours hours'"]
    params = {"limit": limit, "hours": hours}

    if event_type:
        conditions.append("event_type = :event_type")
        params["event_type"] = event_type

    if user_id:
        conditions.append("user_id = :user_id::uuid")
        params["user_id"] = user_id

    if ip_address:
        conditions.append("ip_address = :ip_address")
        params["ip_address"] = ip_address

    where_clause = " AND ".join(conditions).replace(":hours", str(hours))

    query = text(
        f"""
        SELECT id, event_type, user_id, email, ip_address,
               user_agent, details, severity, created_at
        FROM security.security_events
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """
    )

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        events = []
        for row in rows:
            events.append(
                {
                    "id": str(row.id),
                    "event_type": row.event_type,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent[:100] if row.user_agent else None,
                    "details": row.details,
                    "severity": row.severity,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
            )

        return {"events": events, "count": len(events)}

    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")


# ============================================
# Blocked IPs Management
# ============================================


@router.get("/blocked-ips", tags=["Security Dashboard"])
async def get_blocked_ips(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get list of blocked IP addresses (SUPER_ADMIN only)."""
    require_super_admin(current_user)

    query = text(
        """
        SELECT b.id, b.ip_address, b.reason, b.blocked_at, b.expires_at, b.notes,
               u.email as blocked_by_email
        FROM security.blocked_ips b
        LEFT JOIN identity.users u ON b.blocked_by = u.id
        WHERE b.is_active = true
        ORDER BY b.blocked_at DESC
    """
    )

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        blocked = []
        for row in rows:
            blocked.append(
                {
                    "id": str(row.id),
                    "ip_address": row.ip_address,
                    "reason": row.reason,
                    "blocked_at": row.blocked_at.isoformat() if row.blocked_at else None,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    "notes": row.notes,
                    "blocked_by": row.blocked_by_email,
                    "is_permanent": row.expires_at is None,
                }
            )

        return {"blocked_ips": blocked, "count": len(blocked)}

    except Exception as e:
        logger.error(f"Failed to get blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve blocked IPs")


@router.post("/blocked-ips", tags=["Security Dashboard"])
async def block_ip(
    request: BlockIPRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Block an IP address (SUPER_ADMIN only)."""
    require_super_admin(current_user)

    user_id = current_user.get("sub") or current_user.get("id")

    # Calculate expiration
    expires_at = None
    if request.expires_hours:
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(hours=request.expires_hours)

    query = text(
        """
        INSERT INTO security.blocked_ips (ip_address, reason, blocked_by, expires_at)
        VALUES (:ip_address, :reason, :blocked_by::uuid, :expires_at)
        ON CONFLICT (ip_address)
        DO UPDATE SET
            is_active = true,
            reason = :reason,
            blocked_by = :blocked_by::uuid,
            expires_at = :expires_at,
            blocked_at = NOW()
        RETURNING id
    """
    )

    try:
        result = await db.execute(
            query,
            {
                "ip_address": request.ip_address,
                "reason": request.reason,
                "blocked_by": user_id,
                "expires_at": expires_at,
            },
        )
        await db.commit()

        logger.info(f"IP {request.ip_address} blocked by {current_user.get('email')}")

        return {
            "message": f"IP {request.ip_address} has been blocked",
            "expires_at": expires_at.isoformat() if expires_at else None,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to block IP: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to block IP")


@router.delete("/blocked-ips/{ip_address}", tags=["Security Dashboard"])
async def unblock_ip(
    ip_address: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unblock an IP address (SUPER_ADMIN only)."""
    require_super_admin(current_user)

    query = text(
        """
        UPDATE security.blocked_ips
        SET is_active = false
        WHERE ip_address = :ip_address
        RETURNING id
    """
    )

    try:
        result = await db.execute(query, {"ip_address": ip_address})
        await db.commit()

        if not result.scalar():
            raise HTTPException(status_code=404, detail="IP not found in blocked list")

        logger.info(f"IP {ip_address} unblocked by {current_user.get('email')}")

        return {"message": f"IP {ip_address} has been unblocked", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unblock IP: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unblock IP")


# ============================================
# Account Security Actions
# ============================================


@router.post("/restore-account", tags=["Security Dashboard"])
async def restore_account(
    request: RestoreAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a security-disabled account (SUPER_ADMIN only).

    This action:
    - Removes security disabled flag
    - Resets lockout count
    - Clears PIN lock
    - Optionally resets PIN (requiring user to set new one)
    """
    require_super_admin(current_user)

    # Build update query
    if request.reset_pin:
        query = text(
            """
            UPDATE identity.users
            SET is_security_disabled = false,
                lockout_count = 0,
                pin_attempts = 0,
                pin_locked_until = NULL,
                pin_hash = NULL,
                pin_reset_required = true,
                mfa_setup_complete = false,
                updated_at = NOW()
            WHERE id = :user_id::uuid
            RETURNING email
        """
        )
    else:
        query = text(
            """
            UPDATE identity.users
            SET is_security_disabled = false,
                lockout_count = 0,
                pin_attempts = 0,
                pin_locked_until = NULL,
                updated_at = NOW()
            WHERE id = :user_id::uuid
            RETURNING email
        """
        )

    try:
        result = await db.execute(query, {"user_id": request.user_id})
        row = result.fetchone()
        await db.commit()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Account {row.email} restored by {current_user.get('email')}")

        # Resolve any related alerts
        resolve_query = text(
            """
            UPDATE security.admin_alerts
            SET status = 'resolved',
                resolved_by = :admin_id::uuid,
                resolved_at = NOW()
            WHERE user_id = :user_id::uuid
              AND status IN ('new', 'acknowledged')
              AND event_type = 'account_locked'
        """
        )
        await db.execute(
            resolve_query,
            {
                "user_id": request.user_id,
                "admin_id": current_user.get("sub") or current_user.get("id"),
            },
        )
        await db.commit()

        return {
            "message": f"Account {row.email} has been restored",
            "pin_reset": request.reset_pin,
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore account: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to restore account")


@router.get("/disabled-accounts", tags=["Security Dashboard"])
async def get_disabled_accounts(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get list of security-disabled accounts (SUPER_ADMIN only)."""
    require_super_admin(current_user)

    query = text(
        """
        SELECT id, email, first_name, last_name, lockout_count, last_lockout_at
        FROM identity.users
        WHERE is_security_disabled = true
        ORDER BY last_lockout_at DESC
    """
    )

    try:
        result = await db.execute(query)
        rows = result.fetchall()

        accounts = []
        for row in rows:
            accounts.append(
                {
                    "id": str(row.id),
                    "email": row.email,
                    "name": f"{row.first_name or ''} {row.last_name or ''}".strip()
                    or row.email.split("@")[0],
                    "lockout_count": row.lockout_count,
                    "last_lockout_at": (
                        row.last_lockout_at.isoformat() if row.last_lockout_at else None
                    ),
                }
            )

        return {"disabled_accounts": accounts, "count": len(accounts)}

    except Exception as e:
        logger.error(f"Failed to get disabled accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve disabled accounts")


# ============================================
# Login History & IP Monitoring
# ============================================


@router.get("/login-history", tags=["Security Dashboard"])
async def get_login_history(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    suspicious_only: bool = Query(False),
    hours: int = Query(24, ge=1, le=720),  # Max 30 days
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get login history with IP tracking (SUPER_ADMIN only).

    Filters:
    - user_id: Filter by specific user
    - ip_address: Filter by IP address
    - suspicious_only: Show only flagged logins
    - hours: How far back to look (default 24, max 720)
    """
    require_super_admin(current_user)

    conditions = ["login_at > NOW() - INTERVAL ':hours hours'"]
    params = {"limit": limit}

    if user_id:
        conditions.append("user_id = CAST(:user_id AS uuid)")
        params["user_id"] = user_id

    if ip_address:
        conditions.append("ip_address = :ip_address")
        params["ip_address"] = ip_address

    if suspicious_only:
        conditions.append("is_suspicious = true")

    where_clause = " AND ".join(conditions).replace(":hours", str(hours))

    query = text(
        f"""
        SELECT id, user_id, email, ip_address, user_agent,
               country, city, browser, os, device_type,
               is_new_ip, is_suspicious, success, login_at
        FROM security.login_history
        WHERE {where_clause}
        ORDER BY login_at DESC
        LIMIT :limit
    """
    )

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        history = []
        for row in rows:
            history.append(
                {
                    "id": str(row.id),
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent[:100] if row.user_agent else None,
                    "country": row.country,
                    "city": row.city,
                    "browser": row.browser,
                    "os": row.os,
                    "device_type": row.device_type,
                    "is_new_ip": row.is_new_ip,
                    "is_suspicious": row.is_suspicious,
                    "success": row.success,
                    "login_at": row.login_at.isoformat() if row.login_at else None,
                }
            )

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Failed to get login history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve login history")


@router.get("/login-history/user/{user_id}", tags=["Security Dashboard"])
async def get_user_login_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get login history for a specific user (SUPER_ADMIN only).

    Shows all logins with device and location info.
    """
    require_super_admin(current_user)

    from services.security_monitoring_service import SecurityMonitoringService

    try:
        security = SecurityMonitoringService(db)
        history = await security.get_user_login_history(user_id, limit)

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Failed to get user login history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve login history")


@router.get("/login-history/ip/{ip_address:path}", tags=["Security Dashboard"])
async def get_ip_login_history(
    ip_address: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get login history for a specific IP address (SUPER_ADMIN only).

    Shows all accounts that logged in from this IP.
    """
    require_super_admin(current_user)

    from services.security_monitoring_service import SecurityMonitoringService

    try:
        security = SecurityMonitoringService(db)
        history = await security.get_ip_login_history(ip_address, limit)

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Failed to get IP login history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve login history")


@router.get("/known-ips/{user_id}", tags=["Security Dashboard"])
async def get_user_known_ips(
    user_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get list of known/trusted IPs for a user (SUPER_ADMIN only).

    Shows all IPs the user has logged in from.
    """
    require_super_admin(current_user)

    query = text(
        """
        SELECT ip_address, country, city, first_seen, last_seen, login_count, is_trusted
        FROM security.known_user_ips
        WHERE user_id = CAST(:user_id AS uuid)
        ORDER BY last_seen DESC
    """
    )

    try:
        result = await db.execute(query, {"user_id": user_id})
        rows = result.fetchall()

        ips = []
        for row in rows:
            ips.append(
                {
                    "ip_address": row.ip_address,
                    "country": row.country,
                    "city": row.city,
                    "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                    "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                    "login_count": row.login_count,
                    "is_trusted": row.is_trusted,
                }
            )

        return {"known_ips": ips, "count": len(ips)}

    except Exception as e:
        logger.error(f"Failed to get known IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve known IPs")


@router.get("/suspicious-logins", tags=["Security Dashboard"])
async def get_suspicious_logins(
    hours: int = Query(168, ge=1, le=720),  # Default 7 days
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent suspicious logins (SUPER_ADMIN only).

    Shows logins flagged as suspicious due to:
    - New IP address
    - Geo-impossible travel
    - Bad IP reputation
    - Multiple accounts from same IP
    """
    require_super_admin(current_user)

    query = text(
        """
        SELECT lh.id, lh.user_id, lh.email, lh.ip_address,
               lh.country, lh.city, lh.browser, lh.os, lh.device_type,
               lh.is_new_ip, lh.login_at,
               (SELECT COUNT(*) FROM security.admin_alerts a
                WHERE a.ip_address = lh.ip_address
                AND a.created_at > NOW() - INTERVAL '24 hours') as alert_count
        FROM security.login_history lh
        WHERE lh.is_suspicious = true
          AND lh.login_at > NOW() - INTERVAL ':hours hours'
        ORDER BY lh.login_at DESC
        LIMIT :limit
    """.replace(
            ":hours", str(hours)
        )
    )

    try:
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()

        logins = []
        for row in rows:
            logins.append(
                {
                    "id": str(row.id),
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "country": row.country,
                    "city": row.city,
                    "browser": row.browser,
                    "os": row.os,
                    "device_type": row.device_type,
                    "is_new_ip": row.is_new_ip,
                    "login_at": row.login_at.isoformat() if row.login_at else None,
                    "alert_count": row.alert_count or 0,
                }
            )

        return {"suspicious_logins": logins, "count": len(logins)}

    except Exception as e:
        logger.error(f"Failed to get suspicious logins: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve suspicious logins")
