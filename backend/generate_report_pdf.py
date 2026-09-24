from fpdf import FPDF

class Report(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, "MT5Pulse - Report Progetto", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

def section_title(pdf, title):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(17, 85, 204)
    pdf.cell(0, 8, title)
    pdf.ln(6)
    pdf.set_draw_color(17, 85, 204)
    pdf.set_line_width(0.6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

def sub_title(pdf, title):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 6, title)
    pdf.ln(5)

def body(pdf, text):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)

def bullets(pdf, items):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    for item in items:
        x = pdf.get_x()
        pdf.cell(4, 5, "-")
        pdf.multi_cell(0, 5, item)
        pdf.set_x(x)
    pdf.ln(2)

def table(pdf, headers, rows, widths=None, header_fill=(17, 85, 204)):
    if widths is None:
        widths = [190.0 / len(headers)] * len(headers)
    col_w = widths
    cell_h = 6
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*header_fill)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], cell_h, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    fill = False
    for row in rows:
        y0 = pdf.get_y()
        line_h = cell_h
        for i, val in enumerate(row):
            if isinstance(val, str) and "\n" in val:
                lines = val.split("\n")
                if len(lines) > line_h:
                    line_h = len(lines) * 5
        if y0 + line_h > pdf.page_break_trigger - 12:
            pdf.add_page()
            y0 = pdf.get_y()
        if fill:
            pdf.set_fill_color(238, 242, 255)
        for i, val in enumerate(row):
            pdf.cell(col_w[i], line_h, str(val), border=1, fill=fill)
        pdf.ln(line_h)
        fill = not fill
    pdf.ln(3)


pdf = Report(format="A4")
pdf.set_margins(12, 12, 12)
pdf.set_auto_page_break(auto=True, margin=14)

pdf.add_page()
pdf.set_fill_color(17, 85, 204)
pdf.rect(0, 0, 210, 46, "F")
pdf.set_text_color(255, 255, 255)
pdf.set_y(12)
pdf.set_font("Helvetica", "B", 24)
pdf.cell(0, 12, "MT5Pulse", align="C")
pdf.ln(13)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 7, "Piattaforma di Trading Automatico su MetaTrader 5", align="C")
pdf.ln(8)
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 5, "Report di progetto", align="C")
pdf.set_text_color(40, 40, 40)

pdf.ln(12)
section_title(pdf, "1. Cos'e")
body(pdf, "MT5Pulse e una piattaforma di trading automatico (bot) multi-strategia basata su MetaTrader 5. "
          "Gestisce piu 'trader' (coppie strategia + simbolo) che eseguono segnali in automatico su conti MT5, "
          "con dashboard web, backtesting, ottimizzazione AI e supervisione automatica delle strategie.")

section_title(pdf, "2. Architettura")
sub_title(pdf, "Monorepo con 3 componenti")
table(pdf,
      ["Componente", "Stack", "Ruolo"],
      [
          ["backend/", "FastAPI (Python) + MySQL", "Manager: API centrale, DB, strategie, supervisione AI"],
          ["frontend/", "Angular 20 (standalone) + Supabase", "UI web per gestione trader/server, trading, backtest"],
          ["trading_api/ + backend/mt5_api/", "FastAPI + libreria MetaTrader5", "Agente slave: gira su ogni server con MT5 installato (solo Windows), espone dati e invia ordini"],
      ],
      widths=[52, 70, 68])
body(pdf, "Flusso master/slave: il manager (backend) comunica via HTTP con gli agenti MT5 remoti, che a loro volta "
          "inizializzano il terminale, eseguono il login al broker, leggono i prezzi e piazzano/chiudono ordini.")

section_title(pdf, "3. Funzionalita principali")

sub_title(pdf, "3.1 Gestione trader e server")
bullets(pdf, [
    "Registrazione dei server MT5 (avvio / init / login remoto del terminale via /mt5/start_server).",
    "Creazione di 'trader': account configurato con server master/slave, simbolo, strategia, SL/TP, lotto, moltiplicatore e sessione di trading (ASIA / LONDON / NY-LON / NY / OFF).",
    "Copy-trading automatico (copia ordini da master a slave).",
    "Autenticazione utente (login, bcrypt) e supporto Supabase.",
])

