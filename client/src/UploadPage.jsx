import React, { useMemo, useRef, useState } from "react";
import { uploadXlsx } from "./api.js";

export default function UploadPage({ onDone }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const canSubmit = useMemo(() => !!file && !busy, [file, busy]);

  function setPickedFile(f) {
    if (!f) return;
    if (!String(f.name || "").toLowerCase().endsWith(".xlsx")) {
      setError("Please choose an .xlsx file.");
      return;
    }
    setError("");
    setOk("");
    setFile(f);
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setOk("");
    try {
      const res = await uploadXlsx(file);
      setOk(`Uploaded. Exported: ${res?.meta?.["Exported Raw"] || res?.meta?.Exported || "—"}`);
      setTimeout(() => onDone?.(), 400);
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
        <section className="panel uploadPanel">
          <form onSubmit={onSubmit} className="uploadForm">
            <input
              id="xlsx-input"
              className="fileInput"
              type="file"
              accept=".xlsx"
              onChange={(e) => setPickedFile(e.target.files?.[0] ?? null)}
              disabled={busy}
              ref={inputRef}
            />

            <div
              className={"dropzone" + (dragOver ? " dragOver" : "")}
              role="button"
              tabIndex={0}
              onClick={() => {
                if (!busy) inputRef.current?.click?.();
              }}
              onKeyDown={(e) => {
                if (busy) return;
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  inputRef.current?.click?.();
                }
              }}
              onDragEnter={(e) => {
                e.preventDefault();
                if (!busy) setDragOver(true);
              }}
              onDragOver={(e) => {
                e.preventDefault();
                if (!busy) setDragOver(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setDragOver(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (busy) return;
                const f = e.dataTransfer?.files?.[0];
                setPickedFile(f ?? null);
              }}
            >
              <div className="dropTitle">{file ? "File selected" : "Drop your daily XLSX here"}</div>
              <div className="dropSub">
                {file ? (
                  <>
                    <span className="mono">{file.name}</span>
                    <span className="muted"> — Click to change</span>
                  </>
                ) : (
                  <>
                    or <span className="linkLike">click to browse</span>
                  </>
                )}
              </div>
            </div>

            <button className="button" type="submit" disabled={!canSubmit}>
              {busy ? "Uploading…" : "Upload"}
            </button>
          </form>
          {error ? <div className="notice error">{error}</div> : null}
          {ok ? <div className="notice ok">{ok}</div> : null}
        </section>
      </main>
    </div>
  );
}


