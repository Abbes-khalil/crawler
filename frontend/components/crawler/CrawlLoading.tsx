"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Connecting to website",
  "Discovering relevant pages",
  "Extracting business content",
  "Preparing results",
];

const STEP_INTERVAL_MS = 1400;

export function CrawlLoading() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((step) => (step < STEPS.length - 1 ? step + 1 : step));
    }, STEP_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5"
    >
      <p className="text-sm font-medium text-text">Analyzing website...</p>
      <ul className="flex flex-col gap-2">
        {STEPS.map((label, index) => {
          const state =
            index < currentStep ? "done" : index === currentStep ? "active" : "pending";

          return (
            <li key={label} className="flex items-center gap-2 text-sm">
              <span
                aria-hidden="true"
                className={
                  state === "done"
                    ? "text-emerald-600"
                    : state === "active"
                      ? "text-accent"
                      : "text-text-muted"
                }
              >
                {state === "done" ? "✓" : state === "active" ? "●" : "○"}
              </span>
              <span className={state === "pending" ? "text-text-muted" : "text-text"}>
                {label}
                {state === "active" && <span className="sr-only"> (in progress)</span>}
                {state === "done" && <span className="sr-only"> (done)</span>}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
