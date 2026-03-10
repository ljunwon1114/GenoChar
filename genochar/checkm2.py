from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from .utils import canonicalize_name, find_column, open_maybe_gzip, parse_numeric, sniff_delimiter


def parse_checkm2_report(path: Path | str) -> Dict[str, dict]:
    delimiter = sniff_delimiter(path)
    with open_maybe_gzip(path, "rt") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            return {}

        name_col = find_column(reader.fieldnames, ["Name", "Bin Id", "Bin", "Genome", "Sample", "Strain"])
        completeness_col = find_column(reader.fieldnames, ["Completeness", "Completeness (%)"])
        contamination_col = find_column(reader.fieldnames, ["Contamination", "Contamination (%)"])

        if not name_col:
            raise ValueError(f"Could not identify the strain/name column in CheckM2 file: {path}")

        out: Dict[str, dict] = {}
        for row in reader:
            name = canonicalize_name(str(row.get(name_col, "")).strip())
            if not name:
                continue
            completeness = parse_numeric(row.get(completeness_col)) if completeness_col else None
            contamination = parse_numeric(row.get(contamination_col)) if contamination_col else None
            out[name] = {
                "Completeness (%)": round(completeness, 2) if completeness is not None else None,
                "Contamination (%)": round(contamination, 2) if contamination is not None else None,
            }
        return out
