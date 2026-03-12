"""Pydantic schemas shared across the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────────────────────────────
class AuthStatus(BaseModel):
    authenticated: bool
    auth_url: str | None = None


# ── Calendar Events ──────────────────────────────────────────────────────────
class EventCreate(BaseModel):
    title: str
    start: datetime
    end: datetime
    timezone: str = "Asia/Kolkata"


class EventOut(BaseModel):
    id: str
    summary: str
    start: str
    end: str
    formatted_time: str
    all_day: bool = False


class EventDeleteConfirm(BaseModel):
    id: str
    summary: str
    start: str
    end: str


# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    error: str | None = None


# ── Analytics ─────────────────────────────────────────────────────────────────
class DailyMetric(BaseModel):
    date: str
    total_hours: float
    work_hours: float
    leisure_hours: float


class AnalyticsMetrics(BaseModel):
    total_hours: float
    avg_daily_hours: float
    work_hours: float
    avg_work_hours: float
    heavy_work_days: int
    moderate_work_days: int
    free_days: int
    stress_level: int
    freedom_score: int


class AnalyticsResponse(BaseModel):
    metrics: AnalyticsMetrics
    chart_data: list[DailyMetric]
