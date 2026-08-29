"use client";

/**
 * Standalone one-page crawl tool for the hosted (Vercel) deployment.
 *
 * Unlike the main app at "/", this does not use the background-job flow
 * (which needs a long-running server). It calls the synchronous
 * POST /api/crawl-now endpoint and shows a single copy-paste text block.
 * Any "?k=" access token in the URL is forwarded to the API.
 */

import { useState } from "react";

type CrawlNowResponse = {
  text: string;
  data: { status: string; canonical_url: string };
};

const PAGE_CHOICES = [3, 5, 8];

export default function CrawlNowPage() {
  const [website, setWebsite] = useState("");
  const [maxPages, setMaxPages] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function runCrawl(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setCopied(false);

    const search = typeof window !== "undefined" ? window.location.search : "";

    try {
      const res = await fetch(`/api/crawl-now${search}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ website, max_pages: maxPages }),
      });

      if (res.status === 403) {
        setError("Clé d'accès invalide ou absente dans le lien.");
        return;
      }
      if (res.status === 429) {
        setError("Trop de requêtes. Réessayez dans un moment.");
        return;
      }
      if (res.status === 422) {
        setError("Adresse invalide. Entrez un site d'entreprise public (https://…).");
        return;
      }
      if (!res.ok) {
        setError("Le service a renvoyé une erreur. Réessayez.");
        return;
      }

      const body: CrawlNowResponse = await res.json();
      setResult(body.text);
    } catch {
      setError("Impossible de joindre le service. Vérifiez votre connexion.");
    } finally {
      setLoading(false);
    }
  }

  async function copyResult() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Copie impossible. Sélectionnez le texte manuellement.");
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <header>
        <h1 className="text-xl font-semibold">Analyse de site web</h1>
        <p className="text-sm text-text-muted">
          Entrez le site d&apos;une entreprise. Le résultat est un texte prêt à
          coller dans votre agent ChatGPT.
        </p>
      </header>

      <form onSubmit={runCrawl} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          <span>Site web de l&apos;entreprise</span>
          <input
            type="text"
            required
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="exemple.com"
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            className="rounded border border-border bg-surface px-3 py-2 text-base outline-none focus:border-accent"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span>Pages à analyser</span>
          <select
            value={maxPages}
            onChange={(e) => setMaxPages(Number(e.target.value))}
            className="w-32 rounded border border-border bg-surface px-3 py-2 text-base outline-none focus:border-accent"
          >
            {PAGE_CHOICES.map((n) => (
              <option key={n} value={n}>
                {n} pages
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={loading || website.trim() === ""}
          className="rounded bg-accent px-4 py-2 font-medium text-accent-foreground disabled:opacity-50"
        >
          {loading ? "Analyse en cours… (jusqu'à 1 min)" : "Analyser"}
        </button>
      </form>

      {error && (
        <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}

      {result && (
        <section className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Résultat</h2>
            <button
              type="button"
              onClick={copyResult}
              className="rounded border border-border px-3 py-1 text-sm hover:border-accent"
            >
              {copied ? "Copié ✓" : "Copier"}
            </button>
          </div>
          <textarea
            readOnly
            value={result}
            rows={20}
            className="w-full rounded border border-border bg-surface p-3 font-mono text-xs"
          />
        </section>
      )}
    </main>
  );
}