sub_title(pdf, "3.2 Strategie di trading automatico (16 strategie)")
body(pdf, "In trading_signals_multi2.py, implementate con pattern strategy pattern: BASE, BASE_NOHOLD, TRENDGUARD, "
          "TRENDGUARD_XAU, EURUSD_NOHOLD, SUPER, SUPER_PRO, SUPER_LIVE, ICHIMOKU, MSFT, NVDA, SUPER_USDJPY, GBPUSD, "
          "GBPJPY, AUDJPY, SCALPER_M1.")
body(pdf, "Ogni trader avvia un polling loop (intervallo configurabile, default 5s) che analizza i dati tramite indicatori "
          "tecnici (EMA, RSI, MACD, ATR, Bollinger, HMA, ADX, Ichimoku) e piazza ordini. Logica SL/TP dinamica via ATR M5 "
          "con override fisso configurabile.")

sub_title(pdf, "3.3 AI Strategy Supervisor")
body(pdf, "Agente (strategy_supervisor.py) che valuta periodicamente tutti i trader attivi e produce raccomandazioni "
          "ACTIVE / PAUSE / WATCH:")
bullets(pdf, [
    "Regole di sicurezza deterministiche (mercato chiuso, notte, news, perdite consecutive, win rate basso, drawdown) che forzano PAUSE.",
    "LLM via OpenRouter per il ragionamento testuale. Solo raccomandazioni: non agisce in autonomia.",
    "API /supervisor/* + pannello frontend con start / stop / run-now / apply.",
])

sub_title(pdf, "3.4 Backtest e ottimizzazione AI")
bullets(pdf, [
    "backtest.py: motore di backtesting per tutte le strategie.",
    "Signal Research (signal_research_routes.py): ottimizzazione brute-force di SL/TP (griglia di parametri) per piu strategie in parallelo, con sessioni async.",
    "Auto Signal Discovery: ricerca automatica delle migliori combinazioni di parametri.",
    "AI analysis (ai_analysis.py, ai_backtest.py): analisi LLM dei trade chiusi e dei risultati di backtest.",
])

sub_title(pdf, "3.5 Adaptive Agent")
body(pdf, "Agente che monitora i trade chiusi e adatta automaticamente i fattori SL/TP (ATR) tramite regole if/else.")

section_title(pdf, "4. Le 16 strategie in dettaglio")

sub_title(pdf, "4.0 Framework comune")
body(pdf, "Tutte le strategie derivano dalla classe base SignalStrategy in trading_signals_multi2.py. "
          "Ogni trader configurato avvia un polling loop (intervallo customizzabile, default 5s) che, a ogni ciclo, "
          "carica le candele richieste dall'agente slave, calcola gli indicatori, applica i controlli (mercato aperto, "
          "blocco notturno, filtro sessioni, direction filter) e valuta le condizioni BUY / SELL / HOLD. Se il segnale "
          "scatta e non esiste gia una posizione nella stessa direzione, invia l'ordine allo slave con SL/TP calcolato.")
body(pdf, "Regime di volatilita: il sistema classifica lo stato del mercato in RANGE / NORMAL / TREND / NEWS usando "
          "il percentile dell'ATR M15 su 192 candele (~2 giorni) e lo score di tendenza dell'EMA50 M15. Le strategie "
          "'Super' usano il regime per adattare le soglie RSI e i fattori SL/TP; il regime NEWS (spike o ATR nel "
          "9 decimo percentile) esclude quasi sempre gli ingressi.")

def strategy_block(pdf, name, symbol, timeframe, concept, entry, exit_rule, sltp):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(17, 85, 204)
    pdf.set_fill_color(238, 242, 255)
    pdf.cell(0, 6, f"{name}  |  {symbol}  |  {timeframe}", fill=True, border=1)
    pdf.ln(7)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 5, "Concetto")
    pdf.ln(4)
    body(pdf, concept)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, "Condizioni di ingresso")
    pdf.ln(4)
    body(pdf, entry)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, "Gestione uscita / SL / TP")
    pdf.ln(4)
    body(pdf, exit_rule)
    body(pdf, sltp)
    pdf.ln(1)

