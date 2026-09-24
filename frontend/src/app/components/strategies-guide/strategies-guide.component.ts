import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

interface StrategyInfo {
  name: string;
  title: string;
  description: string;
  symbols: string[];
  timeframe: string;
  polling: string;
  slRange: string;
  tpRange: string;
  bestSession: string;
  riskLevel: 'Basso' | 'Medio' | 'Alto';
  frequency: string;
  tags: string[];
  tips: string[];
}

@Component({
  selector: 'app-strategies-guide',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './strategies-guide.component.html',
  styleUrls: ['./strategies-guide.component.css']
})
export class StrategiesGuideComponent {
  strategies: StrategyInfo[] = [
    {
      name: 'SUPER',
      title: 'SUPER — Multi-Timeframe Trend',
      description: 'Trend-following su 3 timeframe: entry su M1 (EMA9/21 + MACD), conferma HMA su M5, trend macro EMA50 su M15. Include regime filter (ATR percentile) e spike protection. SL/TP dinamici basati su ATR M5, scalati per regime (TREND: 2×/3×, NORMAL: 1.5×/2.2×).',
      symbols: ['XAUUSD', 'EURUSD', 'GBPUSD'],
      timeframe: 'M1 + M5 + M15',
      polling: '30-60 sec',
      slRange: '500-2000 (dinamico ATR)',
      tpRange: '600-3000 (dinamico ATR)',
      bestSession: 'London + New York (08:00-16:00 UTC)',
      riskLevel: 'Medio',
      frequency: '2-5 trade/giorno',
      tags: ['Trend', 'Multi-TF', 'Momentum', 'Regime Filter'],
      tips: [
        'News Filter attivo: trading sospeso ±30 min da NFP/CPI/FOMC automaticamente',
        'Funziona meglio in sessione London/NY dove la volatilità è sufficiente',
        'In sessione asiatica tende a stare in hold (corretto)',
        'Se il mercato è in range stretto, non darà segnali per ore — è normale'
      ]
    },
    {
      name: 'SUPER_PRO',
      title: 'SUPER PRO — Versione Strutturata',
      description: 'Stessa logica di SUPER con filtri M5/M15 più restrittivi. Meno trade ma di qualità superiore. Ideale per chi preferisce few-and-far-over.',
      symbols: ['XAUUSD', 'EURUSD'],
      timeframe: 'M1 + M5 + M15',
      polling: '30-60 sec',
      slRange: '500-2000 (dinamico ATR)',
      tpRange: '600-3000 (dinamico ATR)',
      bestSession: 'London + New York (08:00-16:00 UTC)',
      riskLevel: 'Medio',
      frequency: '1-3 trade/giorno',
      tags: ['Trend', 'Multi-TF', 'Selettivo'],
      tips: [
        'Più selettivo di SUPER: aspetta più conferme prima di entrare',
        'Win rate leggermente superiore, ma meno opportunità',
        'Ottimo come "secondo parere" alongside SUPER'
      ]
    },
    {
      name: 'SUPER_LIVE',
      title: 'SUPER LIVE — Production Tuned',
      description: 'Variante di SUPER ottimizzata per il trading live. Stessa logica multi-timeframe con parametri tarati per ridurre i falsi segnali in condizioni reali (spread, slippage).',
      symbols: ['XAUUSD', 'EURUSD', 'GBPUSD'],
      timeframe: 'M1 + M5 + M15',
      polling: '30-60 sec',
      slRange: '500-2000 (dinamico ATR)',
      tpRange: '600-3000 (dinamico ATR)',
      bestSession: 'London + New York (08:00-16:00 UTC)',
      riskLevel: 'Medio',
      frequency: '2-4 trade/giorno',
      tags: ['Trend', 'Multi-TF', 'Live'],
      tips: [
        'Usa questa variante per il trading live reale',
        'Parametri leggermente più conservativi rispetto a SUPER'
      ]
    },
    {
      name: 'LONDON_BREAKOUT',
      title: 'London Breakout — Range Asiatico',
      description: 'Tradà il breakout del range asiatico (00:00-07:00 UTC) all\'apertura di Londra. Entry su M5 quando il prezzo chiude fuori dal range con volume > 1.5× media. SL al centro del range, TP 1.5× altezza range. Max 1 trade/giorno.',
      symbols: ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY'],
      timeframe: 'M5',
      polling: '60 sec',
      slRange: '200-1500 (distanza dal centro range)',
      tpRange: '300-3000 (1.5× altezza range)',
      bestSession: 'Solo 07:00-11:00 UTC (apertura Londra)',
      riskLevel: 'Medio',
      frequency: 'Max 1 trade/giorno',
      tags: ['Breakout', 'Time-based', 'One-shot', 'Volume'],
      tips: [
        'Funziona meglio quando il range asiatico è stretto (< 200 punti su gold)',
        'News Filter: nei giorni di NFP/FOMC il trading è bloccato automaticamente ±30 min',
        'Complementare a SUPER: LB tradà la mattina, SUPER può tradare tutto il giorno',
        'Se il prezzo torna dentro il range dopo il breakout, il SL al centro ti protegge',
        'Non forzare: se non c\'è breakout nelle prime 2 ore, il giorno è "no trade"'
      ]
    },
    {
      name: 'MSFT',
      title: 'MSFT — US Tech Session',
      description: 'Strategia dedicata a Microsoft. Entry su M5 con EMA cross + HMA slope + trend macro M15. Solo durante la sessione di mercato USA (09:30-16:00 ET). Include spike protection (3× ATR) e volume filter (1.2×). Time-based exit dopo 30 min.',
      symbols: ['MSFT', 'MSFT.NAS'],
      timeframe: 'M5 + M15',
      polling: '30-60 sec',
      slRange: '150-600 (dinamico ATR)',
      tpRange: '250-1000 (dinamico ATR)',
      bestSession: 'Solo 09:30-16:00 America/New_York',
      riskLevel: 'Medio',
      frequency: '1-3 trade/giorno (solo in sessione USA)',
      tags: ['US Stocks', 'Session Filter', 'Trend', 'Time Exit'],
      tips: [
        'Non darà MAI segnale fuori dalla sessione USA — è by design',
        'I primi 30 min dopo l\'apertura (09:30-10:00 ET) sono i più volatili',
        'Il time exit (30 min) evita di tenere posizioni in sideways',
        'News Filter: earnings MSFT e dati USA bloccano il trading automaticamente'
      ]
    },
    {
      name: 'NVDA',
      title: 'NVDA — US Tech Volatile',
      description: 'Strategia dedicata a NVIDIA su M15. Trend following con EMA + RSI + volume. Solo durante la sessione USA. SL/TP più ampi rispetto a MSFT data la maggiore volatilità. Spike protection 3× ATR M15.',
      symbols: ['NVDA', 'NVDA.NAS'],
      timeframe: 'M15',
      polling: '60 sec',
      slRange: '200-1500 (dinamico ATR)',
      tpRange: '400-3000 (dinamico ATR)',
      bestSession: 'Solo 09:30-16:00 America/New_York',
      riskLevel: 'Alto',
      frequency: '1-2 trade/giorno (solo in sessione USA)',
      tags: ['US Stocks', 'Volatile', 'Session Filter', 'Trend'],
      tips: [
        'NVDA è molto più volatile di MSFT: SL/TP devono essere ampi',
        'Non usare lot alti: un movimento del 5% su NVDA è normale',
        'Il time frame M15 filtra il noise di M1/M5',
        'News Filter: earnings NVDA e giorni di Fed bloccano il trading automaticamente'
      ]
    },
    {
      name: 'ICHIMOKU',
      title: 'Ichimoku Cloud — Multi-TF',
      description: 'Strategia basata sull\'Ichimoku Kinko Hyo su 4 timeframe (M1/M5/M15/H1). Entry su kumo breakout + Tenkan/Kijun cross. Adatta a mercati con trend chiaro e persistente.',
      symbols: ['XAUUSD', 'EURUSD', 'GBPUSD'],
      timeframe: 'M1 + M5 + M15 + H1',
      polling: '60 sec',
      slRange: '100-500',
      tpRange: '200-1000',
      bestSession: 'London + New York',
      riskLevel: 'Medio',
      frequency: '1-3 trade/giorno',
      tags: ['Ichimoku', 'Multi-TF', 'Trend', 'Cloud'],
      tips: [
        'Funziona meglio quando il prezzo è fuori dal kumo (trend chiaro)',
        'In range (prezzo dentro il kumo) tende a dare segnali falsi',
        'Il componente H1 dà il contesto macro: se H1 è in range, evita'
      ]
    },
    {
      name: 'EURUSD_NOHOLD',
      title: 'EURUSD NoHold — Intraday',
      description: 'Strategia intraday dedicata a EURUSD su M5. Breakout con EMA + RSI. Flat prima della chiusura del mercato (no overnight hold). Minimizza il rischio di gap notturni.',
      symbols: ['EURUSD'],
      timeframe: 'M5',
      polling: '30-60 sec',
      slRange: '30-200',
      tpRange: '60-400',
      bestSession: 'London + New York (08:00-16:00 UTC)',
      riskLevel: 'Basso',
      frequency: '2-5 trade/giorno',
      tags: ['Intraday', 'No Overnight', 'Breakout', 'M5'],
      tips: [
        'Nessuna posizione overnight: rischio gap eliminato',
        'SL/TP stretti: adatta a spread bassi (broker ECN)',
        'In sessione asiatica darà pochi segnali (range troppo stretto)'
      ]
    },
    {
      name: 'GBPUSD',
      title: 'GBPUSD — Intraday Breakout',
      description: 'Scalping intraday su GBPUSD con M5. Entry su breakout con EMA + RSI confirmation. SL/TP stretti per quick scalps.',
      symbols: ['GBPUSD'],
      timeframe: 'M5',
      polling: '30 sec',
      slRange: '30-200',
      tpRange: '60-400',
      bestSession: 'London (08:00-12:00 UTC)',
      riskLevel: 'Medio',
      frequency: '3-6 trade/giorno',
      tags: ['Scalping', 'Intraday', 'M5', 'Breakout'],
      tips: [
        'GBPUSD è più volatile di EURUSD: SL/TP leggermente più ampi',
        'La sessione London è la migliore (massima liquidità)',
        'Attenzione alle news UK (CPI, BoE decisions)'
      ]
    },
    {
      name: 'GBPJPY',
      title: 'GBPJPY — Trend Scalper',
      description: 'Trend scalping su GBPJPY con M5. Coppia ad alta volatilità: SL/TP più ampi rispetto alle major EUR. Momentum entry con EMA + RSI.',
      symbols: ['GBPJPY'],
      timeframe: 'M5',
      polling: '30-60 sec',
      slRange: '50-400',
      tpRange: '100-800',
      bestSession: 'London + Tokyo overlap (00:00-02:00 UTC) e London (08:00-12:00 UTC)',
      riskLevel: 'Alto',
      frequency: '2-4 trade/giorno',
      tags: ['Volatile', 'Trend', 'Scalping', 'Cross'],
      tips: [
        'GBPJPY ("The Beast") può muoversi 1000+ punti/giorno',
        'Usa lot piccoli: la volatilità è 2-3× quella di EURUSD',
        'Lo spread è più largo: assicurati che TP > 2× spread'
      ]
    },
    {
      name: 'AUDJPY',
      title: 'AUDJPY — Momentum',
      description: 'Momentum entry su AUDJPY con M5. Coppia con volatilità media, adatta a chi cerca un\'alternativa alle major con buon R:R.',
      symbols: ['AUDJPY'],
      timeframe: 'M5',
      polling: '30-60 sec',
      slRange: '30-200',
      tpRange: '60-400',
      bestSession: 'Sydney + Tokyo (00:00-04:00 UTC) e London (08:00-12:00 UTC)',
      riskLevel: 'Medio',
      frequency: '2-4 trade/giorno',
      tags: ['Momentum', 'Cross', 'M5'],
      tips: [
        'AUDJPY reagisce forte ai dati Australiani (employment, RBA)',
        'La sessione asiatica è più attiva rispetto alle EUR pairs',
        'Correlata negativamente con USDJPY in molti periodi'
      ]
    },
    {
      name: 'SCALPER_M1',
      title: 'Scalper M1 — Mean Reversion',
      description: 'Mean-reversion scalper su M1. Buy se prezzo < EMA21 e RSI < 35. Sell se prezzo > EMA21 e RSI > 65. SL/TP stretti per quick scalps. Adatto a mercati in range.',
      symbols: ['EURUSD', 'GBPUSD'],
      timeframe: 'M1',
      polling: '15-30 sec',
      slRange: '50-200',
      tpRange: '100-400',
      bestSession: 'London (08:00-12:00 UTC) — evitare apertura',
      riskLevel: 'Alto',
      frequency: '5-15 trade/giorno',
      tags: ['Scalping', 'Mean Reversion', 'M1', 'High Frequency'],
      tips: [
        'REQUIRE uno spread molto basso (ECN/Raw account, < 0.1 pips)',
        'Non funzionare in trend forte: il prezzo continua a muoversi contro di te',
        'Ideale in range: quando ADX < 20',
        'Attenzione ai costi: con 10+ trade/giorno lo spread incide molto',
        'Polling a 15-30 sec è essenziale per non perdere l\'entry'
      ]
    },
    {
      name: 'BASE_NOHOLD',
      title: 'BASE NoHold — Simple M5',
      description: 'Strategia base su M5 senza overnight hold. Semplice breakout con EMA. Flat prima della chiusura. Utile come fallback o per testare nuovi simboli.',
      symbols: ['EURUSD', 'GBPUSD', 'USDJPY'],
      timeframe: 'M5',
      polling: '30-60 sec',
      slRange: '50-300',
      tpRange: '100-600',
      bestSession: 'London + New York',
      riskLevel: 'Basso',
      frequency: '2-4 trade/giorno',
      tags: ['Simple', 'M5', 'No Overnight', 'Fallback'],
      tips: [
        'La strategia più semplice: buona per iniziare',
        'Nessun overnight risk',
        'Prestazioni moderate: non aspettarti win rate elevati'
      ]
    },
    {
      name: 'SUPER_USDJPY',
      title: 'SUPER USDJPY — Yen Tuned',
      description: 'Variante di SUPER tarata per USDJPY. Stessa logica multi-timeframe con SL/TP range adattati alla volatilità del yen.',
      symbols: ['USDJPY'],
      timeframe: 'M1 + M5 + M15',
      polling: '30-60 sec',
      slRange: '50-300',
      tpRange: '100-600',
      bestSession: 'London + Tokyo + New York',
      riskLevel: 'Medio',
      frequency: '2-4 trade/giorno',
      tags: ['Trend', 'Multi-TF', 'Yen', 'USDJPY'],
      tips: [
        'USDJPY reagisce forte ai yield USA (bond auctions, Fed)',
        'La sessione Tokyo (00:00-04:00 UTC) è attiva per il yen',
        'SL/TP più stretti rispetto a XAUUSD (meno volatile)'
      ]
    }
  ];

  get riskColors(): { [key: string]: string } {
    return { 'Basso': 'risk-low', 'Medio': 'risk-medium', 'Alto': 'risk-high' };
  }
}
