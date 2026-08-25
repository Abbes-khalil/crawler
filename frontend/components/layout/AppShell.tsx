import type { ReactNode } from "react";

export function AppShell({
  children,
  statusSlot,
}: {
  children: ReactNode;
  statusSlot?: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-border bg-navy px-6 py-3">
        <span className="text-sm font-semibold tracking-wide text-white">AS Biz Dev</span>
        <div className="text-xs text-white/70">{statusSlot}</div>
      </header>
      <main className="flex-1 px-6 py-6">{children}</main>
    </div>
  );
}
