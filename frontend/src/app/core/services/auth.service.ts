import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

interface AuthStatus {
  authenticated: boolean;
  auth_url: string | null;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = environment.apiUrl;

  /** Reactive signal that tracks authentication state. */
  isAuthenticated = signal(false);

  constructor(private http: HttpClient, private router: Router) {}

  /** Check backend auth status and update the signal. */
  async checkStatus(): Promise<boolean> {
    try {
      const status = await firstValueFrom(
        this.http.get<AuthStatus>(`${this.api}/auth/status`)
      );
      this.isAuthenticated.set(status.authenticated);
      return status.authenticated;
    } catch {
      this.isAuthenticated.set(false);
      return false;
    }
  }

  /** Redirect the user to Google OAuth consent page. */
  async login(): Promise<void> {
    const res = await firstValueFrom(
      this.http.get<{ auth_url: string }>(`${this.api}/auth/login`)
    );
    window.location.href = res.auth_url;
  }

  /** Logout and redirect to login page. */
  async logout(): Promise<void> {
    await firstValueFrom(this.http.post(`${this.api}/auth/logout`, {}));
    this.isAuthenticated.set(false);
    this.router.navigate(['/login']);
  }
}
