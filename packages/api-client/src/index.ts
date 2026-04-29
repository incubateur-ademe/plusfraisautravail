export type Severity = 'vert' | 'jaune' | 'orange' | 'rouge';

export interface DepartmentAlert {
  code: string;
  day1: Severity;
  day2: Severity;
}

export interface HeatwaveSnapshot {
  phenomenon: string;
  phenomenon_id: string;
  departments: DepartmentAlert[];
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

  async getHeatwave(): Promise<HeatwaveSnapshot> {
    return this.request<HeatwaveSnapshot>('/alerts/heatwave');
  }

  async getHeatwaveForDepartment(dept: string): Promise<HeatwaveSnapshot> {
    return this.request<HeatwaveSnapshot>(`/alerts/heatwave/${encodeURIComponent(dept)}`);
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

export const isVigilanceActive = (severity: Severity): boolean =>
  severity === 'orange' || severity === 'rouge';
