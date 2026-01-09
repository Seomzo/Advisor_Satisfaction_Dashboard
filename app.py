"""
Advisor Satisfaction Dashboard - Streamlit App
Full-screen dashboard for Tekion Service Employee Rank Excel exports.
"""

import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from streamlit.components.v1 import html

# Excel parsing namespace
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

# Initialize session state
if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None


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


def parse_xlsx_file(file_bytes: bytes) -> Dict[str, Any]:
    """Parse Excel file from bytes and return dashboard data structure."""
    with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
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
            "filename": "uploaded.xlsx",
        },
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    return doc


def safe_number(v) -> Optional[float]:
    """Safely convert value to number."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v) if (isinstance(v, float) or isinstance(v, int)) else None
    try:
        n = float(v)
        return n if not (n != n or abs(n) == float("inf")) else None
    except (ValueError, TypeError):
        return None


def format_percent(v) -> str:
    """Format number as percentage."""
    n = safe_number(v)
    if n is None:
        return "—"
    return f"{n:.1f}%"


def format_score(v) -> str:
    """Format satisfaction score."""
    n = safe_number(v)
    if n is None:
        return "—"
    if n >= 100:
        return f"{n:.0f}"
    return f"{n:.1f}"


def guess_key(columns: List[str], candidates: List[str]) -> Optional[str]:
    """Find column name matching candidates (case-insensitive)."""
    lower_map = {c.lower(): c for c in columns}
    for candidate in candidates:
        hit = lower_map.get(candidate.lower())
        if hit:
            return hit
    return None


def rank_color(rank: Optional[int]) -> str:
    """Get color class for rank."""
    if rank == 1:
        return "gold"
    if rank == 2:
        return "silver"
    if rank == 3:
        return "bronze"
    return "neutral"


def percent_threshold_for_column(column_name: str) -> float:
    """Get threshold for percentage column (green if >= threshold)."""
    key = column_name.lower().strip().replace("  ", " ")
    if key == "vehicle returned cleaner":
        return 50
    if key == "paperwork <7 minutes":
        return 75
    if key == "advisor provided video":
        return 75
    if key == "escorted to vehicle":
        return 75
    return 100


def render_percent_cell(value, column_name: str) -> str:
    """Render percentage cell with color indicator."""
    n = safe_number(value)
    if n is None:
        return "—"
    threshold = percent_threshold_for_column(column_name)
    good = n >= threshold
    color = "#38d996" if good else "#ff6b6b"
    return f'<span style="color: {color}">{format_percent(n)}</span>'


def render_cell(value, field_type: str, column_name: str) -> str:
    """Render cell value based on field type."""
    if field_type == "percent":
        return render_percent_cell(value, column_name)
    if field_type == "number":
        n = safe_number(value)
        return f'<span class="mono">{n if n is not None else "—"}</span>'
    if value == "" or value is None:
        return "—"
    return str(value)


# Custom CSS
st.markdown(
    """
    <style>
    :root {
        --bg0: #070A14;
        --bg1: #0B1026;
        --card: #0E1636cc;
        --text: #EAF0FF;
        --muted: #A7B3DA;
        --gold: #F6C356;
        --silver: #C7D2E7;
        --bronze: #E49A6A;
        --good: #38d996;
        --bad: #ff6b6b;
    }
    
    .stApp {
        background: radial-gradient(1200px 800px at 20% 10%, #1a2a6c55, transparent 60%),
                     radial-gradient(900px 700px at 90% 20%, #b21f1f33, transparent 55%),
                     radial-gradient(900px 700px at 60% 90%, #fdbb2d22, transparent 55%),
                     linear-gradient(160deg, var(--bg0), var(--bg1));
        color: var(--text);
    }
    
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 20px 26px;
        border-bottom: 1px solid #ffffff14;
        margin-bottom: 20px;
    }
    
    .title-block {
        min-width: 0;
    }
    
    .title-row {
        display: flex;
        gap: 12px;
        align-items: center;
    }
    
    .title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: .2px;
        color: var(--text);
    }
    
    .subtitle {
        margin-top: 6px;
        font-size: 13px;
        opacity: .95;
        color: var(--muted);
    }
    
    .status-line {
        display: flex;
        gap: 10px;
        align-items: baseline;
        font-size: 13px;
    }
    
    .status-value {
        font-weight: 700;
        color: var(--text);
    }
    
    .advisor-card {
        border: 1px solid #ffffff14;
        border-radius: 16px;
        background: linear-gradient(180deg, #0c1436cc, #0b1230cc);
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0 25px 60px #00000055;
    }
    
    .advisor-card.gold {
        border-color: #f6c35655;
    }
    
    .advisor-card.silver {
        border-color: #c7d2e755;
    }
    
    .advisor-card.bronze {
        border-color: #e49a6a55;
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        padding: 8px;
    }
    
    .card-left {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
    }
    
    .rank-small {
        font-weight: 950;
        font-size: 18px;
        opacity: .95;
        width: 56px;
    }
    
    .name-small {
        font-weight: 950;
        font-size: 18px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .card-right {
        display: grid;
        grid-template-columns: repeat(4, minmax(140px, 1fr));
        gap: 10px;
        align-items: center;
    }
    
    .chip {
        border: 1px solid #ffffff18;
        border-radius: 999px;
        padding: 6px 10px;
        background: #0b1230aa;
        display: flex;
        align-items: baseline;
        justify-content: space-between;
    }
    
    .chip-label {
        font-size: 11px;
        color: var(--muted);
    }
    
    .chip-value {
        font-size: 13px;
        font-weight: 800;
        text-align: right;
    }
    
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 10px 12px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #ffffff12;
    }
    
    .kpi-item {
        border: 1px solid #ffffff12;
        border-radius: 14px;
        padding: 10px;
        background: #0b1230aa;
    }
    
    .kpi-label {
        font-size: 11px;
        color: var(--muted);
        margin-bottom: 6px;
    }
    
    .kpi-value {
        font-size: 13px;
        font-weight: 800;
    }
    
    .mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    
    .muted {
        color: var(--muted);
    }
    
    .dot {
        opacity: .7;
        margin: 0 .5rem;
    }
    
    /* Streamlit expander styling */
    .streamlit-expanderHeader {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    .streamlit-expanderContent {
        padding: 0 !important;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Make expander look like our card */
    div[data-testid="stExpander"] {
        margin-bottom: 10px;
    }
    
    div[data-testid="stExpander"] > div {
        background: transparent !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_dashboard(doc: Dict[str, Any]):
    """Render the main dashboard."""
    meta = doc.get("meta", {})
    dataset = doc.get("dataset", {})
    title = dataset.get("title", "Advisor Satisfaction")
    columns = dataset.get("columns", [])
    rows = dataset.get("rows", [])
    field_types = doc.get("fieldTypes", {})

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

    # Sort rows by rank
    sorted_rows = sorted(
        rows,
        key=lambda r: safe_number(r.get(key_rank) if key_rank else None) or float("inf"),
    )

    # Header info
    level = meta.get("Level", "")
    dealer_number = ""
    dealer_name = ""
    if " - " in level:
        parts = level.split(" - ", 1)
        dealer_number = parts[0].strip()
        dealer_name = parts[1].strip() if len(parts) > 1 else ""
    else:
        dealer_name = level.strip()

    first_row = sorted_rows[0] if sorted_rows else {}
    area = str(first_row.get(key_area, "")).strip() if key_area else ""
    region = str(first_row.get(key_region, "")).strip() if key_region else ""
    if not dealer_number and key_dealer:
        dealer_number = str(first_row.get(key_dealer, "")).strip()

    # Header
    st.markdown(
        f"""
        <div class="main-header">
            <div class="title-block">
                <div class="title-row">
                    <div class="title">{title}</div>
                </div>
                <div class="subtitle">
                    <span class="muted">{f'Dealer: {dealer_number}' if dealer_number else 'Dealer'}</span>
                    {'<span class="dot">•</span>' if dealer_name else ''}
                    <span class="muted">{dealer_name}</span>
                    {'<span class="dot">•</span>' if area else ''}
                    <span class="muted">{f'Area: {area}' if area else ''}</span>
                    {'<span class="dot">•</span>' if region else ''}
                    <span class="muted">{f'Region: {region}' if region else ''}</span>
                    <span class="dot">•</span>
                    <span class="muted">Period: 1D</span>
                </div>
            </div>
            <div class="status-line">
                <span class="muted">Last update</span>
                <span class="status-value">{meta.get('Exported Raw', meta.get('Exported', '—'))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detail columns (exclude main columns)
    exclude_cols = {
        key_employee,
        key_dealer,
        key_area,
        key_region,
        key_rank,
        key_score,
        key_impact,
        key_total,
        key_completes,
    }
    detail_columns = [c for c in columns if c not in exclude_cols and c]

    # Render advisor cards
    for idx, row in enumerate(sorted_rows):
        rank = safe_number(row.get(key_rank) if key_rank else None)
        name = str(row.get(key_employee, "")) if key_employee else ""
        score = row.get(key_score) if key_score else None
        impact = row.get(key_impact) if key_impact else None
        completes = row.get(key_completes) if key_completes else None
        total = row.get(key_total) if key_total else None

        color_class = rank_color(rank)
        rank_display = f"#{rank}" if rank is not None else "#—"
        name_display = name if name else "—"
        
        # Summary row HTML
        summary_html = f"""
        <div class="advisor-card {color_class}">
            <div class="card-header">
                <div class="card-left">
                    <div class="rank-small">{rank_display}</div>
                    <div class="name-small">{name_display}</div>
                </div>
                <div class="card-right">
                    <div class="chip">
                        <div class="chip-label">Satisfaction Score</div>
                        <div class="chip-value">{format_score(score)}</div>
                    </div>
                    <div class="chip">
                        <div class="chip-label">Impact</div>
                        <div class="chip-value">{safe_number(impact) if impact is not None else '—'}</div>
                    </div>
                    <div class="chip">
                        <div class="chip-label">Records</div>
                        <div class="chip-value">{safe_number(total) if total is not None else '—'}</div>
                    </div>
                    <div class="chip">
                        <div class="chip-label">Completes</div>
                        <div class="chip-value">{safe_number(completes) if completes is not None else '—'}</div>
                    </div>
                </div>
            </div>
        """
        
        # Show summary always visible
        st.markdown(summary_html, unsafe_allow_html=True)
        
        # Use expander for details only
        expander_label = f"View Details"
        with st.expander(expander_label, expanded=False):
            # Detail KPIs
            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            detail_cols = st.columns(3)
            for i, detail_col in enumerate(detail_columns):
                col_idx = i % 3
                with detail_cols[col_idx]:
                    value = row.get(detail_col, "")
                    field_type = field_types.get(detail_col, "string")
                    rendered = render_cell(value, field_type, detail_col)
                    st.markdown(
                        f"""
                        <div class="kpi-item">
                            <div class="kpi-label">{detail_col}</div>
                            <div class="kpi-value">{rendered}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing between cards


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Advisor Satisfaction Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Sidebar for file upload
    with st.sidebar:
        st.title("📤 Upload Excel File")
        uploaded_file = st.file_uploader(
            "Choose a Tekion Excel file (.xlsx)",
            type=["xlsx"],
            help="Upload the daily Tekion Service Employee Rank export",
        )

        if uploaded_file is not None:
            try:
                with st.spinner("Parsing Excel file..."):
                    file_bytes = uploaded_file.read()
                    doc = parse_xlsx_file(file_bytes)
                    st.session_state.dashboard_data = doc
                    st.success("File uploaded successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing file: {str(e)}")

    # Main content
    if st.session_state.dashboard_data:
        render_dashboard(st.session_state.dashboard_data)
    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 60px 20px;">
                <h1 style="color: var(--text); margin-bottom: 20px;">Advisor Satisfaction Dashboard</h1>
                <p style="color: var(--muted); font-size: 18px;">
                    Upload a Tekion Excel file (.xlsx) to get started.
                </p>
                <p style="color: var(--muted); font-size: 14px; margin-top: 10px;">
                    Use the sidebar to upload your daily Service Employee Rank export.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

