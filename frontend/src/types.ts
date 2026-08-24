export interface Forecast {
  condition_id: string;
  question: string;
  slug: string;
  asset: string;
  target_price: number;
  deadline: string;
  event_type: "barrier" | "terminal";
  direction: "up" | "down";
  spot_price: number;
  sigma: number;
  model_probability: number;
  market_implied_probability: number | null;
  edge: number | null;
  updated_at: string;
}

export interface ApiHealth {
  api_name: string;
  status: "up" | "down";
  latency_ms: number | null;
  last_checked_at: string;
  last_success_at: string | null;
  last_error: string | null;
}

export type EventLevel = "info" | "warning" | "error";

export interface AppEvent {
  id: number;
  ts: string;
  level: EventLevel;
  api: string | null;
  step: string;
  message: string;
  detail: Record<string, unknown> | null;
}

export interface CalibrationBucket {
  lower: number;
  upper: number;
  count: number;
  mean_forecast: number | null;
  observed_frequency: number | null;
}

export interface Calibration {
  resolved_markets: number;
  compared_markets: number;
  model_brier: number | null;
  model_brier_compared: number | null;
  market_brier_compared: number | null;
  skill_vs_market: number | null;
  base_rate: number | null;
  buckets: CalibrationBucket[];
}

export interface NewsItem {
  url: string;
  title: string;
  source: string;
  summary: string | null;
  published_at: string | null;
  fetched_at: string;
}
