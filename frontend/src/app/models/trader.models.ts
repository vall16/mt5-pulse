
export interface CreateTraderRequest {
  name: string;
  mt5_login: string;
  mt5_password: string;
  mt5_server: string;
}

export interface CopyOrdersResponse {
  logs: string[];
  message?: string;
}

// per il test del server mt5
 export interface CheckServerResponse {
    status: 'ok' | 'ko';
    message: string;
    mt5_version?: string;
    connected?: boolean;
    terminal?: {
      name: string;
      company: string;
      path: string;
    };
}



export interface Trader {
  // id?: number;
  id: number;
  name: string;
  status: 'active' | 'inactive';  // is_active diventa status
  master_server_id?: number;      // riferimento al server master
  slave_server_id?: number;       // riferimento al server slave
  sl?: number;                    // Stop Loss
  tp?: number;                    // Take Profit
  tsl?: number;                   // Trailing Stop Loss
  moltiplicatore?: number;        // fattore di copia
  fix_lot?: number;               // lotto fisso 
  created_at?: string;
  updated_at?: string;
  broker?: string;           // il broker corrente, preso dal server slave
  // copying?: boolean;  

  // 🔁 Campi locali (non nel DB)
  autoCopying?: boolean;
  copyInterval?: number;
  selected_signal?: string;

  custom_signal_interval?: number;
  selected_symbol?: string;   
  copying?: boolean;
  logs?: string[];   
  listening?: boolean;
  analyzing?: boolean;
  _listenInterval?: any;   

  // 🆕 Profit TP locale (non salvato in DB)
  use_profit_tp?: boolean;
  profit_tp_value?: number;

  // 🆕 Blocco notturno (non salvato in DB)
  block_night_trading?: boolean;

  // 🆕 Direction filter (buy/sell/both)
  direction_filter?: string;

  // 🆕 Session filter (ASIA,LONDON,NY-LON,NY,OFF)
  sessions_filter?: string;

  // 🆕 Adaptive SL/TP (non salvato in DB)
  adaptive_enabled?: boolean;

  // 🆕 Forza SL/TP dal form (non salvato in DB)
  use_signal_sl_tp?: boolean;
}

export interface NewTrader {
  
  name: string;
  status: 'active' | 'inactive';  // is_active diventa status
  master_server_id?: number;      // riferimento al server master
  slave_server_id?: number;       // riferimento al server slave
  sl?: number;                    // Stop Loss
  tp?: number;                    // Take Profit
  tsl?: number;                   // Trailing Stop Loss
  moltiplicatore?: number;        // fattore di copia
  fix_lot?: number;               // lotto fisso (opzionale)
  created_at?: string;
  updated_at?: string;
}

export interface BuyRequest {
  symbol: string;
  lot: number;
  sl_point?: number;
  tp_point?: number;
  magic?: number;
  comment?: string;
}



export interface SlaveSymbol {
  symbol: string;   // es. "EURAUD"
  base: string;     // valuta base, es. "EUR"
  profit: string;   // valuta di profitto, es. "AUD"
  spread: number;   // spread in punti, es. 18
  digits: number;   // numero di decimali, es. 5
  point: number;    // valore di un punto, es. 0.00001
}

export interface SlaveOrder {
  id: number;
  trader_id: number;
  master_order_id: number | null;
  master_ticket: number | null;
  ticket: number;
  symbol: string;
  type: number;
  volume: number;
  price_open: number;
  price_close: number;
  profit: number;
  comment: string | null;
  opened_at: string;
  closed_at: string;
}



