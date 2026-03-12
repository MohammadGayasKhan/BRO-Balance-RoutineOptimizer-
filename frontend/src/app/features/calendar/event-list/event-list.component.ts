import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CalendarService } from '../../../core/services/calendar.service';
import { CalendarEvent } from '../../../shared/models/event.model';

@Component({
  selector: 'app-event-list',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './event-list.component.html',
  styleUrl: './event-list.component.scss',
})
export class EventListComponent implements OnInit {
  private calendarService = inject(CalendarService);

  events = signal<CalendarEvent[]>([]);
  loading = signal(true);
  deleteTarget = signal<CalendarEvent | null>(null);

  ngOnInit() {
    this.loadEvents();
  }

  loadEvents() {
    this.loading.set(true);
    this.calendarService.getEvents().subscribe({
      next: (events) => {
        this.events.set(events);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  confirmDelete(event: CalendarEvent) {
    this.deleteTarget.set(event);
  }

  cancelDelete() {
    this.deleteTarget.set(null);
  }

  executeDelete() {
    const target = this.deleteTarget();
    if (!target) return;
    this.calendarService.deleteEvent(target.id).subscribe({
      next: () => {
        this.deleteTarget.set(null);
        this.loadEvents();
      },
    });
  }
}
