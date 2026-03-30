# GenoChar

**GenoChar** is a lightweight, summarize-first workflow for generating **publication-ready genome characterization tables** from bacterial and archaeal genome assemblies.

Version **0.6.3.2** focuses on a practical reporting stage that is often still done manually: collecting assembly statistics, annotation summaries, genome quality fields, coverage, and user metadata into a single standardized table.

GenoChar supports three common use cases:

- **Minimal mode**: summarize from assembly FASTA files only
- **Reuse mode**: integrate existing GFF/GFF3 and CheckM2 outputs
- **Managed workflow mode**: run CheckM2 and Prokka through isolated managed environments prepared by `genochar setup`

The main output is a **wide table with one row per strain**. Optional outputs include a **feature-style table** and an **Excel workbook**.

> **Naming note**
>
> The project/display name is **GenoChar**, while the Python package name and command-line executable are lowercase as `genochar`.

---

## Why GenoChar?

Microbial genome papers often report a similar set of values:

- genome size
- GC content
- contig statistics
- annotation counts
- 16S rRNA information
- completeness and contamination
- sequencing coverage and metadata

In many projects, these values already exist across separate FASTA, GFF, CheckM2, and spreadsheet files, but they still need to be merged and reformatted by hand.

GenoChar was designed for that exact step.

It is **not** an end-to-end raw-read pipeline. Instead, it starts from **assembled genomes** and standardizes the assembly-to-table reporting stage.

---

## Installation

### Core Python requirement

GenoChar itself is lightweight and currently requires:

- **Python >= 3.10**

The core Python dependencies are minimal:

- `pandas>=2.0`
- `openpyxl>=3.1`

---

### Option 1. Install from PyPI

```bash
pip install genochar
```

### Option 2. Install from Bioconda

```bash
conda install -c bioconda genochar
```

### Option 3. Install the latest GitHub version

```bash
pip install git+https://github.com/ljunwon1114/genochar.git
```

### For development

```bash
git clone https://github.com/ljunwon1114/genochar.git
cd genochar
pip install -e .
```

---

## One-time managed setup

If you want GenoChar to run **CheckM2** and/or **Prokka** for you, run this once:

```bash
genochar setup
```

This prepares managed environments under `~/.genochar`, typically:

```text
~/.genochar/
  config.json
  envs/
    prokka/
    checkm2/
  databases/
    CheckM2_database/
```

After setup, a normal GenoChar command can automatically use those managed environments when `--annotate prokka` and/or `--check` are requested.

This avoids forcing Prokka and CheckM2 into one shared environment.

### Reuse an existing CheckM2 database

If you already downloaded the CheckM2 database, you can point setup to it directly:

```bash
genochar setup --checkm2-db /path/to/CheckM2_database/uniref100.KO.1.dmnd
```

You can also provide a directory that contains the `.dmnd` file.

### Optional setup flags

```bash
genochar setup --skip-prokka
genochar setup --skip-checkm2
genochar setup --force
```

- `--skip-prokka`: prepare only CheckM2
- `--skip-checkm2`: prepare only Prokka
- `--force`: recreate managed environments even if they already exist

---

## What GenoChar computes

### FASTA-derived fields

These work even if you provide only FASTA files:

- `Strain`
- `Strain name`
- `Genus`
- `Species`
- `Accession`
- `Genome size (bp)`
- `GC content (%)`
- `No. of contigs`
- `N50 (bp)`
- `N90 (bp)`
- `L50`
- `L90`
- `Longest contig (bp)`
- `Gaps (N per 100 kb)`

### GFF-derived fields

These are added when you provide existing GFF/GFF3 files or let GenoChar generate annotation files:

- `CDSs`
- `tRNAs`
- `rRNAs`
- `tmRNA`
- `misc RNA`
- `Repeat regions`
- `16S rRNA count`
- `16S rRNA length (bp)`
- `16S rRNA contig`
- `16S rRNA sequence`

### CheckM2-derived fields

These are added when you provide or generate a CheckM2 report:

- `Completeness (%)`
- `Contamination (%)`

### User-supplied metadata

Optional input tables can add:

- `Sequencing coverage (×)`
- `Sequencing platforms`
- `Assembly method`
- `Genus`
- `Species`
- `Accession`
- `Repeat regions`

---

## Input model

GenoChar is designed around **assembly FASTA files as the minimal input**.

You can then optionally add:

- existing GFF/GFF3 annotation files
- an existing CheckM2 `quality_report.tsv`
- a coverage table
- a metadata table

In other words, GenoChar can work in three practical ways:

1. **FASTA only**
2. **FASTA + existing results**
3. **FASTA + internally managed CheckM2/Prokka**

---

## Command overview

### A. FASTA only

```bash
genochar -i "assemblies/*.fasta" -o genome_characterization.tsv
```

### B. FASTA + existing GFF + existing CheckM2 report

```bash
genochar \
  -i "assemblies/*.fasta" \
  --gff "annotations/*.gff*" \
  --check-report checkm2_out/quality_report.tsv \
  -o genome_characterization.tsv
```

### C. FASTA + managed CheckM2 first + managed Prokka annotation

```bash
genochar \
  -i "assemblies/*.fasta" \
  --check \
  --annotate prokka \
  -k Archaea \
  -t 8 \
  -w genochar_work \
  -o genome_characterization.tsv
```

### D. Reuse existing GFF files automatically

```bash
genochar \
  -i "assemblies/*.fasta" \
  --annotate existing \
  --check-report checkm2_out/quality_report.tsv \
  -o genome_characterization.tsv
```

### E. Reuse explicitly supplied GFF files in existing-annotation mode

```bash
genochar \
  -i "assemblies/*.fasta" \
  --annotate existing \
  --gff "annotations/*.gff*" \
  --check-report checkm2_out/quality_report.tsv \
  -o genome_characterization.tsv
```

---

## Optional extra outputs

### Feature-style table

```bash
genochar \
  -i "assemblies/*.fasta" \
  -f genome_characterization_feature.tsv \
  -o genome_characterization.tsv
```

### Excel workbook

```bash
genochar \
  -i "assemblies/*.fasta" \
  -x genome_characterization.xlsx \
  -o genome_characterization.tsv
```

---

## Coverage input

Coverage cannot be derived from FASTA alone. To fill `Sequencing coverage (×)`, provide a coverage table.

Example:

```text
Strain	Coverage
IOH03	55.7
IOH05	50.3
```

or:

```text
Strain	Total bases
IOH03	110.8 Mbp
IOH05	107.6 Mbp
```

If `Total bases` is provided, GenoChar computes:

```text
Sequencing coverage (×) = Total bases / Genome size
```

---

## Metadata input

Optional metadata columns include:

- `Strain`
- `Sequencing platforms`
- `Assembly method`
- `Genus`
- `Species`
- `Accession`
- `Repeat regions`
- `Sequencing coverage (×)`

Example:

```text
Strain	Genus	Species	Accession	Sequencing platforms	Assembly method
IOH03	Thermococcus	waiotapuensis	GCF_032304395	Illumina iSeq 100	Unicycler (short-read assembly)
IOH05	Thermococcus	sp.	GCA_000000000	Illumina iSeq 100	Unicycler (short-read assembly)
```

---

## Notes and behavior

- **GenoChar is summarize-first by default.** If you only pass FASTA, GFF, CheckM2, coverage, and metadata inputs, it behaves like a direct summarization tool.
- **`genochar setup`** is the recommended way to prepare Prokka and CheckM2 without forcing them into one shared environment.
- `--annotate prokka` tells GenoChar to create annotation files before building the final table.
- `--annotate existing` tells GenoChar to reuse nearby GFF files or explicitly supplied `--gff` inputs.
- `--check` runs CheckM2 internally **before annotation** and automatically integrates the resulting `quality_report.tsv` into the final table.
- `--check-report` reuses an existing CheckM2 `quality_report.tsv` file.
- `--check` and `--check-report` are mutually exclusive.
- `--gff` is intended for existing annotation files and should not be combined with `--annotate prokka`.
- If more than one 16S rRNA feature is found, GenoChar stores the **longest** detected 16S sequence in the main table.

---

## Reproducibility and availability

Source code:

- GitHub: https://github.com/ljunwon1114/genochar

Archived software release used for the manuscript:

- Zenodo DOI: https://doi.org/10.5281/zenodo.19279904

distribution:

- PyPI: https://pypi.org/project/GenoChar/

- Bioconda: https://anaconda.org/bioconda/genochar

---

## Contact

For questions or feedback, please open a [GitHub Issue](https://github.com/ljunwon1114/genochar/issues)

or contact the author at ljunwon1114@gmail.com

---

## License

Copyright (c) Lee Jun Won.

GenoChar is distributed by **Lee Jun Won** under the **MIT License**.

