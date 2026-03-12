"""Calendar event CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import EventCreate, EventOut, EventDeleteConfirm
from app.services import google_calendar as gcal
from app.services import vector_db

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
async def list_events():
    """List upcoming calendar events."""
    try:
        events = gcal.list_upcoming_events(max_results=20)
        return events
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/events", response_model=EventOut)
async def create_event(body: EventCreate):
    """Create a new calendar event and index it in the vector DB."""
    try:
        created = gcal.create_event(body.title, body.start, body.end, body.timezone)

        # Index in vector DB (best-effort)
        event_text = f"{body.title} from {body.start.isoformat()} to {body.end.isoformat()}"
        user_email = gcal.get_user_email()
        vector_db.upsert_event(
            namespace=user_email,
            event_id=created["id"],
            text=event_text,
            metadata={
                "text": event_text,
                "title": body.title,
                "start": body.start.isoformat(),
                "end": body.end.isoformat(),
                "event_id": created["id"],
            },
        )

        start_str = created["start"].get("dateTime", created["start"].get("date", ""))
        end_str = created["end"].get("dateTime", created["end"].get("date", ""))
        is_all_day = "date" in created["start"]
        if is_all_day:
            formatted = f"All-day: {start_str}"
        else:
            formatted = f"{start_str[:10]} {start_str[11:16]} – {end_str[11:16]}"

        return EventOut(
            id=created["id"],
            summary=created.get("summary", ""),
            start=start_str,
            end=end_str,
            formatted_time=formatted,
            all_day=is_all_day,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.get("/events/{event_id}", response_model=EventDeleteConfirm)
async def get_event(event_id: str):
    """Get details of a single event (used for delete confirmation)."""
    try:
        ev = gcal.get_event(event_id)
        start = ev["start"].get("dateTime", ev["start"].get("date", ""))
        end = ev["end"].get("dateTime", ev["end"].get("date", ""))
        return EventDeleteConfirm(
            id=ev["id"],
            summary=ev.get("summary", ""),
            start=start,
            end=end,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete a calendar event and remove from vector DB."""
    try:
        user_email = gcal.get_user_email()
        gcal.delete_event(event_id)
        vector_db.delete_event(namespace=user_email, event_id=event_id)
        return {"status": "deleted", "event_id": event_id}
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
