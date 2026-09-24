import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TraderService } from '../../services/trader.service';

interface BreakdownItem {
  wins: number;
  losses: number;
  pnl: number;
  win_rate: number;
  total: number;
  avg_pnl: number;
}

interface BacktestSummary {
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  trades_per_day: number;
  gross_profit: number;
  gross_loss: number;
  net_pnl: number;
  final_balance: number;
  return_pct: number;
  avg_win: number;
  avg_loss: number;
  win_loss_ratio: number;
  max_drawdown: number;
  by_session: { [key: string]: BreakdownItem };
  by_hour: { [key: number]: BreakdownItem };
  by_day: { [key: string]: BreakdownItem };
  by_direction: { [key: string]: BreakdownItem };
}

interface BacktestTrade {
  time: string;
  type: string;
  exit: string;
  pnl: number;
  balance: number;
}

interface BacktestResult {
  strategy: string;
  symbol: string;
  days: number;
  lot: number;
  initial_balance: number;
  summary: BacktestSummary;
  trades: BacktestTrade[];
}

@Component({
  selector: 'app-backtest',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './backtest.component.html',
  styleUrls: ['./backtest.component.css']
})
export class BacktestComponent implements OnDestroy, OnInit {
  strategies = [
    'SUPER', 'SUPER_LIVE', 'SUPER_PRO', 'SUPER_USDJPY',
    'BASE', 'BASE_NOHOLD', 'TRENDGUARD', 'TRENDGUARD_XAU',
    'ICHIMOKU', 'EURUSD_NOHOLD',
    'MSFT', 'NVDA',
    'GBPUSD', 'GBPJPY', 'AUDJPY'
  ];

  symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDJPY', 'MSFT', 'MSFT.NAS', 'NVDA', 'NVDA.NAS'];

  traders: any[] = [];
  selectedTraderId: number | null = null;

  strategy = 'SUPER';
  symbol = 'XAUUSD';
  days = 30;
  lot = 0.01;
  balance = 10000;
  direction = 'both';

  loading = false;
  error = '';
  result: BacktestResult | null = null;
  sessionId: string | null = null;
  progress = 0;
  progressTrades = 0;
  progressBalance = 0;
  mt5Url = '';
  traderName = '';
  traderLogin = '';
  traderServer = '';
  aiAnalysis = '';
  aiLoading = false;
  aiError = '';
  private pollTimer: any = null;

  constructor(private traderService: TraderService) {}

