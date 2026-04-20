from __future__ import annotations

from pathlib import Path
import csv


def load_script_order(path: Path) -> dict[str, int]:
    """Return filename->order from CSV/XLSX/TXT.

    First column is used; header row is ignored when present.
    """
    ext = path.suffix.lower()
    entries: list[str] = []

    if ext == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    entries.append(row[0].strip())
    elif ext in {".xlsx", ".xls"}:
        try:
            import openpyxl  # type: ignore
        except ImportError as exc:
            raise RuntimeError("To read Excel files install openpyxl: pip install openpyxl") from exc

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_col=1, max_col=1, values_only=True):
            val = row[0]
            if val is not None and str(val).strip():
                entries.append(str(val).strip())
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(line)

    if entries and entries[0].lower() in {"name", "filename", "file", "audio"}:
        entries = entries[1:]

    order: dict[str, int] = {}
    for idx, e in enumerate(entries):
        order[e.lower()] = idx
    return order
