"""Calendar analytics – working hours, stress level, freedom score."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import dateutil.parser
from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyticsMetrics, AnalyticsResponse, DailyMetric
from app.services import google_calendar as gcal

router = APIRouter()

LEISURE_KEYWORDS = [
    "movie", "picnic", "party", "dinner", "holiday",
    "vacation", "leisure", "fun", "gym", "yoga",
    "walk", "gaming", "hangout", "chill", "rest",
]


@router.get("/time-stats", response_model=AnalyticsResponse)
async def time_stats(
    days: int = 30,
    offset_days: int = 0,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Analyse calendar events over a date window with optional offset or explicit range."""
    try:
        if start_date and end_date:
            range_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            range_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            days = (range_end - range_start).days + 1
        else:
            today = datetime.utcnow().date()
            range_end = today + timedelta(days=offset_days)
            range_start = range_end - timedelta(days=days - 1)

        start_dt = datetime.combine(range_start, datetime.min.time())
        end_dt = datetime.combine(range_end, datetime.max.time())

        raw_events = gcal.list_events_between(start=start_dt, end=end_dt)
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    daily_total: dict[str, float] = defaultdict(float)
    daily_work: dict[str, float] = defaultdict(float)
    daily_leisure: dict[str, float] = defaultdict(float)

    for event in raw_events:
        if "dateTime" in event.get("start", {}):
            start = dateutil.parser.parse(event["start"]["dateTime"])
            end = dateutil.parser.parse(event["end"]["dateTime"])
            duration_h = (end - start).total_seconds() / 3600
        else:
            start = dateutil.parser.parse(event["start"].get("date", ""))
            duration_h = 8.0  # assume 8 h for all-day events

        date_key = start.strftime("%Y-%m-%d")
        summary_lower = event.get("summary", "").lower()
        is_leisure = any(kw in summary_lower for kw in LEISURE_KEYWORDS)

        daily_total[date_key] += duration_h
        if is_leisure:
            daily_leisure[date_key] += duration_h
        else:
            daily_work[date_key] += duration_h

    # Ensure we return a contiguous date range, even if there are no events.
    dates = [
        (range_start + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(max(days, 1))
    ]

    total_hours = sum(daily_total.values())
    work_hours = sum(daily_work.values())
    avg_daily = total_hours / max(days, 1)
    avg_work = work_hours / max(days, 1)

    heavy_work_days = sum(1 for h in daily_work.values() if h >= 6)
    moderate_work_days = sum(1 for h in daily_work.values() if 4 <= h < 6)

    # Stress scoring
    # Blend average work intensity with the frequency of heavy days.
    avg_work_ratio = min(1.0, avg_work / 6.0) if days > 0 else 0.0
    heavy_ratio = heavy_work_days / max(days, 1)
    stress_raw = (avg_work_ratio * 0.7) + (heavy_ratio * 0.3)
    stress_level = min(10, max(1 if work_hours > 0 else 0, int(round(stress_raw * 10))))

    free_days = days - sum(1 for h in daily_work.values() if h > 2)
    freedom_ratio = free_days / max(days, 1)
    freedom_score = min(10, int(round(freedom_ratio * 10)))

    chart_data = [
        DailyMetric(
            date=d,
            total_hours=round(daily_total.get(d, 0), 2),
            work_hours=round(daily_work.get(d, 0), 2),
            leisure_hours=round(daily_leisure.get(d, 0), 2),
        )
        for d in dates
    ]

    metrics = AnalyticsMetrics(
        total_hours=round(total_hours, 2),
        avg_daily_hours=round(avg_daily, 2),
        work_hours=round(work_hours, 2),
        avg_work_hours=round(avg_work, 2),
        heavy_work_days=heavy_work_days,
        moderate_work_days=moderate_work_days,
        free_days=free_days,
        stress_level=stress_level,
        freedom_score=freedom_score,
    )

    return AnalyticsResponse(metrics=metrics, chart_data=chart_data)
