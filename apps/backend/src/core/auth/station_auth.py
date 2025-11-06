"""
Station-Aware Authentication Service
Extends the existing authentication system with multi-tenant station context.
"""

from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Any
from uuid import UUID, uuid4

from core.auth.models import (  # Phase 2C: Updated from api.app.auth.models
    AuthenticationService as BaseAuthenticationService,
)
from core.auth.models import (  # Phase 2C: Updated from api.app.auth.models
    User,
    UserSession,
)
from core.auth.station_models import (  # Phase 2C: Updated from api.app.auth.station_models
    Station,
    StationAccessToken,
    StationAuditLog,
    StationPermission,
    StationRole,
    StationUser,
    can_access_station,
    can_perform_cross_station_action,
    get_station_permissions,
)
from utils.encryption import FieldEncryption  # Phase 2C: Updated from api.app.utils.encryption
import jwt
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class StationContext:
    """Context object containing station information for authenticated users."""

    def __init__(
        self,
        user_id: UUID,
        station_assignments: list[dict[str, Any]] | None = None,
        primary_station_id: UUID | None = None,
        current_station_id: UUID | None = None,
        highest_role: str | None = None,
        # Backward compatibility
        stations: list[dict[str, Any]] | None = None,
    ):
        self.user_id = user_id
        # Support both 'stations' and 'station_assignments' parameter names
        self.station_assignments = station_assignments or stations or []
        self.primary_station_id = primary_station_id
        self.current_station_id = current_station_id or primary_station_id

        # Build quick lookup maps
        self.station_roles = {
            assignment["station_id"]: assignment["role"] for assignment in self.station_assignments
        }
        self.station_permissions = {
            assignment["station_id"]: set(assignment["permissions"])
            for assignment in self.station_assignments
        }

        # Determine highest role across all stations
        role_hierarchy = {
            StationRole.SUPER_ADMIN: 4,
            StationRole.ADMIN: 3,
            StationRole.STATION_ADMIN: 2,
            StationRole.CUSTOMER_SUPPORT: 1,
        }

        # Allow explicit highest_role or calculate from assignments
        if highest_role:
            self.highest_role = (
                StationRole(highest_role) if isinstance(highest_role, str) else highest_role
            )
        else:
            self.highest_role = StationRole.CUSTOMER_SUPPORT
            max_level = 0
            for assignment in self.station_assignments:
                role = StationRole(assignment["role"])
                level = role_hierarchy.get(role, 0)
                if level > max_level:
                    max_level = level
                    self.highest_role = role

    @property
    def is_super_admin(self) -> bool:
        """Check if user has super admin role."""
        return self.highest_role == StationRole.SUPER_ADMIN

    @property
    def is_admin(self) -> bool:
        """Check if user has admin or super admin role."""
        return self.highest_role in {StationRole.SUPER_ADMIN, StationRole.ADMIN}

    @property
    def accessible_station_ids(self) -> set[UUID]:
        """Get all station IDs the user can access."""
        return set(self.station_roles.keys())

    def get_role_for_station(self, station_id: UUID) -> StationRole | None:
        """Get user's role for a specific station."""
        role_str = self.station_roles.get(station_id)
        return StationRole(role_str) if role_str else None

    def get_permissions_for_station(self, station_id: UUID) -> set[str]:
        """Get user's permissions for a specific station."""
        return self.station_permissions.get(station_id, set())

    def can_access_station(self, station_id: UUID) -> bool:
        """Check if user can access a specific station."""
        return can_access_station(self.highest_role, station_id, list(self.accessible_station_ids))

    def has_permission_in_station(self, permission: StationPermission, station_id: UUID) -> bool:
        """Check if user has specific permission in a station."""
        if not self.can_access_station(station_id):
            return False

        station_permissions = self.get_permissions_for_station(station_id)
        return permission.value in station_permissions

    def can_perform_cross_station_action(self, permission: StationPermission) -> bool:
        """Check if user can perform cross-station actions."""
        return can_perform_cross_station_action(self.highest_role, permission)


