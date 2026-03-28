"""
Auth Module — GitHub + Bitbucket OAuth + JWT Authentication
=============================================================
Handles:
  1. GitHub OAuth flow (redirect → callback → token exchange)
  2. Bitbucket OAuth 2.0 flow (redirect → callback → token exchange)
  3. JWT creation and verification
  4. Auth dependency for protected endpoints
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from database import get_session
from models import User

# Ensure .env is loaded even when this module is imported before config.py
load_dotenv(override=True)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ═══════════════════════════════════════════
# Config — read at runtime so they always pick up the loaded .env
# ═══════════════════════════════════════════

def _cfg(key: str, default: str = "") -> str:
    """Read env var at call time (not import time) so dotenv is already loaded."""
    return os.getenv(key, default)


JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72  # 3 days
_JWT_SECRET: Optional[str] = None

PRODUCTION = os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes")

def _jwt_secret() -> str:
    """Get JWT secret. Required in production; auto-generated (with warning) in dev."""
    global _JWT_SECRET
    if _JWT_SECRET is None:
        env_secret = os.getenv("JWT_SECRET")
        if env_secret:
            _JWT_SECRET = env_secret
        elif PRODUCTION:
            raise RuntimeError(
                "JWT_SECRET environment variable is REQUIRED in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        else:
            _JWT_SECRET = secrets.token_hex(32)
            import logging
            logging.getLogger("agenticpr.auth").warning(
                "⚠ JWT_SECRET not set — auto-generated for dev. "
                "Set JWT_SECRET env var for production!"
            )
    return _JWT_SECRET


# ═══════════════════════════════════════════
# JWT Helpers
# ═══════════════════════════════════════════

def create_token(user_id: int, username: str, provider: str = "github") -> str:
    """Create a JWT token for a user."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "provider": provider,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    FastAPI dependency: Extract user from Authorization header.
    Usage: user = Depends(get_current_user)
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ", 1)[1]
    payload = verify_token(token)
    
    user_id = int(payload["sub"])
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# ═══════════════════════════════════════════
# GitHub OAuth Endpoints
# ═══════════════════════════════════════════

