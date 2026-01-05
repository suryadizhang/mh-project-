"""
Google OAuth Service
Handles Google OAuth 2.0 authentication flow
"""

import logging
import os
from pathlib import Path
import secrets
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
import httpx

# Load environment variables from parent directory (apps/backend/.env)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """
    Google OAuth 2.0 service for user authentication

    Features:
    - OAuth 2.0 authorization code flow
    - Token exchange
    - User profile fetching
    - Token refresh (for future use)

    Note: Credentials are lazy-loaded via properties to support GSM initialization.
    GSM exports secrets to os.environ AFTER module imports, so we must read
    credentials on first use, not at instantiation time.
    """

    # Google OAuth endpoints
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    # Scopes needed for user authentication
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self):
        """
        Initialize Google OAuth service.

        Note: Credentials are NOT loaded here - they are lazy-loaded via properties
        to support GSM (Google Secret Manager) which exports secrets to os.environ
        AFTER all modules are imported but BEFORE the first request is handled.
        """
        # Internal cache for credentials (None = not yet loaded)
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._redirect_uri: str | None = None
        self._credentials_loaded = False

    def _load_credentials(self) -> None:
        """Load credentials from environment (called on first use)"""
        if self._credentials_loaded:
            return

        self._client_id = os.getenv("GOOGLE_CLIENT_ID")
        self._client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self._redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:3001/auth/google/callback"
        )
        self._credentials_loaded = True

        if not self._client_id or not self._client_secret:
            logger.warning("Google OAuth credentials not configured")
        else:
            logger.info("✅ Google OAuth credentials loaded successfully")

    @property
    def client_id(self) -> str | None:
        """Get Google OAuth client ID (lazy-loaded from environment)"""
        self._load_credentials()
        return self._client_id

    @property
    def client_secret(self) -> str | None:
        """Get Google OAuth client secret (lazy-loaded from environment)"""
        self._load_credentials()
        return self._client_secret

    @property
    def redirect_uri(self) -> str:
        """Get OAuth redirect URI (lazy-loaded from environment)"""
        self._load_credentials()
        return self._redirect_uri or "http://localhost:3001/auth/google/callback"

    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)

    def generate_state_token(self) -> str:
        """
        Generate a random state token for CSRF protection

        Returns:
            Random 32-character hex string
        """
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str, redirect_uri: str | None = None) -> str:
        """
        Generate Google OAuth authorization URL

        Args:
            state: CSRF protection token (store in session)
            redirect_uri: Optional override for redirect URI

        Returns:
            Authorization URL to redirect user to
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured",
            )

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent to get refresh token
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str | None = None
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from Google callback
            redirect_uri: Optional override for redirect URI (must match authorization)

        Returns:
            Dict with access_token, token_type, expires_in, refresh_token (optional)

        Raises:
            HTTPException: If token exchange fails
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured",
            )

        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to exchange code for token: {response.text}",
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.exception(f"Token exchange request error: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to Google OAuth service",
            )

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user profile information from Google

        Args:
            access_token: OAuth access token

        Returns:
            Dict with id, email, verified_email, name, given_name, family_name, picture

        Raises:
            HTTPException: If user info fetch fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code != 200:
                    logger.error(f"User info fetch failed: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to fetch user information from Google",
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.exception(f"User info request error: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to Google OAuth service",
            )

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an expired access token

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Dict with new access_token, token_type, expires_in

        Raises:
            HTTPException: If token refresh fails
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured",
            )

        data = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to refresh access token",
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.exception(f"Token refresh request error: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to Google OAuth service",
            )


# Singleton instance
google_oauth_service = GoogleOAuthService()
