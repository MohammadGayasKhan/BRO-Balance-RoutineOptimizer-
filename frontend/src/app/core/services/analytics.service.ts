import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AnalyticsResponse } from '../../shared/models/analytics.model';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly api = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  getTimeStats(days: number = 30): Observable<AnalyticsResponse> {
    return this.http.get<AnalyticsResponse>(`${this.api}/time-stats`, {
      params: { days: days.toString() },
    });
  }
}