sub_title(pdf, "4.1 Strategie base (SL/TP fissi dell'utente)")

strategy_block(pdf, "BASE", "XAUUSD", "M5",
    "Strategia di trend-following semplice: segue l'incrocio tra due medie mobili EMA sul grafico M5.",
    "BUY quando EMA5 > EMA15 e RSI(14) < 68. SELL quando EMA5 < EMA15 e RSI(14) > 32. Le soglie RSI evitano ingressi "
    "a mercato gia surriscaldato.",
    "Chiude la posizione aperta quando il segnale torna HOLD (modalita close_on_hold=True): se prima era BUY/SELL e "
    "c'e una posizione in quella direzione, viene chiusa.",
    "Non calcola SL/TP dinamici: usa sempre i valori fissi impostati dall'utente nel form.")

strategy_block(pdf, "BASE_NOHOLD", "XAUUSD", "M5",
    "Identica a BASE ma senza chiusura su HOLD: tiene la posizione aperta finche non arriva un segnale inverso, "
    "uno stop loss o il take profit.",
    "Stesse condizioni di BASE: BUY con EMA5 > EMA15 e RSI < 68; SELL con EMA5 < EMA15 e RSI > 32.",
    "Non chiude la posizione su HOLD (close_on_hold=False); la lascia correre fino a segnale opposto, SL o TP.",
    "SL/TP fissi dell'utente.")

strategy_block(pdf, "TRENDGUARD / TRENDGUARD_XAU", "XAUUSD", "M5",
    "Variante di BASE registrata con nome dedicato ('XAUUSD Trend Guard' nell'interfaccia). Stessa logica EMA+RSI "
    "con chiusura su HOLD.",
    "BUY con EMA5 > EMA15 e RSI < 68; SELL con EMA5 < EMA15 e RSI > 32.",
    "Chiude la posizione al ritorno del segnale HOLD.",
    "SL/TP fissi dell'utente.")

strategy_block(pdf, "EURUSD_NOHOLD", "EURUSD", "M5",
    "Strategia per EURUSD basata su incrocio EMA con medie piu distanziate (5/20) per catturare movimenti piu ampi.",
    "BUY quando EMA5 > EMA20 e RSI < 65. SELL quando EMA5 < EMA20 e RSI > 35.",
    "Non chiude su HOLD: la posizione resta attiva fino a segnale inverso, SL o TP.",
    "SL/TP fissi dell'utente.")

sub_title(pdf, "4.2 La famiglia SUPER (XAUUSD, SL/TP dinamici via ATR M5)")

strategy_block(pdf, "SUPER", "XAUUSD", "M1 + M5 + M15",
    "Strategia principale multi-timeframe: combina micro-trend M1 (EMA9/21, MACD), conferma HMA M5, filtro di trend "
    "EMA50 su M15 e regime di volatilita. E il 'flagship' del progetto, usato anche come base del backtesting.",
    "Tutte le condizioni devono essere vere: EMA9 M1 > EMA21 M1; MACD M1 > linea di segnale; HMA M5 in salita "
    "(hma > hma precedente); prezzo M15 sopra EMA50 (trend rialzista); RSI M1 nel range 45-70 (80 in regime TREND) "
    "per il BUY (sell speculare con RSI 25-30 / 55); espansione di volatilita (ATR M1 > media 10 candele); candela "
    "non-spike (corpo < 4x ATR); regime non RANGE.",
    "Non inverte posizione (reverse_on_buy/sell = False) e non chiude su HOLD: esce solo con SL/TP o segnale opposto.",
    "SL/TP dinamici proporzionali all'ATR M5 e al regime: in TREND 2.0x/3.0x ATR, altrimenti 1.5x/2.2x. Valori "
    "clampati tra 500-2000 (SL) e 600-3000 (TP).")

