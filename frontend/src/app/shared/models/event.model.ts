export interface CalendarEvent {
  id: string;
  summary: string;
  start: string;
  end: string;
  formatted_time: string;
  all_day: boolean;
}

export interface EventCreate {
  title: string;
  start: string; // ISO datetime
  end: string;
  timezone?: string;
}
