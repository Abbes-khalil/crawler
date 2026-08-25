"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

interface CrawlFormProps {
  onSubmit: (website: string, maxPages: number) => void;
  disabled: boolean;
  loading?: boolean;
}

export function CrawlForm({ onSubmit, disabled, loading = disabled }: CrawlFormProps) {
  const [website, setWebsite] = useState("");
  const [maxPages, setMaxPages] = useState(5);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | undefined>();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = website.trim();
    if (!trimmed) {
      setError("Enter a website address to analyze.");
      return;
    }

    setError(undefined);
    onSubmit(trimmed, maxPages);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        label="Website URL"
        placeholder="https://company.com"
        value={website}
        onChange={(e) => setWebsite(e.target.value)}
        error={error}
        disabled={disabled}
      />

      <button
        type="button"
        onClick={() => setShowAdvanced((v) => !v)}
        className="w-fit text-xs font-medium text-text-muted hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
        aria-expanded={showAdvanced}
      >
        {showAdvanced ? "Hide advanced options" : "Advanced options"}
      </button>

      {showAdvanced && (
        <Input
          label="Max pages"
          type="number"
          min={1}
          max={20}
          value={maxPages}
          onChange={(e) => setMaxPages(Number(e.target.value) || 1)}
          hint="How many pages to crawl (1–20). Default is 5."
          disabled={disabled}
        />
      )}

      <Button type="submit" disabled={disabled} loading={loading} className="w-fit">
        {loading ? "Analyzing..." : "Analyze website"}
      </Button>
    </form>
  );
}
