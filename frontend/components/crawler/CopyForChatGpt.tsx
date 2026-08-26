"use client";

import { useState } from "react";
import type { CrawlCompanyResponse } from "@/types/crawler";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function CopyForChatGpt({
  response,
  onViewJson,
}: {
  response: CrawlCompanyResponse;
  onViewJson: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(response, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable — "View JSON" still lets the user select and copy manually.
    }
  }

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-text">JSON pour l&apos;agent ChatGPT</h2>
          <p className="text-xs text-text-muted">
            Copiez ceci et collez-le dans l&apos;agent d&apos;intelligence AS Biz Dev.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onViewJson}>
            Voir le JSON
          </Button>
          <Button onClick={handleCopy}>{copied ? "Copié !" : "Copier pour ChatGPT"}</Button>
        </div>
      </div>
    </Card>
  );
}
