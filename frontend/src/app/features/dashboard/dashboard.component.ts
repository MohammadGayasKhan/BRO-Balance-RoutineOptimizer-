import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CalendarService } from '../../core/services/calendar.service';
import { CalendarEvent } from '../../shared/models/event.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private calendarService = inject(CalendarService);

  upcomingEvents = signal<CalendarEvent[]>([]);
  loading = signal(true);

  ngOnInit() {
    this.calendarService.getEvents().subscribe({
      next: (events) => {
        this.upcomingEvents.set(events.slice(0, 5));
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
