import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TraderService } from '../../services/trader.service';

interface OptimizationResult {
  strategy: string;
  sl: number;
  tp: number;
  direction: string;
  max_hold: number;
  trades: number;
  win_rate: number;
  return_pct: number;
  max_dd: number;
  avg_hold: number;
  sharpe: number;
}

interface ResearchConfig {
  symbol: string;
  timeframe: string;
  days: number;
  lot: number;
  balance: number;
  sl_min: number;
  sl_max: number;
  sl_step: number;
  tp_min: number;
  tp_max: number;
  tp_step: number;
  direction: string;
  strategies: string[];
}

interface BacktestTrade {
  time: string;
  type: string;
  exit: string;
  pnl: number;
  balance: number;
}

@Component({
  selector: 'app-signal-research',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signal-research.component.html',
  styleUrls: ['./signal-research.component.css']
})
export class SignalResearchComponent implements OnInit {
  symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDJPY', 'MSFT', 'MSFT.NAS', 'NVDA', 'NVDA.NAS'];

  strategyTimeframes: { [key: string]: string } = {
    'SUPER': 'M1+M5+M15',
    'SUPER_PRO': 'M1+M5+M15',
    'SUPER_LIVE': 'M1+M5+M15',
    'SUPER_USDJPY': 'M1+M5+M15',
    'BASE_NOHOLD': 'M5',
    'ICHIMOKU': 'M1+M5+M15+H1',
    'EURUSD_NOHOLD': 'M5',
    'MSFT': 'M1+M5+M15',
    'NVDA': 'M15',
    'GBPUSD': 'M5',
    'GBPJPY': 'M5',
    'AUDJPY': 'M5',
    'SCALPER_M1': 'M1',
    'LONDON_BREAKOUT': 'M5',
  };

  strategyDefaults: { [key: string]: { sl_min: number; sl_max: number; sl_step: number; tp_min: number; tp_max: number; tp_step: number } } = {
    'SUPER': { sl_min: 100, sl_max: 600, sl_step: 50, tp_min: 200, tp_max: 1200, tp_step: 50 },
    'SUPER_PRO': { sl_min: 100, sl_max: 400, sl_step: 50, tp_min: 200, tp_max: 1000, tp_step: 50 },
    'SUPER_LIVE': { sl_min: 100, sl_max: 600, sl_step: 50, tp_min: 200, tp_max: 1200, tp_step: 50 },
    'SUPER_USDJPY': { sl_min: 50, sl_max: 300, sl_step: 25, tp_min: 100, tp_max: 600, tp_step: 50 },
    'BASE_NOHOLD': { sl_min: 50, sl_max: 300, sl_step: 25, tp_min: 100, tp_max: 600, tp_step: 50 },
    'ICHIMOKU': { sl_min: 100, sl_max: 500, sl_step: 50, tp_min: 200, tp_max: 1000, tp_step: 50 },
    'EURUSD_NOHOLD': { sl_min: 30, sl_max: 200, sl_step: 10, tp_min: 60, tp_max: 400, tp_step: 20 },
    'MSFT': { sl_min: 200, sl_max: 600, sl_step: 50, tp_min: 400, tp_max: 1500, tp_step: 100 },
    'NVDA': { sl_min: 300, sl_max: 1500, sl_step: 100, tp_min: 600, tp_max: 3000, tp_step: 200 },
    'GBPUSD': { sl_min: 30, sl_max: 200, sl_step: 10, tp_min: 60, tp_max: 400, tp_step: 20 },
    'GBPJPY': { sl_min: 50, sl_max: 400, sl_step: 25, tp_min: 100, tp_max: 800, tp_step: 50 },
    'AUDJPY': { sl_min: 30, sl_max: 200, sl_step: 10, tp_min: 60, tp_max: 400, tp_step: 20 },
    'SCALPER_M1': { sl_min: 50, sl_max: 200, sl_step: 10, tp_min: 100, tp_max: 400, tp_step: 20 },
    'LONDON_BREAKOUT': { sl_min: 200, sl_max: 800, sl_step: 50, tp_min: 300, tp_max: 1500, tp_step: 100 },
  };

  strategyDescriptions: { [key: string]: string } = {
    'SUPER': 'Trend-following entry on M1 with M5/M15 confirmation. Best for trending markets.',
    'SUPER_PRO': 'SUPER entry + reduced risk from M5/M15 filters. Stricter but higher quality signals.',
    'SUPER_LIVE': 'SUPER variant for live trading. Same logic as SUPER with production-tuned parameters.',
    'SUPER_USDJPY': 'SUPER variant tuned for USDJPY. Same logic, adjusted SL/TP ranges for yen pairs.',
    'BASE_NOHOLD': 'Simple M5 strategy without overnight hold. Flat before market close, re-enters next day.',
    'ICHIMOKU': 'Ichimoku Cloud across M1/M5/M15/H1. Uses kumo breakout + TK cross.',
    'EURUSD_NOHOLD': 'EURUSD-specific, flat before rollover. No overnight exposure.',
    'MSFT': 'MSFT/NASDAQ hybrid — runs SUPER logic on M1+M5+M15. Use SL 200-600.',
    'NVDA': 'NVDA-specific trend on M15 only. Volatile — wide SL recommended.',
    'GBPUSD': 'GBPUSD intraday breakout on M5. Quick scalps with tight SL.',
    'GBPJPY': 'GBPJPY trend scalper on M5. High volatility — wide SL/TP ranges expected.',
    'AUDJPY': 'AUDJPY momentum entry on M5. Medium vol, moderate hold times.',
    'SCALPER_M1': 'Mean-reversion scalper su M1. Buy se price < EMA21 e RSI < 35. Sell se price > EMA21 e RSI > 65. Default SL 120/TP 250 (EURUSD).',
    'LONDON_BREAKOUT': 'Breakout del range asiatico (00:00-07:00 UTC) all\'apertura di Londra. Entry su M5 con volume confirmation. SL al centro del range, TP 1.5x altezza range. Solo 07:00-11:00 UTC.',
  };

