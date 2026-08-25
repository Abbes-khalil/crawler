import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "error";

const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-surface-muted text-text-muted border-border",
  success: "bg-emerald-50 text-emerald-800 border-emerald-200",
  warning: "bg-amber-50 text-amber-800 border-amber-200",
  error: "bg-red-50 text-red-800 border-red-200",
};

const TONE_ICON: Record<Tone, string> = {
  neutral: "●",
  success: "✓",
  warning: "▲",
  error: "✕",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      <span aria-hidden="true">{TONE_ICON[tone]}</span>
      {children}
    </span>
  );
}
