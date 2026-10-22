import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { ConsumptionPoint, PeakPrediction, Recommendation } from './models';

/** Données énergétiques. Le jeton est ajouté automatiquement par authInterceptor. */
@Injectable({ providedIn: 'root' })
export class EnergyService {
  private readonly http = inject(HttpClient);

  getPredictions(): Observable<PeakPrediction[]> {
    return this.http.get<PeakPrediction[]>(`${API_URL}/api/predictions`);
  }

  getHistory(days = 7): Observable<ConsumptionPoint[]> {
    return this.http.get<ConsumptionPoint[]>(`${API_URL}/api/history`, { params: { days } });
  }

  getRecommendations(): Observable<Recommendation[]> {
    return this.http.get<Recommendation[]>(`${API_URL}/api/recommendations`);
  }
}
