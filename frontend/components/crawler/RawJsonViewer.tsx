"use client";

import { useState } from "react";
import type { CrawlCompanyResponse } from "@/types/crawler";
import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";

export function RawJsonViewer({
  response,
  onClose,
}: {
  response: CrawlCompanyResponse | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!response) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(response, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable — the JSON is still visible to select manually.
    }
  }

  return (
    <Drawer open={response !== null} onClose={onClose} title="Raw JSON">
      {response && (
        <div className="flex flex-col gap-3">
          <Button variant="secondary" onClick={handleCopy} className="w-fit">
            {copied ? "Copied" : "Copy JSON"}
          </Button>
          <pre className="overflow-x-auto rounded-md bg-navy p-3 font-mono text-xs text-white">
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}
    </Drawer>
  );
}
