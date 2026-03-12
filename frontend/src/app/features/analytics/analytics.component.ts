import {
  Component,
  inject,
  signal,
  OnInit,
  AfterViewInit,
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
export class AnalyticsComponent implements OnInit {
  @ViewChild('chartCanvas', { static: false }) chartCanvas!: ElementRef<HTMLCanvasElement>;

  private analyticsService = inject(AnalyticsService);

  metrics = signal<AnalyticsMetrics | null>(null);
  chartData = signal<DailyMetric[]>([]);
  loading = signal(true);
  private chart: Chart | null = null;

  ngOnInit() {
    this.analyticsService.getTimeStats(30).subscribe({
      next: (res) => {
        this.metrics.set(res.metrics);
        this.chartData.set(res.chart_data);
        this.loading.set(false);
        // Build chart after data is loaded and view is updated
        setTimeout(() => this.buildChart(), 0);
      },
      error: () => this.loading.set(false),
    });
  }

  private buildChart() {
    const canvas = this.chartCanvas?.nativeElement;
    if (!canvas) return;

    const data = this.chartData();
    if (data.length === 0) return;

    if (this.chart) this.chart.destroy();

    this.chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data.map((d) => d.date),
        datasets: [
          {
            label: 'Work hours',
            data: data.map((d) => d.work_hours),
            backgroundColor: 'rgba(99, 102, 241, 0.7)',
            borderRadius: 4,
          },
          {
            label: 'Leisure hours',
            data: data.map((d) => d.leisure_hours),
            backgroundColor: 'rgba(6, 182, 212, 0.7)',
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            ticks: { color: '#94a3b8', maxRotation: 45 },
            grid: { display: false },
          },
          y: {
            stacked: true,
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(148, 163, 184, 0.1)' },
            title: { display: true, text: 'Hours', color: '#94a3b8' },
          },
        },
        plugins: {
          legend: { labels: { color: '#f1f5f9' } },
        },
      },
    });
  }
}
