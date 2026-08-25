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
          <h2 className="text-sm font-semibold text-text">JSON for ChatGPT Agent</h2>
          <p className="text-xs text-text-muted">
            Copy this and paste it into the AS Biz Dev intelligence agent.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onViewJson}>
            View JSON
          </Button>
          <Button onClick={handleCopy}>{copied ? "Copied!" : "Copy for ChatGPT"}</Button>
        </div>
      </div>
    </Card>
  );
}
