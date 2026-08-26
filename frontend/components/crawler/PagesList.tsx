"use client";

import { useState } from "react";
import type { CrawledPage, PageError } from "@/types/crawler";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageDetailDrawer } from "@/components/crawler/PageDetailDrawer";

function excerpt(text: string, length = 160): string {
  const trimmed = text.trim();
  return trimmed.length > length ? `${trimmed.slice(0, length)}…` : trimmed;
}

export function PagesList({
  pages,
  pageErrors,
}: {
  pages: CrawledPage[];
  pageErrors: PageError[];
}) {
  const [selectedPage, setSelectedPage] = useState<CrawledPage | null>(null);

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-text">Pages analysées</h2>
      <div className="flex flex-col gap-2">
        {pages.map((page) => (
          <Card key={page.url}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-text">{page.title ?? page.url}</p>
                <p className="truncate text-xs text-text-muted">{page.url}</p>
              </div>
              <Badge tone={page.status_code && page.status_code < 400 ? "success" : "error"}>
                {page.status_code ?? "—"}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-text-muted">{excerpt(page.text)}</p>
            <Button variant="ghost" className="mt-2 px-0" onClick={() => setSelectedPage(page)}>
              Voir le contenu extrait
            </Button>
          </Card>
        ))}
      </div>

      {pageErrors.length > 0 && (
        <details className="rounded-lg border border-border bg-surface-muted p-3">
          <summary className="cursor-pointer text-sm font-medium text-text-muted">
            {pageErrors.length} page{pageErrors.length > 1 ? "s" : ""} n&apos;
            {pageErrors.length > 1 ? "ont" : "a"} pas pu être analysée
            {pageErrors.length > 1 ? "s" : ""}
          </summary>
          <ul className="mt-2 flex flex-col gap-1">
            {pageErrors.map((error) => (
              <li key={error.url} className="text-xs text-text-muted">
                {error.url} — {error.status}
              </li>
            ))}
          </ul>
        </details>
      )}

      <PageDetailDrawer page={selectedPage} onClose={() => setSelectedPage(null)} />
    </div>
  );
}
