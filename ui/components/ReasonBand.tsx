export default function ReasonBand({ reason }: { reason?: string | null }) {
  const message = reason && reason.length > 0 ? reason : "No reason reported.";
  return (
    <div className="reason-band border border-[color:var(--shu)]/60 rounded p-4 bg-[color:var(--shu)] text-white">
      <div className="text-[12px] uppercase tracking-wide">reason</div>
      <div className="text-[16px] font-semibold mt-1">{message}</div>
    </div>
  );
}
