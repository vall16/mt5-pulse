import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Server } from '../../models/server.model';
import { TraderService } from '../../services/trader.service';

@Component({
  selector: 'app-servers-list',
  standalone: true,
  imports: [CommonModule, FormsModule, DragDropModule],
  templateUrl: './servers-list.component.html',
  styleUrls: ['./servers-list.component.css']
})
export class ServersListComponent implements OnInit {

  servers: Server[] = [];
  loading = true;
  error: string | null = null;

  showAddForm = false;

  testingIndex: number | null = null;
  startingIndex: number | null = null;
  editingIndex: number | null = null;

  backupServer: Server | null = null;

  newServer: Partial<Server> = {
    server: '',
    server_alias: '',
    platform: '',
    user: '',
    pwd: '',
    ip: '',
    path: '',
    port: 0,
    is_active: true
  };

  constructor(private traderService: TraderService) {}

  ngOnInit(): void {
    this.loadServers();
  }

  // ---------------- LOAD ----------------
  loadServers(): void {
    this.loading = true;
    this.traderService.getAllServers().subscribe({
      next: data => {
        this.servers = data;
        this.loading = false;
      },
      error: err => {
        this.error = err.message || 'Failed to load servers';
        this.loading = false;
      }
    });
  }

  // ---------------- ADD ----------------
  toggleAddForm(): void {
    this.showAddForm = !this.showAddForm;
  }

  addServer(): void {
    this.traderService.insertServer(this.newServer).subscribe({
      next: () => {
        this.toggleAddForm();
        this.newServer = {
          server: '',
          server_alias: '',
          platform: '',
          user: '',
          pwd: '',
          ip: '',
          path: '',
          port: 0,
          is_active: true
        };
        this.loadServers();
      },
      error: err => alert(err.message)
    });
  }

  // ---------------- DELETE ----------------
  deleteServer(server: Server): void {
    if (!confirm(`Eliminare il server "${server.server}"?`)) return;

    this.traderService.deleteServer(server.id!).subscribe({
      next: () => this.loadServers(),
      error: err => alert(err.message)
    });
  }

  // ---------------- TEST ----------------
  checkServer(index: number): void {
    const server = this.servers[index];
    this.testingIndex = index;

    this.traderService.checkServer(server).subscribe({
      next: res => {
        this.testingIndex = null;
        this.servers[index].runtimeStatus = res.status === 'ok' ? 'online' : 'offline';
      },
      error: () => {
        this.testingIndex = null;
        this.servers[index].runtimeStatus = 'offline';
      }
    });
  }

  // ---------------- START ----------------
  startServer(server: Server, index: number): void {
    this.startingIndex = index;

    this.traderService.startServer(server).subscribe({
      next: () => this.startingIndex = null,
      error: () => this.startingIndex = null
    });
  }

  // ---------------- REORDER ----------------
  onDrop(event: CdkDragDrop<Server[]>): void {
    moveItemInArray(this.servers, event.previousIndex, event.currentIndex);

    this.traderService.reorderServers(this.servers.map(s => s.id!)).subscribe({
      error: err => {
        alert('Errore riordino: ' + (err.message || err));
        this.loadServers();
      }
    });
  }

  // ---------------- EDIT ----------------
  startEdit(index: number): void {
    this.editingIndex = index;
    this.backupServer = JSON.parse(JSON.stringify(this.servers[index]));
  }

  cancelEdit(): void {
    if (this.editingIndex === null || !this.backupServer) return;

    this.servers[this.editingIndex] =
      JSON.parse(JSON.stringify(this.backupServer));

    this.editingIndex = null;
    this.backupServer = null;
  }

  saveEdit(server: Server): void {
    this.traderService.updateServer(server).subscribe({
      next: () => {
        this.editingIndex = null;
        this.backupServer = null;
      },
      error: err => {
        alert('Errore salvataggio: ' + err.message);
        this.cancelEdit();
      }
    });
  }
}