  allStrategies = Object.keys(this.strategyTimeframes);
  selectedStrategies: string[] = [];
  tfFilter = '';

  get filteredStrategies(): string[] {
    if (!this.tfFilter) return this.allStrategies;
    return this.allStrategies.filter(s => this.strategyTimeframes[s].includes(this.tfFilter));
  }

  config: ResearchConfig = {
    symbol: 'NVDA',
    timeframe: 'M15',
    days: 90,
    lot: 0.01,
    balance: 1000,
    sl_min: 100,
    sl_max: 600,
    sl_step: 50,
    tp_min: 200,
    tp_max: 1200,
    tp_step: 100,
    direction: 'both',
    strategies: []
  };

  optimizationResults: OptimizationResult[] = [];
  selectedResult: OptimizationResult | null = null;
  detailTrades: BacktestTrade[] = [];

  loading = false;
  error = '';
  progress = 0;
  sessionId: string | null = null;
  private pollTimer: any = null;

  sortKey = 'return_pct';
  sortDir: 'asc' | 'desc' = 'desc';

  constructor(private traderService: TraderService) {}

  ngOnInit() {
  }

  toggleStrategy(s: string) {
    const idx = this.selectedStrategies.indexOf(s);
    if (idx >= 0) {
      this.selectedStrategies.splice(idx, 1);
    } else {
      this.selectedStrategies.push(s);
    }
    this.config.strategies = [...this.selectedStrategies];
    this.applyStrategyDefaults(s);
  }

  applyStrategyDefaults(s: string) {
    const d = this.strategyDefaults[s];
    if (!d) return;
    this.config.sl_min = d.sl_min;
    this.config.sl_max = d.sl_max;
    this.config.sl_step = d.sl_step;
    this.config.tp_min = d.tp_min;
    this.config.tp_max = d.tp_max;
    this.config.tp_step = d.tp_step;
  }

  isStrategySelected(s: string): boolean {
    return this.selectedStrategies.includes(s);
  }

  runOptimization() {
    if (this.selectedStrategies.length === 0) {
      this.error = 'Seleziona almeno una strategia';
      return;
    }

    this.loading = true;
    this.error = '';
    this.optimizationResults = [];
    this.selectedResult = null;
    this.progress = 0;

    this.traderService.runSignalResearch(this.config).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.startPolling();
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to start research';
        this.loading = false;
      }
    });
  }

  cancelResearch() {
    if (!this.sessionId) return;
    this.traderService.cancelSignalResearch(this.sessionId).subscribe({
      next: () => {
        this.error = 'Research cancelled';
        this.loading = false;
        this.stopPolling();
      }
    });
  }

  selectResult(r: OptimizationResult) {
    this.selectedResult = r;
    this.detailTrades = [];
  }

  ngOnDestroy() {
    this.stopPolling();
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
              this.optimizationResults = res.result?.results || [];
            }
            this.loading = false;
            this.stopPolling();
            if (!this.error && this.optimizationResults.length === 0) {
              this.error = "Nessun risultato. Verifica che le strategie selezionate supportino il simbolo e timeframe scelti.";
            }
          } else if (res.status === 'error') {
            this.error = res.result?.error || 'Research failed';
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

  get sortedResults(): OptimizationResult[] {
    const sorted = [...this.optimizationResults];
    sorted.sort((a: any, b: any) => {
      const va = a[this.sortKey];
      const vb = b[this.sortKey];
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

  getComboCount(): number {
    const slValues = [];
    const tpValues = [];
    for (let sl = this.config.sl_min; sl <= this.config.sl_max; sl += this.config.sl_step) slValues.push(sl);
    for (let tp = this.config.tp_min; tp <= this.config.tp_max; tp += this.config.tp_step) tpValues.push(tp);
    let count = 0;
    for (const sl of slValues) {
      for (const tp of tpValues) {
        if (tp > sl) count++;
      }
    }
    return count;
  }

  exportCsv() {
    if (!this.optimizationResults.length) return;
    const headers = ['Strategy', 'SL', 'TP', 'Direction', 'Trades', 'WinRate%', 'Return%', 'MaxDD', 'AvgHold', 'Sharpe'];
    const rows = this.optimizationResults.map(r => [
      r.strategy, r.sl, r.tp, r.direction, r.trades, r.win_rate, r.return_pct, r.max_dd, r.avg_hold, r.sharpe
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `signal_research_${this.config.symbol}_${this.config.days}d.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportPdf() {
    if (!this.optimizationResults.length) return;

    const payload = {
      ...this.config,
      strategies: this.selectedStrategies,
    };

    this.traderService.exportSignalResearchPdf(payload, this.optimizationResults).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `signal_research_${this.config.symbol}_${this.config.days}d.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: (err) => {
        console.error('PDF export error:', err);
        alert('Errore durante l\'esportazione PDF');
      }
    });
  }
}
