from __future__ import annotations

import csv
import glob
import gzip
import os
import re
from pathlib import Path
from typing import Dict, List, Sequence


FASTA_SUFFIXES = (
    ".fa", ".fna", ".fasta", ".fas", ".fa.gz", ".fna.gz", ".fasta.gz", ".fas.gz"
)
GFF_SUFFIXES = (".gff", ".gff3", ".gff.gz", ".gff3.gz")
GENERIC_BASENAMES = {"assembly", "contigs", "scaffolds", "genome", "sequences"}
TRAILING_SUFFIX_PATTERNS = [
    r"_unicycler$",
    r"_prokka$",
    r"_bakta$",
    r"_annotation$",
    r"_annotations$",
    r"_assembly$",
    r"_assemblies$",
    r"_contigs$",
]
_COMPLEMENT = str.maketrans(
    "ACGTRYMKHBVDNacgtrymkhbvdn",
    "TGCAYRKMVDHBNtgcayrkmvdhbn",
)


def open_maybe_gzip(path: os.PathLike[str] | str, mode: str = "rt"):
    path = str(path)
    if path.endswith(".gz"):
        return gzip.open(path, mode)
    return open(path, mode)


def strip_known_extensions(name: str) -> str:
    for suffix in [
        ".fasta.gz", ".fna.gz", ".fa.gz", ".fas.gz",
        ".gff3.gz", ".gff.gz", ".fasta", ".fna", ".fa", ".fas",
        ".gff3", ".gff", ".tsv", ".csv", ".txt",
    ]:
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return name


def canonicalize_name(name: str) -> str:
    base = strip_known_extensions(name)
    for pattern in TRAILING_SUFFIX_PATTERNS:
        base = re.sub(pattern, "", base, flags=re.IGNORECASE)
    return base


def infer_strain_name(path: os.PathLike[str] | str) -> str:
    p = Path(path)
    base = canonicalize_name(p.name)
    if base.lower() in GENERIC_BASENAMES:
        parent = canonicalize_name(p.parent.name)
        if parent:
            return parent
    return base


def looks_like_fasta(path: os.PathLike[str] | str) -> bool:
    s = str(path).lower()
    return any(s.endswith(sfx) for sfx in FASTA_SUFFIXES)


def looks_like_gff(path: os.PathLike[str] | str) -> bool:
    s = str(path).lower()
    return any(s.endswith(sfx) for sfx in GFF_SUFFIXES)


def resolve_inputs(items: Sequence[str], kind: str = "any") -> List[Path]:
    resolved: List[Path] = []
    for item in items:
        if any(ch in item for ch in ["*", "?", "["]):
            for matched in sorted(glob.glob(item, recursive=True)):
                p = Path(matched)
                if p.is_file():
                    resolved.append(p.resolve())
            continue

        p = Path(item)
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if not child.is_file():
                    continue
                if kind == "fasta" and looks_like_fasta(child):
                    resolved.append(child.resolve())
                elif kind == "gff" and looks_like_gff(child):
                    resolved.append(child.resolve())
                elif kind == "any":
                    resolved.append(child.resolve())
            continue

        if p.is_file():
            resolved.append(p.resolve())

    seen = set()
    unique: List[Path] = []
    for p in resolved:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def ensure_parent(path: os.PathLike[str] | str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def sniff_delimiter(path: os.PathLike[str] | str) -> str:
    with open_maybe_gzip(path, "rt") as handle:
        sample = handle.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        return dialect.delimiter
    except csv.Error:
        return "\t" if "\t" in sample else ","


def normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", header.strip().lower())


def find_column(headers: Sequence[str], candidates: Sequence[str]) -> str | None:
    normalized = {normalize_header(h): h for h in headers}
    candidate_norms = [normalize_header(c) for c in candidates]
    for cand in candidate_norms:
        if cand in normalized:
            return normalized[cand]
    for h in headers:
        nh = normalize_header(h)
        for cand in candidate_norms:
            if cand in nh:
                return h
    return None


def parse_numeric(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text.lower() in {"na", "nan", "none", "nd", "notdetected"}:
        return None

    text = text.replace(",", "").replace("×", "").strip()
    lower = text.lower()

    multiplier = 1.0
    unit_map = {
        "gbp": 1e9,
        "gb": 1e9,
        "g": 1e9,
        "mbp": 1e6,
        "mb": 1e6,
        "m": 1e6,
        "kbp": 1e3,
        "kb": 1e3,
        "k": 1e3,
        "bp": 1.0,
        "x": 1.0,
    }
    for suffix, mult in unit_map.items():
        if lower.endswith(suffix):
            multiplier = mult
            lower = lower[: -len(suffix)].strip()
            break

    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", lower)
    if not match:
        return None
    return float(match.group()) * multiplier


def pretty_float(value: float | None, digits: int = 2) -> str | None:
    if value is None:
        return None
    return f"{value:.{digits}f}"


def pretty_int(value: int | float | None) -> str | None:
    if value is None:
        return None
    return f"{int(value):,}"


def reverse_complement(seq: str) -> str:
    return seq.translate(_COMPLEMENT)[::-1]


def read_fasta_dict(path: os.PathLike[str] | str) -> Dict[str, str]:
    records: Dict[str, str] = {}
    current_id: str | None = None
    chunks: List[str] = []
    with open_maybe_gzip(path, "rt") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    records[current_id] = "".join(chunks)
                current_id = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
        if current_id is not None:
            records[current_id] = "".join(chunks)
    return records


def match_strain_name(name: str, known_names: Sequence[str]) -> str:
    can = canonicalize_name(name)
    for item in known_names:
        if canonicalize_name(item) == can:
            return item
    return name