@router.get("/github")
async def github_login():
    """Redirect user to GitHub OAuth authorization page."""
    client_id = _cfg("GITHUB_CLIENT_ID")
    frontend_url = _cfg("FRONTEND_URL", "http://localhost:8080")
    if not client_id:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID not configured")
    
    params = urlencode({
        "client_id": client_id,
        "scope": "repo read:user user:email",
        "redirect_uri": f"{frontend_url}/auth/callback",
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@router.post("/callback")
async def github_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Exchange GitHub OAuth code for access token, create/update user, return JWT.
    Called by the frontend after GitHub redirects back with ?code=xxx.
    """
    body = await request.json()
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter")
    
    gh_client_id = _cfg("GITHUB_CLIENT_ID")
    gh_client_secret = _cfg("GITHUB_CLIENT_SECRET")
    if not gh_client_id or not gh_client_secret:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    # 1. Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": gh_client_id,
                "client_secret": gh_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
    
    access_token = token_data.get("access_token")
    if not access_token:
        error = token_data.get("error_description", "Unknown error")
        print(f"🚨 GITHUB TOKEN EXCHANGE FAILED: {token_data}")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {error}")
    
    # 2. Fetch GitHub user profile
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AgenticPR-App"
            },
        )
        
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch user profile: {user_resp.text}")
            
        github_user = user_resp.json()
    
    github_id = github_user.get("id")
    if not github_id:
        raise HTTPException(status_code=400, detail=f"GitHub profile missing 'id': {github_user}")
    username = github_user["login"]
    avatar_url = github_user.get("avatar_url", "")
    provider_id = str(github_id)
    
    # 3. Create or update user in DB (match by provider + provider_id)
    result = await session.execute(
        select(User).where(User.provider == "github", User.provider_id == provider_id)
    )
    user = result.scalars().first()
    
    # Fallback: match by legacy github_id for existing users
    if not user:
        result = await session.execute(
            select(User).where(User.github_id == github_id)
        )
        user = result.scalars().first()
    
    if user:
        user.username = username
        user.avatar_url = avatar_url
        user.access_token = access_token
        user.provider = "github"
        user.provider_id = provider_id
    else:
        user = User(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
            access_token=access_token,
            provider="github",
            provider_id=provider_id,
        )
        session.add(user)
    
    await session.commit()
    await session.refresh(user)
    
    # 4. Generate JWT
    token = create_token(user.id, user.username, "github")
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "github_id": user.github_id,
            "provider": "github",
        },
    }


# ═══════════════════════════════════════════
# Bitbucket OAuth 2.0 Endpoints
# ═══════════════════════════════════════════

@router.get("/bitbucket")
async def bitbucket_login():
    """Redirect user to Bitbucket OAuth 2.0 authorization page."""
    client_id = _cfg("BITBUCKET_CLIENT_ID")
    frontend_url = _cfg("FRONTEND_URL", "http://localhost:5173")
    if not client_id:
        raise HTTPException(status_code=500, detail="BITBUCKET_CLIENT_ID not configured")
    
    params = urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": f"{frontend_url}/auth/bitbucket/callback",
    })
    return RedirectResponse(f"https://bitbucket.org/site/oauth2/authorize?{params}")


@router.post("/bitbucket/callback")
async def bitbucket_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Exchange Bitbucket OAuth code for access token, create/update user, return JWT.
    Bitbucket uses Basic Auth (client_id:client_secret) for token exchange.
    """
    body = await request.json()
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter")
    
    bb_client_id = _cfg("BITBUCKET_CLIENT_ID")
    bb_client_secret = _cfg("BITBUCKET_CLIENT_SECRET")
    frontend_url = _cfg("FRONTEND_URL", "http://localhost:5173")
    if not bb_client_id or not bb_client_secret:
        raise HTTPException(status_code=500, detail="Bitbucket OAuth not configured")
    
    # 1. Exchange code for access token (Bitbucket uses form-encoded + Basic Auth)
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://bitbucket.org/site/oauth2/access_token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{frontend_url}/auth/bitbucket/callback",
            },
            auth=(bb_client_id, bb_client_secret),
            headers={"Accept": "application/json"},
        )
        
        if token_resp.status_code != 200:
            print(f"🚨 BITBUCKET TOKEN EXCHANGE FAILED: {token_resp.text}")
            raise HTTPException(
                status_code=400,
                detail=f"Bitbucket OAuth failed: {token_resp.text}",
            )

        token_data = token_resp.json()
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token", "")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Bitbucket: no access_token returned")
    
    # 2. Fetch Bitbucket user profile
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.bitbucket.org/2.0/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch Bitbucket profile: {user_resp.text}",
            )
        
        bb_user = user_resp.json()
    
    # Bitbucket user fields
    bb_uuid = bb_user.get("uuid", "")           # e.g. "{some-uuid}"
    bb_username = bb_user.get("username", "") or bb_user.get("nickname", "")
    bb_display_name = bb_user.get("display_name", bb_username)
    bb_avatar = ""
    links = bb_user.get("links", {})
    avatar_link = links.get("avatar", {})
    if isinstance(avatar_link, dict):
        bb_avatar = avatar_link.get("href", "")
    bb_profile_url = links.get("html", {}).get("href", "")
    
    if not bb_uuid:
        raise HTTPException(status_code=400, detail=f"Bitbucket profile missing 'uuid': {bb_user}")
    
    provider_id = bb_uuid  # unique identifier
    
    # 3. Create or update user in DB
    result = await session.execute(
        select(User).where(User.provider == "bitbucket", User.provider_id == provider_id)
    )
    user = result.scalars().first()
    
    if user:
        user.username = bb_username
        user.avatar_url = bb_avatar
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.provider_url = bb_profile_url
    else:
        user = User(
            github_id=0,  # not applicable for Bitbucket
            username=bb_username,
            avatar_url=bb_avatar,
            access_token=access_token,
            refresh_token=refresh_token,
            provider="bitbucket",
            provider_id=provider_id,
            provider_url=bb_profile_url,
        )
        session.add(user)
    
    await session.commit()
    await session.refresh(user)
    
    # 4. Generate JWT
    token = create_token(user.id, user.username, "bitbucket")
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "provider": "bitbucket",
            "display_name": bb_display_name,
        },
    }


# ═══════════════════════════════════════════
# Bitbucket Token Refresh Helper
# ═══════════════════════════════════════════

async def refresh_bitbucket_token(user: User, session: AsyncSession) -> str:
    """
    Refresh a Bitbucket OAuth access token using the stored refresh_token.
    Updates the user record and returns the new access_token.
    """
    if not user.refresh_token:
        raise HTTPException(status_code=401, detail="No Bitbucket refresh token available — please re-login")
    
    bb_client_id = _cfg("BITBUCKET_CLIENT_ID")
    bb_client_secret = _cfg("BITBUCKET_CLIENT_SECRET")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://bitbucket.org/site/oauth2/access_token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": user.refresh_token,
            },
            auth=(bb_client_id, bb_client_secret),
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Bitbucket token refresh failed — please re-login")
        data = resp.json()
    
    user.access_token = data["access_token"]
    user.refresh_token = data.get("refresh_token", user.refresh_token)
    await session.commit()
    return user.access_token


# ═══════════════════════════════════════════
# /me Endpoint
# ═══════════════════════════════════════════

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    return {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "github_id": user.github_id,
        "provider": getattr(user, "provider", "github"),
    }
