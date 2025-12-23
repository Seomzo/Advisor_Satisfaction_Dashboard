import React, { useEffect, useMemo, useRef, useState } from "react";
import { fetchDashboardData } from "./api.js";
import { cx, formatPercent, formatScore, safeNumber } from "./utils.js";
import UploadPage from "./UploadPage.jsx";

function guessKey(columns, candidates) {
  const lowerMap = new Map(columns.map((c) => [c.toLowerCase(), c]));
  for (const c of candidates) {
    const hit = lowerMap.get(c.toLowerCase());
    if (hit) return hit;
  }
  return null;
}

function rankColor(rank) {
  if (rank === 1) return "gold";
  if (rank === 2) return "silver";
  if (rank === 3) return "bronze";
  return "neutral";
}

export default function App() {
  const pathname = window.location.pathname || "/";
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState(() => new Set());
  const abortRef = useRef(null);
  const requestIdRef = useRef(0);

  async function load() {
    const reqId = ++requestIdRef.current;
    setError("");
    setLoading(true);
    abortRef.current?.abort?.();
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const data = await fetchDashboardData({ signal: controller.signal });
      if (reqId === requestIdRef.current) setDoc(data);
    } catch (e) {
      // Ignore normal request cancellations (common in dev/StrictMode or rapid reloads)
      const msg = String(e?.message || "").toLowerCase();
      if (e?.name === "AbortError" || msg.includes("aborted")) return;
      if (reqId === requestIdRef.current) setError(e?.message || "Failed to load data.");
    } finally {
      if (reqId === requestIdRef.current) setLoading(false);
    }
  }

  useEffect(() => {
    load();
    return () => {
      abortRef.current?.abort?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const meta = doc?.meta ?? {};
  const title = doc?.dataset?.title ?? "Advisor Satisfaction";
  const columns = doc?.dataset?.columns ?? [];
  const rows = doc?.dataset?.rows ?? [];
  const fieldTypes = doc?.fieldTypes ?? {};

  const keyEmployee = useMemo(
    () => guessKey(columns, ["Employee", "Advisor", "Service Advisor", "Name"]),
    [columns]
  );
  const keyRank = useMemo(() => guessKey(columns, ["Rank"]), [columns]);
  const keyScore = useMemo(() => guessKey(columns, ["Satisfaction Score", "Score"]), [columns]);
  const keyImpact = useMemo(() => guessKey(columns, ["Impact"]), [columns]);
  const keyCompletes = useMemo(() => guessKey(columns, ["Completes"]), [columns]);
  const keyTotal = useMemo(() => guessKey(columns, ["Total Records", "Total"]), [columns]);
  const keyDealer = useMemo(() => guessKey(columns, ["Dealer"]), [columns]);
  const keyArea = useMemo(() => guessKey(columns, ["Area"]), [columns]);
  const keyRegion = useMemo(() => guessKey(columns, ["Region"]), [columns]);

  const sorted = useMemo(() => {
    const r = [...rows];
    const getRank = (row) => safeNumber(keyRank ? row[keyRank] : null);
    r.sort((a, b) => {
      const ra = getRank(a);
      const rb = getRank(b);
      if (ra === null && rb === null) return 0;
      if (ra === null) return 1;
      if (rb === null) return -1;
      return ra - rb;
    });
    return r;
  }, [rows, keyRank]);

  if (pathname === "/upload") {
    return (
      <UploadPage
        onDone={() => {
          window.location.href = "/";
        }}
      />
    );
  }

  const allDetailColumns = useMemo(() => {
    // Show every column (no horizontal scrolling) as a wrapped grid under each advisor.
    // Keep Employee/Dealer/Area/Region out (they are shown in the header area once).
    // Also keep Rank / Satisfaction Score / Impact / Records / Completes out since they’re shown in the collapsed row summary.
    const exclude = new Set(
      [keyEmployee, keyDealer, keyArea, keyRegion, keyRank, keyScore, keyImpact, keyTotal, keyCompletes].filter(
        Boolean
      )
    );
    return columns.filter((c) => !exclude.has(c));
  }, [columns, keyEmployee, keyDealer, keyArea, keyRegion, keyRank, keyScore, keyImpact, keyTotal, keyCompletes]);

  const headerInfo = useMemo(() => {
    const level = typeof meta?.Level === "string" ? meta.Level : "";

    // Tekion Level example: "426085 - Stevens Creek Volkswagen"
    let dealerNumber = "";
    let dealerName = "";
    if (level.includes(" - ")) {
      const [num, ...rest] = level.split(" - ");
      dealerNumber = (num || "").trim();
      dealerName = rest.join(" - ").trim();
    } else {
      dealerName = level.trim();
    }

    const first = sorted[0] ?? {};
    const area = keyArea ? String(first[keyArea] ?? "").trim() : "";
    const region = keyRegion ? String(first[keyRegion] ?? "").trim() : "";

    // Fallback dealer number from sheet if Level is missing.
    if (!dealerNumber && keyDealer) dealerNumber = String(first[keyDealer] ?? "").trim();

    return { dealerNumber, dealerName, area, region };
  }, [meta, sorted, keyDealer, keyArea, keyRegion]);

  return (
    <div className="screen">
      <header className="topbar">
        <div className="titleBlock">
          <div className="titleRow">
            <div className="title">{title}</div>
            <a className="pill" href="/upload">
              Upload
            </a>
          </div>
          <div className="subtitle">
            <span className="muted">
              {headerInfo.dealerNumber ? `Dealer: ${headerInfo.dealerNumber}` : "Dealer"}
            </span>
            {headerInfo.dealerName ? <span className="dot">•</span> : null}
            <span className="muted">{headerInfo.dealerName || ""}</span>
            {headerInfo.area ? <span className="dot">•</span> : null}
            <span className="muted">{headerInfo.area ? `Area: ${headerInfo.area}` : ""}</span>
            {headerInfo.region ? <span className="dot">•</span> : null}
            <span className="muted">{headerInfo.region ? `Region: ${headerInfo.region}` : ""}</span>
            <span className="dot">•</span>
            <span className="muted">Period: 1D</span>
          </div>
        </div>
        <div className="status">
          <div className="statusLine">
            <span className="muted">Last update</span>
            <span className="value">{meta?.["Exported Raw"] || meta?.Exported || "—"}</span>
          </div>
        </div>
      </header>

      <main className="content">
        <section className="leaderboardWrap">
          {loading && !doc ? (
            <div className="panel">Loading…</div>
          ) : error ? (
            <div className="panel error">
              <div className="errorTitle">Couldn’t load data</div>
              <div className="errorBody">{error}</div>
              <button className="button" onClick={load}>
                Retry
              </button>
            </div>
          ) : sorted.length === 0 ? (
            <div className="panel">
              No rows found. Upload a new `.xlsx` via <span className="mono">/upload</span>.
            </div>
          ) : (
            <div className="leaderboard">
              {sorted.map((row, idx) => {
                const rank = safeNumber(keyRank ? row[keyRank] : null);
                const name = keyEmployee ? row[keyEmployee] : "";
                const score = keyScore ? row[keyScore] : null;
                const impact = keyImpact ? row[keyImpact] : null;
                const completes = keyCompletes ? row[keyCompletes] : null;
                const total = keyTotal ? row[keyTotal] : null;
                const id = `${rank ?? "na"}-${String(name || "na")}-${idx}`;
                const open = expandedIds.has(id);

                return (
                  <div key={id} className={cx("card", "accordionCard", rankColor(rank), open && "open")}>
                    <button
                      type="button"
                      className="accordionButton"
                      onClick={() =>
                        setExpandedIds((prev) => {
                          const next = new Set(prev);
                          if (next.has(id)) next.delete(id);
                          else next.add(id);
                          return next;
                        })
                      }
                      aria-expanded={open}
                    >
                      <div className="rowLeft">
                        <div className="rankSmall">#{rank ?? "—"}</div>
                        <div className="nameSmall">{String(name || "—")}</div>
                      </div>
                      <div className="rowRight">
                        <div className="chip">
                          <div className="chipLabel">Satisfaction Score</div>
                          <div className="chipValue">{formatScore(score)}</div>
                        </div>
                        <div className="chip">
                          <div className="chipLabel">Impact</div>
                          <div className="chipValue">{safeNumber(impact) ?? "—"}</div>
                        </div>
                        <div className="chip">
                          <div className="chipLabel">Records</div>
                          <div className="chipValue">{safeNumber(total) ?? "—"}</div>
                        </div>
                        <div className="chip">
                          <div className="chipLabel">Completes</div>
                          <div className="chipValue">{safeNumber(completes) ?? "—"}</div>
                        </div>
                      </div>
                      <div className="chev" aria-hidden="true">
                        {open ? "▾" : "▸"}
                      </div>
                    </button>

                    {open ? (
                      <div className="accordionBody">
                        <div className="kpiGrid">
                          {allDetailColumns.map((col) => (
                            <div key={col} className="kpiItem">
                              <div className="kpiLabel">{col}</div>
                              <div className="kpiValue">{renderCell(row[col], fieldTypes[col], col)}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function renderCell(value, type, columnName) {
  if (type === "percent") return <PercentCell value={value} columnName={columnName} />;
  if (type === "number") {
    const n = safeNumber(value);
    return <span className="mono">{n ?? "—"}</span>;
  }
  return <span>{value === "" || value === null || value === undefined ? "—" : String(value)}</span>;
}

function normalizeColumnName(name) {
  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function percentThresholdForColumn(columnName) {
  const key = normalizeColumnName(columnName);

  // Special thresholds (green if >= threshold, otherwise red)
  if (key === "vehicle returned cleaner") return 50;
  if (key === "paperwork <7 minutes") return 75;
  if (key === "advisor provided video") return 75;
  if (key === "escorted to vehicle") return 75;

  // Default: only perfect scores are green
  return 100;
}

function PercentCell({ value, columnName }) {
  const n = safeNumber(value);
  if (n === null) return <span>—</span>;
  const clamped = Math.max(0, Math.min(100, n));
  const r = 12;
  const c = 2 * Math.PI * r;
  const dash = (clamped / 100) * c;
  const threshold = percentThresholdForColumn(columnName);
  const good = n >= threshold;
  const pctColor = good ? "var(--good)" : "var(--bad)";
  return (
    <div className="pct">
      <svg className="pctSvg" viewBox="0 0 36 36" aria-hidden="true">
        <circle className="pctTrack" cx="18" cy="18" r={r} />
        <circle
          className="pctProgress"
          cx="18"
          cy="18"
          r={r}
          strokeDasharray={`${dash} ${c - dash}`}
          style={{ "--pctColor": pctColor }}
        />
      </svg>
      <div className="pctText mono">{formatPercent(n)}</div>
    </div>
  );
}


