"""
Google OAuth Authentication Endpoints

Handles Google OAuth 2.0 login flow:
1. User clicks "Sign in with Google"
2. Redirect to Google authorization
3. Google redirects back with code
4. Exchange code for token
5. Fetch user profile
6. Create or link GoogleOAuthAccount
7. Return JWT token

Features:
- Pending approval workflow for new users
- Super admin approval required
- Automatic email verification (Google verifies emails)
- Uses GoogleOAuthAccount table for OAuth linking
"""

from datetime import datetime, timezone
import logging

from core.config import get_settings
from core.database import get_db
from core.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from db.models.identity import User, UserStatus, UserRole, AuthProvider
from db.models.identity.admin import GoogleOAuthAccount
from pydantic import BaseModel
from services.google_oauth import google_oauth_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])
logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleAuthResponse(BaseModel):
    """Response from Google OAuth authentication"""

    access_token: str
    token_type: str = "bearer"
    user: dict
    is_new_user: bool
    requires_approval: bool


@router.get("/authorize")
async def google_authorize(
    request: Request, redirect_url: str | None = None, origin: str | None = None
):
    """
    Step 1: Redirect user to Google OAuth authorization page

    Query params:
        redirect_url: Optional URL to redirect to after successful login (deprecated)
        origin: Frontend origin URL (e.g., https://admin.mysticdatanode.net)
                Used to redirect back to the correct frontend after OAuth

    Returns:
        Redirect to Google authorization page
    """
    if not google_oauth_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Please contact administrator.",
        )

    # Use origin parameter, falling back to redirect_url for backwards compatibility
    frontend_origin = origin or redirect_url

    # Generate state token with origin URL encoded for CSRF protection
    # This allows the callback to know which frontend to redirect to
    state = google_oauth_service.generate_state_token(origin_url=frontend_origin)

    # Get authorization URL
    auth_url = google_oauth_service.get_authorization_url(state)

    logger.info(f"Redirecting to Google OAuth. Origin: {frontend_origin}")

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_callback(
    code: str, state: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Handle Google OAuth callback

    Query params:
        code: Authorization code from Google
        state: CSRF protection token (may contain encoded origin URL)

    Returns:
        Redirect to frontend with token or error
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code not provided"
        )

    # Decode state to get CSRF token and origin URL
    csrf_token, origin_url = google_oauth_service.decode_state_token(state)

    # Determine redirect URL: use origin from state, or fall back to FRONTEND_URL
    frontend_url = origin_url or settings.FRONTEND_URL or "http://localhost:3001"

    logger.info(f"OAuth callback - Origin from state: {origin_url}, Using: {frontend_url}")

    try:
        # Exchange code for access token
        token_data = await google_oauth_service.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token from Google",
            )

        # Fetch user info from Google
        user_info = await google_oauth_service.get_user_info(access_token)

        google_id = user_info.get("id")
        email = user_info.get("email")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")
        email_verified = user_info.get("verified_email", False)

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get required user information from Google",
            )

        # Check if Google OAuth account already exists
        result = await db.execute(
            select(GoogleOAuthAccount).where(GoogleOAuthAccount.provider_account_id == google_id)
        )
        oauth_account = result.scalar_one_or_none()

        user = None
        is_new_user = False

        if oauth_account:
            # OAuth account exists - get the linked user
            # Use selectinload to eagerly load user_roles and role for is_super_admin check
            result = await db.execute(
                select(User)
                .where(User.id == oauth_account.user_id)
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"OAuth account {google_id} has no linked user")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OAuth account has no linked user - contact administrator",
                )

            # Update OAuth account with latest info
            oauth_account.provider_account_email = email.lower()
            oauth_account.profile_picture_url = avatar_url
            oauth_account.last_login_at = datetime.now(timezone.utc)
        else:
            # No OAuth account - check if email already exists
            # Use selectinload to eagerly load user_roles and role for is_super_admin check
            result = await db.execute(
                select(User)
                .where(User.email == email.lower())
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
            )
            user = result.scalar_one_or_none()

            if user:
                # Link Google account to existing user
                oauth_account = GoogleOAuthAccount(
                    user_id=user.id,
                    provider="google",
                    provider_account_id=google_id,
                    provider_account_email=email.lower(),
                    profile_picture_url=avatar_url,
                    is_approved=user.status == UserStatus.ACTIVE,  # Auto-approve if user is active
                    approved_at=(
                        datetime.now(timezone.utc) if user.status == UserStatus.ACTIVE else None
                    ),
                )
                db.add(oauth_account)
                logger.info(f"Linked Google account {google_id} to existing user {user.email}")
            else:
                # Create new user with PENDING status (awaiting approval)
                user = User(
                    email=email.lower(),
                    first_name=full_name.split()[0] if full_name else None,
                    last_name=(
                        " ".join(full_name.split()[1:])
                        if full_name and len(full_name.split()) > 1
                        else None
                    ),
                    avatar_url=avatar_url,
                    status=UserStatus.PENDING,  # Requires super admin approval
                    auth_provider=AuthProvider.GOOGLE,  # Set auth provider for Google OAuth
                )
                db.add(user)
                await db.flush()  # Get user.id for OAuth account

                # Create OAuth account linked to new user
                oauth_account = GoogleOAuthAccount(
                    user_id=user.id,
                    provider="google",
                    provider_account_id=google_id,
                    provider_account_email=email.lower(),
                    profile_picture_url=avatar_url,
                    is_approved=False,  # Needs approval
                )
                db.add(oauth_account)
                is_new_user = True
                logger.info(f"Created new user {email} via Google OAuth - pending approval")

        # Update user's last login
        user.last_login_at = datetime.now(timezone.utc)
        user.avatar_url = avatar_url or user.avatar_url

        await db.commit()

        # Re-fetch user with eager-loaded relationships for is_super_admin check
        # db.refresh() doesn't load relationships, so we need to query again
        result = await db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        user = result.scalar_one()

        # Send welcome email for new users
        if is_new_user:
            try:
                from services.email_service import email_service

                first_name = user.first_name or full_name or "there"
                email_service.send_welcome_email(user.email, first_name)
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {user.email}: {e}")

        # Check if user is approved
        if user.status == UserStatus.PENDING:
            logger.info(f"New user {email} signed up via Google - awaiting approval")

            # Return to frontend with pending approval message
            # Uses frontend_url determined at start of callback (from state or FRONTEND_URL)
            return RedirectResponse(url=f"{frontend_url}/auth/pending-approval?email={email}")

        elif user.status != UserStatus.ACTIVE:
            # User is suspended or deactivated
            logger.warning(f"User {email} attempted login but account is {user.status}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status}. Please contact administrator.",
            )

        # Generate JWT token for the user
        jwt_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "is_super_admin": user.is_super_admin}
        )

        logger.info(f"User {email} logged in successfully via Google OAuth")

        # Redirect to frontend with token
        # Uses frontend_url determined at start of callback (from state or FRONTEND_URL)
        redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}&new_user={is_new_user}"
        logger.info(f"Redirecting to: {redirect_url[:100]}...")  # Log first 100 chars for debugging

        # Use 302 Found instead of default 307 - browser will follow redirect properly
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e!s}", exc_info=True)
        logger.exception(f"Error type: {type(e).__name__}")
        logger.exception(f"Code received: {code[:20] if code else 'None'}...")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during Google authentication: {e!s}",
        )


# TODO: Implement link-account endpoint after get_current_user dependency is ready
# @router.post("/link-account")
# async def link_google_account(
#     access_token: str,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Link Google account to existing logged-in user"""
#     pass