strategy_block(pdf, "SUPER_PRO", "XAUUSD", "M1 + M5 + M15",
    "Evoluzione di SUPER con filtri piu stringenti: trend macro filtrato da EMA200 M15 (anziche EMA50) piu conferma "
    "EMA50 M15, e parametri adattati alla sessione di trading corrente.",
    "BUY solo se prezzo sopra EMA200 M15 e sopra EMA50 M15, regime ok, EMA9>EMA21, MACD>segnale, HMA M5 in salita, "
    "RSI nel range della sessione (es. LONDON 45-72, NY-LON 42-68, ASIA 50-78) e volatilita in espansione. SELL "
    "speculare sotto EMA200.",
    "Exit rule dedicata: chiude la posizione long se il trend macro inverte (prezzo sotto EMA200 con HMA M5 in calo) "
    "e viceversa per lo short, oltre a SL/TP.",
    "SL/TP dinamici per sessione: fattori ATR M5 scalati (ASIA 4.0x, LONDON 3.0x, NY-LON 2.5x, NY 3.0x, OFF 5.0x) "
    "con moltiplicatore 10, modulati dal regime (x1.0 in TREND, x0.8 in NORMAL), clamp 300-2000 / 400-3000.")

strategy_block(pdf, "SUPER_LIVE", "XAUUSD", "M1 + M5 + M15",
    "Versione 'live' di SUPER: scatta sulla candela M1 ancora in formazione invece che sulla candela chiusa, "
    "rivalutata a ogni poll. Pensata per polling ad alta frequenza (5-15s) per anticipare il segnale.",
    "Crossover fresco sul prezzo live: prezzo > EMA9 live con EMA9 precedente sopra il prezzo della candela chiusa "
    "(crossover EMA9 appena avvenuto), EMA9>EMA21, MACD>segnale, HMA M5 in salita, trend EMA50 M15 up, RSI 45-70, "
    "volatilita in espansione e no spike.",
    "Non inverte e non chiude su HOLD (quiet_holds sopprime i log di HOLD per ridurre il rumore).",
    "SL/TP piu stretti per l'ingresso anticipato: 1.5x/2.5x ATR M5, clamp 400-1500 / 500-2500.")

strategy_block(pdf, "SUPER_USDJPY", "USDJPY", "M1 + M5 + M15",
    "Stessa architettura multi-timeframe di SUPER adattata a USDJPY (valuta con volatilita molto piu bassa).",
    "BUY con EMA9>EMA21, MACD>segnale, HMA M5 in salita, prezzo sopra EMA50 M15, RSI 40-68, espansione volatilita e "
    "no spike. SELL speculare con RSI 32-60.",
    "Non inverte e non chiude su HOLD.",
    "SL/TP condizionati: se ATR M5 <= 0.050 usa 500/600 fissi, altrimenti torna ai valori dell'utente.")

strategy_block(pdf, "GBPUSD", "GBPUSD", "M1 + M5 + M15",
    "Implementazione della famiglia SUPER su GBPUSD.",
    "BUY con EMA9>EMA21, MACD>segnale, HMA M5 in salita, trend EMA50 M15 up, RSI 40-70, espansione e no spike. "
    "SELL speculare con RSI 30-60.",
    "Non inverte e non chiude su HOLD.",
    "SL/TP condizionati: se ATR M5 <= 0.0012 usa 500/600 fissi, altrimenti valori dell'utente.")

strategy_block(pdf, "GBPJPY", "GBPJPY", "M1 + M5 + M15",
    "Famiglia SUPER su GBPJPY (coppia volatile, RSI piu permissivo).",
    "BUY con EMA9>EMA21, MACD>segnale, HMA M5 in salita, trend up, RSI 35-75, espansione e no spike. SELL speculare "
    "con RSI 25-65.",
    "Non inverte e non chiude su HOLD.",
    "SL/TP condizionati: se ATR M5 <= 0.080 usa 800/1000 fissi, altrimenti valori dell'utente.")

strategy_block(pdf, "AUDJPY", "AUDJPY", "M1 + M5 + M15",
    "Famiglia SUPER su AUDJPY.",
    "BUY con EMA9>EMA21, MACD>segnale, HMA M5 in salita, trend up, RSI 38-72, espansione e no spike. SELL speculare "
    "con RSI 28-62.",
    "Non inverte e non chiude su HOLD.",
    "SL/TP condizionati: se ATR M5 <= 0.060 usa 600/800 fissi, altrimenti valori dell'utente.")

