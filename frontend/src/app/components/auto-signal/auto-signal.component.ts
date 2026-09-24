import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TraderService } from '../../services/trader.service';

interface AutoResult {
  label: string;
  ema_fast: number;
  ema_slow: number;
  rsi_period: number;
  rsi_oversold: number;
  rsi_overbought: number;
  sl: number;
  tp: number;
  direction: string;
  trades: number;
  win_rate: number;
  return_pct: number;
  max_dd: number;
  sharpe: number;
  oos_trades: number;
  oos_win_rate: number;
  oos_return_pct: number;
  oos_max_dd: number;
  oos_sharpe: number;
  target_hit: boolean;
}

@Component({
  selector: 'app-auto-signal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auto-signal.component.html',
  styleUrls: ['./auto-signal.component.css']
})
export class AutoSignalComponent implements OnInit, OnDestroy {
  symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDJPY', 'MSFT', 'MSFT.NAS', 'NVDA', 'NVDA.NAS'];

  config = {
    symbol: 'NVDA',
    days: 365,
    lot: 0.01,
    balance: 1000,
    direction: 'both',
    target_return: 30,
    min_trades: 20,
    volume_filter: false,
    sessions_filter: '',
    use_spread: true,
  };

  mode: 'agent' | 'grid' = 'grid';
  iterations = 4;
  batchSize = 6;

  results: AutoResult[] = [];
  targetHits: string[] = [];
  targetReturn = 30;
  analysis = '';
  loading = false;
  error = '';
  progress = 0;
  sessionId: string | null = null;
  private pollTimer: any = null;

  sortKey = 'oos_return_pct';
  sortDir: 'asc' | 'desc' = 'desc';

  constructor(private traderService: TraderService) {}

  ngOnInit() {}

  ngOnDestroy() {
    this.stopPolling();
  }

  runDiscovery() {
    this.loading = true;
    this.error = '';
    this.results = [];
    this.analysis = '';
    this.progress = 0;

    const payload: any = { ...this.config };
    if (this.mode === 'agent') {
      payload.iterations = this.iterations;
      payload.batch_size = this.batchSize;
    }

    const call = this.mode === 'agent'
      ? this.traderService.runAgentSignalResearch(payload)
      : this.traderService.runAutoSignalResearch(payload);

    call.subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.startPolling();
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to start discovery';
        this.loading = false;
      }
    });
  }

  cancelResearch() {
    if (!this.sessionId) return;
    this.traderService.cancelSignalResearch(this.sessionId).subscribe({
      next: () => {
        this.error = 'Cancelled';
        this.loading = false;
        this.stopPolling();
      }
    });
  }

  exportPdf() {
    if (!this.results.length) return;
    const top = [...this.results].sort((a, b) => b.return_pct - a.return_pct).slice(0, 10);
    this.traderService.exportAutoDiscoverPdf(this.config, top).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `auto_discover_${this.config.symbol}_${this.config.days}d.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: (err) => {
        console.error('PDF export error:', err);
        alert('Errore durante l\'esportazione PDF');
      }
    });
  }

  private startPolling() {
    this.stopPolling();
    this.pollTimer = setInterval(() => {
      if (!this.sessionId) return;
      this.traderService.getSignalResearchStatus(this.sessionId).subscribe({
        next: (res) => {
          if (res.status === 'running') {
            this.progress = res.progress || 0;
          } else if (res.status === 'done') {
            if (res.result?.error) {
              this.error = res.result.error;
            } else {
              this.results = res.result?.results || [];
              this.targetHits = res.result?.target_hits || [];
              this.targetReturn = res.result?.target_return || 30;
              this.analysis = res.result?.analysis || '';
            }
            this.loading = false;
            this.stopPolling();
            if (!this.error && this.results.length === 0) {
              this.error = 'Nessuna combinazione ha prodotto risultati.';
            }
          } else if (res.status === 'error') {
            this.error = res.result?.error || 'Discovery failed';
            this.loading = false;
            this.stopPolling();
          }
        },
        error: () => {
          this.error = 'Lost connection to server';
          this.loading = false;
          this.stopPolling();
        }
      });
    }, 2000);
  }

  private stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  get sortedResults(): AutoResult[] {
    const sorted = [...this.results];
    sorted.sort((a, b) => {
      const va = (a as any)[this.sortKey];
      const vb = (b as any)[this.sortKey];
      if (va == null) return 1;
      if (vb == null) return -1;
      return this.sortDir === 'asc' ? va - vb : vb - va;
    });
    return sorted;
  }

  sortBy(key: string) {
    if (this.sortKey === key) {
      this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortKey = key;
      this.sortDir = 'desc';
    }
  }

  bestPerParams(): AutoResult[] {
    const map = new Map<string, AutoResult>();
    for (const r of this.results) {
      const key = r.label;
      const existing = map.get(key);
      const score = r.oos_return_pct ?? r.return_pct;
      const existingScore = existing ? (existing.oos_return_pct ?? existing.return_pct) : -Infinity;
      if (!existing || score > existingScore) {
        map.set(key, r);
      }
    }
    return Array.from(map.values()).sort((a, b) =>
      (b.oos_return_pct ?? b.return_pct) - (a.oos_return_pct ?? a.return_pct)
    );
  }
}
