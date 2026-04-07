"""Groq conversational AI service with tool-calling support.

Uses the OpenAI-compatible Groq API to power the BRO assistant.
The LLM can create, update, delete, and search Google Calendar events
through function/tool calls.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from openai import OpenAI

from app.config import settings
from app.services import google_calendar as gcal

log = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.GROK_API_KEY:
            raise RuntimeError("GROK_API_KEY is not configured.")
        _client = OpenAI(
            api_key=settings.GROK_API_KEY,
            base_url=settings.GROK_BASE_URL,
        )
    return _client


# ── Tool / function definitions ───────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": (
                "Create a new Google Calendar event. "
                "You MUST ask the user for a title, start time, and end time before calling this. "
                "If the user only gives a start time, assume 1 hour duration."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title / summary.",
                    },
                    "start": {
                        "type": "string",
                        "description": "ISO-8601 start datetime, e.g. 2025-07-20T14:00:00.",
                    },
                    "end": {
                        "type": "string",
                        "description": "ISO-8601 end datetime, e.g. 2025-07-20T15:00:00.",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone (default Asia/Kolkata).",
                    },
                },
                "required": ["title", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": (
                "Update an existing Google Calendar event. "
                "You must know the event_id – use search_events first if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The Google Calendar event ID.",
                    },
                    "title": {
                        "type": "string",
                        "description": "New event title (optional).",
                    },
                    "start": {
                        "type": "string",
                        "description": "New ISO-8601 start datetime (optional).",
                    },
                    "end": {
                        "type": "string",
                        "description": "New ISO-8601 end datetime (optional).",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone (default Asia/Kolkata).",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": (
                "Delete a Google Calendar event by its event ID. "
                "You must know the event_id – use search_events first if needed. "
                "Always confirm with the user before deleting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The Google Calendar event ID to delete.",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_events",
            "description": "List the user's upcoming Google Calendar events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum events to return (default 10).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": (
                "Search for Google Calendar events matching a text query. "
                "Use this to find an event when the user wants to update or delete by name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search text to match against event titles.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

def _execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool call and return a JSON string result."""
    try:
        if name == "create_event":
            start_dt = datetime.fromisoformat(arguments["start"])
            end_dt = datetime.fromisoformat(arguments["end"])
            tz = arguments.get("timezone", "Asia/Kolkata")
            created = gcal.create_event(
                title=arguments["title"], start=start_dt, end=end_dt, timezone=tz
            )
            return json.dumps(
                {
                    "status": "success",
                    "event_id": created["id"],
                    "summary": created.get("summary"),
                    "htmlLink": created.get("htmlLink"),
                }
            )

        elif name == "update_event":
            kwargs: dict[str, Any] = {"event_id": arguments["event_id"]}
            if "title" in arguments:
                kwargs["title"] = arguments["title"]
            if "start" in arguments:
                kwargs["start"] = datetime.fromisoformat(arguments["start"])
            if "end" in arguments:
                kwargs["end"] = datetime.fromisoformat(arguments["end"])
            if "timezone" in arguments:
                kwargs["timezone"] = arguments["timezone"]
            updated = gcal.update_event(**kwargs)
            return json.dumps(
                {
                    "status": "success",
                    "event_id": updated["id"],
                    "summary": updated.get("summary"),
                }
            )

        elif name == "delete_event":
            gcal.delete_event(arguments["event_id"])
            return json.dumps({"status": "success", "message": "Event deleted."})

        elif name == "list_upcoming_events":
            max_r = arguments.get("max_results", 10)
            events = gcal.list_upcoming_events(max_results=max_r)
            return json.dumps({"status": "success", "events": events})

        elif name == "search_events":
            results = gcal.search_events_by_title(arguments["query"])
            return json.dumps({"status": "success", "events": results})

        else:
            return json.dumps({"status": "error", "message": f"Unknown tool: {name}"})

    except Exception as exc:
        log.exception("Tool execution failed: %s", name)
        return json.dumps({"status": "error", "message": str(exc)})


# ── System prompt builder ─────────────────────────────────────────────────────

