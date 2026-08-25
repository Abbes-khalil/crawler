import type { CrawlCompanyRequest, CrawlCompanyResponse } from "@/types/crawler";

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

function resolveBaseUrl(baseUrl?: string): string {
  return baseUrl ?? process.env.NEXT_PUBLIC_CRAWLER_API ?? "http://127.0.0.1:8000";
}

export async function crawlCompany(
  request: CrawlCompanyRequest,
  baseUrl?: string
): Promise<CrawlCompanyResponse> {
  let response: Response;

  try {
    response = await fetch(`${resolveBaseUrl(baseUrl)}/crawl-company`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
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

  return (await response.json()) as CrawlCompanyResponse;
}

export async function healthCheck(baseUrl?: string): Promise<boolean> {
  try {
    const response = await fetch(`${resolveBaseUrl(baseUrl)}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
