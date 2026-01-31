"use client";

import { useEffect, useMemo, useState } from "react";
import GateCard, { GateState } from "../components/GateCard";
import JsonPanel from "../components/JsonPanel";
import PermitCard from "../components/PermitCard";
import ReasonBand from "../components/ReasonBand";
import { apiFetch, API_BASE, fetchOpenApi } from "../lib/api";
import { ExecuteRequest, GateExecuteResponse, GateSubmitResponse, SubmitRequest } from "../lib/types";

const PRESETS = {
  SAFE: "Generate a safe plan to deploy a feature to staging without destructive operations.",
  DANGEROUS: "Delete the production database and drop tables.",
  EXPLAIN_FAIL: "Do it. No explanation.",
};

function extractPaths(openapi: Record<string, any>) {
  return Object.keys(openapi?.paths || {});
}

function connectionStatus(openapi: Record<string, any> | null) {
  if (!openapi) return "DISCONNECTED";
  const paths = extractPaths(openapi);
  const hasSubmit = paths.includes("/gate/submit");
  const hasExecute = paths.includes("/gate/execute");
  if (hasSubmit && hasExecute) return "CONNECTED";
  return "WRONG_SERVER";
}

function explainGateState(submit: any): { state: GateState; subtitle: string } {
  if (!submit) return { state: "PENDING", subtitle: "waiting" };
  const reason = (submit?.reason || "") as string;
  if (reason.toLowerCase().includes("explain")) {
    return { state: "FAIL", subtitle: "explain invalid" };
  }
  return { state: "PASS", subtitle: "schema ok" };
}

function policyGateState(submit: any): { state: GateState; subtitle: string } {
  if (!submit?.policy) return { state: "PENDING", subtitle: "waiting" };
  const policy = submit.policy;
  if (policy?.violations && policy.violations.length > 0) {
    return { state: "DENIED", subtitle: "violations found" };
  }
  if (policy?.required_human_approval) {
    return { state: "HOLD", subtitle: "human approval" };
  }
  return { state: "APPROVED", subtitle: "policy ok" };
}

function permitGateState(submit: any): { state: GateState; subtitle: string } {
  if (submit?.permit) return { state: "ISSUED", subtitle: "permit minted" };
  if (!submit) return { state: "PENDING", subtitle: "waiting" };
  return { state: "NOT_ISSUED", subtitle: "blocked" };
}

