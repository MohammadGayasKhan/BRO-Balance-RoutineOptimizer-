"""Calendar analytics – working hours, stress level, freedom score."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

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
async def time_stats(days: int = 30):
    """Analyse calendar events over the past *days* days."""
    try:
        raw_events = gcal.list_events_in_range(days=days)
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

    dates = sorted(daily_total.keys())

    total_hours = sum(daily_total.values())
    work_hours = sum(daily_work.values())
    avg_daily = total_hours / max(days, 1)
    avg_work = work_hours / max(days, 1)

    heavy_work_days = sum(1 for h in daily_work.values() if h >= 6)
    moderate_work_days = sum(1 for h in daily_work.values() if 4 <= h < 6)

    # Stress scoring
    stress_points = sum(3 if h >= 6 else (1 if h >= 4 else 0) for h in daily_work.values())
    max_points = days * 3
    stress_level = min(10, int((stress_points / max(max_points, 1)) * 20))

    free_days = days - sum(1 for h in daily_work.values() if h > 2)
    freedom_score = min(10, int((free_days / max(days, 1)) * 15))

    chart_data = [
        DailyMetric(
            date=d,
            total_hours=round(daily_total[d], 2),
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
