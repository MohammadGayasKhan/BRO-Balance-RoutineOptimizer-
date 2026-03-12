import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);

  async ngOnInit() {
    const ok = await this.auth.checkStatus();
    if (ok) {
      this.router.navigate(['/dashboard']);
    }
  }

  async connectGoogle() {
    await this.auth.login();
  }
}
