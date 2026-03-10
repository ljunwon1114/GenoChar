# genochar

**genochar** generates publication-ready genome characterization tables for bacterial and archaeal draft or complete genomes.

This version is designed around a practical manuscript workflow:

1. start from assembled **FASTA** files
2. optionally create **GFF** files with **Prokka** or **Bakta**
3. optionally reuse **existing GFF** files
4. optionally read an **existing CheckM2** `quality_report.tsv`
5. optionally read a **coverage table** and/or **metadata table**
6. export a **wide characterization table** by default

The default output is a wide table with one row per strain.

## What the tool can compute

### FASTA-derived fields
These work even if you provide only FASTA files:

- `Strain`
- `Strain name`
- `Genome size (bp)`
- `GC content (%)`
- `No. of contigs`
- `N50 (bp)`
- `N90 (bp)`
- `L50`
- `L90`
- `Longest contig (bp)`
- `Gaps (N per 100 kb)`
- `Genome status`
- `Circularity`

### GFF-derived fields
These are added when you provide GFF files or run annotation through `pipeline`:

- `CDSs`
- `tRNAs`
- `rRNAs`
- `tmRNA`
- `Repeat regions`
- `16S rRNA count`
- `16S rRNA length (bp)`
- `16S rRNA contig`
- `16S rRNA sequence`

### CheckM2-derived fields
These are added only if you provide an existing CheckM2 report:

- `Completeness (%)`
- `Contamination (%)`

### User-supplied metadata
Optional input tables can add:

- `Sequencing coverage (×)`
- `Sequencing platforms`
- `Assembly method`
- `Genome status` (override)

## Default output columns

The main output table contains:

- `Strain`
- `Strain name`
- `Genome size (bp)`
- `GC content (%)`
- `No. of contigs`
- `N50 (bp)`
- `N90 (bp)`
- `L50`
- `L90`
- `Longest contig (bp)`
- `Gaps (N per 100 kb)`
- `Sequencing coverage (×)`
- `Sequencing platforms`
- `Assembly method`
- `Genome status`
- `CDSs`
- `tRNAs`
- `rRNAs`
- `tmRNA`
- `Repeat regions`
- `16S rRNA count`
- `16S rRNA length (bp)`
- `16S rRNA contig`
- `16S rRNA sequence`
- `Completeness (%)`
- `Contamination (%)`
- `Circularity`

## Installation

### 1) Install genochar itself
Clone the repository and install it into the currently active environment:

```bash
git clone https://github.com/your-username/genochar.git
cd genochar
pip install -e .
```

### 2) Recommended environment strategy

Because **Prokka**, **Bakta**, and **CheckM2** often have different dependency constraints, the easiest setup is:

- one environment for **genochar + Prokka**
- one environment for **genochar + Bakta**
- one environment for **CheckM2**

`genochar` can still merge everything later because it accepts:

- existing GFF files
- existing CheckM2 `quality_report.tsv`

Detailed commands are in:
- `docs/INSTALLATION_AND_WORKFLOWS.md`
- `envs/genochar_prokka.yml`
- `envs/genochar_bakta.yml`
- `envs/checkm2.yml`

## Command overview

### A. FASTA only

```bash
genochar summarize \
  --assemblies "assemblies/*.fasta" \
  --output genome_characterization.tsv
```

### B. FASTA + existing GFF + existing CheckM2

```bash
genochar summarize \
  --assemblies "assemblies/*.fasta" \
  --gffs "annotations/*.gff*" \
  --checkm2 checkm2_out/quality_report.tsv \
  --output genome_characterization.tsv
```

### C. FASTA + Prokka annotation + existing CheckM2

```bash
genochar pipeline \
  --assemblies "assemblies/*.fasta" \
  --annotation-mode prokka \
  --kingdom Archaea \
  --threads 8 \
  --workdir genochar_work \
  --checkm2 checkm2_out/quality_report.tsv \
  --output genome_characterization.tsv
```

### D. FASTA + Bakta annotation + existing CheckM2

```bash
genochar pipeline \
  --assemblies "assemblies/*.fasta" \
  --annotation-mode bakta \
  --threads 8 \
  --workdir genochar_work \
  --checkm2 checkm2_out/quality_report.tsv \
  --output genome_characterization.tsv
```

### E. Reuse existing GFFs

```bash
genochar pipeline \
  --assemblies "assemblies/*.fasta" \
  --annotation-mode existing \
  --gffs "annotations/*.gff*" \
  --checkm2 checkm2_out/quality_report.tsv \
  --output genome_characterization.tsv
```

## Optional extra outputs

### Feature-style table
If you also want the `Strain / Feature / Description` format:

```bash
genochar summarize \
  --assemblies "assemblies/*.fasta" \
  --feature-output genome_characterization_feature.tsv \
  --output genome_characterization.tsv
```

### Excel workbook
To get both wide and feature tables in one workbook:

```bash
genochar summarize \
  --assemblies "assemblies/*.fasta" \
  --xlsx genome_characterization.xlsx \
  --output genome_characterization.tsv
```

## Coverage input
Coverage cannot be derived from FASTA alone. If you want to fill `Sequencing coverage (×)`, provide a coverage table.

Example:

```tsv
Strain	Coverage
IOH03	55.7
IOH05	50.3
```

or

```tsv
Strain	Total bases
IOH03	110.8 Mbp
IOH05	107.6 Mbp
```

If `Total bases` is provided, `genochar` computes:

```text
Sequencing coverage (×) = Total bases / Genome size
```

## Metadata input
Optional metadata columns include:

- `Strain`
- `Sequencing platforms`
- `Assembly method`
- `Genome status`
- `Repeat regions`
- `Sequencing coverage (×)`

Example:

```tsv
Strain	Sequencing platforms	Assembly method
IOH03	Illumina iSeq 100	Unicycler (short-read assembly)
IOH05	Illumina iSeq 100	Unicycler (short-read assembly)
```

## Notes

- In this version, **CheckM2 is read-only**. Run it separately and pass `--checkm2 quality_report.tsv`.
- `pipeline` can still create GFF files using **Prokka** or **Bakta**, or reuse existing GFF files.
- If more than one 16S rRNA feature is found, `genochar` stores the **longest 16S sequence** in the main table.
- `Genome status` is inferred if not explicitly provided:
  - `Complete genome` if there is one contig and circularity is detected
  - `Draft genome` otherwise

## Example output shape

| Strain | Genome size (bp) | No. of contigs | N50 (bp) | CDSs | 16S rRNA sequence | Completeness (%) |
|---|---:|---:|---:|---:|---|---:|
| IOH03 | 1,990,719 | 3 | 1,175,002 | 2,092 | ATTCCGGTT... | 98.53 |

## License

MIT
