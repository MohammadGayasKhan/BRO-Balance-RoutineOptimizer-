import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AnalyticsResponse } from '../../shared/models/analytics.model';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly api = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  getTimeStats(options?: {
    days?: number;
    offsetDays?: number;
    startDate?: string;
    endDate?: string;
  }): Observable<AnalyticsResponse> {
    const params: Record<string, string> = {};
    if (options?.days !== undefined) params['days'] = options.days.toString();
    if (options?.offsetDays !== undefined) {
      params['offset_days'] = options.offsetDays.toString();
    }
    if (options?.startDate) params['start_date'] = options.startDate;
    if (options?.endDate) params['end_date'] = options.endDate;

    return this.http.get<AnalyticsResponse>(`${this.api}/time-stats`, { params });
  }
}
