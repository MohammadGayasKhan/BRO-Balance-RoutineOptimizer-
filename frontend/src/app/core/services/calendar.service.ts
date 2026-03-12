import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { CalendarEvent, EventCreate } from '../../shared/models/event.model';

@Injectable({ providedIn: 'root' })
export class CalendarService {
  private readonly api = `${environment.apiUrl}/calendar`;

  constructor(private http: HttpClient) {}

  getEvents(): Observable<CalendarEvent[]> {
    return this.http.get<CalendarEvent[]>(`${this.api}/events`);
  }

  getEvent(eventId: string): Observable<CalendarEvent> {
    return this.http.get<CalendarEvent>(`${this.api}/events/${eventId}`);
  }

  createEvent(event: EventCreate): Observable<CalendarEvent> {
    return this.http.post<CalendarEvent>(`${this.api}/events`, event);
  }

  deleteEvent(eventId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(
      `${this.api}/events/${eventId}`
    );
  }
}
