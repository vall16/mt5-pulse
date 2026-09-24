import { Component, OnInit, ChangeDetectorRef } from '@angular/core';

import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { AuthService } from '../../services/auth.service';
import { TraderService } from '../../services/trader.service';
import { NewTrader, Trader,BuyRequest } from '../../models/trader.models';
import { AddTraderModalComponent } from '../add-trader-modal/add-trader-modal.component';
import { ServersListComponent } from '../servers-list/servers-list.component';
import { Server } from '../../models/server.model';
import { FormsModule } from '@angular/forms';
import { catchError, finalize, of, switchMap } from 'rxjs';
import { interval, Subscription } from 'rxjs';


@Component({
  selector: 'app-user-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule, AddTraderModalComponent, ServersListComponent],
  
  templateUrl: './user-dashboard.component.html',
  styleUrls: ['./user-dashboard.component.css']
})
export class UserDashboardComponent implements OnInit {
  traders: Trader[] = [];
  servers: Server[] = [];
  // ✅ Aggiungi questa proprietà
  signal: string | null = null;
  slaveSymbols: { [key: number]: any[] } = {}; 
  // slaveSymbols: { [key: number]: SymbolType[] } = {};slaveSymbols: { [key: number]: SymbolType[] } = {};


  private copySubscriptions: { [key: number]: Subscription } = {}; // Mappa traderId → Subscription

  
  newTrader: NewTrader = {
    name: '',
    status: 'active'
  };


  showAddModal = false;
  showServersList = false;
  showAnalyzeModal = false;
  selectedTrader: Trader | null = null;
  loading: boolean=false;
  error: string="";
  serverService: any;
  errorMessage: string | undefined;
  serverConnected: { [serverId: number]: boolean } = {};
  analyzeTraderName = '';
  analyzeLoading = false;
  analyzeError = '';
  analyzeResult: any = null;
  analyzeSource: string = 'mt5';
  analyzeDays: number = 30;

  // ── AI Strategy Supervisor ──
  supervisorStatus: any = null;
  supervisorLoading = false;
  supervisorInterval: number = 600;
  supervisorModel: string = 'openrouter/free';
  supervisorApplying: { [traderId: number]: boolean } = {};
  private supervisorRefreshSub: Subscription | null = null;

  availableSignals = [
  { value: 'SUPER', label: 'XAUUSD Super' },
  { value: 'SUPER_LIVE', label: 'XAUUSD Super Live' },
  { value: 'SUPER_PRO', label: 'XAUUSD Super Pro' },
  { value: 'LONDON_BREAKOUT', label: 'XAUUSD London Breakout' },
  { value: 'BASE_NOHOLD', label: 'XAUUSD Base NoHold' },
  { value: 'ICHIMOKU', label: 'XAUUSD Ichimoku H1' },
  { value: 'SUPER_USDJPY', label: 'USDJPY Super' },
  { value: 'GBPUSD', label: 'GBPUSD Super' },
  { value: 'GBPJPY', label: 'GBPJPY Super' },
  { value: 'AUDJPY', label: 'AUDJPY Super' },
  { value: 'MSFT', label: 'MSFT M15' },
  { value: 'NVDA', label: 'NVDA M15' },
  { value: 'SCALPER_M1', label: 'EURUSD Scalper M1' },
  ];

  availableSessions = [
    { value: 'ASIA', label: 'ASIA', hours: '01:00 - 08:59' },
    { value: 'LONDON', label: 'LONDON', hours: '09:00 - 13:59' },
    { value: 'NY-LON', label: 'NY-LON', hours: '14:00 - 17:29' },
    { value: 'NY', label: 'NY', hours: '17:30 - 21:59' },
    { value: 'OFF', label: 'OFF', hours: '22:00 - 00:59' },
  ];

  sessionsDropdownOpen: { [traderId: number]: boolean } = {};

  toggleSessionsDropdown(traderId: number) {
    this.sessionsDropdownOpen[traderId] = !this.sessionsDropdownOpen[traderId];
  }

