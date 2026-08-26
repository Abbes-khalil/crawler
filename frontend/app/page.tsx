"use client";

import { useEffect, useState } from "react";
import type { CrawlCompanyResponse } from "@/types/crawler";
import { CrawlerApiError, crawlCompany, healthCheck } from "@/lib/api/crawler";
import { AppShell } from "@/components/layout/AppShell";
import { CrawlForm } from "@/components/crawler/CrawlForm";
import { CrawlLoading } from "@/components/crawler/CrawlLoading";
import { CrawlSummary } from "@/components/crawler/CrawlSummary";
import { ContactInfo } from "@/components/crawler/ContactInfo";
import { PagesList } from "@/components/crawler/PagesList";
import { CopyForChatGpt } from "@/components/crawler/CopyForChatGpt";
import { RawJsonViewer } from "@/components/crawler/RawJsonViewer";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type UiState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "result"; response: CrawlCompanyResponse }
  | { kind: "transport-error"; error: CrawlerApiError };

export default function Home() {
  const [state, setState] = useState<UiState>({ kind: "idle" });
  const [lastRequest, setLastRequest] = useState<{ website: string; maxPages: number } | null>(
    null
  );
  const [showRawJson, setShowRawJson] = useState(false);
  const [serviceAvailable, setServiceAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    // fetch is only available client-side; reading it during the initial render
    // (instead of here) would produce a server/client hydration mismatch.
    let cancelled = false;
    const maxAttempts = 20; // ~20s: the packaged sidecar needs a moment to bind its port

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

  async function runCrawl(website: string, maxPages: number) {
    setLastRequest({ website, maxPages });
    setState({ kind: "loading" });

    try {
      const response = await crawlCompany({ website, max_pages: maxPages });
      setState({ kind: "result", response });
    } catch (error) {
      setState({
        kind: "transport-error",
        error:
          error instanceof CrawlerApiError ? error : new CrawlerApiError("Erreur inconnue", "network"),
      });
    }
  }

  function handleRetry() {
    if (lastRequest) {
      runCrawl(lastRequest.website, lastRequest.maxPages);
    }
  }

  return (
    <AppShell
      statusSlot={
        serviceAvailable === false ? (
          <span className="text-amber-300">Le robot n&apos;a pas pu démarrer</span>
        ) : serviceAvailable === true ? (
          <span>Service d&apos;analyse en ligne</span>
        ) : (
          <span className="text-text-muted">Démarrage du robot…</span>
        )
      }
    >
      <div className="mx-auto flex max-w-2xl flex-col gap-6">
        <div>
          <h1 className="text-xl font-semibold text-text">Intelligence Web</h1>
          <p className="text-sm text-text-muted">
            Entrez le site web d&apos;une entreprise pour analyser son contenu public.
          </p>
        </div>

        {serviceAvailable === false && (
          <Card className="border-amber-300 bg-amber-50">
            <p className="text-sm text-amber-900">
              Le robot n&apos;a pas pu démarrer. Fermez et rouvrez l&apos;application, ou{" "}
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
          disabled={state.kind === "loading" || serviceAvailable !== true}
          loading={state.kind === "loading"}
        />

        {state.kind === "loading" && <CrawlLoading />}

        {state.kind === "transport-error" && (
          <Card>
            <Badge tone="error">Service d&apos;analyse indisponible</Badge>
            <p className="mt-2 text-sm text-text-muted">
              Impossible de contacter le service d&apos;analyse. Vérifiez qu&apos;il est bien
              lancé et réessayez.
            </p>
          </Card>
        )}

        {state.kind === "result" && (
          <>
            <CrawlSummary response={state.response} onRetry={handleRetry} />
            {(state.response.status === "SUCCESS" || state.response.status === "PARTIAL_SUCCESS") && (
              <>
                <ContactInfo observations={state.response.observations} />
                <PagesList pages={state.response.pages} pageErrors={state.response.page_errors} />
              </>
            )}
            <CopyForChatGpt response={state.response} onViewJson={() => setShowRawJson(true)} />
          </>
        )}
      </div>

      <RawJsonViewer
        response={showRawJson && state.kind === "result" ? state.response : null}
        onClose={() => setShowRawJson(false)}
      />
    </AppShell>
  );
}
