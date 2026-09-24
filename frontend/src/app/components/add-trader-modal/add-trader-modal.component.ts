import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TraderService } from '../../services/trader.service';
import { CreateTraderRequest } from '../../models/trader.models';

@Component({
  selector: 'app-add-trader-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './add-trader-modal.component.html',
  styleUrls: ['./add-trader-modal.component.css']
})
export class AddTraderModalComponent {
  @Output() traderAdded = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  traderForm: CreateTraderRequest = {
    name: '',
    mt5_login: '',
    mt5_password: '',
    mt5_server: ''
  };

  loading = false;
  errorMessage = '';

  constructor(private traderService: TraderService) {}

  async onSubmit() {
    // if (!this.validateForm()) {
    //   return;
    // }

    // this.loading = true;
    // this.errorMessage = '';

    // // const result = await this.traderService.createTrader(this.traderForm);
    // const result = await this.traderService.createTrader(this.traderForm);

    // if (result.success) {
    //   this.traderAdded.emit();
    //   this.resetForm();
    // } else {
    //   this.errorMessage = result.message;
    // }

    // this.loading = false;
  }

  validateForm(): boolean {
    if (!this.traderForm.name.trim()) {
      this.errorMessage = 'Please enter a trader name';
      return false;
    }
    if (!this.traderForm.mt5_login.trim()) {
      this.errorMessage = 'Please enter MT5 login';
      return false;
    }
    if (!this.traderForm.mt5_password.trim()) {
      this.errorMessage = 'Please enter MT5 password';
      return false;
    }
    if (!this.traderForm.mt5_server.trim()) {
      this.errorMessage = 'Please enter MT5 server';
      return false;
    }
    return true;
  }

  resetForm() {
    this.traderForm = {
      name: '',
      mt5_login: '',
      mt5_password: '',
      mt5_server: ''
    };
    this.errorMessage = '';
  }

  onCancel() {
    this.cancel.emit();
    this.resetForm();
  }
}
