import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TraderService } from '../../services/trader.service';
import { SlaveOrder, Trader } from '../../models/trader.models';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {
  traders: Trader[] = [];
  selectedTraderId: number | null = null;
  deals: SlaveOrder[] = [];
  filteredDeals: SlaveOrder[] = [];
  loading = false;
  symbolFilter: string = '';

  constructor(private traderService: TraderService) {}

  ngOnInit() {
    this.loadTraders();
  }

  loadTraders() {
    this.traderService.loadTraders().subscribe({
      next: (traders) => {
        this.traders = traders;
        if (traders.length > 0) {
          this.selectedTraderId = traders[0].id;
          this.loadDealsHistory();
        }
      },
      error: (err) => {
        console.error('Failed to load traders', err);
      }
    });
  }

  onTraderChange() {
    this.symbolFilter = '';
    if (this.selectedTraderId != null) {
      this.loadDealsHistory();
    } else {
      this.deals = [];
      this.filteredDeals = [];
    }
  }

  loadDealsHistory(symbol?: string) {
    if (this.selectedTraderId == null) return;
    this.loading = true;
    this.traderService.getTradeHistory(this.selectedTraderId, symbol).subscribe({
      next: (data) => {
        this.deals = data;
        this.filteredDeals = this.deals;
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load deals history', err);
        this.deals = [];
        this.filteredDeals = [];
        this.loading = false;
      }
    });
  }

  filterBySymbol() {
    if (this.selectedTraderId == null) return;
    if (this.symbolFilter.trim() === '') {
      this.loadDealsHistory();
    } else {
      this.loadDealsHistory(this.symbolFilter.trim());
    }
  }

  clearFilter() {
    this.symbolFilter = '';
    this.loadDealsHistory();
  }

  getDealType(type: number): string {
    const types: { [key: number]: string } = {
      0: 'BUY',
      1: 'SELL'
    };
    return types[type] || `TYPE_${type}`;
  }

  getDealTypeClass(type: number): string {
    if (type === 0) return 'deal-buy';
    if (type === 1) return 'deal-sell';
    return 'deal-other';
  }

  formatDate(timestamp: string): string {
    if (!timestamp) return '-';
    return new Date(timestamp.replace(' ', 'T')).toLocaleString();
  }

  getTotalProfit(): number {
    return this.filteredDeals.reduce((sum, deal) => sum + deal.profit, 0);
  }

  getNetProfit(): number {
    return this.getTotalProfit();
  }

  refresh() {
    this.loadDealsHistory(this.symbolFilter.trim() || undefined);
  }
}
