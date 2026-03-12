export interface AnalyticsMetrics {
  total_hours: number;
  avg_daily_hours: number;
  work_hours: number;
  avg_work_hours: number;
  heavy_work_days: number;
  moderate_work_days: number;
  free_days: number;
  stress_level: number;
  freedom_score: number;
}

export interface DailyMetric {
  date: string;
  total_hours: number;
  work_hours: number;
  leisure_hours: number;
}

export interface AnalyticsResponse {
  metrics: AnalyticsMetrics;
  chart_data: DailyMetric[];
}
