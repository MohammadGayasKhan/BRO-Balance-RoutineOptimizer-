import {
  Component,
  inject,
  signal,
  ElementRef,
  ViewChild,
  AfterViewChecked,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../core/services/chat.service';
import { ChatMessage } from '../../shared/models/chat.model';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

  private chatService = inject(ChatService);

  messages = signal<ChatMessage[]>([]);
  input = '';
  sending = signal(false);
  private shouldScroll = false;

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  send() {
    const text = this.input.trim();
    if (!text || this.sending()) return;

    // Add user message
    this.messages.update((msgs) => [
      ...msgs,
      { role: 'user', content: text, timestamp: new Date() },
    ]);
    this.input = '';
    this.sending.set(true);
    this.shouldScroll = true;

    this.chatService.sendMessage(text).subscribe({
      next: (res) => {
        this.messages.update((msgs) => [
          ...msgs,
          {
            role: 'bro',
            content: res.error ? `Error: ${res.error}` : res.response,
            timestamp: new Date(),
          },
        ]);
        this.sending.set(false);
        this.shouldScroll = true;
      },
      error: (err) => {
        this.messages.update((msgs) => [
          ...msgs,
          {
            role: 'bro',
            content: 'Sorry bro, something went wrong. Try again!',
            timestamp: new Date(),
          },
        ]);
        this.sending.set(false);
        this.shouldScroll = true;
      },
    });
  }

  clearChat() {
    this.chatService.clearHistory().subscribe();
    this.messages.set([]);
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  private scrollToBottom() {
    try {
      const el = this.messagesContainer?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    } catch {}
  }
}
