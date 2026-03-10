from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd

from . import __version__
from .assembly_stats import compute_assembly_stats, assembly_stats_to_row, infer_genome_status
from .checkm2 import parse_checkm2_report
from .coverage import parse_coverage_table
from .gff_stats import gff_stats_to_row, parse_gff_stats
from .metadata import parse_metadata_table
from .pipeline import PipelineError, find_existing_gffs, run_bakta, run_prokka
from .utils import (
    canonicalize_name,
    ensure_parent,
    looks_like_fasta,
    looks_like_gff,
    pretty_float,
    pretty_int,
    resolve_inputs,
)


WIDE_COLUMNS = [
    "Strain",
    "Strain name",
    "Genome size (bp)",
    "GC content (%)",
    "No. of contigs",
    "N50 (bp)",
    "N90 (bp)",
    "L50",
    "L90",
    "Longest contig (bp)",
    "Gaps (N per 100 kb)",
    "Sequencing coverage (×)",
    "Sequencing platforms",
    "Assembly method",
    "Genome status",
    "CDSs",
    "tRNAs",
    "rRNAs",
    "tmRNA",
    "Repeat regions",
    "16S rRNA count",
    "16S rRNA length (bp)",
    "16S rRNA contig",
    "16S rRNA sequence",
    "Completeness (%)",
    "Contamination (%)",
    "Circularity",
]

FEATURE_ORDER = [
    "Strain name",
    "Genome size (bp)",
    "GC content (%)",
    "No. of contigs",
    "N50 (bp)",
    "N90 (bp)",
    "L50",
    "L90",
    "Longest contig (bp)",
    "Gaps (N per 100 kb)",
    "Sequencing coverage (×)",
    "Sequencing platforms",
    "Assembly method",
    "Genome status",
    "CDSs",
    "tRNAs",
    "rRNAs",
    "tmRNA",
    "Repeat regions",
    "16S rRNA count",
    "16S rRNA length (bp)",
    "16S rRNA contig",
    "16S rRNA sequence",
    "Completeness (%)",
    "Contamination (%)",
    "Circularity",
]


def resolve_assemblies(paths: Sequence[str]) -> List[Path]:
    found = [p for p in resolve_inputs(paths, kind="fasta") if looks_like_fasta(p)]
    if not found:
        raise SystemExit("No assembly FASTA files found.")
    return found


def resolve_gffs(paths: Sequence[str] | None) -> List[Path]:
    if not paths:
        return []
    return [p for p in resolve_inputs(paths, kind="gff") if looks_like_gff(p)]


def _apply_optional(df: pd.DataFrame, other: Dict[str, dict]) -> pd.DataFrame:
    if not other:
        return df
    lookup = {canonicalize_name(key): val for key, val in other.items()}
    for idx, row in df.iterrows():
        can = canonicalize_name(str(row["Strain"]))
        rec = lookup.get(can)
        if not rec:
            continue
        for col, value in rec.items():
            if col not in df.columns:
                df[col] = pd.NA
            if value is not None and not (isinstance(value, str) and value == ""):
                df.at[idx, col] = value
    return df


def build_wide_dataframe(
    assemblies: Sequence[Path],
    gffs: Sequence[Path] | None = None,
    checkm2_path: Path | None = None,
    coverage_path: Path | None = None,
    metadata_path: Path | None = None,
    sequencing_platforms: str | None = None,
    assembly_method: str | None = None,
    genome_status: str | None = None,
) -> pd.DataFrame:
    assembly_rows = [assembly_stats_to_row(compute_assembly_stats(p)) for p in assemblies]
    df = pd.DataFrame(assembly_rows)
    if df.empty:
        return pd.DataFrame(columns=WIDE_COLUMNS)

    df["Strain name"] = df["Strain"]

    assembly_map = {
        canonicalize_name(str(row["Strain"])): Path(str(row["_assembly_path"]))
        for _, row in df.iterrows()
    }
    assembly_size_map = {
        canonicalize_name(str(row["Strain"])): int(row["Genome size (bp)"])
        for _, row in df.iterrows()
    }

    if gffs:
        gff_rows = []
        for gff in gffs:
            strain_key = canonicalize_name(Path(gff).stem)
            asm = assembly_map.get(strain_key)
            stats = parse_gff_stats(gff, assembly_path=asm) if asm is not None else parse_gff_stats(gff)
            gff_rows.append(gff_stats_to_row(stats))
        gff_map = {
            canonicalize_name(r["Strain"]): {k: v for k, v in r.items() if k != "Strain"}
            for r in gff_rows
        }
        df = _apply_optional(df, gff_map)

    if checkm2_path:
        df = _apply_optional(df, parse_checkm2_report(checkm2_path))

    if coverage_path:
        df = _apply_optional(df, parse_coverage_table(coverage_path, assembly_size_map=assembly_size_map))

    if metadata_path:
        df = _apply_optional(df, parse_metadata_table(metadata_path))

    if sequencing_platforms:
        df["Sequencing platforms"] = sequencing_platforms
    if assembly_method:
        df["Assembly method"] = assembly_method
    if genome_status:
        df["Genome status"] = genome_status

    if "Genome status" not in df.columns:
        df["Genome status"] = pd.NA
    df["Genome status"] = df.apply(
        lambda row: row["Genome status"]
        if pd.notna(row["Genome status"]) and str(row["Genome status"]).strip()
        else infer_genome_status(int(row["No. of contigs"]), str(row["Circularity"])),
        axis=1,
    )

    for col in WIDE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[WIDE_COLUMNS].sort_values("Strain").reset_index(drop=True)
    return df


