#!/usr/bin/env python3
"""
Advisor Satisfaction Dashboard - Streamlit Version

A full-screen dashboard for daily Tekion Service Employee Rank Excel exports.
"""

import streamlit as st
import json
import re
import zipfile
import xml.etree.ElementTree as ET
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# ============================================================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================================================

st.set_page_config(
    page_title="Advisor Satisfaction Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS - Recreating the original design
# ============================================================================

CUSTOM_CSS = """
<style>
:root {
  --bg0: #FFFFFF;
  --bg1: #F9FAFB;
  --card: #F3F4F6;
  --line: #E5E7EB;
  --text: #111827;
  --muted: #6B7280;
  --gold: #F59E0B;
  --silver: #9CA3AF;
  --bronze: #D97706;
  --good: #10B981;
  --bad: #EF4444;
  
  /* Responsive font sizes - scale with viewport */
  --font-base: clamp(14px, 1.1vw, 18px);
  --font-title: clamp(22px, 2.8vw, 36px);
  --font-subtitle: clamp(12px, 1vw, 16px);
  --font-rank: clamp(18px, 1.6vw, 26px);
  --font-name: clamp(18px, 1.6vw, 24px);
  --font-chip-label: clamp(12px, 1vw, 15px);
  --font-chip-value: clamp(14px, 1.2vw, 20px);
  --font-kpi-label: clamp(12px, 1vw, 15px);
  --font-kpi-value: clamp(15px, 1.3vw, 20px);
  
  /* Responsive spacing */
  --spacing-xs: clamp(4px, 0.4vw, 8px);
  --spacing-sm: clamp(6px, 0.6vw, 10px);
  --spacing-md: clamp(8px, 0.8vw, 12px);
  --spacing-lg: clamp(10px, 1vw, 16px);
  --spacing-xl: clamp(12px, 1.2vw, 20px);
  
  /* Card spacing */
  --card-padding: clamp(8px, 1vw, 14px);
  --card-gap: clamp(6px, 0.8vw, 12px);
}

/* Hide Streamlit branding and padding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Full screen light background */
.stApp {
    background: linear-gradient(160deg, #FFFFFF, #F9FAFB);
    color: #111827;
}

/* Remove default Streamlit padding */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: clamp(0.5rem, 1.5vw, 2rem) !important;
    padding-right: clamp(0.5rem, 1.5vw, 2rem) !important;
    max-width: 100% !important;
}

/* Custom styling for elements */
.stButton button {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    color: #111827;
    font-weight: 800;
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: clamp(8px, 0.8vw, 12px);
    cursor: pointer;
    font-size: var(--font-base);
    transition: all 0.2s ease;
}

.stButton button:hover {
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
}

/* File uploader styling */
.uploadedFile {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: var(--spacing-md);
    background: #F9FAFB;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: transparent !important;
    border: none !important;
    color: #111827 !important;
    font-weight: 800 !important;
}

/* Mono font for numbers */
.mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

/* Muted text */
.muted {
    color: #A7B3DA;
    opacity: 0.95;
}

/* Dot separator */
.dot {
    opacity: 0.7;
    margin: 0 0.5rem;
}

/* Responsive title and headers */
.dashboard-title {
    font-size: var(--font-title);
    font-weight: 800;
    margin-bottom: var(--spacing-sm);
    line-height: 1.2;
}

.dashboard-subtitle {
    font-size: var(--font-subtitle);
    margin-bottom: var(--spacing-md);
    line-height: 1.4;
}

/* Responsive advisor card */
.advisor-card {
    border-radius: clamp(12px, 1.2vw, 18px);
    margin-bottom: var(--spacing-md);
    overflow: hidden;
    box-shadow: 0 clamp(4px, 0.5vw, 8px) clamp(12px, 1.5vw, 20px) rgba(0, 0, 0, 0.1);
}

/* Collapsed view - responsive layout */
.advisor-collapsed {
    padding: var(--card-padding);
    display: grid;
    grid-template-columns: 
        minmax(50px, 0.4fr) 
        minmax(150px, 2fr) 
        repeat(4, minmax(120px, 1fr)) 
        minmax(40px, 0.3fr);
    gap: clamp(4px, 0.5vw, 8px);
    align-items: center;
}

.advisor-rank {
    font-weight: 950;
    font-size: var(--font-rank);
    opacity: 0.95;
}

.advisor-name {
    font-weight: 950;
    font-size: var(--font-name);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Metric chips - responsive */
.metric-chip {
    border: 1px solid #E5E7EB;
    border-radius: 999px;
    padding: var(--spacing-md) var(--spacing-lg);
    background: #F9FAFB;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    min-width: 0;
}

.chip-label {
    font-size: var(--font-chip-label);
    font-weight: 700;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.chip-value {
    font-size: var(--font-chip-value);
    font-weight: 800;
}

/* Expanded view - responsive grid - HORIZONTAL OPTIMIZED */
.kpi-grid-container {
    border-top: 1px solid #E5E7EB;
    padding: var(--spacing-md) var(--spacing-lg);
    background: #F9FAFB;
}

.kpi-grid {
    display: grid;
    /* Optimize for horizontal layout - more columns, fewer rows */
    grid-template-columns: repeat(auto-fit, minmax(clamp(160px, 15vw, 220px), 1fr));
    gap: var(--spacing-sm) var(--spacing-md);
    grid-auto-flow: row;
    align-items: stretch;
}

.kpi-card {
    border: 1px solid #E5E7EB;
    border-radius: clamp(10px, 1vw, 14px);
    padding: var(--spacing-md) var(--spacing-lg);
    background: #FFFFFF;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: clamp(75px, 8vw, 95px);
}

.kpi-label {
    font-size: var(--font-kpi-label);
    font-weight: 700;
    color: var(--muted);
    margin-bottom: var(--spacing-xs);
    line-height: 1.25;
    word-wrap: break-word;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.kpi-value {
    font-size: var(--font-kpi-value);
    font-weight: 800;
    min-width: 0;
    word-wrap: break-word;
    line-height: 1.2;
}

/* Circular progress - responsive sizing */
.progress-container {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.progress-svg {
    width: clamp(36px, 3vw, 48px);
    height: clamp(36px, 3vw, 48px);
    transform: rotate(-90deg);
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    flex-shrink: 0;
}

.progress-text {
    font-size: var(--font-chip-value);
    font-weight: 800;
    min-width: clamp(55px, 5.5vw, 80px);
}

/* Media queries for specific breakpoints - HORIZONTAL OPTIMIZED */
@media (max-width: 1400px) {
    .advisor-collapsed {
        grid-template-columns: 
            minmax(50px, 0.4fr) 
            minmax(120px, 1.5fr) 
            repeat(4, minmax(100px, 1fr)) 
            minmax(35px, 0.2fr);
    }
    
    .kpi-grid {
        /* Keep 5-6 columns even on medium screens */
        grid-template-columns: repeat(auto-fit, minmax(clamp(150px, 14vw, 200px), 1fr));
    }
}

@media (max-width: 1100px) {
    .advisor-collapsed {
        grid-template-columns: 
            minmax(45px, 0.3fr) 
            minmax(100px, 1.2fr) 
            repeat(2, minmax(90px, 1fr)) 
            minmax(30px, 0.2fr);
        grid-template-rows: auto auto;
    }
    
    .advisor-collapsed > :nth-child(n+5):nth-child(-n+6) {
        grid-column: 3 / 5;
    }
    
    .kpi-grid {
        /* Keep 4-5 columns on tablets - prioritize horizontal */
        grid-template-columns: repeat(auto-fit, minmax(clamp(140px, 18vw, 180px), 1fr));
    }
}

@media (max-width: 900px) {
    .kpi-grid {
        /* 3-4 columns on smaller tablets */
        grid-template-columns: repeat(auto-fit, minmax(clamp(130px, 22vw, 170px), 1fr));
    }
}

@media (max-width: 768px) {
    .advisor-collapsed {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: var(--spacing-sm);
    }
    
    .metric-chip {
        width: 100%;
    }
    
    .kpi-grid {
        /* Still maintain 2-3 columns on mobile landscape */
        grid-template-columns: repeat(auto-fit, minmax(clamp(120px, 30vw, 160px), 1fr));
    }
    
    .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
}

@media (max-width: 600px) {
    .kpi-grid {
        /* Only go to 2 columns on very small screens */
        grid-template-columns: repeat(auto-fit, minmax(clamp(140px, 45vw, 200px), 1fr));
    }
}

@media (min-width: 1800px) {
    :root {
        --font-base: 16px;
        --font-title: 34px;
        --font-rank: 24px;
        --font-name: 22px;
    }
    
    .kpi-grid {
        /* Maximum columns on large screens */
        grid-template-columns: repeat(auto-fit, minmax(clamp(160px, 12vw, 220px), 1fr));
    }
}
</style>
"""

# ============================================================================
# XLSX PARSING (stdlib only - from parse_xlsx.py)
# ============================================================================

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

def _col_to_index(col: str) -> int:
    idx = 0
    for ch in col:
        if "A" <= ch <= "Z":
            idx = idx * 26 + (ord(ch) - 64)
    return idx

def _parse_shared_strings(z: zipfile.ZipFile) -> List[str]:
    p = "xl/sharedStrings.xml"
    if p not in z.namelist():
        return []
    root = ET.fromstring(z.read(p))
    out: List[str] = []
    for si in root.findall("main:si", NS):
        ts = [t.text or "" for t in si.findall(".//main:t", NS)]
        out.append("".join(ts))
    return out

def _parse_workbook_sheets(z: zipfile.ZipFile) -> List[Tuple[str, str]]:
    wb_root = ET.fromstring(z.read("xl/workbook.xml"))
    rel_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {
        rel.get("Id"): rel.get("Target") for rel in rel_root.findall("rel:Relationship", NS)
    }

    sheets: List[Tuple[str, str]] = []
    for s in wb_root.findall("main:sheets/main:sheet", NS):
        rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        name = s.get("name") or "Sheet"
        target = rid_to_target.get(rid)
        if not target:
            continue
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheets.append((name, target))
    return sheets

def _parse_sheet_rows(z: zipfile.ZipFile, sheet_path: str, shared: List[str]) -> List[List[str]]:
    root = ET.fromstring(z.read(sheet_path))
    rows: List[List[str]] = []
    for row in root.findall(".//main:sheetData/main:row", NS):
        cells: Dict[str, str] = {}
        for c in row.findall("main:c", NS):
            r = c.get("r")
            if not r:
                continue
            col = "".join([ch for ch in r if ch.isalpha()])
            v = c.find("main:v", NS)
            if v is None:
                continue
            val = v.text or ""
            t = c.get("t")
            if t == "s":
                try:
                    val = shared[int(val)]
                except Exception:
                    pass
            cells[col] = val

        if not cells:
            rows.append([])
            continue

        max_col = max(_col_to_index(k) for k in cells)
        arr = [""] * max_col
        for k, v in cells.items():
            arr[_col_to_index(k) - 1] = v
        rows.append(arr)
    return rows

def _normalize_row(row: List[str]) -> List[str]:
    r = list(row)
    while r and (r[-1] is None or str(r[-1]).strip() == ""):
        r.pop()
    return [("" if v is None else str(v).strip()) for v in r]

def _find_header_row(rows: List[List[str]]) -> Optional[int]:
    for i, row in enumerate(rows):
        r = _normalize_row(row)
        if not r:
            continue
        lower = [c.lower() for c in r if c]
        if "employee" in lower and "rank" in lower:
            return i
    return None

PERCENT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*%\s*$")
NUMBER_RE = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*$")

def _coerce_value(v: str) -> Tuple[Any, str]:
    if v is None:
        return "", "string"
    s = str(v).strip()
    if s == "":
        return "", "string"
    m = PERCENT_RE.match(s)
    if m:
        return float(m.group(1)), "percent"
    if NUMBER_RE.match(s):
        if "." in s:
            return float(s), "number"
        try:
            return int(s), "number"
        except Exception:
            return float(s), "number"
    return s, "string"

def _parse_filters(filters_rows: List[List[str]]) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    for row in filters_rows:
        r = _normalize_row(row)
        if len(r) < 2:
            continue
        k, v = r[0], r[1]
        if not k or k.lower() == "parameters":
            continue
        meta_key = re.sub(r"\s+", " ", k.strip())
        meta[meta_key] = v

    exported = meta.get("Exported")
    if isinstance(exported, str) and exported.strip():
        raw = exported.strip()
        meta["Exported Raw"] = raw
        m = re.match(
            r"^(?P<mon>[A-Za-z]{3})\s+(?P<day>\d{1,2})\s+(?P<year>\d{4})\s+(?P<h>\d{1,2}):(?P<mi>\d{2}):(?P<s>\d{2}):(?P<ms>\d{3})(?P<ampm>AM|PM)$",
            raw.replace(" ", ""),
        )
        if m:
            try:
                mon = m.group("mon")
                day = int(m.group("day"))
                year = int(m.group("year"))
                h = int(m.group("h"))
                mi = int(m.group("mi"))
                sec = int(m.group("s"))
                ms = int(m.group("ms"))
                ampm = m.group("ampm")
                dt = datetime.strptime(f"{mon} {day} {year} {h}:{mi}:{sec} {ampm}", "%b %d %Y %I:%M:%S %p")
                dt = dt.replace(microsecond=ms * 1000)
                meta["Exported ISO"] = dt.isoformat()
            except Exception:
                pass
    return meta

@dataclass
class Dataset:
    title: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    field_types: Dict[str, str]

def _build_dataset(data_rows: List[List[str]]) -> Dataset:
    header_idx = _find_header_row(data_rows)
    if header_idx is None:
        raise RuntimeError("Could not find header row (expected 'Employee' and 'Rank').")

    title = ""
    for j in range(header_idx - 1, -1, -1):
        r = _normalize_row(data_rows[j])
        if len(r) == 1 and r[0]:
            title = r[0]
            break
    if not title:
        title = "Service Employee Rank"

    columns = _normalize_row(data_rows[header_idx])
    columns = [c for c in columns if c]

    rows_out: List[Dict[str, Any]] = []
    field_types: Dict[str, str] = {c: "string" for c in columns}

    for raw_row in data_rows[header_idx + 1 :]:
        r = _normalize_row(raw_row)
        if not r or not any(c for c in r):
            continue
        if len(r) < len(columns):
            r = r + [""] * (len(columns) - len(r))

        obj: Dict[str, Any] = {}
        has_employee = False
        for i, col in enumerate(columns):
            val, t = _coerce_value(r[i] if i < len(r) else "")
            obj[col] = val
            if field_types.get(col) == "string" and t in ("number", "percent"):
                field_types[col] = t
            if col.lower() == "employee" and isinstance(val, str) and val.strip():
                has_employee = True
        if has_employee:
            rows_out.append(obj)

    return Dataset(title=title, columns=columns, rows=rows_out, field_types=field_types)

def parse_xlsx_bytes(xlsx_bytes: bytes) -> Dict[str, Any]:
    """Parse XLSX from bytes and return document dict"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        tmp.write(xlsx_bytes)
        tmp_path = tmp.name
    
    try:
        with zipfile.ZipFile(tmp_path, "r") as z:
            shared = _parse_shared_strings(z)
            sheets = _parse_workbook_sheets(z)
            sheet_map: Dict[str, List[List[str]]] = {}
            for name, sheet_path in sheets:
                sheet_map[name] = _parse_sheet_rows(z, sheet_path, shared)

        data_sheet = None
        filters_sheet = None
        for k in sheet_map.keys():
            if k.lower() == "data":
                data_sheet = k
            if k.lower() == "filters":
                filters_sheet = k

        if not data_sheet:
            for k, rows in sheet_map.items():
                if _find_header_row(rows) is not None:
                    data_sheet = k
                    break
        if not data_sheet:
            data_sheet = list(sheet_map.keys())[0]

        dataset = _build_dataset(sheet_map[data_sheet])
        meta = {}
        if filters_sheet and filters_sheet in sheet_map:
            meta = _parse_filters(sheet_map[filters_sheet])

        doc = {
            "meta": meta,
            "dataset": {
                "title": dataset.title,
                "columns": dataset.columns,
                "rows": dataset.rows,
            },
            "fieldTypes": dataset.field_types,
            "source": {
                "dataSheet": data_sheet,
                "filtersSheet": filters_sheet or "",
            },
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        return doc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ============================================================================
# UTILITY FUNCTIONS (from utils.js)
# ============================================================================

def safe_number(v):
    """Convert value to number or return None"""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return v if not (isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf'))) else None
    try:
        n = float(v)
        return n if not (n != n or n == float('inf') or n == float('-inf')) else None
    except:
        return None

def format_percent(v):
    """Format number as percentage"""
    n = safe_number(v)
    if n is None:
        return "—"
    return f"{n:.1f}%"

def format_score(v):
    """Format score with appropriate decimals"""
    n = safe_number(v)
    if n is None:
        return "—"
    if n >= 100:
        return f"{int(n)}"
    return f"{n:.1f}"

def guess_key(columns, candidates):
    """Find column name from candidates (case-insensitive)"""
    lower_map = {c.lower(): c for c in columns}
    for c in candidates:
        hit = lower_map.get(c.lower())
        if hit:
            return hit
    return None

def rank_color(rank):
    """Get color class for rank"""
    if rank == 1:
        return "gold"
    if rank == 2:
        return "silver"
    if rank == 3:
        return "bronze"
    return "neutral"

def normalize_column_name(name):
    """Normalize column name for comparison"""
    return re.sub(r"\s+", " ", str(name or "").strip().lower())

def percent_threshold_for_column(column_name):
    """Get threshold for green/red coloring"""
    key = normalize_column_name(column_name)
    
    if key == "vehicle returned cleaner":
        return 50
    if key == "paperwork <7 minutes":
        return 75
    if key == "advisor provided video":
        return 75
    if key == "escorted to vehicle":
        return 75
    
    return 100

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_circular_progress(value, column_name=""):
    """Render circular progress indicator for percentages"""
    n = safe_number(value)
    if n is None:
        return "—"
    
    clamped = max(0, min(100, n))
    r = 12
    c = 2 * 3.14159 * r
    dash = (clamped / 100) * c
    threshold = percent_threshold_for_column(column_name)
    good = n >= threshold
    pct_color = "#10B981" if good else "#EF4444"
    
    # Return clean HTML without extra whitespace
    svg = f'<div class="progress-container"><svg class="progress-svg" viewBox="0 0 36 36"><circle cx="18" cy="18" r="{r}" fill="none" stroke="#E5E7EB" stroke-width="4"/><circle cx="18" cy="18" r="{r}" fill="none" stroke="{pct_color}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{dash} {c - dash}"/></svg><span class="mono progress-text">{format_percent(n)}</span></div>'
    return svg

def render_score_progress(value):
    """Render circular progress indicator for satisfaction score (out of 1100)"""
    n = safe_number(value)
    if n is None:
        return "—"
    
    # Calculate percentage out of 1100
    percentage = (n / 1100) * 100
    clamped = max(0, min(100, percentage))
    
    r = 12
    c = 2 * 3.14159 * r
    dash = (clamped / 100) * c
    
    # Red if under 895, green otherwise
    score_color = "#EF4444" if n < 895 else "#10B981"
    
    # Display the raw score, not percentage
    score_display = format_score(n)
    
    # Return clean HTML without extra whitespace
    svg = f'<div class="progress-container"><svg class="progress-svg" viewBox="0 0 36 36"><circle cx="18" cy="18" r="{r}" fill="none" stroke="#E5E7EB" stroke-width="4"/><circle cx="18" cy="18" r="{r}" fill="none" stroke="{score_color}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{dash} {c - dash}"/></svg><span class="mono progress-text">{score_display}</span></div>'
    return svg

def render_cell(value, cell_type, column_name=""):
    """Render cell based on type"""
    if cell_type == "percent":
        return render_circular_progress(value, column_name)
    if cell_type == "number":
        n = safe_number(value)
        return f'<span class="mono">{n if n is not None else "—"}</span>'
    return f'<span>{value if value not in ["", None] else "—"}</span>'

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

if 'doc' not in st.session_state:
    # Try to load from storage/latest.json if exists
    storage_path = Path(__file__).parent / 'storage' / 'latest.json'
    if storage_path.exists():
        try:
            with open(storage_path, 'r') as f:
                st.session_state.doc = json.load(f)
        except:
            st.session_state.doc = None
    else:
        st.session_state.doc = None

if 'expanded_rows' not in st.session_state:
    st.session_state.expanded_rows = set()

# ============================================================================
# MAIN APP
# ============================================================================

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("📊 Dashboard" if st.session_state.page == 'upload' else "📊", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()
with col3:
    if st.button("📤 Upload" if st.session_state.page == 'dashboard' else "📤", use_container_width=True):
        st.session_state.page = 'upload'
        st.rerun()

# ============================================================================
# UPLOAD PAGE
# ============================================================================

if st.session_state.page == 'upload':
    st.markdown("<h1 class='dashboard-title'>Upload daily XLSX</h1>", unsafe_allow_html=True)
    st.markdown("<p class='muted dashboard-subtitle'>Choose the exported Tekion file. The dashboard updates immediately.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=['xlsx'], key='xlsx_uploader')
    
    if uploaded_file is not None:
        try:
            with st.spinner('Processing XLSX file...'):
                xlsx_bytes = uploaded_file.read()
                doc = parse_xlsx_bytes(xlsx_bytes)
                
                # Save to session state
                st.session_state.doc = doc
                
                # Save to storage/latest.json
                storage_dir = Path(__file__).parent / 'storage'
                storage_dir.mkdir(exist_ok=True)
                with open(storage_dir / 'latest.json', 'w') as f:
                    json.dump(doc, f, indent=2)
                
                exported = doc.get('meta', {}).get('Exported Raw') or doc.get('meta', {}).get('Exported') or '—'
                st.success(f"✅ Uploaded successfully! Exported: {exported}")
                st.info("Redirecting to dashboard...")
                
                # Auto-redirect after short delay
                import time
                time.sleep(1)
                st.session_state.page = 'dashboard'
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Failed to process file: {str(e)}")

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

else:
    doc = st.session_state.doc
    
    if doc is None:
        st.markdown("<h1 class='dashboard-title'>Advisor Satisfaction</h1>", unsafe_allow_html=True)
        st.info("📂 No data available. Please upload an XLSX file to get started.")
        st.markdown("""
        <div style='padding: var(--spacing-xl); border: 1px solid #E5E7EB; 
                    border-radius: clamp(12px, 1.2vw, 18px); background: #F9FAFB;'>
            <h3 style='font-size: var(--font-name);'>Getting Started</h3>
            <ol style='font-size: var(--font-base); line-height: 1.6;'>
                <li>Click the "Upload" button in the top right</li>
                <li>Select your Tekion Service Employee Rank XLSX file</li>
                <li>The dashboard will load automatically</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Extract data
        meta = doc.get('meta', {})
        dataset = doc.get('dataset', {})
        title = dataset.get('title', 'Advisor Satisfaction')
        columns = dataset.get('columns', [])
        rows = dataset.get('rows', [])
        field_types = doc.get('fieldTypes', {})
        
        # Find key columns
        key_employee = guess_key(columns, ["Employee", "Advisor", "Service Advisor", "Name"])
        key_rank = guess_key(columns, ["Rank"])
        key_score = guess_key(columns, ["Satisfaction Score", "Score"])
        key_impact = guess_key(columns, ["Impact"])
        key_completes = guess_key(columns, ["Completes"])
        key_total = guess_key(columns, ["Total Records", "Total"])
        key_dealer = guess_key(columns, ["Dealer"])
        key_area = guess_key(columns, ["Area"])
        key_region = guess_key(columns, ["Region"])
        
        # Additional columns for collapsed view
        key_fixed_first = guess_key(columns, ["Fixed right first time"])
        key_spoke_immediately = guess_key(columns, ["Spoke to advisor immediately"])
        key_kept_informed = guess_key(columns, ["Kept informed"])
        
        # Sort by rank
        sorted_rows = sorted(rows, key=lambda r: safe_number(r.get(key_rank)) if key_rank else float('inf'))
        sorted_rows = [r for r in sorted_rows if safe_number(r.get(key_rank) if key_rank else None) is not None]
        
        # Header info
        level = meta.get('Level', '')
        dealer_number = ""
        dealer_name = ""
        if ' - ' in level:
            parts = level.split(' - ', 1)
            dealer_number = parts[0].strip()
            dealer_name = parts[1].strip()
        else:
            dealer_name = level.strip()
        
        first_row = sorted_rows[0] if sorted_rows else {}
        area = str(first_row.get(key_area, '')).strip() if key_area else ""
        region = str(first_row.get(key_region, '')).strip() if key_region else ""
        if not dealer_number and key_dealer:
            dealer_number = str(first_row.get(key_dealer, '')).strip()
        
        # Header
        st.markdown(f"<h1 class='dashboard-title'>{title}</h1>", unsafe_allow_html=True)
        
        subtitle_parts = []
        if dealer_number:
            subtitle_parts.append(f"Dealer: {dealer_number}")
        if dealer_name:
            subtitle_parts.append(dealer_name)
        if area:
            subtitle_parts.append(f"Area: {area}")
        if region:
            subtitle_parts.append(f"Region: {region}")
        subtitle_parts.append("Period: 1D")
        
        subtitle = " <span class='dot'>•</span> ".join(subtitle_parts)
        st.markdown(f"<p class='muted dashboard-subtitle'>{subtitle}</p>", unsafe_allow_html=True)
        
        exported_display = meta.get('Exported Raw') or meta.get('Exported') or '—'
        st.markdown(f"<p class='muted dashboard-subtitle'>Last update: <strong>{exported_display}</strong></p>", unsafe_allow_html=True)
        
        # Detail columns (exclude only collapsed view fields and metadata)
        exclude = set([key_employee, key_dealer, key_area, key_region, key_rank, key_score, key_fixed_first, key_spoke_immediately, key_kept_informed])
        exclude = {c for c in exclude if c}
        detail_columns = [c for c in columns if c not in exclude]
        
        # Leaderboard
        if not sorted_rows:
            st.warning("No advisor data found in the uploaded file.")
        else:
            for idx, row in enumerate(sorted_rows):
                rank = safe_number(row.get(key_rank) if key_rank else None)
                name = row.get(key_employee) if key_employee else "—"
                score = row.get(key_score) if key_score else None
                impact = row.get(key_impact) if key_impact else None
                completes = row.get(key_completes) if key_completes else None
                total = row.get(key_total) if key_total else None
                
                # Unique ID for expander
                row_id = f"{rank}_{name}_{idx}"
                
                # Rank styling - all dividers now gray
                rank_class = rank_color(rank)
                border_color = "#E5E7EB"
                
                # Card container with responsive classes
                with st.container():
                    st.markdown(f"""
                    <div class='advisor-card' style='border: 2px solid {border_color}; 
                                background: linear-gradient(180deg, #FFFFFF, #F9FAFB);'>
                    """, unsafe_allow_html=True)
                    
                    # Get values for collapsed view metrics
                    fixed_first = row.get(key_fixed_first) if key_fixed_first else None
                    spoke_immediately = row.get(key_spoke_immediately) if key_spoke_immediately else None
                    kept_informed = row.get(key_kept_informed) if key_kept_informed else None
                    
                    # Get field types for rendering
                    fixed_first_type = field_types.get(key_fixed_first, 'string') if key_fixed_first else 'string'
                    spoke_immediately_type = field_types.get(key_spoke_immediately, 'string') if key_spoke_immediately else 'string'
                    kept_informed_type = field_types.get(key_kept_informed, 'string') if key_kept_informed else 'string'
                    
                    # Header row (always visible) - using responsive layout
                    col_rank, col_name, col_score, col_fixed, col_spoke, col_kept, col_expand = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5, 0.5], gap="small")
                    
                    with col_rank:
                        st.markdown(f"<div class='advisor-rank' style='padding: var(--spacing-sm) var(--spacing-xs);'>#{int(rank) if rank else '—'}</div>", unsafe_allow_html=True)
                    with col_name:
                        st.markdown(f"<div class='advisor-name' style='padding: var(--spacing-sm) var(--spacing-xs);'>{name}</div>", unsafe_allow_html=True)
                    with col_score:
                        score_rendered = render_score_progress(score)
                        st.markdown(f"""
                        <div class='metric-chip'>
                            <div class='chip-label'>Satisfaction Score</div>
                            <div>{score_rendered}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_fixed:
                        if fixed_first_type == 'percent':
                            rendered_value = render_circular_progress(fixed_first, key_fixed_first or "")
                        else:
                            rendered_value = f'<span class="mono chip-value">{safe_number(fixed_first) if safe_number(fixed_first) is not None else "—"}</span>'
                        st.markdown(f"""
                        <div class='metric-chip'>
                            <div class='chip-label'>Fixed right first time</div>
                            <div>{rendered_value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_spoke:
                        if spoke_immediately_type == 'percent':
                            rendered_value = render_circular_progress(spoke_immediately, key_spoke_immediately or "")
                        else:
                            rendered_value = f'<span class="mono chip-value">{safe_number(spoke_immediately) if safe_number(spoke_immediately) is not None else "—"}</span>'
                        st.markdown(f"""
                        <div class='metric-chip'>
                            <div class='chip-label'>Spoke to advisor immediately</div>
                            <div>{rendered_value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_kept:
                        if kept_informed_type == 'percent':
                            rendered_value = render_circular_progress(kept_informed, key_kept_informed or "")
                        else:
                            rendered_value = f'<span class="mono chip-value">{safe_number(kept_informed) if safe_number(kept_informed) is not None else "—"}</span>'
                        st.markdown(f"""
                        <div class='metric-chip'>
                            <div class='chip-label'>Kept informed</div>
                            <div>{rendered_value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_expand:
                        is_expanded = row_id in st.session_state.expanded_rows
                        if st.button("▾" if is_expanded else "▸", key=f"expand_{row_id}"):
                            if is_expanded:
                                st.session_state.expanded_rows.remove(row_id)
                            else:
                                st.session_state.expanded_rows.add(row_id)
                            st.rerun()
                    
                    # Expanded details with responsive grid
                    if row_id in st.session_state.expanded_rows:
                        # Build entire grid HTML as single string to preserve CSS grid layout
                        grid_html = "<div class='kpi-grid-container'><div class='kpi-grid'>"
                        
                        # KPI Grid - responsive auto-fit layout
                        for col_name in detail_columns:
                            value = row.get(col_name)
                            cell_type = field_types.get(col_name, 'string')
                            rendered = render_cell(value, cell_type, col_name)
                            
                            # Escape HTML in column name to prevent breaking the layout
                            safe_col_name = str(col_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                            
                            # Build card HTML - single line to avoid whitespace issues
                            grid_html += f"<div class='kpi-card'><div class='kpi-label'>{safe_col_name}</div><div class='kpi-value'>{rendered}</div></div>"
                        
                        grid_html += "</div></div>"
                        st.markdown(grid_html, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<p class='muted' style='text-align: center; font-size: 12px;'>Advisor Satisfaction Dashboard • Streamlit Version</p>", unsafe_allow_html=True)

