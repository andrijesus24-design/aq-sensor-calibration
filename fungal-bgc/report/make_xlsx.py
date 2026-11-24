"""Build the evidence matrix (Excel) for the fungal BGC mini-report."""
import csv, os, sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import GENOMES, RES, load
from findings import FINDINGS, LIMITS
from sources import ACCESSED, PATENTS, SOURCES

OUT = sys.argv[1] if len(sys.argv) > 1 else "XERABINET_fungal_BGC_evidence_matrix.xlsx"

HEAD = PatternFill("solid", fgColor="1F3864")
HEADF = Font(color="FFFFFF", bold=True, size=10)
BODY = Font(size=10)
MONO = Font(name="Consolas", size=9)
WARN = PatternFill("solid", fgColor="FFF2CC")
TITLE = Font(size=14, bold=True, color="1F3864")


def sheet(wb, name, headers, rows, widths, wrap_cols=(), freeze="A2"):
    ws = wb.create_sheet(name)
    ws.append(headers)
    for c in ws[1]:
        c.fill, c.font = HEAD, HEADF
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = BODY
            c.alignment = Alignment(vertical="top",
                                    wrap_text=c.column_letter in wrap_cols)
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    return ws


def read_tsv(acc, name):
    path = f"{RES}/{acc}/{name}"
    with open(path) as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main():
    rows = load()
    wb = Workbook()

    # ---------- Overview ----------
    ws = wb.active
    ws.title = "Overview"
    ws["A1"] = "Secondary-metabolite gene clusters in three fungal genomes used for food protein"
    ws["A1"].font = TITLE
    ws["A2"] = (f"Xerabinet sample analysis. All data generated and all sources read on {ACCESSED}. "
                "antiSMASH 8.0.4, fungal mode, compared with MIBiG.")
    ws["A3"] = ("Read this sheet first, then Findings. Clusters holds every region found, "
                "MIBiG_matches the comparisons behind each claim, and Method_and_limits what this "
                "analysis cannot tell you.")
    for r in ("A2", "A3"):
        ws[r].font = BODY
        ws[r].alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 120
    ws.row_dimensions[2].height = 30
    ws.row_dimensions[3].height = 30

    hdr = ["Species / strain", "Assembly", "Assembly size (bp)", "Sequences",
           "BGC regions", "MIBiG match >=70%", "Regions on a contig edge",
           "Most frequent cluster types"]
    table = []
    for acc, sp in GENOMES.items():
        rs = [r for r in rows if r["accession"] == acc]
        rep = read_tsv(acc, "regions.tsv")
        import json
        meta = json.loads(open(f"{RES}/{acc}/assembly_report.jsonl").readline())
        stats = meta["assemblyStats"]
        types = {}
        for r in rep:
            for p in r["products"].split(";"):
                types[p] = types.get(p, 0) + 1
        top = ", ".join(f"{k} ({v})" for k, v in sorted(types.items(), key=lambda x: -x[1])[:5])
        table.append([sp, acc, int(stats["totalSequenceLength"]),
                      int(stats.get("numberOfScaffolds") or stats.get("numberOfContigs")),
                      len(rs),
                      sum(1 for r in rs if r["hits"] and r["hits"][0]["similarity"] >= 70),
                      sum(1 for r in rs if r["contig_edge"] == "True"), top])
    ws.append([])
    ws.append(hdr)
    for c in ws[5]:
        if c.value:
            c.fill, c.font = HEAD, HEADF
            c.alignment = Alignment(wrap_text=True, vertical="center")
    for t in table:
        ws.append(t)
    for col, w in zip("ABCDEFGH", (34, 18, 20, 11, 12, 18, 20, 52)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=6, max_row=8):
        for c in row:
            c.font = BODY
            c.alignment = Alignment(vertical="top", wrap_text=c.column_letter == "H")

    # ---------- Findings ----------
    sheet(wb, "Findings",
          ["ID", "Species / strain", "Finding", "Basis", "Where to check it",
           "Sources", "Confidence", "Open question"],
          [list(f) for f in FINDINGS],
          (7, 28, 70, 20, 34, 14, 40, 44),
          wrap_cols=("B", "C", "E", "G", "H"))

    # ---------- Clusters ----------
    crow = []
    for r in rows:
        h = r["hits"][0] if r["hits"] else {}
        crow.append([r["species"], r["accession"], r["region"], r["products"],
                     int(r["start"]), int(r["end"]), int(r["length_bp"]), int(r["n_cds"]),
                     int(r["n_core_genes"]), r["contig_edge"],
                     h.get("mibig", ""), h.get("compound", ""), h.get("mibig_class", ""),
                     h.get("similarity", ""), h.get("mean_identity", ""),
                     r["core_genes"]])
    ws = sheet(wb, "Clusters",
               ["Species / strain", "Assembly", "Region", "Cluster type(s)", "Start", "End",
                "Length (bp)", "Genes in region", "Core biosynthetic genes", "On contig edge",
                "Best MIBiG match", "Closest known compound(s)", "MIBiG class",
                "Similarity (% of reference genes)", "Mean identity (%)",
                "Core biosynthetic genes (locus tags)"],
               crow, (28, 17, 26, 26, 11, 11, 11, 10, 11, 11, 15, 38, 24, 14, 12, 70),
               wrap_cols=("A", "D", "L", "P"))
    for row in ws.iter_rows(min_row=2):
        if row[9].value == "True":
            row[9].fill = WARN

    # ---------- MIBiG matches ----------
    mrow = []
    for acc, sp in GENOMES.items():
        for h in read_tsv(acc, "mibig_hits.tsv"):
            mrow.append([sp, h["region"], int(h["rank"]), h["mibig"], h["compound"],
                         h["mibig_type"], int(h["proteins_hit"]), int(h["proteins_total"]),
                         int(h["similarity_pct"]), int(h["core_gene_hits"] or 0)])
    sheet(wb, "MIBiG_matches",
          ["Species / strain", "Region", "Rank", "MIBiG entry", "Compound(s)", "MIBiG class",
           "Reference genes hit", "Reference genes total", "Similarity (%)", "Core genes hit"],
          mrow, (28, 26, 7, 15, 44, 26, 13, 14, 12, 12),
          wrap_cols=("A", "E", "F"))

    # ---------- Core genes ----------
    grow = []
    for acc, sp in GENOMES.items():
        for g in read_tsv(acc, "core_genes.tsv"):
            grow.append([sp, g["region"], g["products"], g["locus_tag"], g["protein_id"],
                         g["ncbi_product"], g["gene_functions"], g["domains"]])
    sheet(wb, "Core_genes",
          ["Species / strain", "Region", "Cluster type(s)", "Locus tag", "Protein ID",
           "Annotation in the genome", "antiSMASH gene function", "NRPS/PKS domains"],
          grow, (28, 26, 22, 20, 16, 34, 56, 40),
          wrap_cols=("A", "F", "G", "H"))

    # ---------- Sources ----------
    sheet(wb, "Sources",
          ["ID", "Species", "Type", "Evidence level", "Citation", "Link", "What it supports"],
          [list(s) for s in SOURCES], (7, 24, 11, 14, 88, 56, 80),
          wrap_cols=("E", "F", "G"))

    # ---------- Patents ----------
    sheet(wb, "Patents",
          ["Publication number", "Title", "Applicant / assignee", "Earliest priority",
           "Publication date", "Species", "Why it is here"],
          [list(p) for p in PATENTS], (22, 60, 34, 15, 15, 26, 64),
          wrap_cols=("B", "C", "G"))

    # ---------- Method and limits ----------
    ws = wb.create_sheet("Method_and_limits")
    ws["A1"] = "Method"
    ws["A1"].font = TITLE
    method = [
        f"Date of analysis: {ACCESSED}.",
        "Genomes: the RefSeq annotated assemblies named on the Overview sheet, downloaded from NCBI "
        "Datasets as GenBank flat files. Existing gene annotation was used; no genes were re-predicted.",
        "Cluster detection: antiSMASH 8.0.4 (bioconda build) in fungal mode, with KnownClusterBlast "
        "and ClusterCompare against MIBiG. Databases downloaded with download-antismash-databases "
        "on the date above.",
        "Similarity (%) is antiSMASH's own KnownClusterBlast score: the share of the reference "
        "cluster's genes with a significant BLAST hit in the detected region. Mean identity (%) is "
        "the mean amino-acid identity of those best-hit pairs, computed in this analysis.",
        "Literature: PubMed searches on each species plus the cited papers' own content. Every "
        "source is listed on the Sources sheet with what it supports.",
        "Patents: Google Patents searches per species and theme. The Patents sheet is a starting "
        "point, not a cleared landscape, and it is not freedom-to-operate advice.",
        "Everything in this workbook can be regenerated from the public pipeline in the repository "
        "named in the report, on a clean machine, with one command.",
    ]
    r = 2
    for m in method:
        ws.cell(row=r, column=1, value=m)
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="What this analysis does not tell you").font = TITLE
    r += 1
    for l in LIMITS:
        ws.cell(row=r, column=1, value=l)
        r += 1
    ws.column_dimensions["A"].width = 120
    for row in ws.iter_rows(min_row=2, max_row=r):
        for c in row:
            if c.font.size != 14:
                c.font = BODY
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if c.value and len(str(c.value)) > 110:
                ws.row_dimensions[c.row].height = 15 * (len(str(c.value)) // 110 + 1)

    wb.save(OUT)
    print("wrote", OUT, "sheets:", wb.sheetnames)


if __name__ == "__main__":
    main()
