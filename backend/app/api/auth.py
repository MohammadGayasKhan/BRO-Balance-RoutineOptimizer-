"""Google OAuth2 authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.models.schemas import AuthStatus
from app.services import google_calendar as gcal

router = APIRouter()


@router.get("/status", response_model=AuthStatus)
async def auth_status():
    """Check whether the user has connected their Google Calendar."""
    authenticated = gcal.is_authenticated()
    auth_url = None
    if not authenticated:
        auth_url, _, _ = gcal.get_authorization_url()
    return AuthStatus(authenticated=authenticated, auth_url=auth_url)


@router.get("/login")
async def login(request: Request):
    """Start OAuth flow – returns the Google consent URL."""
    url, state, code_verifier = gcal.get_authorization_url()
    request.session["oauth_state"] = state
    request.session["code_verifier"] = code_verifier
    return {"auth_url": url}


@router.get("/callback")
async def callback(request: Request):
    """Handle the OAuth callback from Google, then redirect to frontend."""
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=missing_code")
    try:
        code_verifier = request.session.get("code_verifier")
        gcal.exchange_code_for_credentials(code, code_verifier=code_verifier)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard")
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("OAuth callback failed")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=auth_failed")


@router.post("/logout")
async def logout(request: Request):
    """Revoke stored credentials."""
    gcal.revoke_credentials()
    request.session.clear()
    return {"status": "logged_out"}
