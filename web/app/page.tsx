"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Job } from "@/types/crawler";
import {
  CrawlerApiError,
  cancelJob,
  getJob,
  healthCheck,
  startCrawl,
} from "@/lib/api/crawler";
import { AppShell } from "@/components/layout/AppShell";
import { CrawlForm } from "@/components/crawler/CrawlForm";
import { CrawlProgress } from "@/components/crawler/CrawlProgress";
import { CrawlSummary } from "@/components/crawler/CrawlSummary";
import { ContactInfo } from "@/components/crawler/ContactInfo";
import { PagesList } from "@/components/crawler/PagesList";
import { CopyForChatGpt } from "@/components/crawler/CopyForChatGpt";
import { RawJsonViewer } from "@/components/crawler/RawJsonViewer";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type UiState =
  | { kind: "idle" }
  | { kind: "job"; job: Job }
  | { kind: "transport-error"; error: CrawlerApiError };

const POLL_INTERVAL_MS = 700;
const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export default function Home() {
  const [state, setState] = useState<UiState>({ kind: "idle" });
  const [showRawJson, setShowRawJson] = useState(false);
  const [serviceAvailable, setServiceAvailable] = useState<boolean | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    const maxAttempts = 20; // ~20s: the backend needs a moment to bind its port

    async function pollHealth(attempt: number) {
      const available = await healthCheck();
      if (cancelled) return;
      if (available || attempt >= maxAttempts) {
        setServiceAvailable(available);
        return;
      }
      setTimeout(() => pollHealth(attempt + 1), 1000);
    }

    pollHealth(1);
    return () => {
      cancelled = true;
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const pollJob = useCallback(
    (id: string) => {
      const tick = async () => {
        try {
          const job = await getJob(id);
          setState({ kind: "job", job });
          if (!TERMINAL.has(job.status)) {
            pollRef.current = setTimeout(tick, POLL_INTERVAL_MS);
          }
        } catch (error) {
          setState({
            kind: "transport-error",
            error:
              error instanceof CrawlerApiError
                ? error
                : new CrawlerApiError("Unknown error", "network"),
          });
        }
      };
      pollRef.current = setTimeout(tick, POLL_INTERVAL_MS);
    },
    []
  );

  async function runCrawl(website: string, maxPages: number) {
    stopPolling();
    try {
      const job = await startCrawl({ website, max_pages: maxPages });
      setState({ kind: "job", job });
      pollJob(job.id);
    } catch (error) {
      setState({
        kind: "transport-error",
        error:
          error instanceof CrawlerApiError
            ? error
            : new CrawlerApiError("Unknown error", "network"),
      });
    }
  }

  async function handleCancel() {
    if (state.kind !== "job") return;
    try {
      await cancelJob(state.job.id);
    } catch {
      // The next poll will reflect the real state; nothing to do here.
    }
  }

  function reset() {
    stopPolling();
    setState({ kind: "idle" });
  }

  const job = state.kind === "job" ? state.job : null;
  const running = job != null && !TERMINAL.has(job.status);
  const result = job?.result ?? null;

  return (
    <AppShell
      statusSlot={
        serviceAvailable === false ? (
          <span className="text-amber-300">Le service n&apos;a pas démarré</span>
        ) : serviceAvailable === true ? (
          <span>Service en ligne</span>
        ) : (
          <span className="text-text-muted">Démarrage du service…</span>
        )
      }
    >
      <div className="mx-auto flex max-w-2xl flex-col gap-6">
        <div>
          <h1 className="text-xl font-semibold text-text">Web Intelligence</h1>
          <p className="text-sm text-text-muted">
            Entrez le site web d&apos;une entreprise pour analyser son contenu public.
          </p>
        </div>

        {serviceAvailable === false && (
          <Card className="border-amber-300 bg-amber-50">
            <p className="text-sm text-amber-900">
              Le service local n&apos;a pas pu démarrer. Fermez puis rouvrez
              l&apos;application, ou{" "}
              <button
                type="button"
                className="underline"
                onClick={() => {
                  setServiceAvailable(null);
                  healthCheck().then(setServiceAvailable);
                }}
              >
                réessayez
              </button>
              .
            </p>
          </Card>
        )}

        <CrawlForm
          onSubmit={runCrawl}
          disabled={running || serviceAvailable !== true}
          loading={running}
        />

        {running && job && (
          <CrawlProgress job={job} onCancel={handleCancel} />
        )}

        {state.kind === "transport-error" && (
          <Card>
            <Badge tone="error">Service indisponible</Badge>
            <p className="mt-2 text-sm text-text-muted">
              Impossible de joindre le service local. Vérifiez qu&apos;il est en
              cours d&apos;exécution puis réessayez.
            </p>
          </Card>
        )}

        {job?.status === "cancelled" && (
          <Card>
            <Badge tone="warning">Analyse annulée</Badge>
            <p className="mt-2 text-sm text-text-muted">
              L&apos;analyse a été interrompue avant la fin.{" "}
              <button type="button" className="underline" onClick={reset}>
                Nouvelle analyse
              </button>
            </p>
          </Card>
        )}

        {job?.status === "failed" && (
          <Card>
            <Badge tone="error">Échec de l&apos;analyse</Badge>
            <p className="mt-2 text-sm text-text-muted">
              {job.error ?? "Une erreur inattendue s'est produite."}
            </p>
            <button
              type="button"
              className="mt-2 text-sm underline"
              onClick={() => runCrawl(job.website, job.max_pages)}
            >
              Réessayer
            </button>
          </Card>
        )}

        {job?.status === "completed" && result && (
          <>
            <CrawlSummary
              response={result}
              onRetry={() => runCrawl(job.website, job.max_pages)}
            />
            {(result.status === "SUCCESS" || result.status === "PARTIAL_SUCCESS") && (
              <>
                <ContactInfo observations={result.observations} />
                <PagesList pages={result.pages} pageErrors={result.page_errors} />
              </>
            )}
            <CopyForChatGpt response={result} onViewJson={() => setShowRawJson(true)} />
          </>
        )}
      </div>

      <RawJsonViewer
        response={showRawJson && result ? result : null}
        onClose={() => setShowRawJson(false)}
      />
    </AppShell>
  );
}
