from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Mapping

from .utils import canonicalize_name, find_column, open_maybe_gzip, parse_numeric, sniff_delimiter


def parse_coverage_table(
    path: Path | str,
    assembly_size_map: Mapping[str, int] | None = None,
) -> Dict[str, dict]:
    delimiter = sniff_delimiter(path)
    with open_maybe_gzip(path, "rt") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            return {}

        name_col = find_column(reader.fieldnames, ["Strain", "Sample", "Genome", "Bin", "Name"])
        coverage_col = find_column(
            reader.fieldnames,
            ["Sequencing coverage (×)", "Sequencing coverage (x)", "Coverage (×)", "Coverage", "Depth"],
        )
        total_bases_col = find_column(reader.fieldnames, ["Total bases", "Total Bases", "Bases", "Mbp", "Total bp"])

        if not name_col:
            raise ValueError(f"Could not identify the strain/name column in coverage file: {path}")

        out: Dict[str, dict] = {}
        for row in reader:
            name = canonicalize_name(str(row.get(name_col, "")).strip())
            if not name:
                continue

            coverage = None
            if coverage_col:
                coverage = parse_numeric(row.get(coverage_col))
            elif total_bases_col:
                total_bases = parse_numeric(row.get(total_bases_col))
                assembly_size = assembly_size_map.get(name) if assembly_size_map else None
                if total_bases is not None and assembly_size:
                    coverage = total_bases / assembly_size

            out[name] = {
                "Sequencing coverage (×)": round(coverage, 2) if coverage is not None else None,
            }
        return out