  toggleSession(trader: Trader, sessionValue: string) {
    const current = this.getSessionsList(trader);
    const idx = current.indexOf(sessionValue);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(sessionValue);
    }
    trader.sessions_filter = current.join(',');
  }

  isSessionSelected(trader: Trader, sessionValue: string): boolean {
    return this.getSessionsList(trader).includes(sessionValue);
  }

  getSessionsList(trader: Trader): string[] {
    if (!trader.sessions_filter) {
      return ['ASIA', 'LONDON', 'NY-LON', 'NY', 'OFF'];
    }
    return trader.sessions_filter.split(',').map(s => s.trim()).filter(s => s);
  }

  getSessionsLabel(trader: Trader): string {
    const list = this.getSessionsList(trader);
    if (list.length === 5) return 'All';
    if (list.length === 0) return 'None';
    if (list.length <= 2) return list.join(', ');
    return list.length + ' sessions';
  }

  closeSessionsDropdown(traderId: number) {
    this.sessionsDropdownOpen[traderId] = false;
  }



  // @Output() serverAdded = new EventEmitter<void>(); // <=== AGGIUNTO


  constructor(
    public authService: AuthService,
    private traderService: TraderService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  private readonly ORDER_KEY = 'mt5pulse_trader_order';

  ngOnInit() {

    this.loadServersAndTraders();
    this.loadSupervisorStatus();

    this.supervisorRefreshSub = interval(30000).subscribe(() => {
      if (this.supervisorStatus?.running) this.loadSupervisorStatus();
    });

  }

  onDrop(event: CdkDragDrop<Trader[]>) {
    moveItemInArray(this.traders, event.previousIndex, event.currentIndex);
    this.saveTraderOrder();
  }

  private loadTraderOrder(): number[] | null {
    try {
      const raw = localStorage.getItem(this.ORDER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  private saveTraderOrder() {
    try {
      const ids = this.traders.filter(t => t.id != null).map(t => t.id);
      localStorage.setItem(this.ORDER_KEY, JSON.stringify(ids));
    } catch {}
  }



    loadServersAndTraders() {
  this.loading = true; // flag di caricamento opzionale

  this.traderService.getAllServers().pipe(
    catchError(err => {
      console.error('Errore caricamento servers:', err);
      this.errorMessage = 'Impossibile caricare i server.';
      return of([] as Server[]); // ritorna array vuoto per continuare
    }),
    switchMap((serversData: Server[]) => {
      this.servers = serversData;
      console.log('Servers ricevuti dal backend:', JSON.stringify(serversData, null, 2));

      if (!serversData.length) {
        console.warn('Nessun server trovato.');
      }

      return this.traderService.loadTraders().pipe(
        catchError(err => {
          console.error('Errore caricamento traders:', err);
          this.errorMessage = 'Impossibile caricare i trader.';
          return of([] as Trader[]);
        })
      );
    }),
    finalize(() => {
      this.loading = false;
    })
  ).subscribe({
    next: (tradersData: Trader[]) => {
      this.traders = tradersData;

      // 🔄 Applica ordinamento salvato (drag & drop)
      const savedOrder = this.loadTraderOrder();
      if (savedOrder) {
        const map = new Map(this.traders.map(t => [t.id, t]));
        const reordered: Trader[] = [];
        for (const id of savedOrder) {
          const t = map.get(id);
          if (t) { reordered.push(t); map.delete(id); }
        }
        reordered.push(...map.values());
        this.traders = reordered;
      }

      // ✅ DEFAULT SIGNAL SEMPRE IL PRIMO + carica simboli slave
      this.traders.forEach(trader => {
        if (!trader.selected_signal) {
          trader.selected_signal = this.availableSignals[0].value;
        }
        if (!trader.sessions_filter) {
          trader.sessions_filter = 'ASIA,LONDON,NY-LON,NY,OFF';
        }
        if (trader.slave_server_id) {
          this.onSlaveSelected(trader);
        }
      });

      if (!tradersData.length) {
        console.warn('Nessun trader trovato.');
      }

      this.checkAllServersConnection();
    },
    error: (err) => {
      // Qui non dovrebbe più arrivare nulla perché catchError intercetta tutto
      console.error('Errore imprevisto:', err);
      this.errorMessage = 'Errore imprevisto durante il caricamento.';
    }
  });
}
  async loadTraders() {
    this.loading = true;
    this.error = '';

    this.traderService.loadTraders().subscribe({
      next: (res: Trader[]) => {
        this.traders = res.map(t => ({ ...t, direction_filter: t.direction_filter || 'both' }));
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore nel caricamento traders:', err);
        this.error = 'Errore durante il caricamento dei traders';
        this.loading = false;
      }
    });
  }

  addTrader(): void {
    // Validazione minima
    if (!this.newTrader.name || !this.newTrader.master_server_id || !this.newTrader.slave_server_id) {
      alert('Please fill in all required fields (Name, Master, Slave).');
      return;
    }

    // Imposta lo status di default
    this.newTrader.status = 'active';
    this.newTrader.created_at = new Date().toISOString();

    // Prepara payload per il backend
  const payload = {
    name: this.newTrader.name,
    status: 'active',
    master_server_id: Number(this.newTrader.master_server_id),
    slave_server_id: Number(this.newTrader.slave_server_id),
    sl: this.newTrader.sl ?? null,
    tp: this.newTrader.tp ?? null,
    tsl: this.newTrader.tsl ?? null,
    moltiplicatore: this.newTrader.moltiplicatore ?? null,
    fix_lot: this.newTrader.fix_lot ?? null
  };


  console.log('Payload:', payload); // Controllo rapido del JSON inviato


    this.traderService.insertTrader(payload as Trader).subscribe({
      next: (createdTrader: Trader) => {

        const name = createdTrader.name;
        this.traders.push(createdTrader); // Aggiunge alla lista in tempo reale
        // ✅ 1. Reset form
        this.newTrader = { name: '', status: 'active' };
        this.loadTraders();
        alert(`Trader aggiunto con successo!`);



      },
      error: (err: any) => {
        console.error('Error adding trader:', err);
        alert('Failed to add trader. See console for details.');
      }
      
    });
  }

// All'interno di UserDashboardComponent
async deleteTrader(trader: Trader) {
  if (!trader.id) {
    alert('Trader ID missing.');
    return;
  }

  // Conferma con l'utente
  const confirmed = confirm(`Sei sicuro di voler eliminare il trader "${trader.name}"?`);
  if (!confirmed) return;

  // Chiamata al service per eliminare il trader
  this.traderService.deleteTrader(trader.id).subscribe({
    next: (res: any) => {
      // Aggiorna la lista locali dei traders senza ricaricare tutto
      this.traders = this.traders.filter(t => t.id !== trader.id);
      alert(`Trader "${trader.name}" eliminato con successo.`);
    },
    error: (err: any) => {
      console.error('Errore eliminazione trader:', err);
      alert(`Errore durante l'eliminazione del trader "${trader.name}".`);
    }
  });
}

  toggleAutoCopy(trader: Trader) {
    if (!trader.id) return;

    if (trader.autoCopying) {
      // 🔴 Ferma
      this.stopAutoCopy(trader);
    } else {
      // 🟢 Avvia
      const seconds = trader.copyInterval || 5; // default 5s se non impostato
      trader.autoCopying = true;
      console.log(`🔁 Avvio auto-copy per ${trader.name} ogni ${seconds}s`);

      this.copySubscriptions[trader.id] = interval(seconds * 1000).subscribe(() => {
        this.traderService.copyOrders(trader.id!).subscribe({
          next: (res) => console.log(`✅ Copia automatica OK per ${trader.name}`),
          error: (err) => console.error(`❌ Errore auto-copy ${trader.name}:`, err)
        });
      });


    }
  }

  stopAutoCopy(trader: Trader) {
    const sub = this.copySubscriptions[trader.id!];
    if (sub) {
      sub.unsubscribe();
      delete this.copySubscriptions[trader.id!];
      trader.autoCopying = false;
      console.log(`⏹ Auto-copy fermato per ${trader.name}`);
    }
  }

  ngOnDestroy() {
    // 🔒 Stoppa tutti gli auto-copy quando si lascia la pagina
    Object.values(this.copySubscriptions).forEach(sub => sub.unsubscribe());
    if (this.supervisorRefreshSub) {
      this.supervisorRefreshSub.unsubscribe();
      this.supervisorRefreshSub = null;
    }
  }

  // ── AI Strategy Supervisor ──
  loadSupervisorStatus() {
    this.traderService.getSupervisorStatus().subscribe({
      next: (res: any) => {
        this.supervisorStatus = res;
        if (res?.interval_seconds) this.supervisorInterval = res.interval_seconds;
      },
      error: (err) => console.error('Supervisor status error:', err)
    });
  }

  toggleSupervisor() {
    if (this.supervisorStatus?.running) this.stopSupervisor();
    else this.startSupervisor();
  }

  startSupervisor() {
    this.supervisorLoading = true;
    this.traderService.startSupervisor({
      interval_seconds: Number(this.supervisorInterval),
      model: this.supervisorModel
    }).subscribe({
      next: () => {
        this.supervisorLoading = false;
        this.loadSupervisorStatus();
      },
      error: (err) => {
        this.supervisorLoading = false;
        console.error('Supervisor start error:', err);
        alert(err.error?.detail || 'Errore avvio supervisore');
      }
    });
  }

  stopSupervisor() {
    this.supervisorLoading = true;
    this.traderService.stopSupervisor().subscribe({
      next: () => {
        this.supervisorLoading = false;
        this.loadSupervisorStatus();
      },
      error: (err) => {
        this.supervisorLoading = false;
        console.error('Supervisor stop error:', err);
        alert(err.error?.detail || 'Errore stop supervisore');
      }
    });
  }

  runSupervisorNow() {
    this.supervisorLoading = true;
    this.traderService.runSupervisorNow().subscribe({
      next: (res: any) => {
        this.supervisorLoading = false;
        this.supervisorStatus = res;
        if (res?.interval_seconds) this.supervisorInterval = res.interval_seconds;
      },
      error: (err) => {
        this.supervisorLoading = false;
        console.error('Supervisor run-now error:', err);
        alert(err.error?.detail || 'Errore analisi immediata');
      }
    });
  }

  saveSupervisorConfig() {
    this.traderService.updateSupervisorConfig({
      interval_seconds: Number(this.supervisorInterval),
      model: this.supervisorModel
    }).subscribe({
      next: () => {
        alert('Config supervisore salvata');
        this.loadSupervisorStatus();
      },
      error: (err) => {
        console.error('Supervisor config error:', err);
        alert(err.error?.detail || 'Errore salvataggio config');
      }
    });
  }

  applySupervisor(rec: any, action: string) {
    if (!rec?.trader_id) return;
    this.supervisorApplying[rec.trader_id] = true;
    this.traderService.applySupervisorAction(rec.trader_id, action).subscribe({
      next: (res: any) => {
        console.log('Supervisor apply:', res);
        alert(res.message || `Azione ${action} applicata`);
        this.loadSupervisorStatus();
      },
      error: (err: any) => {
        console.error('Supervisor apply error:', err);
        alert(err.error?.detail || 'Errore applicando azione');
      },
      complete: () => { this.supervisorApplying[rec.trader_id] = false; }
    });
  }


// copyOrders(trader: Trader) {
//   if (!trader.id) return;

//   trader.copying = true;  // mostra spinner e disabilita button

//   this.traderService.copyOrders(trader.id).subscribe({
//     next: (res: any) => {
//       trader.copying = false;
//       alert(`✅ Copied ${res?.copied_orders || 0} orders for trader "${trader.name}"`);
//     },
//     error: (err: any) => {
//       trader.copying = false;
//       console.error(err);
//       alert(`❌ Error copying orders for trader "${trader.name}"`);
//     }
//   });
// }

copyOrders(trader: Trader) {
  trader.copying = true;
  // 🔹 Reset dei log precedenti prima di iniziare
  trader.logs = [];

  this.traderService.copyOrders(trader.id!).subscribe({
    next: (res) => {
      trader.copying = false;
      trader.logs = res.logs || [];   // 👈 assegna i log qui
      console.log("Logs ricevuti:", trader.logs);
    },
    error: (err) => {
      trader.copying = false;
      console.error("Errore copyOrders:", err);
    }
  });
}


saveTrader(trader: Trader) {
  console.log('🛠️ [SAVE TRADER] Avvio aggiornamento trader');
  console.log('──────────────────────────────────────────');
  console.log('📤 Dati inviati:', {
    id: trader.id,
    master_server_id: trader.master_server_id,
    slave_server_id: trader.slave_server_id,
    sl: trader.sl,
    tp: trader.tp,
    tsl: trader.tsl,
    moltiplicatore: trader.moltiplicatore,
    fix_lot: trader.fix_lot
  });
  console.log('──────────────────────────────────────────');

  this.traderService.updateTraderServers(
    trader.id!,
    trader.master_server_id ?? null,
    trader.slave_server_id ?? null,
    trader.sl ?? null,
    trader.tp ?? null,
    trader.tsl ?? null,
    trader.moltiplicatore ?? null,
    trader.fix_lot ?? null,
    trader.selected_signal ?? null,
    trader.custom_signal_interval ?? null,
    trader.selected_symbol ?? null,
    trader.sessions_filter ?? null


  ).subscribe({
    next: (res) => {
      console.log('✅ [UPDATE OK] Trader aggiornato dal backend:', res);

      this.traders = [...this.traders];
      this.cdr.detectChanges();
      alert(`Trader "${trader.name}" aggiornato con successo!`);

    },
    error: (err) => {
      console.error('❌ [UPDATE ERROR] Errore durante l\'aggiornamento trader:', err);
      alert('Errore durante l\'aggiornamento del trader');
    }
  });
}




  openAddModal() {
    this.showAddModal = true;
  }

  openServersList() {
    this.showServersList = true;
  }

  openBuyPosition() {
    
    const order: BuyRequest = {
      symbol: 'EURUSD',
      lot: 0.1,
      sl_point: 50,  // 50 punti stop loss
      tp_point: 100, // 100 punti take profit
      magic: 123456,
      comment: 'Ordine da Angular'
    };

    this.traderService.openBuyOrder(order).subscribe({
      next: (res: any) => console.log('Ordine aperto:', res),
      error: (err: any) => console.error('Errore ordine:', err)
    });
  }

  

  closeAddModal() {
    this.showAddModal = false;
  }

  closeServersList() {
    this.showServersList = false;
  }

  openAnalyze(trader: Trader) {
    if (!trader.id) return;
    this.analyzeTraderName = trader.name;
    this.analyzeLoading = true;
    this.analyzeError = '';
    this.analyzeResult = null;
    this.showAnalyzeModal = true;

    this.traderService.analyzeTrader(trader.id, 1000, this.analyzeSource, this.analyzeDays).subscribe({
      next: (res) => {
        this.analyzeResult = res;
        this.analyzeLoading = false;
      },
      error: (err) => {
        this.analyzeError = err.error?.detail || 'Errore durante l\'analisi';
        this.analyzeLoading = false;
      }
    });
  }

  closeAnalyze() {
    this.showAnalyzeModal = false;
    this.analyzeResult = null;
    this.analyzeError = '';
  }

  // async onTraderAdded() {
  //   this.showAddModal = false;
  //   await this.loadTraders();
  // }

  // async deleteTrader(trader: Trader) {
  //   if (!confirm(`Delete trader "${trader.name}"?`)) {
  //     return;
  //   }

  //   const result = await this.traderService.deleteTrader(trader.id);
  //   if (result.success) {
  //     await this.loadTraders();
  //   } else {
  //     alert(result.message);
  //   }
  // }

  async toggleTraderStatus(trader: Trader) {
    const newStatus = trader.status === 'active' ? 'inactive' : 'active';
    // await this.traderService.updateTrader(trader.id, { status: newStatus });
  }

  getServerNameById(serverId?: number): string {
  if (!this.servers || this.servers.length === 0) return 'Unknown';

  const server = this.servers.find(s => s.id === serverId);
  return server ? server.server : 'Unknown';
}

  checkAllServersConnection() {
    const uniqueSlaveIds = [...new Set(this.traders.map(t => t.slave_server_id).filter(id => id != null))];
    uniqueSlaveIds.forEach(serverId => {
      const server = this.servers.find(s => s.id === serverId);
      if (!server) return;
      this.traderService.checkServerConnection(server).subscribe({
        next: (res) => {
          this.serverConnected[res.serverId] = res.connected;
        },
        error: () => {
          this.serverConnected[serverId!] = false;
        }
      });
    });
  }

  isTraderConnected(trader: Trader): boolean {
    if (!trader.slave_server_id) return false;
    return this.serverConnected[trader.slave_server_id] ?? false;
  }

  
  toggleAdaptive(trader: Trader) {
    if (!trader.id) return;

    if (trader.adaptive_enabled) {
      const strategy = trader.selected_signal || 'SUPER';
      const symbol = trader.selected_symbol || 'XAUUSD';
      this.traderService.startAdaptive(trader.id, strategy, symbol).subscribe({
        next: (res: any) => {
          console.log(`🧬 Adaptive agent avviato per ${trader.name}:`, res);
        },
        error: (err: any) => {
          console.error(`❌ Errore avvio adaptive per ${trader.name}:`, err);
          trader.adaptive_enabled = false;
        }
      });
    } else {
      this.traderService.stopAdaptive(trader.id).subscribe({
        next: (res: any) => {
          console.log(`🧬 Adaptive agent fermato per ${trader.name}:`, res);
        },
        error: (err: any) => {
          console.error(`❌ Errore stop adaptive per ${trader.name}:`, err);
        }
      });
    }
  }

  logout() {
    this.authService.logout();
  }


  startListeningForBuy(trader: Trader) {
    // Verifica che sia stato selezionato un segnale
    if (!trader.selected_signal) {
      alert("Seleziona un segnale prima di avviare il listening!");
      return;
    }

    // Toggle ON/OFF
    trader.listening = !trader.listening;

    // 🔹 recupero lo slave server reale, per trovare il broker
    const slaveServer = this.servers.find(
      s => s.id === trader.slave_server_id
    );

    if (!slaveServer) {
      alert('❌ Slave server non trovato');
      trader.listening = false;
      return;
    }
    
    trader.broker = slaveServer.server;
    console.log("broker corrente:",slaveServer.server);

    if (trader.listening) {
      // ⭐ START LISTENING..
      console.log("Segnale selezionato:", trader.selected_signal);
      console.log("Intervallo custom:", trader.custom_signal_interval);
      console.log("Simbolo selezionato:", trader.selected_symbol);

      if (!trader.selected_symbol) {
        alert("Seleziona un simbolo prima di avviare il listening!");
        trader.listening = false;
        return;
      }

      // Passa anche il segnale selezionato al servizioo
      this.traderService.startListening(trader, trader.selected_signal).subscribe({
        next: (res: any) => {
          console.log("Polling started:", res);
        },
        error: (err: any) => {
          console.error("Error starting polling:", err);
          trader.listening = false;
        }
      });
      } else {
      // ⭐ STOP LISTENING
      // this.traderService.stopListeningBuy().subscribe({
      //   next: (res: any) => {
      //     console.log("Polling BUY stopped:", res);
      //   },
      //   error: (err: any) => {
      //     console.error("Error stopping polling:", err);
      //     trader.listening = true;
      //   }
      // });
      this.traderService.stopListening(trader).subscribe({
        next: (res: any) => {
          console.log("Polling BUY stopped:", res);
        },
        error: (err: any) => {
          console.error("Error stopping polling:", err);
          trader.listening = true;
        }
      });

    }
  }

  // carico i simboli tradabii dallo slave
  onSlaveSelected(trader: Trader) {
    const slaveServer = this.servers.find(s => s.id === trader.slave_server_id);
    if (!slaveServer) return;

    const slaveApiUrl = `http://${slaveServer.ip}:${slaveServer.port}`;
    // alert (slaveApiUrl);

    this.traderService.getSlaveSymbols(slaveApiUrl).subscribe({
      next: (res: any) => {
        console.log('Symbols from slave:', res);
        // memorizza i simboli per il trader selezionato
        this.slaveSymbols[trader.id] = res.symbols;
      },
      error: (err) => {
        console.error('Errore fetching symbols', err);
        // Log dettagliato
    if (err.status) {
      console.error(`Status: ${err.status} ${err.statusText || ''}`);
    }
    if (err.error) {
      console.error('Response body:', err.error);
    }
    if (err.message) {
      console.error('Message:', err.message);
    }
    console.error('Full error object:', err);

        this.slaveSymbols[trader.id] = [];
      }
    });
  }


}
