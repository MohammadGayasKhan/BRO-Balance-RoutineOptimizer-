import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CalendarService } from '../../../core/services/calendar.service';

@Component({
  selector: 'app-event-create',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './event-create.component.html',
  styleUrl: './event-create.component.scss',
})
export class EventCreateComponent {
  private calendarService = inject(CalendarService);
  private router = inject(Router);

  title = '';
  start = '';
  end = '';
  saving = false;
  error = '';

  constructor() {
    // Default to 1h from now
    const now = new Date();
    const later = new Date(now.getTime() + 60 * 60 * 1000);
    this.start = this.toLocalISO(now);
    this.end = this.toLocalISO(later);
  }

  onSubmit() {
    if (!this.title || !this.start || !this.end) {
      this.error = 'Please fill in all fields.';
      return;
    }
    this.saving = true;
    this.error = '';

    this.calendarService
      .createEvent({ title: this.title, start: this.start, end: this.end })
      .subscribe({
        next: () => this.router.navigate(['/events']),
        error: (err) => {
          this.error = err?.error?.detail || 'Failed to create event.';
          this.saving = false;
        },
      });
  }

  goToChat() {
    this.router.navigate(['/chat']);
  }

  private toLocalISO(d: Date): string {
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
}
