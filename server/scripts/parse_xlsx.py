#!/usr/bin/env python3
"""
Parse Tekion-exported XLSX (Office Open XML) using Python stdlib only.

Usage:
  python3 parse_xlsx.py /path/to/input.xlsx /path/to/output.json
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
    # Trim trailing empty cells
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
        # ints should remain ints
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

    # Best-effort normalize Exported to ISO
    exported = meta.get("Exported")
    if isinstance(exported, str) and exported.strip():
        raw = exported.strip()
        meta["Exported Raw"] = raw
        # Example: "Dec 22 2025  5:17:17:583PM"
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
    # best-effort title: previous non-empty single-cell row
    for j in range(header_idx - 1, -1, -1):
        r = _normalize_row(data_rows[j])
        if len(r) == 1 and r[0]:
            title = r[0]
            break
    if not title:
        title = "Service Employee Rank"

    columns = _normalize_row(data_rows[header_idx])
    # remove empty column names
    columns = [c for c in columns if c]

    rows_out: List[Dict[str, Any]] = []
    field_types: Dict[str, str] = {c: "string" for c in columns}

    for raw_row in data_rows[header_idx + 1 :]:
        r = _normalize_row(raw_row)
        if not r or not any(c for c in r):
            continue
        # pad to columns length
        if len(r) < len(columns):
            r = r + [""] * (len(columns) - len(r))

        obj: Dict[str, Any] = {}
        has_employee = False
        for i, col in enumerate(columns):
            val, t = _coerce_value(r[i] if i < len(r) else "")
            obj[col] = val
            # promote type if more specific
            if field_types.get(col) == "string" and t in ("number", "percent"):
                field_types[col] = t
            if col.lower() == "employee" and isinstance(val, str) and val.strip():
                has_employee = True
        if has_employee:
            rows_out.append(obj)

    return Dataset(title=title, columns=columns, rows=rows_out, field_types=field_types)


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("Usage: parse_xlsx.py input.xlsx output.json", file=sys.stderr)
        return 2

    in_path = Path(argv[1]).expanduser().resolve()
    out_path = Path(argv[2]).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(str(in_path))

    with zipfile.ZipFile(in_path, "r") as z:
        shared = _parse_shared_strings(z)
        sheets = _parse_workbook_sheets(z)
        sheet_map: Dict[str, List[List[str]]] = {}
        for name, sheet_path in sheets:
            sheet_map[name] = _parse_sheet_rows(z, sheet_path, shared)

    data_sheet = None
    filters_sheet = None
    # Prefer expected names, else fallback
    for k in sheet_map.keys():
        if k.lower() == "data":
            data_sheet = k
        if k.lower() == "filters":
            filters_sheet = k

    if not data_sheet:
        # pick first sheet that looks like it has Employee+Rank
        for k, rows in sheet_map.items():
            if _find_header_row(rows) is not None:
                data_sheet = k
                break
    if not data_sheet:
        # last resort: first sheet
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
            "filename": in_path.name,
        },
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


