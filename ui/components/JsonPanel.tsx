"use client";

import { useState } from "react";

export default function JsonPanel({
  title,
  data,
  defaultOpen = false,
}: {
  title: string;
  data: unknown;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-[color:var(--sumi)]/20 rounded p-4 bg-white">
      <div className="flex items-center justify-between">
        <div className="text-[12px] uppercase tracking-wide text-[color:var(--sumi)]/70">
          {title}
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="text-[12px] px-3 py-1 border border-[color:var(--sumi)]/30 rounded"
        >
          {open ? "Collapse" : "Expand"}
        </button>
      </div>
      {open ? (
        <pre className="scrollbox mt-3 text-[12px] bg-[color:var(--paper)] p-3 rounded border border-[color:var(--sumi)]/10">
          {JSON.stringify(data ?? {}, null, 2)}
        </pre>
      ) : (
        <div className="mt-3 text-[12px] text-[color:var(--sumi)]/60">(collapsed)</div>
      )}
    </div>
  );
}
