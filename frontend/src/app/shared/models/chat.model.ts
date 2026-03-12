export interface ChatMessage {
  role: 'user' | 'bro';
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  response: string;
  error?: string;
}
