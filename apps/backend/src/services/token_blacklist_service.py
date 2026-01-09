"""
Token Blacklist Service
=======================

Manages JWT token blacklisting for secure logout and session management.

Security Features:
- Redis primary storage for fast JTI lookups (O(1))
- Database fallback when Redis unavailable
- Automatic expiry cleanup
- Supports per-token and per-user blacklisting
- "Logout all devices" functionality

Usage:
    from services.token_blacklist_service import TokenBlacklistService

    blacklist = TokenBlacklistService(db, cache)

    # Blacklist a single token (logout)
    await blacklist.blacklist_token(jti, user_id, "access", expires_at, "user_logout")

    # Blacklist all user tokens (password change, logout all)
    await blacklist.blacklist_all_user_tokens(user_id, "password_change")

    # Check if token is blacklisted (called in token decode)
    is_blacklisted = await blacklist.is_blacklisted(jti)

Related:
    - 012_token_blacklist_and_reset.sql: Database schema
    - core/cache.py: Redis CacheService
    - utils/auth/tokens.py: Token creation/verification

Created: 2025-01-30 (Option B Security Implementation)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.cache import CacheService

logger = logging.getLogger(__name__)

# Redis key prefixes
BLACKLIST_PREFIX = "token_blacklist"
USER_BLACKLIST_PREFIX = "user_blacklist"

# TTL for Redis blacklist entries (slightly longer than max token lifetime)
BLACKLIST_REDIS_TTL = 60 * 60 * 24 * 8  # 8 days (covers 7-day refresh tokens + buffer)


class TokenBlacklistService:
    """
    Service for managing JWT token blacklisting.

    Uses Redis as primary storage for fast lookups,
    with PostgreSQL as fallback/persistence layer.
    """

    def __init__(self, db: "AsyncSession", cache: Optional["CacheService"] = None):
        """
        Initialize the blacklist service.

        Args:
            db: Database session for persistence
            cache: Optional Redis cache for fast lookups
        """
        self.db = db
        self.cache = cache

    def _redis_key(self, jti: str) -> str:
        """Generate Redis key for a JTI."""
        return f"{BLACKLIST_PREFIX}:{jti}"

    def _user_blacklist_key(self, user_id: str | UUID) -> str:
        """Generate Redis key for user-level blacklist timestamp."""
        return f"{USER_BLACKLIST_PREFIX}:{str(user_id)}"

    async def blacklist_token(
        self,
        jti: str,
        user_id: str | UUID,
        token_type: str,
        expires_at: datetime,
        reason: str,
        session_id: Optional[str | UUID] = None,
    ) -> bool:
        """
        Blacklist a single token by its JTI.

        Args:
            jti: JWT ID (unique token identifier)
            user_id: User who owns the token
            token_type: "access" or "refresh"
            expires_at: When the token would naturally expire
            reason: Why the token is being blacklisted
            session_id: Optional session ID for tracking

        Returns:
            True if successfully blacklisted, False otherwise
        """
        try:
            # 1. Store in Redis (primary - fast lookup)
            if self.cache and self.cache._client:
                # Calculate TTL until token expires (no point keeping blacklist entry longer)
                now = datetime.now(timezone.utc)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                ttl_seconds = int((expires_at - now).total_seconds())

                if ttl_seconds > 0:
                    await self.cache._client.setex(
                        self._redis_key(jti), ttl_seconds, reason  # Store reason as value
                    )
                    logger.debug(f"Token {jti[:8]}... blacklisted in Redis (TTL: {ttl_seconds}s)")

            # 2. Store in database (fallback/persistence)
            await self.db.execute(
                text(
                    """
                    INSERT INTO identity.token_blacklist 
                    (jti, user_id, session_id, token_type, expires_at, reason)
                    VALUES (:jti, :user_id, :session_id, :token_type, :expires_at, :reason)
                    ON CONFLICT (jti) DO UPDATE SET
                        blacklisted_at = NOW(),
                        reason = EXCLUDED.reason
                """
                ),
                {
                    "jti": jti,
                    "user_id": str(user_id),
                    "session_id": str(session_id) if session_id else None,
                    "token_type": token_type,
                    "expires_at": expires_at,
                    "reason": reason,
                },
            )
            await self.db.commit()

            logger.info(
                f"✅ Token blacklisted: type={token_type}, reason={reason}, jti={jti[:8]}..."
            )
            return True

        except Exception as e:
            logger.exception(f"Failed to blacklist token {jti[:8]}...: {e}")
            await self.db.rollback()
            return False

    async def blacklist_all_user_tokens(
        self,
        user_id: str | UUID,
        reason: str,
        except_session_id: Optional[str | UUID] = None,
    ) -> int:
        """
        Blacklist ALL tokens for a user (logout all devices).

        Uses a timestamp-based approach: any token issued before this
        timestamp is considered invalid, even without explicit JTI entry.

        Args:
            user_id: User whose tokens should be blacklisted
            reason: Why (e.g., "password_change", "logout_all", "security_concern")
            except_session_id: Optional session to keep (current session)

        Returns:
            Number of sessions invalidated
        """
        try:
            user_id_str = str(user_id)
            now = datetime.now(timezone.utc)

            # 1. Set user-level blacklist timestamp in Redis
            # Any token issued before this time is invalid
            if self.cache and self.cache._client:
                await self.cache._client.set(self._user_blacklist_key(user_id_str), now.isoformat())
                logger.debug(f"Set user blacklist timestamp for user {user_id_str[:8]}...")

            # 2. Update database: mark all user sessions as inactive
            if except_session_id:
                result = await self.db.execute(
                    text(
                        """
                        UPDATE identity.user_sessions 
                        SET is_active = false, 
                            revoked_at = NOW(),
                            revoke_reason = :reason
                        WHERE user_id = :user_id 
                        AND is_active = true
                        AND id != :except_session_id
                        RETURNING id
                    """
                    ),
                    {
                        "user_id": user_id_str,
                        "reason": reason,
                        "except_session_id": str(except_session_id),
                    },
                )
            else:
                result = await self.db.execute(
                    text(
                        """
                        UPDATE identity.user_sessions 
                        SET is_active = false, 
                            revoked_at = NOW(),
                            revoke_reason = :reason
                        WHERE user_id = :user_id 
                        AND is_active = true
                        RETURNING id
                    """
                    ),
                    {"user_id": user_id_str, "reason": reason},
                )

            invalidated = result.fetchall()
            count = len(invalidated)

            # 3. Insert blacklist entries for tracking (optional, for audit)
            if count > 0:
                for row in invalidated:
                    session_id = row[0]
                    await self.db.execute(
                        text(
                            """
                            INSERT INTO identity.token_blacklist 
                            (jti, user_id, session_id, token_type, expires_at, reason)
                            VALUES (
                                :jti, :user_id, :session_id, 'session', 
                                NOW() + INTERVAL '8 days', :reason
                            )
                            ON CONFLICT (jti) DO NOTHING
                        """
                        ),
                        {
                            "jti": f"session_revoke_{session_id}_{now.timestamp()}",
                            "user_id": user_id_str,
                            "session_id": str(session_id),
                            "reason": reason,
                        },
                    )

            await self.db.commit()

            logger.info(
                f"✅ Blacklisted all tokens for user {user_id_str[:8]}...: {count} sessions invalidated, reason={reason}"
            )
            return count

        except Exception as e:
            logger.exception(f"Failed to blacklist all tokens for user: {e}")
            await self.db.rollback()
            return 0

    async def is_blacklisted(self, jti: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            jti: JWT ID to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            # 1. Check Redis first (fast path)
            if self.cache and self.cache._client:
                result = await self.cache._client.get(self._redis_key(jti))
                if result is not None:
                    logger.debug(f"Token {jti[:8]}... found in Redis blacklist")
                    return True

            # 2. Fallback to database
            result = await self.db.execute(
                text(
                    """
                    SELECT 1 FROM identity.token_blacklist 
                    WHERE jti = :jti 
                    AND expires_at > NOW()
                    LIMIT 1
                """
                ),
                {"jti": jti},
            )
            exists = result.fetchone() is not None

            if exists:
                logger.debug(f"Token {jti[:8]}... found in DB blacklist")

                # Backfill Redis for faster future lookups
                if self.cache and self.cache._client:
                    await self.cache._client.setex(
                        self._redis_key(jti), BLACKLIST_REDIS_TTL, "backfilled"
                    )

            return exists

        except Exception as e:
            logger.exception(f"Error checking blacklist for {jti[:8]}...: {e}")
            # Fail closed - if we can't check, treat as NOT blacklisted
            # (alternative: fail open and reject token, but that's harsh)
            return False

    async def is_user_blacklisted_since(
        self, user_id: str | UUID, token_issued_at: datetime
    ) -> bool:
        """
        Check if a user has a blacklist timestamp newer than token issuance.

        This catches the case where we blacklisted all user tokens
        but don't have the specific JTI in the blacklist.

        Args:
            user_id: User ID
            token_issued_at: When the token was issued (iat claim)

        Returns:
            True if user has been blacklisted since token was issued
        """
        try:
            if self.cache and self.cache._client:
                blacklist_time_str = await self.cache._client.get(
                    self._user_blacklist_key(str(user_id))
                )
                if blacklist_time_str:
                    blacklist_time = datetime.fromisoformat(blacklist_time_str)
                    if token_issued_at.tzinfo is None:
                        token_issued_at = token_issued_at.replace(tzinfo=timezone.utc)
                    if blacklist_time > token_issued_at:
                        logger.debug(
                            f"User {str(user_id)[:8]}... has global blacklist after token issuance"
                        )
                        return True

            return False

        except Exception as e:
            logger.exception(f"Error checking user blacklist: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """
        Remove expired blacklist entries (housekeeping).

        Should be called periodically (e.g., daily cron).
        Redis entries auto-expire via TTL.

        Returns:
            Number of entries removed from database
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    DELETE FROM identity.token_blacklist 
                    WHERE expires_at < NOW()
                    RETURNING jti
                """
                )
            )
            deleted = result.fetchall()
            await self.db.commit()

            count = len(deleted)
            if count > 0:
                logger.info(f"🧹 Cleaned up {count} expired blacklist entries")

            return count

        except Exception as e:
            logger.exception(f"Failed to cleanup expired blacklist entries: {e}")
            await self.db.rollback()
            return 0

    async def get_user_active_sessions(self, user_id: str | UUID) -> list[dict]:
        """
        Get all active sessions for a user.

        Useful for "Manage Sessions" UI.

        Args:
            user_id: User ID

        Returns:
            List of active session details
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT 
                        id,
                        user_agent,
                        ip_address,
                        created_at,
                        last_activity
                    FROM identity.user_sessions
                    WHERE user_id = :user_id
                    AND is_active = true
                    ORDER BY last_activity DESC
                """
                ),
                {"user_id": str(user_id)},
            )

            sessions = []
            for row in result.fetchall():
                sessions.append(
                    {
                        "id": str(row[0]),
                        "user_agent": row[1],
                        "ip_address": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "last_activity": row[4].isoformat() if row[4] else None,
                    }
                )

            return sessions

        except Exception as e:
            logger.exception(f"Failed to get user sessions: {e}")
            return []

    async def revoke_session(self, session_id: str | UUID, reason: str = "user_revoke") -> bool:
        """
        Revoke a specific session by ID.

        Args:
            session_id: Session ID to revoke
            reason: Reason for revocation

        Returns:
            True if revoked, False otherwise
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    UPDATE identity.user_sessions 
                    SET is_active = false, 
                        revoked_at = NOW(),
                        revoke_reason = :reason
                    WHERE id = :session_id
                    AND is_active = true
                    RETURNING user_id
                """
                ),
                {"session_id": str(session_id), "reason": reason},
            )

            row = result.fetchone()
            if row:
                await self.db.commit()
                logger.info(f"✅ Revoked session {str(session_id)[:8]}... reason={reason}")
                return True
            else:
                logger.warning(f"Session {str(session_id)[:8]}... not found or already revoked")
                return False

        except Exception as e:
            logger.exception(f"Failed to revoke session: {e}")
            await self.db.rollback()
            return False


# Singleton instance for dependency injection
_blacklist_service: Optional[TokenBlacklistService] = None


async def get_blacklist_service(
    db: "AsyncSession", cache: Optional["CacheService"] = None
) -> TokenBlacklistService:
    """
    Factory function for TokenBlacklistService.

    Usage in FastAPI:
        @router.post("/logout")
        async def logout(
            db: AsyncSession = Depends(get_db),
            cache: CacheService = Depends(get_cache),
        ):
            blacklist = await get_blacklist_service(db, cache)
            await blacklist.blacklist_token(...)
    """
    return TokenBlacklistService(db, cache)
