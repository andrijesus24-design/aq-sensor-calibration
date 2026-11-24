# Fungal BGC mining — sample analysis

Secondary-metabolite biosynthetic gene clusters (BGCs) in three public fungal genomes used
for food protein, mined with [antiSMASH 8](https://antismash.secondarymetabolites.org/) and
compared with [MIBiG](https://mibig.secondarymetabolites.org/).

| Species / strain | Assembly | BGC regions | MIBiG match ≥70% |
|---|---|---|---|
| *Rhizomucor pusillus* CBS 183.67 | `GCF_041956525.1` | 10 | 1 |
| *Aspergillus oryzae* RIB40 | `GCF_000184455.2` | 80 | 18 |
| *Fusarium venenatum* A3/5 (Quorn) | `GCF_900007375.1` | 45 | 11 |

**Read the report:** [`report/XERABINET_fungal_BGC_mini_report.pdf`](report/XERABINET_fungal_BGC_mini_report.pdf)
(13 pages) · [two-page summary](report/XERABINET_fungal_BGC_two_page_summary.pdf) ·
[evidence matrix](report/XERABINET_fungal_BGC_evidence_matrix.xlsx) (Excel, 8 sheets).

This is scientific intelligence, not regulatory, legal or freedom-to-operate advice.

## What the pipeline does

`.github/workflows/fungal-bgc.yml` runs one job per accession in `genomes.tsv`:

1. downloads the antiSMASH databases;
2. fetches the annotated genome (GenBank flat file) from NCBI Datasets;
3. runs antiSMASH 8 in fungal mode with `--genefinding-tool none` (the existing annotation is
   used, genes are not re-predicted), with KnownClusterBlast and ClusterCompare against MIBiG;
4. summarises each run with `scripts/summarise_antismash.py` and commits the small outputs.

Run it from the Actions tab (`workflow_dispatch`), or locally:

```bash
micromamba create -n as -c conda-forge -c bioconda antismash=8.0.4 python=3.11
micromamba run -n as download-antismash-databases --database-dir ~/asdb
micromamba run -n as antismash --databases ~/asdb --taxon fungi --genefinding-tool none \
  --cb-knownclusters --cc-mibig --output-dir out/GCF_900007375.1 \
  --output-basename GCF_900007375.1 GCF_900007375.1.gbff
python scripts/summarise_antismash.py out/GCF_900007375.1 GCF_900007375.1 \
  results/GCF_900007375.1
```

To add a genome, add a row to `genomes.tsv` and its accession to the workflow's matrix.

## What is committed

`results/<accession>/` holds, per genome:

| File | Contents |
|---|---|
| `regions.tsv` | one row per BGC region: coordinates, cluster type, gene counts, contig-edge flag, best MIBiG match |
| `mibig_hits.tsv` | up to five MIBiG matches per region, with similarity and genes hit |
| `core_genes.tsv` | one row per core biosynthetic gene, with its annotation and domains |
| `regions/*.gbk` | antiSMASH region GenBank files, openable in any genome viewer |
| `compact.json.gz` | region areas and comparison results, without sequences |
| `assembly_report.jsonl`, `antismash_version.txt` | provenance |

`report/` holds the deliverables and the scripts that build them from `results/`
(`analyse.py` → `make_xlsx.py`, `make_figure.py`, `report.py`, `summary.py`; `sources.py` and
`findings.py` hold the citations and the written findings).

## How to read the two numbers

**Similarity (%)** is antiSMASH's KnownClusterBlast score: the share of the reference cluster's
genes with a significant hit in the detected region — how much of a known cluster is present.
**Mean identity (%)** is the mean amino-acid identity of those best-hit pairs — how close the
shared genes are.

High similarity with low identity means the same cluster architecture, not the same chemistry.
Low similarity with very high identity means part of a known cluster is present almost
unchanged and the rest is missing, which is what a partial or deleted cluster looks like from
outside.

A detected cluster is potential, not product. Expression, cultivation conditions and chemical
analysis decide what an organism actually makes, and none of them is part of this analysis.
No MIBiG match means uncharacterised, not harmless.

## Reproducibility notes

Each run records the antiSMASH version and the assembly report it used. The databases are
downloaded at run time and are versioned by antiSMASH, so a later run may use a newer MIBiG
release; the version files say which was used. Numbers in the report correspond to the run of
24 November 2026.

---

Andri Binet, PhD (c) — CEO, Xerabinet · modbinet@gmail.com
