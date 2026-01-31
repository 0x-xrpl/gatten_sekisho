export type GateState = "PENDING" | "PASS" | "FAIL" | "APPROVED" | "DENIED" | "HOLD" | "NOT_ISSUED" | "ISSUED";

function mapToSeal(state: GateState) {
  if (state === "PASS" || state === "APPROVED" || state === "ISSUED") return "OPEN";
  if (state === "HOLD" || state === "PENDING") return "HOLD";
  return "SEALED";
}

function colorFor(state: GateState) {
  const seal = mapToSeal(state);
  if (seal === "OPEN") return "var(--ai)";
  if (seal === "HOLD") return "var(--tan)";
  return "var(--shu)";
}

export default function GateCard({
  title,
  state,
  subtitle,
}: {
  title: string;
  state: GateState;
  subtitle: string;
}) {
  const seal = mapToSeal(state);
  const color = colorFor(state);
  return (
    <div className="border border-[color:var(--sumi)]/20 rounded p-4 bg-white min-h-[180px] flex flex-col justify-between">
      <div className="text-[12px] uppercase tracking-wide text-[color:var(--sumi)]/70">{title}</div>
      <div className="text-center">
        <div
          className="text-[20px] font-semibold"
          style={{ color }}
        >
          {seal}
        </div>
        <div className="text-[12px] text-[color:var(--sumi)]/70 mt-1">{state}</div>
      </div>
      <div className="text-[12px] text-[color:var(--sumi)]/70">{subtitle}</div>
    </div>
  );
}
