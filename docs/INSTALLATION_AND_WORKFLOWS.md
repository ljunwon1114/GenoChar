# Installation and workflow guide

This file is intentionally more detailed than the README.  
Use it as the step-by-step setup guide when you first publish or reinstall `genochar`.

---

## Recommended workflow order

1. Prepare assembly FASTA files
2. Choose annotation path
   - **Prokka** for bacterial or archaeal genomes
   - **Bakta** mainly for bacterial genomes / plasmids
3. Run annotation and produce GFF files
4. Run **CheckM2** separately
5. Run `genochar` to merge:
   - FASTA-derived statistics
   - GFF-derived counts and 16S sequence
   - CheckM2 completeness / contamination
   - optional metadata / coverage

---

## Why CheckM2 is separate

`genochar` no longer tries to install or run CheckM2 internally.  
That makes the tool easier to maintain and avoids dependency conflicts.

The practical design is:

- annotation can be done from inside `genochar` using `pipeline`
- CheckM2 is run separately
- `genochar` simply reads `quality_report.tsv`

This is the most robust setup on Linux servers and HPC systems.

---

## Workflow A: Prokka + genochar (recommended for archaea)

### Create environment

```bash
conda env create -f envs/genochar_prokka.yml
conda activate genochar-prokka
```

### Install genochar into that environment

```bash
pip install -e .
```

### Check tools

```bash
genochar --help
prokka --version
seqkit version
```

### Run pipeline

```bash
genochar pipeline \
  --assemblies "/path/to/assemblies/*.fasta" \
  --annotation-mode prokka \
  --kingdom Archaea \
  --threads 8 \
  --workdir /path/to/genochar_work \
  --output /path/to/genome_characterization.tsv
```

### Output location
Prokka GFF files will typically land here:

```text
/path/to/genochar_work/prokka/<strain>/<strain>.gff
```

---

## Workflow B: Bakta + genochar (mainly for bacterial genomes)

### Create environment

```bash
conda env create -f envs/genochar_bakta.yml
conda activate genochar-bakta
```

### Install genochar

```bash
pip install -e .
```

### Download Bakta database

Light DB:

```bash
bakta_db download --output /path/to/bakta_db --type light
```

Full DB:

```bash
bakta_db download --output /path/to/bakta_db
```

If you want Bakta to find the DB automatically in later sessions, set:

```bash
export BAKTA_DB=/path/to/bakta_db/db
```

If the DB directory layout differs on your machine, use the exact directory that contains the Bakta database files.

### Check tools

```bash
genochar --help
bakta --version
seqkit version
```

### Run pipeline

```bash
genochar pipeline \
  --assemblies "/path/to/assemblies/*.fasta" \
  --annotation-mode bakta \
  --threads 8 \
  --workdir /path/to/genochar_work \
  --output /path/to/genome_characterization.tsv
```

### Output location
Bakta GFF files will typically land here:

```text
/path/to/genochar_work/bakta/<strain>/<strain>.gff3
```

---

## Workflow C: CheckM2 only

### Create environment

```bash
conda env create -f envs/checkm2.yml
conda activate checkm2
```

### Check installation

```bash
checkm2 --help
```

### Download database

```bash
checkm2 database --download --path /path/to/checkm2_db
```

If desired, make the DB persistent across sessions:

```bash
export CHECKM2DB=/path/to/checkm2_db
```

### Run CheckM2 on FASTA files in one folder

```bash
checkm2 predict \
  --input /path/to/assemblies \
  --output-directory /path/to/checkm2_out \
  --threads 8 \
  -x fasta
```

Expected report:

```text
/path/to/checkm2_out/quality_report.tsv
```

---

## Workflow D: Merge everything with existing files

After Prokka/Bakta and CheckM2 are done, switch back to the `genochar` environment and merge all results:

```bash
genochar summarize \
  --assemblies "/path/to/assemblies/*.fasta" \
  --gffs "/path/to/annotations/*.gff*" \
  --checkm2 "/path/to/checkm2_out/quality_report.tsv" \
  --output "/path/to/genome_characterization.tsv"
```

Or, if you want to reuse GFFs discovered automatically:

```bash
genochar pipeline \
  --assemblies "/path/to/assemblies/*.fasta" \
  --annotation-mode existing \
  --gffs "/path/to/annotations/*.gff*" \
  --checkm2 "/path/to/checkm2_out/quality_report.tsv" \
  --output "/path/to/genome_characterization.tsv"
```

---

## Optional tables

### Feature table
```bash
genochar summarize \
  --assemblies "/path/to/assemblies/*.fasta" \
  --gffs "/path/to/annotations/*.gff*" \
  --checkm2 "/path/to/checkm2_out/quality_report.tsv" \
  --feature-output "/path/to/genome_characterization_feature.tsv" \
  --output "/path/to/genome_characterization.tsv"
```

### XLSX
```bash
genochar summarize \
  --assemblies "/path/to/assemblies/*.fasta" \
  --gffs "/path/to/annotations/*.gff*" \
  --checkm2 "/path/to/checkm2_out/quality_report.tsv" \
  --xlsx "/path/to/genome_characterization.xlsx" \
  --output "/path/to/genome_characterization.tsv"
```

---

## Coverage and metadata

### Coverage file
Recommended minimal format:

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

### Metadata file
Recommended minimal format:

```tsv
Strain	Sequencing platforms	Assembly method
IOH03	Illumina iSeq 100	Unicycler
IOH05	Illumina iSeq 100	Unicycler
```

Then run:

```bash
genochar summarize \
  --assemblies "/path/to/assemblies/*.fasta" \
  --gffs "/path/to/annotations/*.gff*" \
  --checkm2 "/path/to/checkm2_out/quality_report.tsv" \
  --coverage "/path/to/coverage.tsv" \
  --metadata "/path/to/metadata.tsv" \
  --output "/path/to/genome_characterization.tsv"
```

---

## Publishing checklist

Before publishing to GitHub:

- replace `Your Name` in `pyproject.toml`
- replace placeholder GitHub URLs in `pyproject.toml`
- add your real repository name to README examples
- test at least:
  - FASTA-only
  - FASTA + GFF
  - FASTA + GFF + CheckM2
- create a git tag for the release

Suggested first tag:

```bash
git tag v0.4.0
git push origin v0.4.0
```
