export interface AccountInfo {
  login: number;
  trade_mode: number;
  leverage: number;
  limit_orders: number;
  margin_so_mode: number;
  trade_allowed: boolean;
  trade_expert: boolean;
  margin_mode: number;
  currency_digits: number;
  fifo_close: boolean;
  balance: number;
  credit: number;
  profit: number;
  equity: number;
  margin: number;
  margin_free: number;
  margin_level: number;
  margin_so_call: number;
  margin_so_so: number;
  margin_initial: number;
  margin_maintenance: number;
  assets: number;
  liabilities: number;
  commission_blocked: number;
  name: string;
  server: string;
  currency: string;
  company: string;
}

export interface Position {
  ticket: number;
  time: number;
  time_msc: number;
  time_update: number;
  time_update_msc: number;
  type: number;
  magic: number;
  identifier: number;
  reason: number;
  volume: number;
  price_open: number;
  sl: number;
  tp: number;
  price_current: number;
  swap: number;
  profit: number;
  symbol: string;
  comment: string;
  external_id: string;
}

export interface SymbolInfo {
  symbol: string;
  tradable: boolean;
  selected: boolean;
  currency_base: string;
  currency_profit: string;
  spread: number;
  point: number;
}

export interface Tick {
  time: number;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  time_msc: number;
  flags: number;
  volume_real: number;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
  spread: number;
  real_volume: number;
}

export interface OrderRequest {
  symbol: string;
  lot: number;
  sl_point: number;
  tp_point: number;
  deviation: number;
  magic: number;
  comment?: string;
}

export interface CloseRequest {
  symbol: string;
  magic: number;
  deviation: number;
}

export interface OrderResult {
  retcode: number;
  deal: number;
  order: number;
  volume: number;
  price: number;
  bid: number;
  ask: number;
  comment: string;
  request_id: number;
  retcode_external: number;
  request: any;
}

export interface MarginInfo {
  balance: number;
  equity: number;
  margin: number;
  margin_level: number;
}
