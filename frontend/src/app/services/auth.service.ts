import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

interface User {
  id: string;
  username: string;
}

interface LoginResponse {
  success: boolean;
  user?: User;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser: Observable<User | null>;

  // private apiUrl = 'http://127.0.0.1:8080'; // URL del backend FastAPI
  private apiUrl = environment.apiUrl; // URL del backend FastAPI

  constructor(private http: HttpClient, private router: Router) {
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(
      storedUser ? JSON.parse(storedUser) : null
    );
    this.currentUser = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  async login(username: string, password: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.http
        .post<LoginResponse>(`${this.apiUrl}/db/login`, { username, password })
        .toPromise();

      if (response && response.success && response.user) {
        localStorage.setItem('currentUser', JSON.stringify(response.user));
        this.currentUserSubject.next(response.user);
        return { success: true, message: 'Login successful' };
      }

      return { success: false, message: response?.message || 'Invalid credentials' };
    } catch (err: any) {
      console.error('Login error:', err);
      return { success: false, message: err.error?.message || 'Login failed' };
    }
  }

  logout() {
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return this.currentUserValue !== null;
  }
}
