import path from "node:path";
import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import express from "express";
import cors from "cors";
import multer from "multer";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..", "..");

const STORAGE_DIR = path.resolve(projectRoot, "storage");
const LATEST_XLSX_PATH = path.resolve(STORAGE_DIR, "latest.xlsx");
const LATEST_JSON_PATH = path.resolve(STORAGE_DIR, "latest.json");

const PORT = process.env.PORT ? Number(process.env.PORT) : 5179;
const CLIENT_DIST = path.resolve(projectRoot, "client", "dist");

await fs.mkdir(STORAGE_DIR, { recursive: true });

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

const upload = multer({
  storage: multer.diskStorage({
    destination: async (_req, _file, cb) => {
      cb(null, STORAGE_DIR);
    },
    filename: async (_req, _file, cb) => {
      cb(null, "latest.xlsx");
    },
  }),
  limits: {
    fileSize: 25 * 1024 * 1024,
  },
});

let cached = null;
let cachedMtimeMs = 0;

function pickPythonCommand() {
  if (process.env.PYTHON && String(process.env.PYTHON).trim()) return String(process.env.PYTHON).trim();
  // Windows usually provides `python` (or `py`). macOS/Linux typically have `python3`.
  return process.platform === "win32" ? "python" : "python3";
}

function spawnParser(pythonCmd, scriptPath, xlsxPath, outJsonPath) {
  return spawn(pythonCmd, [scriptPath, xlsxPath, outJsonPath], {
    stdio: ["ignore", "pipe", "pipe"],
    env: process.env,
  });
}

function runParser(xlsxPath, outJsonPath) {
  const scriptPath = path.resolve(projectRoot, "server", "scripts", "parse_xlsx.py");

  return new Promise((resolve, reject) => {
    const primaryCmd = pickPythonCommand();
    let attemptedFallback = false;

    function attach(child) {
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (d) => (stdout += d.toString()));
      child.stderr.on("data", (d) => (stderr += d.toString()));

      child.on("error", (err) => {
        // If the command isn't found, try a reasonable fallback once.
        if (!attemptedFallback && err && err.code === "ENOENT" && primaryCmd !== "python") {
          attemptedFallback = true;
          const fallback = "python";
          attach(spawnParser(fallback, scriptPath, xlsxPath, outJsonPath));
          return;
        }
        reject(err);
      });

      child.on("close", (code) => {
        if (code === 0) return resolve({ stdout });
        reject(new Error(`parse_xlsx.py failed (code ${code}). ${stderr || stdout}`));
      });
    }

    attach(spawnParser(primaryCmd, scriptPath, xlsxPath, outJsonPath));
  });
}

async function loadLatestJsonIfFresh() {
  if (!existsSync(LATEST_JSON_PATH)) return null;
  const stat = await fs.stat(LATEST_JSON_PATH);
  if (stat.mtimeMs <= cachedMtimeMs && cached) return cached;
  const raw = await fs.readFile(LATEST_JSON_PATH, "utf-8");
  cached = JSON.parse(raw);
  cachedMtimeMs = stat.mtimeMs;
  return cached;
}

async function ensureLatestXlsx() {
  if (existsSync(LATEST_XLSX_PATH)) return true;
  const entries = await fs.readdir(projectRoot);
  const candidate = entries.find((f) => f.toLowerCase().endsWith(".xlsx"));
  if (!candidate) return false;
  await fs.copyFile(path.resolve(projectRoot, candidate), LATEST_XLSX_PATH);
  return true;
}

async function ensureLatestJson() {
  if (existsSync(LATEST_JSON_PATH)) return loadLatestJsonIfFresh();
  if (!existsSync(LATEST_XLSX_PATH)) {
    const ok = await ensureLatestXlsx();
    if (!ok) return null;
  }

  await runParser(LATEST_XLSX_PATH, LATEST_JSON_PATH);
  return loadLatestJsonIfFresh();
}

app.get("/api/health", (_req, res) => res.json({ ok: true }));

app.get("/api/meta", async (_req, res) => {
  try {
    const doc = await ensureLatestJson();
    if (!doc) return res.status(404).json({ error: "No data yet. Upload an .xlsx first." });
    res.json(doc.meta ?? {});
  } catch (e) {
    res.status(500).json({ error: e?.message ?? "Unknown error" });
  }
});

app.get("/api/data", async (_req, res) => {
  try {
    const doc = await ensureLatestJson();
    if (!doc) return res.status(404).json({ error: "No data yet. Upload an .xlsx first." });
    res.json(doc);
  } catch (e) {
    res.status(500).json({ error: e?.message ?? "Unknown error" });
  }
});

app.post("/api/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "Missing file field 'file'." });
    await runParser(LATEST_XLSX_PATH, LATEST_JSON_PATH);
    const doc = await loadLatestJsonIfFresh();
    res.json({ ok: true, meta: doc?.meta ?? {} });
  } catch (e) {
    res.status(500).json({ error: e?.message ?? "Unknown error" });
  }
});

// Static hosting (for production)
if (existsSync(CLIENT_DIST)) {
  app.use(express.static(CLIENT_DIST));
  app.get("*", (_req, res) => {
    res.sendFile(path.resolve(CLIENT_DIST, "index.html"));
  });
}

// Try to parse any existing XLSX on boot (non-fatal)
ensureLatestJson().catch(() => {});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});