sub_title(pdf, "4.3 Azionario e altre strategie")

strategy_block(pdf, "MSFT", "MSFT", "M5",
    "Strategia per il titolo Microsoft: trend EMA + HMA con filtro di volume per confermare la partecipazione.",
    "BUY con EMA5>EMA15, HMA in salita, RSI 35-80 e tick volume sopra l'80% della media a 20 candele. SELL speculare "
    "con EMA5<EMA15, HMA in calo, RSI 20-65 e volume ok.",
    "Non inverte e non chiude su HOLD.",
    "SL/TP fissi 120 / 250 punti.")

strategy_block(pdf, "NVDA", "NVDA", "M15",
    "Strategia per NVIDIA, solo long (buy-only): cattura rimbalzi, impulsi su medie e ritorni alla media su timeframe "
    "M15, con filtro macro EMA50.",
    "Tre pattern d'ingresso alternativi: (1) rimbalzo RSI da <35 a >35 con EMA5>EMA20; (2) impulso con RSI 40-65 e "
    "EMA5 sopra EMA13; (3) pullback con prezzo tornato sulla EMA20 e RSI<55.",
    "Chiude la posizione long su HOLD quando EMA5 scende sotto EMA20; SL/TP come backup.",
    "SL/TP fissi 150 / 500 punti.")

strategy_block(pdf, "ICHIMOKU", "XAUUSD", "H1",
    "Strategia basata sul sistema Ichimoku su timeframe H1: utilizza Tenkan, Kijun, Senkou (nuvola) e Chikou. E "
    "l'unica strategia che inverte la posizione quando il segnale cambia lato.",
    "BUY con prezzo sopra la nuvola (senkou A e B) e Tenkan > Kijun. SELL con prezzo sotto la nuvola e Tenkan < Kijun.",
    "Inverte la posizione: se il segnale passa a BUY con una SELL aperta, chiude la SELL e apre il BUY (e viceversa).",
    "SL/TP fissi dell'utente.")

strategy_block(pdf, "SCALPER_M1", "EURUSD", "M1",
    "Scalper mean-reversion su M1: compra su estremi ribassisti e vende su estremi rialzisti rispetto all'EMA21, "
    "usando l'ATR per definire le bande di ritorno.",
    "BUY quando prezzo < EMA21 e RSI < 35 (ipervenduto, ritorno verso la media). SELL quando prezzo > EMA21 e RSI > 65 "
    "(ipercomprato). Le bande EMA21 +/- 2 ATR delimitano il range atteso.",
    "Non inverte e non chiude su HOLD; esce con SL/TP.",
    "SL/TP fissi 120 / 250 punti (12 pips SL, 25 pips TP su EURUSD).")

section_title(pdf, "5. Frontend (pagina web)")
table(pdf,
      ["Pagina", "Funzione"],
      [
          ["Dashboard", "Conto MT5, margine, posizioni aperte (auto-refresh)"],
          ["Trading", "Pannello manuale buy/sell con parametri ordine"],
          ["History", "Storico dei trade"],
          ["Backtest / Signal Research / Auto Signal", "UI per backtest e ottimizzazione dei parametri"],
          ["Traders & Servers", "Griglia trader drag&drop, gestione SL/TP, sessione, segnali, pannello Supervisor AI"],
      ],
      widths=[80, 110])

section_title(pdf, "6. Note operative")
bullets(pdf, [
    "Solo Windows per gli agenti MT5 (libreria MetaTrader5).",
    "Configurazione tramite file .env (credenziali MySQL, OpenRouter API key, CORS).",
    "Il supervisor e le analisi AI funzionano anche senza OPENROUTER_API_KEY (fallback a sole regole di sicurezza).",
])

out = r"C:\Users\crist\MT5Pulse\REPORT_MT5PULSE.pdf"
pdf.output(out)
print("OK ->", out)
