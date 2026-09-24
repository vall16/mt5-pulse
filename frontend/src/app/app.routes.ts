import { Routes } from '@angular/router';
import { HistoryComponent } from './components/history/history.component';
import { LoginComponent } from './components/login/login.component';
import { UserDashboardComponent } from './components/user-dashboard/user-dashboard.component';
import { BacktestComponent } from './components/backtest/backtest.component';
import { SignalResearchComponent } from './components/signal-research/signal-research.component';
import { AutoSignalComponent } from './components/auto-signal/auto-signal.component';
import { StrategiesGuideComponent } from './components/strategies-guide/strategies-guide.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  
  { path: '', component: LoginComponent },     
  // { path: '', component: UserDashboardComponent },       
  { path: 'history', component: HistoryComponent, canActivate: [authGuard] },
  { path: 'user-dashboard', component: UserDashboardComponent, canActivate: [authGuard] },
  { path: 'backtest', component: BacktestComponent, canActivate: [authGuard] },
  { path: 'signal-research', component: SignalResearchComponent, canActivate: [authGuard] },
  { path: 'signal-research-auto', component: AutoSignalComponent, canActivate: [authGuard] },
  { path: 'strategies-guide', component: StrategiesGuideComponent, canActivate: [authGuard] },
  //  { path: 'user-dashboard', component: UserDashboardComponent },
  
];