def _build_system_prompt(
    past_events: list[str],
    upcoming_events: list[str],
    vector_context: str,
    conversation_history: list[dict[str, str]],
) -> str:
    today = date.today().isoformat()

    history_text = _format_history(conversation_history)
    past_text = "\n".join(f"• {e}" for e in past_events) if past_events else "No past events found."
    upcoming_text = "\n".join(f"• {e}" for e in upcoming_events) if upcoming_events else "No upcoming events found."

    return f"""You are **BRO** – a warm, enthusiastic **B**rother and **R**outine **O**ptimizer.
Always address the user as "bro" in a friendly, supportive tone.
Today's date: {today}.

## Your capabilities
✅ View and analyse the user's Google Calendar events (use the list_upcoming_events tool).
✅ Create new calendar events (use the create_event tool).
✅ Update / reschedule existing events (use search_events to find the event first, then update_event).
✅ Delete events (use search_events to find the event first, then delete_event – always confirm with the user first).
✅ Analyse working hours and suggest ways to relax.
✅ Tell the user about upcoming work and free time.
✅ Advise on time management, productivity, and work-life balance.
✅ Suggest when the user can go out, exercise, or take a break.

## Rules for tool usage
- When the user asks to create an event, infer the date/time from their message relative to today ({today}).
  If they say "tomorrow at 8pm", compute the correct ISO date.
- If only a start time is given, assume a 1-hour duration.
- Before deleting, always confirm with the user.
- When updating or deleting, search for the event first to get its event_id.

## Conversation so far
{history_text}

## User's recent past events
{past_text}

## User's upcoming events
{upcoming_text}
{vector_context}

## Formatting
- Write like a thoughtful, emotionally intelligent coach, not a chatbot.
- Avoid dry endings like "that's about it" or repetitive filler.
- Keep responses concise but polished: usually 4-8 lines.
- Use clean structure with short paragraphs or bullets.
- Use markdown for emphasis where helpful.

## Response quality style guide
- If user asks about their day/week schedule, use this structure:
    1) Quick headline summary (1 sentence)
    2) Timeline bullets with friendly time windows
    3) A short insight (workload, gaps, or recovery time)
    4) One helpful suggestion or offer (e.g., optimize, create event, block focus)
- Prefer natural phrasing like "10:00-10:30 AM" over raw ISO text.
- Sound confident, warm, and premium.

## Example tone (do not copy literally)
"Bro, your day is nicely spaced. You have a focused review block in the morning and a lunch break around noon. If you want, I can help you protect a 90-minute deep-work slot in the afternoon." 
"""


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "(start of conversation)"
    lines: list[str] = []
    for h in history[-10:]:
        lines.append(f"User: {h.get('user', '')}")
        lines.append(f"BRO: {h.get('bro', '')}")
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

MAX_TOOL_ROUNDS = 5  # safety limit to prevent infinite loops


def chat(
    user_message: str,
    past_events: list[str],
    upcoming_events: list[str],
    vector_context: str = "",
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Send a message to the LLM with tool-calling support.

    The function runs a loop: if the model responds with tool_calls,
    it executes them and feeds the results back until the model produces
    a final text reply (or the safety limit is reached).
    """
    client = _get_client()
    system = _build_system_prompt(
        past_events, upcoming_events, vector_context, conversation_history or []
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    for _round in range(MAX_TOOL_ROUNDS):
        completion = client.chat.completions.create(
            model=settings.GROK_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1024,
        )

        assistant_msg = completion.choices[0].message

        # If no tool calls, we have our final answer
        if not assistant_msg.tool_calls:
            return assistant_msg.content or ""

        # Append the assistant's reply (with tool_calls) to the message list
        messages.append(assistant_msg)  # type: ignore[arg-type]

        # Execute each tool call and append results
        for tool_call in assistant_msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            log.info("Tool call: %s(%s)", fn_name, fn_args)

            result = _execute_tool(fn_name, fn_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    # If we exhausted tool rounds, return whatever text we have
    return assistant_msg.content or "Sorry bro, I ran into an issue processing that request."
