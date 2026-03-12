import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

/**
 * This component only exists to handle the redirect from Google OAuth
 * when the flow goes Frontend → Google → Frontend callback.
 *
 * In our flow the backend handles /api/auth/callback and redirects to /dashboard,
 * so this is a fallback safety net.
 */
@Component({
  selector: 'app-callback',
  standalone: true,
  template: `<div class="callback"><p>Completing authentication…</p></div>`,
  styles: [`.callback { display: flex; align-items: center; justify-content: center; min-height: 60vh; color: var(--color-text-muted); }`],
})
export class CallbackComponent implements OnInit {
  constructor(private router: Router) {}

  ngOnInit() {
    // The backend callback already redirected here; just go to dashboard.
    this.router.navigate(['/dashboard']);
  }
}
