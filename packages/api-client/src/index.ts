export type Severity = 'vert' | 'jaune' | 'orange' | 'rouge';

export interface PhenomenonAlert {
  id: string;
  name: string;
  day1: Severity;
  day2: Severity;
}

export interface DepartmentMeteoAlert {
  code: string;
  name: string;
  phenomena: PhenomenonAlert[];
}

export interface MeteoSnapshot {
  active: boolean;
  departments: DepartmentMeteoAlert[];
  fetched_at: string;
  source: string;
}

export type ElectricityLevel = 'vert' | 'orange' | 'rouge';

export interface ElectricityDayForecast {
  date: string;
  level: ElectricityLevel;
  code: number;
  message: string | null;
}

export interface ElectricitySnapshot {
  days: ElectricityDayForecast[];
  currently_strained: boolean;
  upcoming_strain: boolean;
  fetched_at: string;
  source: string;
}

export interface SourceMeta {
  name: string;
  last_refresh: string | null;
  healthy: boolean;
}

export type ClimadiagYear = 2030 | 2050 | 2100;

export interface ClimadiagTemperatureProjection {
  min: number | null;
  median: number | null;
  max: number | null;
}

export interface ClimadiagLieu {
  id: number;
  nom: string;
  code_postal: string;
  type_lieu: 'commune' | 'epci';
  seuil_jours_tres_chauds: number | null;
  seuil_nuits_chaudes: number | null;
  jours_tres_chauds_ref: number | null;
  nuits_chaudes_ref: number | null;
  jours_vdc_ref: number | null;
  jours_tres_chauds_prevision: Record<ClimadiagYear, ClimadiagTemperatureProjection>;
  nuits_chaudes_prevision: Record<ClimadiagYear, ClimadiagTemperatureProjection>;
  jours_vdc_prevision: Record<ClimadiagYear, ClimadiagTemperatureProjection> | null;
}

export interface ApiClientOptions {
  baseUrl: string;
  fetch?: typeof fetch;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
  }

  async getMeteoAlerts(): Promise<MeteoSnapshot> {
    return this.request<MeteoSnapshot>('/alerts/meteo');
  }

  async getElectricityAlerts(): Promise<ElectricitySnapshot> {
    return this.request<ElectricitySnapshot>('/alerts/electricity');
  }

  async getSources(): Promise<SourceMeta[]> {
    return this.request<SourceMeta[]>('/sources');
  }

  async searchClimadiag(
    search: string,
    options?: { limit?: number; communesOnly?: boolean },
  ): Promise<ClimadiagLieu[]> {
    const params = new URLSearchParams({ search });
    if (options?.limit != null) params.set('limit', String(options.limit));
    if (options?.communesOnly) params.set('communes_only', 'true');
    return this.request<ClimadiagLieu[]>(`/climadiag/search?${params}`);
  }

  private async request<T>(path: string): Promise<T> {
    const res = await this.fetchImpl(`${this.baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(res.status, `Request to ${path} failed: ${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
  }
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export const isVigilanceActive = (severity: Severity): boolean => severity !== 'vert';