def _format_feature_value(feature: str, value) -> str:
    if pd.isna(value):
        return ""

    if feature == "16S rRNA sequence":
        return str(value)

    if feature in {
        "Genome size (bp)", "No. of contigs", "N50 (bp)", "N90 (bp)", "L50", "L90",
        "Longest contig (bp)", "CDSs", "tRNAs", "rRNAs", "tmRNA",
        "Repeat regions", "16S rRNA count", "16S rRNA length (bp)",
    }:
        try:
            return pretty_int(float(value)) or ""
        except Exception:
            return str(value)

    if feature in {"GC content (%)", "Gaps (N per 100 kb)", "Sequencing coverage (×)", "Completeness (%)", "Contamination (%)"}:
        try:
            return pretty_float(float(value), digits=2) or ""
        except Exception:
            return str(value)

    return str(value)


def build_feature_dataframe(wide_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    if wide_df.empty:
        return pd.DataFrame(columns=["Strain", "Feature", "Description"])

    for _, rec in wide_df.iterrows():
        strain = rec["Strain"]
        for feature in FEATURE_ORDER:
            rows.append(
                {
                    "Strain": strain,
                    "Feature": feature,
                    "Description": _format_feature_value(feature, rec.get(feature)),
                }
            )
    return pd.DataFrame(rows, columns=["Strain", "Feature", "Description"])


def write_table(df: pd.DataFrame, path: Path) -> None:
    path = ensure_parent(path)
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_csv(path, sep="\t", index=False)


def write_outputs(
    wide_df: pd.DataFrame,
    output: Path,
    feature_df: pd.DataFrame | None = None,
    feature_output: Path | None = None,
    xlsx_path: Path | None = None,
) -> None:
    write_table(wide_df, output)

    if feature_output and feature_df is not None:
        write_table(feature_df, feature_output)

    if xlsx_path:
        xlsx_path = ensure_parent(xlsx_path)
        with pd.ExcelWriter(xlsx_path) as writer:
            wide_df.to_excel(writer, index=False, sheet_name="wide_table")
            if feature_df is not None:
                feature_df.to_excel(writer, index=False, sheet_name="feature_table")


def _run_summary(
    assemblies: Sequence[Path],
    gffs: Sequence[Path] | None,
    checkm2_path: Path | None,
    coverage_path: Path | None,
    metadata_path: Path | None,
    sequencing_platforms: str | None,
    assembly_method: str | None,
    genome_status: str | None,
    output: Path,
    feature_output: Path | None,
    xlsx_path: Path | None,
) -> int:
    wide_df = build_wide_dataframe(
        assemblies=assemblies,
        gffs=gffs,
        checkm2_path=checkm2_path,
        coverage_path=coverage_path,
        metadata_path=metadata_path,
        sequencing_platforms=sequencing_platforms,
        assembly_method=assembly_method,
        genome_status=genome_status,
    )
    feature_df = None
    if feature_output or xlsx_path:
        feature_df = build_feature_dataframe(wide_df)

    write_outputs(
        wide_df=wide_df,
        output=output,
        feature_df=feature_df,
        feature_output=feature_output,
        xlsx_path=xlsx_path,
    )
    print(f"Wrote wide table: {output}")
    if feature_output:
        print(f"Wrote feature table: {feature_output}")
    if xlsx_path:
        print(f"Wrote workbook: {xlsx_path}")
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    assemblies = resolve_assemblies(args.assemblies)
    gffs = resolve_gffs(args.gffs) or None
    checkm2_path = Path(args.checkm2).resolve() if args.checkm2 else None
    coverage_path = Path(args.coverage).resolve() if args.coverage else None
    metadata_path = Path(args.metadata).resolve() if args.metadata else None
    return _run_summary(
        assemblies=assemblies,
        gffs=gffs,
        checkm2_path=checkm2_path,
        coverage_path=coverage_path,
        metadata_path=metadata_path,
        sequencing_platforms=args.sequencing_platforms,
        assembly_method=args.assembly_method,
        genome_status=args.genome_status,
        output=Path(args.output),
        feature_output=Path(args.feature_output) if args.feature_output else None,
        xlsx_path=Path(args.xlsx) if args.xlsx else None,
    )


def cmd_pipeline(args: argparse.Namespace) -> int:
    assemblies = resolve_assemblies(args.assemblies)
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    gffs: List[Path] = []
    if args.annotation_mode == "prokka":
        gffs = run_prokka(
            assemblies=assemblies,
            outdir=workdir / "prokka",
            threads=args.threads,
            kingdom=args.kingdom,
            extra_args=args.annotation_extra_args,
            verbose=not args.quiet,
        )
    elif args.annotation_mode == "bakta":
        gffs = run_bakta(
            assemblies=assemblies,
            outdir=workdir / "bakta",
            threads=args.threads,
            extra_args=args.annotation_extra_args,
            verbose=not args.quiet,
        )
    elif args.annotation_mode == "existing":
        gffs = find_existing_gffs(assemblies=assemblies, gff_inputs=resolve_gffs(args.gffs))
    elif args.annotation_mode == "none":
        gffs = []

    checkm2_path = Path(args.checkm2).resolve() if args.checkm2 else None
    coverage_path = Path(args.coverage).resolve() if args.coverage else None
    metadata_path = Path(args.metadata).resolve() if args.metadata else None

    return _run_summary(
        assemblies=assemblies,
        gffs=gffs or None,
        checkm2_path=checkm2_path,
        coverage_path=coverage_path,
        metadata_path=metadata_path,
        sequencing_platforms=args.sequencing_platforms,
        assembly_method=args.assembly_method,
        genome_status=args.genome_status,
        output=Path(args.output),
        feature_output=Path(args.feature_output) if args.feature_output else None,
        xlsx_path=Path(args.xlsx) if args.xlsx else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genochar",
        description="Generate publication-ready genome characterization tables from FASTA, GFF, and CheckM2 outputs.",
    )
    parser.add_argument("-V", "--version", action="version", version=f"genochar {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    summarize = sub.add_parser(
        "summarize",
        help="Summarize existing FASTA/GFF/CheckM2/coverage/metadata files.",
    )
    summarize.add_argument("--assemblies", nargs="+", required=True, help="Assembly FASTA files, directories, or glob patterns.")
    summarize.add_argument("--gffs", nargs="+", help="Existing GFF/GFF3 files, directories, or glob patterns.")
    summarize.add_argument("--checkm2", help="Existing CheckM2 quality_report.tsv path.")
    summarize.add_argument("--coverage", help="Coverage TSV/CSV path.")
    summarize.add_argument("--metadata", help="Metadata TSV/CSV path.")
    summarize.add_argument("--sequencing-platforms", help="Set one sequencing platform string for all strains.")
    summarize.add_argument("--assembly-method", help="Set one assembly method string for all strains.")
    summarize.add_argument("--genome-status", help="Set one genome status string for all strains.")
    summarize.add_argument("--output", default="genome_characterization.tsv", help="Main wide-table output (.tsv or .csv).")
    summarize.add_argument("--feature-output", help="Optional feature-table output (.tsv or .csv).")
    summarize.add_argument("--xlsx", help="Optional XLSX workbook with wide_table and feature_table sheets.")
    summarize.set_defaults(func=cmd_summarize)

    pipeline = sub.add_parser(
        "pipeline",
        help="Optionally run Prokka/Bakta to make GFFs, then summarize. CheckM2 is read-only in this version.",
    )
    pipeline.add_argument("--assemblies", nargs="+", required=True, help="Assembly FASTA files, directories, or glob patterns.")
    pipeline.add_argument(
        "--annotation-mode",
        choices=["prokka", "bakta", "existing", "none"],
        default="none",
        help="How to obtain GFFs. Default: none.",
    )
    pipeline.add_argument("--gffs", nargs="+", help="Existing GFF/GFF3 files, directories, or glob patterns.")
    pipeline.add_argument("--kingdom", choices=["auto", "Bacteria", "Archaea"], default="auto", help="Passed to Prokka.")
    pipeline.add_argument("--threads", type=int, default=8, help="Threads used for Prokka/Bakta.")
    pipeline.add_argument("--workdir", default="genochar_work", help="Working directory for annotation outputs.")
    pipeline.add_argument("--annotation-extra-args", help="Extra arguments passed to Prokka/Bakta as a single quoted string.")
    pipeline.add_argument("--checkm2", help="Existing CheckM2 quality_report.tsv path.")
    pipeline.add_argument("--coverage", help="Coverage TSV/CSV path.")
    pipeline.add_argument("--metadata", help="Metadata TSV/CSV path.")
    pipeline.add_argument("--sequencing-platforms", help="Set one sequencing platform string for all strains.")
    pipeline.add_argument("--assembly-method", help="Set one assembly method string for all strains.")
    pipeline.add_argument("--genome-status", help="Set one genome status string for all strains.")
    pipeline.add_argument("--output", default="genome_characterization.tsv", help="Main wide-table output (.tsv or .csv).")
    pipeline.add_argument("--feature-output", help="Optional feature-table output (.tsv or .csv).")
    pipeline.add_argument("--xlsx", help="Optional XLSX workbook with wide_table and feature_table sheets.")
    pipeline.add_argument("--quiet", action="store_true", help="Reduce logging.")
    pipeline.set_defaults(func=cmd_pipeline)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PipelineError as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
