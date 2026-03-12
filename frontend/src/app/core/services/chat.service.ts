import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ChatResponse } from '../../shared/models/chat.model';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly api = `${environment.apiUrl}/chat`;

  constructor(private http: HttpClient) {}

  sendMessage(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.api}/message`, { message });
  }

  clearHistory(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.api}/clear`, {});
  }
}
