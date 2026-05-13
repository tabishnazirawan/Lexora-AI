# app/core/oauth.py

import httpx  # type: ignore[import]
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# Google OAuth 2.0 Constants
# ----------------------------------------------------------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


# ----------------------------------------------------------------
# Step 1: Build Google Authorization URL
# ----------------------------------------------------------------

def build_google_auth_url(state: Optional[str] = None) -> str:
    """
    Builds the Google OAuth 2.0 authorization URL to redirect
    the user to Google's login consent screen.

    Args:
        state: Optional CSRF protection state string.

    Returns:
        Full Google authorization URL string.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{GOOGLE_AUTH_URL}?{query_string}"

    logger.debug(f"Built Google auth URL: {url}")
    return url


# ----------------------------------------------------------------
# Step 2: Exchange Authorization Code for Tokens
# ----------------------------------------------------------------

async def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchanges the Google authorization code for access + id tokens.

    Args:
        code: Authorization code received from Google callback.

    Returns:
        Dictionary containing access_token, id_token, etc.

    Raises:
        ValueError: If token exchange fails.
    """
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )

    if response.status_code != 200:
        logger.error(
            f"Google token exchange failed: "
            f"{response.status_code} — {response.text}"
        )
        raise ValueError("Failed to exchange Google authorization code for tokens.")

    return response.json()


# ----------------------------------------------------------------
# Step 3: Fetch Google User Info
# ----------------------------------------------------------------

async def get_google_user_info(access_token: str) -> dict:
    """
    Fetches the authenticated user's profile from Google.

    Args:
        access_token: Google OAuth access token.

    Returns:
        Dictionary with user info:
            - sub (Google user ID)
            - email
            - name
            - picture (avatar URL)
            - email_verified

    Raises:
        ValueError: If user info fetch fails.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )

    if response.status_code != 200:
        logger.error(
            f"Google userinfo fetch failed: "
            f"{response.status_code} — {response.text}"
        )
        raise ValueError("Failed to fetch user info from Google.")

    user_info = response.json()

    if not user_info.get("email_verified", False):
        raise ValueError("Google account email is not verified.")

    logger.info(f"Google OAuth user fetched: {user_info.get('email')}")
    return user_info


# ----------------------------------------------------------------
# Convenience: Full OAuth Flow (code → user info)
# ----------------------------------------------------------------

async def get_google_user_from_code(code: str) -> dict:
    """
    Convenience function: runs the full Google OAuth flow.
    Exchanges code for tokens, then fetches user profile.

    Args:
        code: Authorization code from Google callback.

    Returns:
        Google user info dictionary.

    Raises:
        ValueError: If any step of the OAuth flow fails.
    """
    tokens = await exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")

    if not access_token:
        raise ValueError("No access token returned from Google.")

    return await get_google_user_info(access_token)