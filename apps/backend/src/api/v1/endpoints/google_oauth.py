"""
Google OAuth Authentication Endpoints

Handles Google OAuth 2.0 login flow:
1. User clicks "Sign in with Google"
2. Redirect to Google authorization
3. Google redirects back with code
4. Exchange code for token
5. Fetch user profile
6. Create or update user in database
7. Return JWT token

Features:
- Pending approval workflow for new users
- Super admin approval required
- Automatic email verification (Google verifies emails)
"""

from datetime import datetime, timezone
import logging

from core.config import get_settings
from core.database import get_db
from core.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from models.user import AuthProvider, User, UserStatus
from pydantic import BaseModel
from services.google_oauth import google_oauth_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
async def google_authorize(request: Request, redirect_url: str | None = None):
    """
    Step 1: Redirect user to Google OAuth authorization page

    Query params:
        redirect_url: Optional URL to redirect to after successful login

    Returns:
        Redirect to Google authorization page
    """
    if not google_oauth_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Please contact administrator.",
        )

    # Generate state token for CSRF protection
    state = google_oauth_service.generate_state_token()

    # Store state and redirect URL in session (you'll need to implement session storage)
    # For now, we'll include redirect_url in state (not production-ready)

    # Get authorization URL
    auth_url = google_oauth_service.get_authorization_url(state)

    logger.info(f"Redirecting to Google OAuth: {auth_url}")

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_callback(
    code: str, state: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Handle Google OAuth callback

    Query params:
        code: Authorization code from Google
        state: CSRF protection token

    Returns:
        Redirect to frontend with token or error
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code not provided"
        )

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

        # Check if user already exists
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        is_new_user = False

        if not user:
            # Check if email already exists (maybe registered with email/password)
            result = await db.execute(select(User).where(User.email == email.lower()))
            user = result.scalar_one_or_none()

            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.auth_provider = AuthProvider.GOOGLE
                user.avatar_url = avatar_url or user.avatar_url
                user.is_email_verified = email_verified
                user.email_verified_at = (
                    datetime.now(timezone.utc) if email_verified else user.email_verified_at
                )
            else:
                # Create new user with PENDING status (awaiting approval)
                user = User(
                    email=email.lower(),
                    full_name=full_name,
                    avatar_url=avatar_url,
                    auth_provider=AuthProvider.GOOGLE,
                    google_id=google_id,
                    status=UserStatus.PENDING,  # Requires super admin approval
                    is_email_verified=email_verified,
                    email_verified_at=datetime.now(timezone.utc) if email_verified else None,
                )
                db.add(user)
                is_new_user = True

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = request.client.host if request.client else None
        user.last_activity_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        # Send welcome email for new users
        if is_new_user:
            try:
                from services.email_service import email_service

                email_service.send_welcome_email(user.email, user.full_name)
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {user.email}: {e}")

        # Check if user is approved
        if user.status == UserStatus.PENDING:
            logger.info(f"New user {email} signed up via Google - awaiting approval")

            # Return to frontend with pending approval message
            frontend_url = settings.FRONTEND_URL or "http://localhost:3001"
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
        frontend_url = settings.FRONTEND_URL or "http://localhost:3001"
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={jwt_token}&new_user={is_new_user}"
        )

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
