import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { forkJoin } from 'rxjs';
import { AuthService } from '../../core/auth.service';
import { EnergyService } from '../../core/energy.service';
import { ConsumptionPoint, PeakPrediction, Recommendation, User } from '../../core/models';

/** Page de test du lien front ↔ back : appelle toutes les routes protégées. */
@Component({
  selector: 'app-dashboard',
  imports: [DatePipe, DecimalPipe, PercentPipe],
  templateUrl: './dashboard.html',
})
export class Dashboard implements OnInit {
  protected readonly auth = inject(AuthService);
  private readonly energy = inject(EnergyService);

  protected readonly user = signal<User | null>(null);
  protected readonly predictions = signal<PeakPrediction[]>([]);
  protected readonly history = signal<ConsumptionPoint[]>([]);
  protected readonly recommendations = signal<Recommendation[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    // forkJoin lance les 4 requêtes en parallèle et attend qu'elles aient toutes répondu
    forkJoin({
      user: this.auth.me(),
      predictions: this.energy.getPredictions(),
      history: this.energy.getHistory(1),
      recommendations: this.energy.getRecommendations(),
    }).subscribe({
      next: (data) => {
        this.user.set(data.user);
        this.predictions.set(data.predictions);
        this.history.set(data.history);
        this.recommendations.set(data.recommendations);
        this.loading.set(false);
      },
      error: () => {
        // Un 401 est déjà géré par l'intercepteur (déconnexion automatique)
        this.error.set("Impossible de charger les données depuis l'API.");
        this.loading.set(false);
      },
    });
  }
}
