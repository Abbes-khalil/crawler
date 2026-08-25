import type { CrawlCompanyResponse, CrawlStatus } from "@/types/crawler";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const STATUS_COPY: Record<CrawlStatus, string> = {
  SUCCESS: "Analysis complete.",
  PARTIAL_SUCCESS: "Analysis completed with some limitations.",
  INVALID_URL: "That doesn't look like a valid website address.",
  DEAD_DOMAIN: "We couldn't reach that website.",
  TIMEOUT: "We couldn't retrieve the website within the allowed time.",
  BLOCKED: "This website blocked our request.",
  ROBOTS_DENIED: "This website's rules don't allow us to analyze it.",
  INSUFFICIENT_CONTENT: "We reached the site but couldn't find readable content.",
  HTTP_ERROR: "The website returned an error.",
  CAPTCHA: "This website requires human verification we can't bypass.",
};

const RETRYABLE_STATUSES: CrawlStatus[] = [
  "PARTIAL_SUCCESS",
  "DEAD_DOMAIN",
  "TIMEOUT",
  "BLOCKED",
  "ROBOTS_DENIED",
  "INSUFFICIENT_CONTENT",
  "HTTP_ERROR",
  "CAPTCHA",
];

function badgeTone(status: CrawlStatus): "success" | "warning" | "error" {
  if (status === "SUCCESS") return "success";
  if (status === "PARTIAL_SUCCESS") return "warning";
  return "error";
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-lg font-semibold text-text">{value}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}

export function CrawlSummary({
  response,
  onRetry,
}: {
  response: CrawlCompanyResponse;
  onRetry: () => void;
}) {
  const emailCount = response.observations.filter((o) => o.field === "email").length;
  const phoneCount = response.observations.filter((o) => o.field === "phone").length;
  const isFailure = response.status !== "SUCCESS" && response.status !== "PARTIAL_SUCCESS";

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge tone={badgeTone(response.status)}>{STATUS_COPY[response.status]}</Badge>
        </div>
        {RETRYABLE_STATUSES.includes(response.status) && (
          <Button variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>

      <p className="mt-2 text-sm text-text-muted">{response.canonical_url}</p>

      {!isFailure && (
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric label="Pages discovered" value={response.pages_discovered} />
          <Metric label="Pages analyzed" value={response.pages_crawled} />
          <Metric label="Emails found" value={emailCount} />
          <Metric label="Phones found" value={phoneCount} />
        </div>
      )}
    </Card>
  );
}