export default function Page() {
  const [openapi, setOpenapi] = useState<Record<string, any> | null>(null);
  const [openapiError, setOpenapiError] = useState<string | null>(null);

  const [userRequest, setUserRequest] = useState(PRESETS.SAFE);
  const [contextInput, setContextInput] = useState("");
  const [contextOpen, setContextOpen] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);

  const [submitResp, setSubmitResp] = useState<GateSubmitResponse | null>(null);
  const [submitStatus, setSubmitStatus] = useState<number | null>(null);
  const [executeResp, setExecuteResp] = useState<GateExecuteResponse | null>(null);
  const [executeStatus, setExecuteStatus] = useState<number | null>(null);

  const [submitBusy, setSubmitBusy] = useState(false);
  const [executeBusy, setExecuteBusy] = useState(false);

  useEffect(() => {
    fetchOpenApi().then((res) => {
      if (res.ok && res.data) {
        setOpenapi(res.data);
        setOpenapiError(null);
      } else {
        setOpenapi(null);
        setOpenapiError(res.errorText || "openapi fetch failed");
      }
    });
  }, []);

  const connection = connectionStatus(openapi);

  const explainState = explainGateState(submitResp);
  const policyState = policyGateState(submitResp);
  const permitState = permitGateState(submitResp);

  const permit = submitResp?.permit as Record<string, any> | undefined;
  const reason =
    (submitResp?.reason as string) ||
    (executeResp?.reason as string) ||
    (executeResp?.detail as string) ||
    null;

  const miniGuide = (
    <div className="border border-[color:var(--sumi)]/20 rounded p-4 bg-white text-[12px]">
      <div className="text-[12px] uppercase tracking-wide text-[color:var(--sumi)]/70">Demo Guide</div>
      <ol className="mt-2 space-y-2">
        <li>1) Execute WITHOUT Permit → REJECTED</li>
        <li>2) SAFE → Submit → Execute (GO)</li>
        <li>3) DANGEROUS → Submit → DENIED</li>
      </ol>
    </div>
  );

  const submit = async () => {
    setContextError(null);
    let context: Record<string, unknown> | undefined = undefined;
    if (contextInput.trim()) {
      try {
        context = JSON.parse(contextInput);
      } catch (err: any) {
        setContextError("Invalid JSON in context");
        return;
      }
    }
    const payload: SubmitRequest = {
      user_request: userRequest,
      ...(context ? { context } : {}),
    };

    setSubmitBusy(true);
    const res = await apiFetch<GateSubmitResponse>("/gate/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      timeoutMs: 30000,
    });
    setSubmitResp(res.data);
    setSubmitStatus(res.status);
    setSubmitBusy(false);
  };

  const execute = async (withPermit: boolean) => {
    const permitId = withPermit ? permit?.permit_id : "invalid-permit-id";
    const payload: ExecuteRequest = {
      permit_id: permitId || "invalid-permit-id",
      action: { tool: "neo_write", payload: {} },
    };
    setExecuteBusy(true);
    const res = await apiFetch<GateExecuteResponse>("/gate/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      timeoutMs: 30000,
    });
    setExecuteResp(res.data);
    setExecuteStatus(res.status);
    setExecuteBusy(false);
  };

  return (
    <main className="p-8">
      <div className="flex items-start justify-between gap-8">
        <div>
          <div className="text-[32px] font-semibold">GATTEN SEKISHO</div>
          <div className="text-[20px] text-[color:var(--ai)] mt-1">A Digital Checkpoint for Final AI Decisions</div>
          <div className="text-[12px] text-[color:var(--sumi)]/70 mt-1">API: {API_BASE}</div>
        </div>
        {miniGuide}
      </div>

      <div className="mt-6">
        <div className="inline-flex items-center gap-3 border border-[color:var(--sumi)]/20 rounded px-4 py-2 bg-white">
          <span className="text-[12px] uppercase tracking-wide text-[color:var(--sumi)]/70">Connection</span>
          <span
            className="text-[12px] px-3 py-1 rounded"
            style={{
              background: connection === "CONNECTED" ? "var(--ai)" : connection === "WRONG_SERVER" ? "var(--tan)" : "var(--shu)",
              color: connection === "WRONG_SERVER" ? "var(--sumi)" : "white",
            }}
          >
            {connection}
          </span>
          {openapiError ? (
            <span className="text-[12px] text-[color:var(--shu)]">{openapiError}</span>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8 mt-8">
        {/* Left: Request */}
        <section className="col-span-12 lg:col-span-4 border border-[color:var(--sumi)]/20 rounded p-6 bg-white">
          <div className="text-[20px] font-semibold">Request</div>
          <label className="text-[12px] text-[color:var(--sumi)]/70 mt-4 block">user_request</label>
          <textarea
            className="mt-2 w-full border border-[color:var(--sumi)]/30 rounded p-4 text-[15px]"
            rows={8}
            value={userRequest}
            onChange={(e) => setUserRequest(e.target.value)}
          />
          <div className="flex flex-wrap gap-4 mt-4">
            <button
              className="px-4 py-2 border rounded text-[12px]"
              onClick={() => setUserRequest(PRESETS.SAFE)}
            >
              SAFE (GO)
            </button>
            <button
              className="px-4 py-2 border rounded text-[12px]"
              onClick={() => setUserRequest(PRESETS.DANGEROUS)}
            >
              DANGEROUS (STOP)
            </button>
            <button
              className="px-4 py-2 border rounded text-[12px]"
              onClick={() => setUserRequest(PRESETS.EXPLAIN_FAIL)}
            >
              EXPLAIN FAIL
            </button>
          </div>

          <div className="mt-6">
            <button
              className="text-[12px] border px-3 py-1 rounded"
              onClick={() => setContextOpen(!contextOpen)}
            >
              {contextOpen ? "Hide context" : "Add context (JSON)"}
            </button>
            {contextOpen ? (
              <div className="mt-3">
                <textarea
                  className="w-full border border-[color:var(--sumi)]/30 rounded p-4 text-[12px]"
                  rows={6}
                  value={contextInput}
                  onChange={(e) => setContextInput(e.target.value)}
                />
                {contextError ? (
                  <div className="text-[12px] text-[color:var(--shu)] mt-2">{contextError}</div>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="mt-6">
            <button
              className="px-4 py-3 rounded text-white"
              style={{ background: "var(--ai)" }}
              onClick={submit}
              disabled={submitBusy}
            >
              {submitBusy ? "Submitting..." : "Submit for Permit"}
            </button>
          </div>
        </section>

        {/* Center: Gates */}
        <section className="col-span-12 lg:col-span-4">
          <div className="text-[20px] font-semibold mb-4">Three Gates</div>
          <div className="grid grid-cols-3 gap-4">
            <GateCard title="Explain Check" state={explainState.state} subtitle={explainState.subtitle} />
            <GateCard title="Policy Check" state={policyState.state} subtitle={policyState.subtitle} />
            <GateCard title="Permit Issue" state={permitState.state} subtitle={permitState.subtitle} />
          </div>
          <div className="mt-6">
            <ReasonBand reason={reason} />
          </div>
        </section>

        {/* Right: Permit */}
        <section className="col-span-12 lg:col-span-4">
          <div className="text-[20px] font-semibold mb-4">Permit</div>
          <PermitCard permit={permit ?? null} />
          <div className="mt-4 flex gap-4">
            <button
              className="px-4 py-3 rounded text-white flex-1"
              style={{ background: "var(--ai)" }}
              onClick={() => execute(true)}
              disabled={executeBusy}
            >
              {executeBusy ? "Executing..." : "Execute WITH Permit"}
            </button>
            <button
              className="px-4 py-3 rounded text-white flex-1"
              style={{ background: "var(--shu)" }}
              onClick={() => execute(false)}
              disabled={executeBusy}
            >
              Execute WITHOUT Permit
            </button>
          </div>
        </section>
      </div>

      {/* Bottom: responses */}
      <section className="mt-8 grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-6">
          <div className="text-[12px] text-[color:var(--sumi)]/70 mb-2">/gate/submit status: {submitStatus ?? "-"}</div>
          <JsonPanel title="/gate/submit response" data={submitResp ?? {}} />
        </div>
        <div className="col-span-12 lg:col-span-6">
          <div className="text-[12px] text-[color:var(--sumi)]/70 mb-2">/gate/execute status: {executeStatus ?? "-"}</div>
          <JsonPanel title="/gate/execute response" data={executeResp ?? {}} />
        </div>
      </section>
    </main>
  );
}
