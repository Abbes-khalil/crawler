import type { CrawlCompanyRequest, Job, ResultSummary } from "@/types/crawler";

export class CrawlerApiError extends Error {
  kind: "network" | "http" | "validation";
  status?: number;
  detail?: unknown;

  constructor(
    message: string,
    kind: "network" | "http" | "validation",
    status?: number,
    detail?: unknown
  ) {
    super(message);
    this.name = "CrawlerApiError";
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

// Empty base = same origin: in production the local backend serves this app,
// so requests go to /api/* on the same host and port. The dev server sets
// NEXT_PUBLIC_CRAWLER_API to reach a separately launched backend.
function base(): string {
  return process.env.NEXT_PUBLIC_CRAWLER_API ?? "";
}

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${base()}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new CrawlerApiError("Could not reach the crawler service.", "network");
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => undefined);

    if (response.status === 422) {
      throw new CrawlerApiError(
        "The crawler service rejected this request.",
        "validation",
        response.status,
        detail
      );
    }

    throw new CrawlerApiError(
      "The crawler service returned an error.",
      "http",
      response.status,
      detail
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function startCrawl(body: CrawlCompanyRequest): Promise<Job> {
  return request<Job>("/api/crawl", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getJob(id: string): Promise<Job> {
  return request<Job>(`/api/jobs/${encodeURIComponent(id)}`);
}

export function cancelJob(id: string): Promise<unknown> {
  return request<unknown>(`/api/jobs/${encodeURIComponent(id)}/cancel`, {
    method: "POST",
  });
}

export function listResults(): Promise<ResultSummary[]> {
  return request<ResultSummary[]>("/api/results");
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${base()}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}
