"use client";

import type { Job } from "@/types/crawler";
import { Button } from "@/components/ui/Button";

const PHASE_LABELS: Record<string, string> = {
  queued: "En file d'attente",
  discovering: "Découverte des pages pertinentes",
  crawling: "Analyse des pages",
  done: "Préparation des résultats",
  cancelled: "Annulation…",
  error: "Erreur",
};

export function CrawlProgress({
  job,
  onCancel,
}: {
  job: Job;
  onCancel: () => void;
}) {
  const { phase, pages_done, pages_total } = job.progress;
  const label = PHASE_LABELS[phase] ?? phase;
  const hasCount = pages_total > 0;
  const pct = hasCount
    ? Math.min(100, Math.round((pages_done / pages_total) * 100))
    : null;
  const starting = job.status === "starting";

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5"
    >
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-medium text-text">
          {starting ? "Démarrage de l'analyse…" : label}
        </p>
        <Button variant="secondary" onClick={onCancel} className="px-3 py-1 text-xs">
          Annuler
        </Button>
      </div>

      <div
        className="h-2 w-full overflow-hidden rounded-full bg-surface-muted"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct ?? undefined}
      >
        <div
          className={`h-full bg-accent transition-all duration-300 ${
            pct == null ? "w-1/3 animate-pulse" : ""
          }`}
          style={pct == null ? undefined : { width: `${pct}%` }}
        />
      </div>

      {hasCount && (
        <p className="text-xs text-text-muted">
          {pages_done} / {pages_total} pages
        </p>
      )}
    </div>
  );
}
