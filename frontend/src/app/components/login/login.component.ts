import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username = '';
  password = '';
  loading = false;
  errorMessage = '';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/user-dashboard']);
    }
  }

  async onSubmit() {
          
    if (!this.username || !this.password) {
      this.errorMessage = 'Please enter username and password';
      return;
    }

    
    this.loading = true;
    this.errorMessage = '';

    const result = await this.authService.login(this.username, this.password);
    

    if (result.success) {
      this.router.navigate(['/user-dashboard']);
    } else {
      
      this.errorMessage = result.message;
      this.loading = false;
    }
  }
}
