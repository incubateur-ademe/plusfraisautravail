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

export interface SourceMeta {
  name: string;
  last_refresh: string | null;
  healthy: boolean;
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

  async getSources(): Promise<SourceMeta[]> {
    return this.request<SourceMeta[]>('/sources');
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
