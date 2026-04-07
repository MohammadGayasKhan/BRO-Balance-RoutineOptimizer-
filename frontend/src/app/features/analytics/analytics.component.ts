import {
  Component,
  inject,
  signal,
  OnInit,
  AfterViewInit,
  OnDestroy,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { AnalyticsService } from '../../core/services/analytics.service';
import {
  AnalyticsMetrics,
  AnalyticsResponse,
  DailyMetric,
} from '../../shared/models/analytics.model';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.scss',
})
export class AnalyticsComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartCanvas', { static: false }) chartCanvas!: ElementRef<HTMLCanvasElement>;

  private analyticsService = inject(AnalyticsService);

  metrics = signal<AnalyticsMetrics | null>(null);
  chartData = signal<DailyMetric[]>([]);
  loading = signal(true);
  rangeDays = signal(7);
  offsetDays = signal(0);
  activePreset = signal<7 | 30 | 90 | null>(7);
  startDate = signal('');
  endDate = signal('');
  isDragScrolling = false;
  dragStartX = 0;
  scrollStartX = 0;
  private viewReady = false;
  private chart: Chart | null = null;
  private pendingRender: ReturnType<typeof setTimeout> | null = null;

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    this.loading.set(true);
    const start = this.startDate();
    const end = this.endDate();
    const options = start && end
      ? { startDate: start, endDate: end }
      : { days: this.rangeDays(), offsetDays: this.offsetDays() };

    this.analyticsService
      .getTimeStats(options)
      .subscribe({
        next: (res) => {
          this.metrics.set(res.metrics);
          this.chartData.set(res.chart_data);
          this.loading.set(false);
          this.scheduleChartRender();
        },
        error: () => this.loading.set(false),
      });
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.scheduleChartRender();
  }

  ngOnDestroy(): void {
    if (this.pendingRender) {
      clearTimeout(this.pendingRender);
    }
    if (this.chart) {
      this.chart.destroy();
    }
  }

  private scheduleChartRender() {
    if (this.pendingRender) {
      clearTimeout(this.pendingRender);
    }
    this.pendingRender = setTimeout(() => {
      this.pendingRender = null;
      this.tryBuildChart();
    }, 80);
  }

  private tryBuildChart() {
    if (!this.viewReady) return;
    if (this.chartData().length === 0) return;
    this.buildChart();
  }

  private buildChart() {
    const canvas = this.chartCanvas?.nativeElement;
    if (!canvas) return;

    const data = this.chartData();
    if (data.length === 0) return;

    const minWidth = Math.max(900, data.length * 34);
    canvas.style.minWidth = `${minWidth}px`;

    if (this.chart) this.chart.destroy();

    this.chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data.map((d) => d.date),
        datasets: [
          {
            label: 'Work hours',
            data: data.map((d) => d.work_hours),
            backgroundColor: 'rgba(33, 199, 216, 0.7)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: false,
            ticks: { color: '#94a3b8', maxRotation: 45 },
            grid: { display: false },
          },
          y: {
            stacked: false,
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(148, 163, 184, 0.1)' },
            title: { display: true, text: 'Hours', color: '#94a3b8' },
          },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });

    // Make sure Chart.js recalculates dimensions after mount in scroll container.
    requestAnimationFrame(() => this.chart?.resize());
  }

  setRange(days: number) {
    if (days === 7 || days === 30 || days === 90) {
      this.activePreset.set(days);
    }
    this.rangeDays.set(days);
    this.offsetDays.set(0);
    this.startDate.set('');
    this.endDate.set('');
    this.loadStats();
  }

  shiftRange(direction: 'prev' | 'next') {
    if (this.startDate() && this.endDate()) return;
    const delta = direction === 'prev' ? -this.rangeDays() : this.rangeDays();
    this.offsetDays.set(this.offsetDays() + delta);
    this.loadStats();
  }

  resetRange() {
    this.activePreset.set(7);
    this.rangeDays.set(7);
    this.offsetDays.set(0);
    this.startDate.set('');
    this.endDate.set('');
    this.loadStats();
  }

  get rangeLabel(): string {
    if (this.startDate() && this.endDate()) {
      return `${this.formatDateLabel(this.startDate())} - ${this.formatDateLabel(this.endDate())}`;
    }
    const days = this.rangeDays();
    const offset = this.offsetDays();
    const end = new Date();
    end.setDate(end.getDate() + offset);
    const start = new Date(end);
    start.setDate(start.getDate() - (days - 1));
    return `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
  }

  applyCustomRange() {
    if (!this.startDate() || !this.endDate()) return;
    if (this.startDate() > this.endDate()) {
      const start = this.startDate();
      this.startDate.set(this.endDate());
      this.endDate.set(start);
    }
    const days = this.calculateDays(this.startDate(), this.endDate());
    this.rangeDays.set(days);
    this.activePreset.set(null);
    this.offsetDays.set(0);
    this.loadStats();
  }

  isPresetActive(days: number): boolean {
    return !this.startDate() && !this.endDate() && this.activePreset() === days;
  }

  private calculateDays(start: string, end: string): number {
    const startDate = new Date(`${start}T00:00:00`);
    const endDate = new Date(`${end}T00:00:00`);
    const diff = endDate.getTime() - startDate.getTime();
    return Math.max(1, Math.floor(diff / 86400000) + 1);
  }

  private formatDateLabel(dateStr: string): string {
    const date = new Date(`${dateStr}T00:00:00`);
    return date.toLocaleDateString();
  }

  onDragStart(event: MouseEvent, scrollContainer: HTMLElement) {
    this.isDragScrolling = true;
    this.dragStartX = event.clientX;
    this.scrollStartX = scrollContainer.scrollLeft;
  }

  onDragMove(event: MouseEvent, scrollContainer: HTMLElement) {
    if (!this.isDragScrolling) return;
    const delta = this.dragStartX - event.clientX;
    scrollContainer.scrollLeft = this.scrollStartX + delta;
  }

  onDragEnd() {
    this.isDragScrolling = false;
  }
}
