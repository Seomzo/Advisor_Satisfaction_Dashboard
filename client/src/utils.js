export function safeNumber(v) {
  if (v === null || v === undefined || v === "") return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function formatPercent(v) {
  const n = safeNumber(v);
  if (n === null) return "—";
  return `${n.toFixed(1)}%`;
}

export function formatScore(v) {
  const n = safeNumber(v);
  if (n === null) return "—";
  if (n >= 100) return n.toFixed(0);
  return n.toFixed(1);
}

export function cx(...parts) {
  return parts.filter(Boolean).join(" ");
}


