# GitHub repository text and setup

This file is for the parts that are **not** the README.

## What shows where on GitHub?

### 1) README
The README is the large document shown on the repository front page.  
That is where installation, usage, examples, and workflow details should live.

### 2) Repository description
This is the short one-line text near the top of the repository page, in the **About** section / Description field.

Suggested description:

> Publication-ready genome characterization table generator for bacterial and archaeal genomes from FASTA, GFF, and CheckM2 outputs.

### 3) Topics
Suggested repository topics:

- bioinformatics
- genomics
- genome-assembly
- genome-annotation
- microbiology
- bacteria
- archaea
- checkm2
- prokka
- bakta
- gff
- fasta

### 4) Website field
Leave empty at first unless you also create documentation pages or a project website.

---

## Suggested repository name

`genochar`

Alternative names if you want something more explicit:

- `genome-characterization`
- `prok-genome-char`
- `genome-char-table`

---

## Suggested first release title

`genochar v0.4.0`

Suggested release summary:

- default wide output table
- FASTA-only support
- optional Prokka/Bakta GFF generation
- existing GFF support
- CheckM2 read-in support
- 16S rRNA sequence extraction into the main table

---

## Suggested repository opening paragraph

Use this in the top of the README or release notes:

> genochar is a lightweight command-line tool that builds manuscript-ready genome characterization tables from assembled FASTA files, optional GFF annotations, and optional CheckM2 quality reports. It is designed for bacterial and archaeal draft or complete genomes and can be used in FASTA-only mode or as a lightweight wrapper around Prokka/Bakta annotation outputs.

---

## Suggested first screenshot / example
After your first public push, add one screenshot showing:

- one wide table row per strain
- columns such as genome size, N50, CDSs, 16S sequence, completeness, contamination

That makes the repository instantly understandable.
