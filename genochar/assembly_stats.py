from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Tuple

from .utils import infer_strain_name, open_maybe_gzip


@dataclass
class AssemblyStats:
    Strain: str
    assembly_path: str
    genome_size_bp: int
    contigs: int
    gc_percent: float
    n50_bp: int
    n90_bp: int
    l50: int
    l90: int
    longest_contig_bp: int
    n_count: int
    gaps_n_per_100kb: float
    circularity: str


def iter_fasta_records(path: Path | str) -> Iterator[Tuple[str, str]]:
    header = None
    chunks: List[str] = []
    with open_maybe_gzip(path, "rt") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(chunks)
                header = line[1:].strip()
                chunks = []
            else:
                chunks.append(line)
    if header is not None:
        yield header, "".join(chunks)


def calc_nx(lengths: List[int], fraction: float) -> int:
    if not lengths:
        return 0
    total = sum(lengths)
    threshold = total * fraction
    running = 0
    for length in sorted(lengths, reverse=True):
        running += length
        if running >= threshold:
            return length
    return 0


def calc_lx(lengths: List[int], fraction: float) -> int:
    if not lengths:
        return 0
    total = sum(lengths)
    threshold = total * fraction
    running = 0
    for idx, length in enumerate(sorted(lengths, reverse=True), start=1):
        running += length
        if running >= threshold:
            return idx
    return 0


def header_is_circular(header: str) -> bool:
    h = header.lower()
    patterns = [
        r"circular\s*=\s*(true|yes|1)",
        r"topology\s*=\s*circular",
        r"\[topology=circular\]",
        r"\[circular=true\]",
        r"\bcircular\b",
    ]
    return any(re.search(p, h) for p in patterns)


def detect_circularity(headers: List[str], contigs: int) -> str:
    if not headers:
        return "not detected"
    circular_count = sum(1 for h in headers if header_is_circular(h))
    if circular_count == 0:
        return "not detected"
    if circular_count == contigs:
        return "detected (all contigs)"
    return f"detected ({circular_count}/{contigs} contigs)"


def compute_assembly_stats(path: Path | str) -> AssemblyStats:
    strain = infer_strain_name(path)
    lengths: List[int] = []
    headers: List[str] = []
    gc = 0
    atgc = 0
    n_count = 0

    for header, seq in iter_fasta_records(path):
        headers.append(header)
        seq_upper = seq.upper()
        lengths.append(len(seq_upper))
        gc += seq_upper.count("G") + seq_upper.count("C")
        atgc += sum(seq_upper.count(base) for base in "ATGC")
        n_count += seq_upper.count("N")

    genome_size = sum(lengths)
    contigs = len(lengths)
    gc_percent = (gc / atgc * 100) if atgc else 0.0
    longest = max(lengths) if lengths else 0
    n50 = calc_nx(lengths, 0.5)
    n90 = calc_nx(lengths, 0.9)
    l50 = calc_lx(lengths, 0.5)
    l90 = calc_lx(lengths, 0.9)
    circularity = detect_circularity(headers, contigs)
    gaps_n_per_100kb = (n_count / genome_size * 100000) if genome_size else 0.0

    return AssemblyStats(
        Strain=strain,
        assembly_path=str(path),
        genome_size_bp=genome_size,
        contigs=contigs,
        gc_percent=gc_percent,
        n50_bp=n50,
        n90_bp=n90,
        l50=l50,
        l90=l90,
        longest_contig_bp=longest,
        n_count=n_count,
        gaps_n_per_100kb=gaps_n_per_100kb,
        circularity=circularity,
    )


def infer_genome_status(contigs: int, circularity: str) -> str:
    if contigs == 1 and circularity != "not detected":
        return "Complete genome"
    return "Draft genome"


def assembly_stats_to_row(stats: AssemblyStats) -> dict:
    return {
        "Strain": stats.Strain,
        "Genome size (bp)": stats.genome_size_bp,
        "GC content (%)": round(stats.gc_percent, 2),
        "No. of contigs": stats.contigs,
        "N50 (bp)": stats.n50_bp,
        "N90 (bp)": stats.n90_bp,
        "L50": stats.l50,
        "L90": stats.l90,
        "Longest contig (bp)": stats.longest_contig_bp,
        "Gaps (N per 100 kb)": round(stats.gaps_n_per_100kb, 2),
        "Circularity": stats.circularity,
        "Genome status": infer_genome_status(stats.contigs, stats.circularity),
        "_assembly_path": stats.assembly_path,
    }
