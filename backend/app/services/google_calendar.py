"""Google Calendar service – handles OAuth flow and calendar CRUD."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Allow OAuth over HTTP for local development (localhost only)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import settings


# ── OAuth helpers ─────────────────────────────────────────────────────────────

def build_oauth_flow() -> Flow:
    """Create a Google OAuth ``Flow`` configured from credentials.json."""
    flow = Flow.from_client_secrets_file(
        str(settings.GOOGLE_CREDENTIALS_FILE),
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


def get_authorization_url() -> tuple[str, str, str]:
    """Return (authorization_url, state, code_verifier) to start the OAuth consent flow."""
    flow = build_oauth_flow()
    url, state = flow.authorization_url(access_type="offline", prompt="consent")
    # PKCE: the flow auto-generates a code_verifier we must save for the callback
    code_verifier = flow.code_verifier
    return url, state, code_verifier


def exchange_code_for_credentials(
    code: str,
    code_verifier: str | None = None,
) -> Credentials:
    """Exchange the authorization code for Google credentials and persist them."""
    flow = build_oauth_flow()
    # Restore PKCE code_verifier so Google can verify the exchange
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_token(creds)
    return creds


def _save_token(creds: Credentials) -> None:
    with open(settings.GOOGLE_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def _load_token() -> Credentials | None:
    if not settings.GOOGLE_TOKEN_FILE.exists():
        return None
    return Credentials.from_authorized_user_file(
        str(settings.GOOGLE_TOKEN_FILE), settings.GOOGLE_SCOPES
    )


def is_authenticated() -> bool:
    creds = _load_token()
    if creds is None:
        return False
    if creds.valid:
        return True
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleAuthRequest())
            _save_token(creds)
            return True
        except Exception:
            return False
    return False


def revoke_credentials() -> None:
    """Remove stored token (logout)."""
    if settings.GOOGLE_TOKEN_FILE.exists():
        os.remove(settings.GOOGLE_TOKEN_FILE)


# ── Calendar service builder ─────────────────────────────────────────────────

def get_calendar_service():
    """Return an authorised Google Calendar API service object."""
    creds = _load_token()
    if creds is None:
        raise RuntimeError("Not authenticated. Please connect your Google Calendar first.")
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
            _save_token(creds)
        else:
            raise RuntimeError("Credentials expired. Please re-authenticate.")
    return build("calendar", "v3", credentials=creds)


def get_user_email() -> str:
    """Return the primary calendar email for the authenticated user."""
    service = get_calendar_service()
    cal = service.calendarList().get(calendarId="primary").execute()
    return cal.get("id", "unknown")


# ── Calendar data helpers ─────────────────────────────────────────────────────

def list_upcoming_events(max_results: int = 20) -> list[dict[str, Any]]:
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + "Z"
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return _format_events(result.get("items", []))


def list_past_events(max_results: int = 20) -> list[dict[str, Any]]:
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + "Z"
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMax=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return _format_events(result.get("items", []))


def list_events_in_range(days: int = 30) -> list[dict[str, Any]]:
    """List events from the past *days* days (for analytics)."""
    service = get_calendar_service()
    time_min = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=500,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def create_event(title: str, start: datetime, end: datetime, timezone: str = "Asia/Kolkata") -> dict[str, Any]:
    service = get_calendar_service()
    body = {
        "summary": title,
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": timezone},
    }
    created = service.events().insert(calendarId="primary", body=body).execute()
    return created


def get_event(event_id: str) -> dict[str, Any]:
    service = get_calendar_service()
    return service.events().get(calendarId="primary", eventId=event_id).execute()


def delete_event(event_id: str) -> None:
    service = get_calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()


def update_event(
    event_id: str,
    title: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    timezone: str = "Asia/Kolkata",
) -> dict[str, Any]:
    """Update an existing calendar event. Only the provided fields are changed."""
    service = get_calendar_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    if title is not None:
        event["summary"] = title
    if start is not None:
        event["start"] = {"dateTime": start.isoformat(), "timeZone": timezone}
    if end is not None:
        event["end"] = {"dateTime": end.isoformat(), "timeZone": timezone}
    updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    return updated


def search_events_by_title(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search for events matching a text query."""
    service = get_calendar_service()
    result = (
        service.events()
        .list(
            calendarId="primary",
            q=query,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            timeMin=(datetime.utcnow() - timedelta(days=90)).isoformat() + "Z",
        )
        .execute()
    )
    return _format_events(result.get("items", []))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _format_events(raw_events: list[dict]) -> list[dict[str, Any]]:
    """Normalise raw Google events into a consistent dict shape."""
    events: list[dict[str, Any]] = []
    for ev in raw_events:
        is_all_day = "date" in ev.get("start", {})
        if is_all_day:
            formatted_time = f"All-day: {ev['start']['date']}"
            start_str = ev["start"]["date"]
            end_str = ev["end"]["date"]
        else:
            start_str = ev["start"]["dateTime"]
            end_str = ev["end"]["dateTime"]
            formatted_time = f"{start_str[:10]} {start_str[11:16]} – {end_str[11:16]}"
        events.append(
            {
                "id": ev["id"],
                "summary": ev.get("summary", "(no title)"),
                "start": start_str,
                "end": end_str,
                "formatted_time": formatted_time,
                "all_day": is_all_day,
            }
        )
    return events
