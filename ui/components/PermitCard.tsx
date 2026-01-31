"use client";

import { useState } from "react";

function shortHash(value?: string, chars = 10) {
  if (!value) return "-";
  if (value.length <= chars * 2) return value;
  return `${value.slice(0, chars)}…${value.slice(-chars)}`;
}

export default function PermitCard({
  permit,
}: {
  permit: Record<string, any> | null;
}) {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = async (label: string, value?: string) => {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    setCopied(label);
    setTimeout(() => setCopied(null), 1200);
  };

  return (
    <div className="border border-[color:var(--sumi)]/20 rounded p-4 bg-white">
      <div className="text-[12px] uppercase tracking-wide text-[color:var(--sumi)]/70">Permit</div>
      <div className="mt-3 space-y-3 text-[14px]">
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">permit_id</div>
          <div className="flex items-center justify-between gap-2">
            <span>{shortHash(permit?.permit_id)}</span>
            <button className="text-[12px] border px-2 py-1 rounded" onClick={() => copy("permit_id", permit?.permit_id)}>copy</button>
          </div>
        </div>
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">decision_hash</div>
          <div className="flex items-center justify-between gap-2">
            <span>{shortHash(permit?.decision_hash)}</span>
            <button className="text-[12px] border px-2 py-1 rounded" onClick={() => copy("decision_hash", permit?.decision_hash)}>copy</button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-[12px] text-[color:var(--sumi)]/60">policy_version</div>
            <div>{permit?.policy_version ?? "-"}</div>
          </div>
          <div>
            <div className="text-[12px] text-[color:var(--sumi)]/60">risk_level</div>
            <div>{permit?.risk_level ?? "-"}</div>
          </div>
        </div>
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">issued_at</div>
          <div>{permit?.issued_at ?? "-"}</div>
        </div>
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">expires_at</div>
          <div>{permit?.expires_at ?? "-"}</div>
        </div>
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">neo_tx_hash</div>
          <div className="flex items-center gap-2">
            <span>{shortHash(permit?.neo_tx_hash)}</span>
            {permit?.neo_tx_hash?.startsWith("MOCK") ? (
              <span className="text-[12px] px-2 py-1 rounded border border-[color:var(--shu)] text-[color:var(--shu)]">MOCK</span>
            ) : null}
          </div>
        </div>
        <div>
          <div className="text-[12px] text-[color:var(--sumi)]/60">neo_mode</div>
          <div>{permit?.neo_mode ?? "-"}</div>
        </div>
        {copied ? (
          <div className="text-[12px] text-[color:var(--ai)]">copied {copied}</div>
        ) : null}
      </div>
    </div>
  );
}
