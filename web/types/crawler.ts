export type CrawlStatus =
  | "SUCCESS"
  | "PARTIAL_SUCCESS"
  | "INVALID_URL"
  | "DEAD_DOMAIN"
  | "TIMEOUT"
  | "BLOCKED"
  | "ROBOTS_DENIED"
  | "CAPTCHA"
  | "INSUFFICIENT_CONTENT"
  | "HTTP_ERROR";

export interface CrawledPage {
  url: string;
  title: string | null;
  meta_description: string | null;
  language: string | null;
  text: string;
  status_code: number | null;
  crawl_method: string;
  content_hash: string;
}

export interface PageError {
  url: string;
  status: string;
  error: string;
}

export interface Observation {
  field: string;
  raw_value: string;
  normalized_value: string | null;
  source_url: string;
  source_type: string;
  observed_at: string;
  confidence: number;
}

export interface CrawlMetrics {
  duration_ms: number;
  http_pages: number;
  playwright_pages: number;
}

export interface CrawlCompanyResponse {
  status: CrawlStatus;
  canonical_url: string;
  pages_discovered: number;
  pages_selected: number;
  pages_crawled: number;
  pages_failed: number;
  pages: CrawledPage[];
  page_errors: PageError[];
  observations: Observation[];
  metrics: CrawlMetrics;
}

export interface CrawlCompanyRequest {
  website: string;
  max_pages?: number;
}

export type JobStatus =
  | "starting"
  | "crawling"
  | "completed"
  | "failed"
  | "cancelled";

export interface JobProgress {
  phase: string;
  pages_done: number;
  pages_total: number;
}

export interface Job {
  id: string;
  website: string;
  max_pages: number;
  status: JobStatus;
  progress: JobProgress;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  result?: CrawlCompanyResponse | null;
}

export interface ResultSummary {
  id: number;
  canonical_url: string;
  crawled_at: string | null;
  pages_count: number;
  observations_count: number;
}
