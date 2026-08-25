import type {
  CrawlCompanyRequest,
  CrawlCompanyResponse,
  CrawledPage,
  Observation,
  PageError,
} from "@/types/crawler";

function page(overrides: Partial<CrawledPage> & { url: string }): CrawledPage {
  return {
    title: null,
    meta_description: null,
    language: "en",
    text: "",
    status_code: 200,
    crawl_method: "http",
    content_hash: "mock-hash",
    ...overrides,
  };
}

function observation(
  overrides: Partial<Observation> & { field: string; raw_value: string; source_url: string }
): Observation {
  return {
    normalized_value: overrides.raw_value,
    source_type: "visible_text",
    observed_at: "2026-08-21T18:43:09.483881Z",
    confidence: 0.9,
    ...overrides,
  };
}

const HOMEPAGE_TEXT =
  "AS Biz Dev supports industrial manufacturers expanding into Africa and the Middle East, " +
  "combining local market access with structured commercial development programs.";

const LONG_TEXT = Array.from({ length: 40 })
  .map(
    (_, i) =>
      `Paragraph ${i + 1}. This site publishes a long-form page describing its services, ` +
      "history, and regional footprint in detail, used here to validate that the page detail " +
      "drawer scrolls correctly instead of overflowing the layout."
  )
  .join("\n\n");

function successResponse(canonicalUrl: string): CrawlCompanyResponse {
  return {
    status: "SUCCESS",
    canonical_url: canonicalUrl,
    pages_discovered: 17,
    pages_selected: 5,
    pages_crawled: 5,
    pages_failed: 0,
    pages: [
      page({ url: canonicalUrl, title: "Home", text: HOMEPAGE_TEXT }),
      page({ url: `${canonicalUrl}/about`, title: "About us", text: HOMEPAGE_TEXT }),
      page({ url: `${canonicalUrl}/contact`, title: "Contact", text: HOMEPAGE_TEXT }),
      page({ url: `${canonicalUrl}/products`, title: "Products", text: HOMEPAGE_TEXT }),
      page({ url: `${canonicalUrl}/careers`, title: "Careers", text: HOMEPAGE_TEXT }),
    ],
    page_errors: [],
    observations: [
      observation({
        field: "email",
        raw_value: "contact@asbizdev.com",
        source_url: `${canonicalUrl}/contact`,
        source_type: "mailto_link",
        confidence: 1.0,
      }),
      observation({
        field: "phone",
        raw_value: "07 38 69 63",
        normalized_value: null,
        source_url: `${canonicalUrl}/contact`,
        source_type: "tel_link",
        confidence: 0.9,
      }),
      observation({
        field: "linkedin_url",
        raw_value: "https://www.linkedin.com/company/asbizdev",
        source_url: canonicalUrl,
        source_type: "social_link",
        confidence: 1.0,
      }),
      observation({
        field: "organization_name",
        raw_value: "AS Biz Dev",
        source_url: canonicalUrl,
        source_type: "json_ld",
        confidence: 0.95,
      }),
    ],
    metrics: { duration_ms: 4200, http_pages: 5, playwright_pages: 0 },
  };
}

function emptyResponse(
  canonicalUrl: string,
  status: CrawlCompanyResponse["status"]
): CrawlCompanyResponse {
  return {
    status,
    canonical_url: canonicalUrl,
    pages_discovered: 0,
    pages_selected: 0,
    pages_crawled: 0,
    pages_failed: 0,
    pages: [],
    page_errors: [],
    observations: [],
    metrics: { duration_ms: 3100, http_pages: 0, playwright_pages: 0 },
  };
}

const SCENARIOS: Record<string, (canonicalUrl: string) => CrawlCompanyResponse> = {
  "success.test": successResponse,
  "empty.test": (canonicalUrl) => ({ ...successResponse(canonicalUrl), observations: [] }),
  "longtext.test": (canonicalUrl) => ({
    ...successResponse(canonicalUrl),
    pages: [page({ url: canonicalUrl, title: "Home", text: LONG_TEXT })],
    pages_selected: 1,
    pages_crawled: 1,
  }),
  "partial.test": (canonicalUrl) => {
    const base = successResponse(canonicalUrl);
    const pageErrors: PageError[] = [
      { url: `${canonicalUrl}/careers`, status: "TIMEOUT", error: "request timed out after 15s" },
    ];
    return {
      ...base,
      status: "PARTIAL_SUCCESS",
      pages: base.pages.slice(0, 4),
      pages_crawled: 4,
      pages_failed: 1,
      page_errors: pageErrors,
    };
  },
  "timeout.test": (canonicalUrl) => emptyResponse(canonicalUrl, "TIMEOUT"),
  "dead.test": (canonicalUrl) => emptyResponse(canonicalUrl, "DEAD_DOMAIN"),
  "blocked.test": (canonicalUrl) => emptyResponse(canonicalUrl, "BLOCKED"),
  "robots.test": (canonicalUrl) => emptyResponse(canonicalUrl, "ROBOTS_DENIED"),
  "captcha.test": (canonicalUrl) => emptyResponse(canonicalUrl, "CAPTCHA"),
  "insufficient.test": (canonicalUrl) => emptyResponse(canonicalUrl, "INSUFFICIENT_CONTENT"),
  "httperror.test": (canonicalUrl) => emptyResponse(canonicalUrl, "HTTP_ERROR"),
};

function extractHost(website: string): string {
  try {
    return new URL(website.includes("://") ? website : `https://${website}`).hostname;
  } catch {
    return website;
  }
}

export async function mockCrawlCompany(
  request: CrawlCompanyRequest
): Promise<CrawlCompanyResponse> {
  await new Promise((resolve) => setTimeout(resolve, 400));

  const host = extractHost(request.website);
  const canonicalUrl = request.website.includes("://")
    ? request.website
    : `https://${request.website}`;

  const scenario = SCENARIOS[host] ?? successResponse;

  return scenario(canonicalUrl);
}
