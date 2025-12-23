import React, { useMemo, useState } from "react";
import { uploadXlsx } from "./api.js";

export default function UploadPage({ onDone }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  const canSubmit = useMemo(() => !!file && !busy, [file, busy]);

  async function onSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setOk("");
    try {
      const res = await uploadXlsx(file);
      setOk(`Uploaded. Exported: ${res?.meta?.["Exported Raw"] || res?.meta?.Exported || "—"}`);
      setTimeout(() => onDone?.(), 700);
    } catch (e2) {
      setError(e2?.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen">
      <header className="topbar">
        <div className="titleBlock">
          <div className="titleRow">
            <div className="title">Upload daily XLSX</div>
            <a className="pill" href="/">
              Back
            </a>
          </div>
          <div className="subtitle">
            Choose the exported Tekion file. The dashboard updates immediately.
          </div>
        </div>
      </header>

      <main className="content">
        <section className="panel">
          <form onSubmit={onSubmit} className="uploadForm">
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={busy}
            />
            <button className="button" type="submit" disabled={!canSubmit}>
              {busy ? "Uploading…" : "Upload"}
            </button>
          </form>
          {error ? <div className="notice error">{error}</div> : null}
          {ok ? <div className="notice ok">{ok}</div> : null}
          <div className="hint">
            Tip: you can also upload via curl:
            <div className="mono codeLine">
              curl -F file=@&quot;VW_EmployeeRank.xlsx&quot; http://localhost:5179/api/upload
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}


