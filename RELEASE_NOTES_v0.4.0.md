# genochar v0.4.0

## New in this version

- Default output is now the **wide genome characterization table**
- `--feature-output` is optional instead of being the main output
- `pipeline` keeps annotation modes:
  - `prokka`
  - `bakta`
  - `existing`
  - `none`
- CheckM2 is now **read-only**:
  - run it separately
  - provide `--checkm2 quality_report.tsv`
- `16S rRNA sequence` stays in the main wide table
- Added:
  - `docs/INSTALLATION_AND_WORKFLOWS.md`
  - `docs/GITHUB_REPO_SETUP.md`
  - `GITHUB_DESCRIPTION.txt`
  - `envs/*.yml`

## Recommended citation-style summary

genochar is a command-line utility for generating publication-ready genome characterization tables from assembled FASTA files, optional GFF annotations, and optional CheckM2 reports for bacterial and archaeal genomes.