  ngOnInit() {
    this.traderService.loadTraders().subscribe({
      next: (traders) => {
        this.traders = traders;
        if (traders.length === 1) {
          this.selectedTraderId = traders[0].id;
        }
      }
    });
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  runBacktest() {
    if (!this.selectedTraderId) {
      this.error = 'Seleziona un trader';
      return;
    }

    this.loading = true;
    this.error = '';
    this.result = null;
    this.progress = 0;
    this.progressTrades = 0;
    this.progressBalance = 0;

    this.traderService.runBacktest(this.strategy, this.symbol, this.days, this.lot, this.balance, this.selectedTraderId, this.direction).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.startPolling();
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to start backtest';
        this.loading = false;
      }
    });
  }

  cancelBacktest() {
    if (!this.sessionId) return;
    this.traderService.cancelBacktest(this.sessionId).subscribe({
      next: () => {
        this.error = 'Backtest cancelled';
        this.loading = false;
        this.stopPolling();
      }
    });
  }

  analyzeWithAI() {
    if (!this.sessionId) return;
    this.aiLoading = true;
    this.aiError = '';
    this.aiAnalysis = '';
    this.traderService.analyzeBacktest(this.sessionId).subscribe({
      next: (res) => {
        if (res.error) {
          this.aiError = res.error;
        } else {
          this.aiAnalysis = res.analysis;
        }
        this.aiLoading = false;
      },
      error: (err) => {
        this.aiError = err.error?.error || 'Errore durante analisi AI';
        this.aiLoading = false;
      }
    });
  }

  private startPolling() {
    this.stopPolling();
    this.pollTimer = setInterval(() => {
      if (!this.sessionId) return;
      this.traderService.getBacktestStatus(this.sessionId).subscribe({
        next: (res) => {
          this.mt5Url = res.mt5_url || this.mt5Url;
          this.traderName = res.trader_name || this.traderName;
          this.traderLogin = res.trader_login || this.traderLogin;
          this.traderServer = res.trader_server || this.traderServer;
          if (res.status === 'running') {
            this.progress = res.progress || 0;
            this.progressTrades = res.trades_count || 0;
            this.progressBalance = res.balance || 0;
          } else if (res.status === 'done') {
            if (res.result?.error) {
              this.error = res.result.error;
            } else {
              this.result = res.result;
            }
            this.loading = false;
            this.stopPolling();
          } else if (res.status === 'error') {
            this.error = res.result?.error || 'Backtest failed';
            this.loading = false;
            this.stopPolling();
          } else if (res.status === 'cancelled') {
            this.error = 'Backtest cancelled';
            this.loading = false;
            this.stopPolling();
          }
          // 'running' -> keep polling
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

  getSessionKeys(): string[] {
    if (!this.result?.summary?.by_session) return [];
    return ['ASIA', 'LONDON', 'NY-LON', 'NY', 'OFF'].filter(k => this.result!.summary.by_session[k]);
  }

  getSessionHours(session: string): string {
    const hours: { [key: string]: string } = {
      'ASIA': '01:00 - 08:59',
      'LONDON': '09:00 - 13:59',
      'NY-LON': '14:00 - 17:29',
      'NY': '17:30 - 21:59',
      'OFF': '22:00 - 00:59'
    };
    return hours[session] || '';
  }

  getDayKeys(): string[] {
    if (!this.result?.summary?.by_day) return [];
    const order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return order.filter(k => this.result!.summary.by_day[k]);
  }

  getTopHours(): number[] {
    if (!this.result?.summary?.by_hour) return [];
    return Object.keys(this.result.summary.by_hour)
      .map(Number)
      .sort((a, b) => this.result!.summary.by_hour[b].pnl - this.result!.summary.by_hour[a].pnl)
      .slice(0, 8);
  }

  exportCsv() {
    if (!this.result || !this.result.trades.length) return;

    const s = this.result.summary;
    const r = this.result;
    const lines: string[] = [];

    lines.push('Strategy,Symbol,Days,Lot,Initial Balance');
    lines.push(`${r.strategy},${r.symbol},${r.days},${r.lot},${r.initial_balance}`);
    lines.push('');
    lines.push('Total Trades,Wins,Losses,Win Rate,Gross Profit,Gross Loss,Net PnL,Final Balance,Return %,Avg Win,Avg Loss,Win/Loss Ratio,Max Drawdown');
    lines.push(`${s.total_trades},${s.wins},${s.losses},${s.win_rate},${s.gross_profit},${s.gross_loss},${s.net_pnl},${s.final_balance},${s.return_pct},${s.avg_win},${s.avg_loss},${s.win_loss_ratio},${s.max_drawdown}`);
    lines.push('');

    if (s.by_session) {
      lines.push('--- PER SESSIONE ---');
      lines.push('Sessione,Trades,Wins,Losses,Win Rate,PnL,Avg PnL');
      for (const k of Object.keys(s.by_session)) {
        const v = s.by_session[k];
        lines.push(`${k},${v.total},${v.wins},${v.losses},${v.win_rate},${v.pnl},${v.avg_pnl}`);
      }
      lines.push('');
    }

    if (s.by_direction) {
      lines.push('--- PER DIREZIONE ---');
      lines.push('Direzione,Trades,Wins,Losses,Win Rate,PnL,Avg PnL');
      for (const k of Object.keys(s.by_direction)) {
        const v = s.by_direction[k];
        lines.push(`${k},${v.total},${v.wins},${v.losses},${v.win_rate},${v.pnl},${v.avg_pnl}`);
      }
      lines.push('');
    }

    lines.push('Time,Type,Exit,PnL,Balance');
    for (const t of r.trades) {
      lines.push(`${t.time},${t.type},${t.exit},${t.pnl},${t.balance}`);
    }

    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backtest_${r.strategy}_${r.symbol}_${r.days}d.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
