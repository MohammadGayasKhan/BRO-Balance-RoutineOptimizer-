"""Conversational AI chat endpoint powered by Groq with tool calling."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ChatRequest, ChatResponse
from app.services import google_calendar as gcal
from app.services import grok_ai
from app.services import vector_db

router = APIRouter()
log = logging.getLogger(__name__)


def _event_to_text(ev: dict) -> str:
    """Convert a formatted event dict to a readable one-liner."""
    return f"{ev['summary']} – {ev['formatted_time']}"


@router.post("/message", response_model=ChatResponse)
async def send_message(body: ChatRequest, request: Request):
    """Process a user message, let BRO use tools if needed, and return the reply."""
    try:
        # ── Gather calendar context ───────────────────────────────────────
        past_events_raw = gcal.list_past_events(max_results=10)
        upcoming_events_raw = gcal.list_upcoming_events(max_results=10)

        past_texts = [_event_to_text(e) for e in past_events_raw]
        upcoming_texts = [_event_to_text(e) for e in upcoming_events_raw]

        # ── Vector search for relevant context ────────────────────────────
        vector_context = ""
        try:
            user_email = gcal.get_user_email()
            similar = vector_db.query_similar(user_email, body.message, top_k=5)
            if similar:
                vector_context = (
                    "\n## Similar past events from knowledge base\n"
                    + "\n".join(f"• {s}" for s in similar)
                )
        except Exception:
            pass  # non-critical

        # ── Conversation history (stored in session) ──────────────────────
        history: list[dict[str, str]] = request.session.get("conversation_history", [])

        # ── Call AI (with tool-calling loop handled internally) ────────────
        reply = grok_ai.chat(
            user_message=body.message,
            past_events=past_texts,
            upcoming_events=upcoming_texts,
            vector_context=vector_context,
            conversation_history=history,
        )

        # ── Persist history ───────────────────────────────────────────────
        history.append({"user": body.message, "bro": reply})
        # Keep last 20 exchanges
        request.session["conversation_history"] = history[-20:]

        return ChatResponse(response=reply)

    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        log.exception("Chat error")
        return ChatResponse(response="", error=str(exc))


@router.post("/clear")
async def clear_history(request: Request):
    """Clear the conversation history."""
    request.session.pop("conversation_history", None)
    return {"status": "cleared"}
