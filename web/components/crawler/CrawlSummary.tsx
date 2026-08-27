import type { CrawlCompanyResponse, CrawlStatus } from "@/types/crawler";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const STATUS_COPY: Record<CrawlStatus, string> = {
  SUCCESS: "Analyse terminée.",
  PARTIAL_SUCCESS: "Analyse terminée avec certaines limites.",
  INVALID_URL: "Cette adresse ne semble pas être un site web valide.",
  DEAD_DOMAIN: "Impossible d'accéder à ce site web.",
  TIMEOUT: "Le site n'a pas répondu dans le délai imparti.",
  BLOCKED: "Ce site web a bloqué notre requête.",
  ROBOTS_DENIED: "Les règles de ce site ne nous autorisent pas à l'analyser.",
  INSUFFICIENT_CONTENT: "Le site a été atteint mais aucun contenu lisible n'a été trouvé.",
  HTTP_ERROR: "Le site web a retourné une erreur.",
  CAPTCHA: "Ce site nécessite une vérification humaine que nous ne pouvons pas contourner.",
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
            Réessayer
          </Button>
        )}
      </div>

      <p className="mt-2 text-sm text-text-muted">{response.canonical_url}</p>

      {!isFailure && (
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric label="Pages découvertes" value={response.pages_discovered} />
          <Metric label="Pages analysées" value={response.pages_crawled} />
          <Metric label="E-mails trouvés" value={emailCount} />
          <Metric label="Téléphones trouvés" value={phoneCount} />
        </div>
      )}
    </Card>
  );
}