class StationAuthenticationService(BaseAuthenticationService):
    """Enhanced authentication service with station-aware capabilities."""

    def __init__(
        self, encryption: FieldEncryption, jwt_secret: str, jwt_issuer: str = "myhibachi-crm"
    ):
        super().__init__(encryption, jwt_secret, jwt_issuer)

        # Station-specific token settings
        self.station_token_lifetime = timedelta(hours=4)  # Shorter for station tokens

    async def get_user_station_context(self, db: AsyncSession, user: User) -> StationContext | None:
        """Get station context for a user including all assignments and permissions."""
        try:
            # Get user's station assignments with station details
            stmt = (
                select(StationUser, Station)
                .join(Station, StationUser.station_id == Station.id)
                .where(and_(StationUser.user_id == user.id, StationUser.is_active))
                .options(selectinload(StationUser.station))
            )

            result = await db.execute(stmt)
            assignments = result.fetchall()

            if not assignments:
                return None

            station_assignments = []
            primary_station_id = None

            for station_user, station in assignments:
                # Get permissions for this role
                role = StationRole(station_user.role)
                permissions = get_station_permissions(role, station_user.additional_permissions)

                assignment = {
                    "station_id": station_user.station_id,
                    "station_code": station.code,
                    "station_name": station.name,
                    "role": station_user.role,
                    "permissions": list(permissions),
                    "is_primary": station_user.is_primary_station,
                    "assigned_at": station_user.assigned_at,
                    "expires_at": station_user.expires_at,
                }

                station_assignments.append(assignment)

                if station_user.is_primary_station:
                    primary_station_id = station_user.station_id

            # If no primary station, use the first one
            if not primary_station_id and station_assignments:
                primary_station_id = station_assignments[0]["station_id"]

            return StationContext(
                user_id=user.id,
                station_assignments=station_assignments,
                primary_station_id=primary_station_id,
            )

        except Exception:
            # Log error but don't expose details
            return None

    def create_station_aware_jwt_tokens(
        self,
        user: User,
        session_id: UUID,
        station_context: StationContext,
        target_station_id: UUID | None = None,
    ) -> tuple[str, str, str, str]:
        """Create JWT tokens with station context embedded."""
        now = datetime.utcnow()

        # Determine which station to include in token
        current_station_id = target_station_id or station_context.current_station_id
        station_role = station_context.get_role_for_station(current_station_id)
        station_permissions = station_context.get_permissions_for_station(current_station_id)

        # Access token with station context
        access_jti = str(uuid4())
        access_payload = {
            "iss": self.jwt_issuer,
            "sub": str(user.id),
            "aud": "myhibachi-api",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "jti": access_jti,
            "typ": "access",
            "session_id": str(session_id),
            # Original role and permissions (for backward compatibility)
            "role": user.role,
            "permissions": list(self.get_user_permissions(user)),
            # Station-specific context
            "station_context": {
                "current_station_id": str(current_station_id),
                "station_role": station_role.value if station_role else None,
                "station_permissions": list(station_permissions),
                "accessible_stations": [str(sid) for sid in station_context.accessible_station_ids],
                "is_super_admin": station_context.is_super_admin,
                "is_admin": station_context.is_admin,
                "highest_role": station_context.highest_role.value,
            },
        }

        # Refresh token (minimal station info)
        refresh_jti = str(uuid4())
        refresh_payload = {
            "iss": self.jwt_issuer,
            "sub": str(user.id),
            "aud": "myhibachi-api",
            "iat": now,
            "exp": now + self.refresh_lifetime,
            "jti": refresh_jti,
            "typ": "refresh",
            "session_id": str(session_id),
            "primary_station_id": (
                str(station_context.primary_station_id)
                if station_context.primary_station_id
                else None
            ),
        }

        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        return access_token, refresh_token, access_jti, refresh_jti

    async def create_station_access_token(
        self,
        db: AsyncSession,
        user: User,
        session: UserSession,
        station_id: UUID,
        station_context: StationContext,
    ) -> StationAccessToken | None:
        """Create a station-specific access token for enhanced security."""
        try:
            # Verify user can access this station
            if not station_context.can_access_station(station_id):
                return None

            # Get role and permissions for this station
            role = station_context.get_role_for_station(station_id)
            permissions = station_context.get_permissions_for_station(station_id)

            if not role:
                return None

            # Generate token
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            jwt_id = str(uuid4())

            # Create station token record
            station_token = StationAccessToken(
                user_id=user.id,
                station_id=station_id,
                session_id=session.id,
                token_hash=token_hash,
                jwt_id=jwt_id,
                role=role.value,
                permissions=list(permissions),
                expires_at=datetime.utcnow() + self.station_token_lifetime,
            )

            db.add(station_token)
            await db.commit()
            await db.refresh(station_token)

            return station_token

        except Exception:
            await db.rollback()
            return None

    async def verify_station_access_token(
        self, db: AsyncSession, token: str, station_id: UUID
    ) -> StationAccessToken | None:
        """Verify and return station access token if valid."""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            stmt = select(StationAccessToken).where(
                and_(
                    StationAccessToken.token_hash == token_hash,
                    StationAccessToken.station_id == station_id,
                    not StationAccessToken.is_revoked,
                    StationAccessToken.expires_at > datetime.utcnow(),
                )
            )

            result = await db.execute(stmt)
            station_token = result.scalar_one_or_none()

            return station_token

        except Exception:
            return None

    async def revoke_station_tokens(
        self, db: AsyncSession, user_id: UUID, station_id: UUID | None = None
    ) -> bool:
        """Revoke station access tokens for user (optionally for specific station)."""
        try:
            from sqlalchemy import update

            conditions = [StationAccessToken.user_id == user_id, not StationAccessToken.is_revoked]

            if station_id:
                conditions.append(StationAccessToken.station_id == station_id)

            stmt = (
                update(StationAccessToken)
                .where(and_(*conditions))
                .values(is_revoked=True, revoked_at=datetime.utcnow())
            )

            await db.execute(stmt)
            await db.commit()

            return True

        except Exception:
            await db.rollback()
            return False

    async def log_station_action(
        self,
        db: AsyncSession,
        station_id: UUID,
        user_id: UUID,
        session_id: UUID | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_role: str | None = None,
        permissions_used: list[str] | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> StationAuditLog:
        """Log station-scoped action for audit trail."""
        try:
            audit_log = StationAuditLog(
                station_id=station_id,
                user_id=user_id,
                session_id=session_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_role=user_role,
                permissions_used=permissions_used,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
            )

            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)

            return audit_log

        except Exception:
            await db.rollback()
            # Create a minimal log entry even if commit fails
            return StationAuditLog(
                station_id=station_id,
                user_id=user_id,
                action=action,
                success=False,
                error_message="Failed to log action",
            )

    def extract_station_context_from_token(
        self, token_payload: dict[str, Any]
    ) -> StationContext | None:
        """Extract station context from JWT token payload."""
        try:
            station_context_data = token_payload.get("station_context")
            if not station_context_data:
                return None

            user_id = UUID(token_payload["sub"])
            current_station_id = UUID(station_context_data["current_station_id"])
            accessible_stations = [UUID(sid) for sid in station_context_data["accessible_stations"]]

            # Reconstruct station assignments (minimal info from token)
            station_assignments = [
                {
                    "station_id": current_station_id,
                    "role": station_context_data["station_role"],
                    "permissions": station_context_data["station_permissions"],
                    "is_primary": True,  # Assume current is primary for token context
                }
            ]

            context = StationContext(
                user_id=user_id,
                station_assignments=station_assignments,
                primary_station_id=current_station_id,
                current_station_id=current_station_id,
            )

            # Override accessible stations from token
            context.station_roles = dict.fromkeys(
                accessible_stations, station_context_data["station_role"]
            )
            context.station_permissions = {
                sid: set(station_context_data["station_permissions"]) for sid in accessible_stations
            }
            context.highest_role = StationRole(station_context_data["highest_role"])

            return context

        except Exception:
            return None

    async def switch_station_context(
        self,
        db: AsyncSession,
        user: User,
        current_station_context: StationContext,
        target_station_id: UUID,
        session_id: UUID,
    ) -> tuple[str, str, str, str] | None:
        """Switch user's current station context and generate new tokens."""
        try:
            # Verify user can access target station
            if not current_station_context.can_access_station(target_station_id):
                return None

            # Update station context
            current_station_context.current_station_id = target_station_id

            # Generate new tokens with updated station context
            access_token, refresh_token, access_jti, refresh_jti = (
                self.create_station_aware_jwt_tokens(
                    user, session_id, current_station_context, target_station_id
                )
            )

            # Log the station switch
            await self.log_station_action(
                db=db,
                station_id=target_station_id,
                user_id=user.id,
                session_id=session_id,
                action="STATION_SWITCH",
                details={
                    "from_station": str(current_station_context.primary_station_id),
                    "to_station": str(target_station_id),
                },
                success=True,
            )

            return access_token, refresh_token, access_jti, refresh_jti

        except Exception:
            return None


__all__ = ["StationAuthenticationService", "StationContext"]
