"""Assemble the mini-report PDF."""
import os, sys
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, NextPageTemplate, PageBreak,
                                Paragraph, Spacer, Table, TableStyle)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import GENOMES, load
from findings import FINDINGS, LIMITS
from make_pdf import (BAND, FTAB, FW, INK2, NAVY, RULE, Doc, P, S, findings_for,
                      hits_table, overview_rows, table)
from sources import ACCESSED, PATENTS, SOURCES

FIG = os.path.expanduser("~/work/figure1.png")
FOOTER = ("Xerabinet · sample analysis · Andri Binet, PhD (c) · modbinet@gmail.com · "
          "scientific intelligence, not regulatory advice")


def cover(st):
    st += [Spacer(1, 26 * mm),
           P("Secondary-metabolite gene clusters in three fungal genomes used for food protein",
             "title"),
           P("<i>Rhizomucor pusillus</i> · <i>Aspergillus oryzae</i> · <i>Fusarium venenatum</i>",
             "subtitle"),
           Spacer(1, 4 * mm),
           P("A sample intelligence report. Public genomes mined with antiSMASH 8 and compared "
             "with the MIBiG reference set of characterised clusters, then read against the "
             "published literature and the patent record.", "body"),
           Spacer(1, 6 * mm)]
    meta = [["Prepared by", "Andri Binet, PhD (c) — CEO, Xerabinet"],
            ["Date", "24 November 2026"],
            ["Analysis and sources", f"All data generated and all sources read on {ACCESSED}"],
            ["Reproducibility",
             "Pipeline and raw outputs: github.com/andrijesus24-design/aq-sensor-calibration "
             "(folder fungal-bgc)"],
            ["Companion files",
             "Evidence matrix (Excel, 8 sheets) · Two-page summary"],
            ["Scope",
             "Public reference strains only. This is scientific intelligence, not regulatory, "
             "legal or freedom-to-operate advice."]]
    t = Table([[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in meta],
              colWidths=[34 * mm, 128 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE)]))
    st += [t, Spacer(1, 10 * mm),
           P("Why this sample exists", "h2"),
           P("Companies making protein by fermentation are increasingly asked what else their "
             "production organism can make. The question is answerable from the genome before "
             "anyone runs a single assay, and the answer is a map: which biosynthetic gene "
             "clusters are there, which ones resemble clusters whose chemistry is already known, "
             "and which ones nobody has characterised. This report is that map for three genomes, "
             "built the way we build them for clients, with every claim traceable and every limit "
             "stated.", "body"),
           NextPageTemplate("body"), PageBreak()]
    return st


def summary_section(st, rows):
    st += [P("Executive summary", "h1"),
           P("Three public fungal genomes central to food-protein fermentation were mined for "
             "secondary-metabolite biosynthetic gene clusters (BGCs): the <i>Rhizomucor pusillus</i> "
             "type strain, <i>Aspergillus oryzae</i> RIB40 and <i>Fusarium venenatum</i> A3/5, the "
             "Quorn strain. The three differ by a factor of eight in cluster count at similar "
             "genome sizes.", "body")]
    st += [table(["Species / strain", "Assembly", "Size (Mb)", "Seqs.", "BGC regions",
                  "MIBiG match ≥70%", "On contig edge"],
                 overview_rows(rows),
                 [46 * mm, 29 * mm, 17 * mm, 13 * mm, 20 * mm, 24 * mm, 21 * mm],
                 align_right=(2, 3, 4, 5, 6)),
           Paragraph("Table 1. What was found in each genome. “MIBiG match ≥70%” counts regions "
                     "where at least 70% of a characterised reference cluster's genes have a hit; "
                     "contig-edge regions may be truncated by the assembly.", S["cap"])]
    st += [P("Four results stand out.", "body"),
           P("<b>1. Host choice sets the size of the characterisation job.</b> "
             "<i>R. pusillus</i> carries 10 cluster regions, <i>F. venenatum</i> 45 and "
             "<i>A. oryzae</i> 80. A company whose host has ten clusters has a tractable list; one "
             "with eighty has a programme.", "body"),
           P("<b>2. In <i>R. pusillus</i>, almost nothing is characterised.</b> Nine of its ten "
             "regions have no match in MIBiG at all, and no polyketide synthase or complete NRPS "
             "was detected. That is a genuinely small repertoire, consistent with published work on "
             "thermophiles and Mucoromycota — but “uncharacterised” is not the same as “absent”, "
             "because Mucorales are thinly represented in the reference set.", "body"),
           P("<b>3. In <i>A. oryzae</i> RIB40, the partial aflatoxin region is visible in the "
             "numbers.</b> It matches three MIBiG aflatoxin clusters at 52% similarity but 98–100% "
             "amino-acid identity: nearly identical genes over roughly half the reference cluster, "
             "the signature of a cluster that has lost part of itself. The same genome carries an "
             "intact 3-nitropropanoic acid region with <i>npaA</i> and <i>npaB</i> — the pathway "
             "that one industrial lineage reports having deleted.", "body"),
           P("<b>4. In <i>F. venenatum</i> A3/5, the trichothecene cluster is where the literature "
             "says it is</b>, matching the MIBiG T-2 toxin cluster at 50% similarity and 89% "
             "identity. Sequence alone does not say whether the compound is made; published work on "
             "this species shows the pathway is functional in at least some strains.", "body"),
           Spacer(1, 2 * mm),
           P("Everything below is traceable: each finding names its basis, the file that holds the "
             "underlying numbers, and the sources behind it. The limits of the method are stated in "
             "their own section rather than buried.", "body"),
           PageBreak()]
    return st


def method_section(st):
    st += [P("What was done", "h1"),
           P("Three annotated RefSeq assemblies were downloaded from NCBI Datasets and run through "
             "antiSMASH 8.0.4 in fungal mode, using the existing gene annotation rather than "
             "re-predicting genes. Each detected region was compared with MIBiG, the reference set "
             "of experimentally characterised biosynthetic gene clusters, by antiSMASH's own "
             "KnownClusterBlast and ClusterCompare. The published literature for each species was "
             "then read against those results, and the patent record searched for the commercial "
             "context.", "body"),
           P("Two numbers appear beside every match, and they must be read together:", "body"),
           P("<b>Similarity (%)</b> is the share of the reference cluster's genes that have a "
             "significant hit in the detected region. It says how much of a known cluster is "
             "present.", "quote"),
           P("<b>Mean identity (%)</b> is the mean amino-acid identity of those matched gene pairs. "
             "It says how close the shared genes actually are.", "quote"),
           P("High similarity with low identity means the gene set lines up but the proteins are "
             "distant relatives — a cluster of the same architecture, not the same chemistry. Low "
             "similarity with very high identity means part of a known cluster is present in almost "
             "unchanged form, and the rest is missing. The second pattern is what a partial or "
             "deleted cluster looks like from the outside, and it is visible twice in this report.",
             "body"),
           P("The whole pipeline is public and runs on a clean machine with one command. Raw "
             "antiSMASH outputs, region GenBank files and the per-genome tables are committed "
             "alongside it, so any number in this report can be traced to the file it came from.",
             "body"),
           Spacer(1, 3 * mm),
           Image(FIG, width=163 * mm, height=163 * mm * 0.98, kind="proportional"),
           Paragraph("Figure 1. Cluster types detected in each genome. <i>A. oryzae</i> leads in "
                     "every polyketide and non-ribosomal peptide category; <i>R. pusillus</i> has "
                     "neither, and what it has is mostly terpene and siderophore machinery.",
                     S["cap"]),
           PageBreak()]
    return st


def species_section(st, title, acc, prefix, intro, note=None, hit_min=40, hit_limit=None):
    st += [P(title, "h1")] + [P(x, "body") for x in intro]
    st += [table(FTAB, findings_for(prefix), FW),
           Paragraph("Each finding states whether it was computed here, taken from the literature, "
                     "or inferred. Source IDs resolve in the Sources section and in the Excel "
                     "matrix.", S["cap"])]
    st += [P("Regions matching a characterised cluster", "h2"),
           hits_table(acc, minimum=hit_min, limit=hit_limit),
           Paragraph("Best MIBiG match per region, matches below 40% similarity omitted. The full "
                     "list, including every region with no match, is in the Excel matrix "
                     "(sheets <i>Clusters</i> and <i>MIBiG_matches</i>).", S["cap"])]
    if note:
        st += [P(note, "body")]
    st += [PageBreak()]
    return st


def limits_section(st):
    st += [P("What this analysis does not tell you", "h1"),
           P("A cluster inventory is a map of potential, not a measurement of what a strain "
             "produces. The honest boundaries:", "body")]
    st += [table(["", "Limit"],
                 [[str(i + 1), l] for i, l in enumerate(LIMITS)],
                 [8 * mm, 154 * mm])]
    st += [Spacer(1, 4 * mm),
           P("Where the method stops, three things take over: expression data under the actual "
             "production conditions, targeted chemistry for the compounds the map flags, and "
             "the same pipeline run on the company's own strain rather than a public reference. "
             "Each is a defined next step rather than an open-ended project.", "body"),
           P("Cross-cutting observations", "h1")]
    st += [table(FTAB, findings_for("Cross"), FW)]
    st += [PageBreak()]
    return st


def sources_section(st):
    st += [P("Sources", "h1"),
           P(f"Every source below was read on {ACCESSED}. Evidence level distinguishes primary "
             "studies and data from reviews and from news reporting, so the weight of each claim is "
             "visible. The same table, with what each source supports, is sheet <i>Sources</i> of "
             "the Excel matrix.", "body")]
    rows = []
    for s in SOURCES:
        rows.append([Paragraph(f"<b>{s[0]}</b>", S["cell"]),
                     Paragraph(f"{s[4]}<br/><font size=7 color='#52514e'>{s[5]}</font>",
                               S["cell"]),
                     s[3]])
    st += [table(["ID", "Citation", "Level"], rows, [12 * mm, 128 * mm, 22 * mm])]
    st += [P("Patent record", "h1"),
           P("A starting point, not a cleared landscape, and not freedom-to-operate advice. "
             "Searched on Google Patents by species and theme.", "body")]
    prows = [[Paragraph(f"<b>{p[0]}</b>", S["cell"]), p[1], p[2], p[3]] for p in PATENTS]
    st += [table(["Publication", "Title", "Applicant", "Priority"], prows,
                 [26 * mm, 70 * mm, 46 * mm, 20 * mm])]
    return st


def closing(st):
    st += [P("About this sample", "h1"),
           P("Xerabinet produces fixed-price scientific intelligence for fermentation and biotech "
             "teams: literature and patent landscapes, public genome and omics mining, and written "
             "analysis answering one decision question. Work is AI-assisted and verified by a "
             "scientist; this report names what was computed, what was read, and what remains "
             "unknown.", "body"),
           P("A report of this kind is normally scoped to a company's own strain and its own "
             "question — which clusters the production strain carries, how it compares with the "
             "public reference, and what a reviewer is likely to ask about. Deliverables are this "
             "PDF, the Excel evidence matrix and a two-page summary.", "body"),
           Spacer(1, 4 * mm),
           P("Andri Binet, PhD (c) — CEO, Xerabinet · modbinet@gmail.com", "h2"),
           P("Pipeline and raw results: github.com/andrijesus24-design/aq-sensor-calibration "
             "(folder <font face='DJS-B'>fungal-bgc</font>)", "small")]
    return st


def build(out):
    rows = load()
    st = []
    st = cover(st)
    st = summary_section(st, rows)
    st = method_section(st)
    st = species_section(
        st, "Rhizomucor pusillus — a small, largely uncharacterised repertoire",
        "GCF_041956525.1", "Rhizomucor",
        ["<i>Rhizomucor pusillus</i> is a thermophilic member of the Mucorales used as a source of "
         "fungal biomass for food. The type strain's genome (25.4 Mb, 48 scaffolds) yields the "
         "smallest cluster count of the three by a wide margin.",
         "The notable result is not the count but what it is made of: seven terpene or "
         "terpene-precursor regions, two siderophore regions and one NRPS-like region, with no "
         "polyketide synthase and no complete non-ribosomal peptide synthetase detected anywhere "
         "in the genome. For a food organism, the absence of PKS and NRPS machinery is the "
         "headline, because most fungal mycotoxins of regulatory concern come from exactly those "
         "two families."],
        note="Only one of the ten regions matches anything characterised, and that match — a "
             "terpene cyclase at 54% mean identity — is too distant to name a compound; at that "
             "level it is as consistent with primary sterol metabolism as with a specialised "
             "pathway. The remaining nine are, as far as the public reference set goes, unknown. "
             "That is the honest result, and it is also the reason this kind of genome deserves "
             "expression data rather than another sequence comparison.")
    st = species_section(
        st, "Aspergillus oryzae RIB40 — eighty clusters, and two that answer specific questions",
        "GCF_000184455.2", "Aspergillus",
        ["<i>A. oryzae</i> is the koji mould, used for centuries in fermented foods and now as a "
         "host for precision fermentation. RIB40 is its reference strain. Its genome carries 80 "
         "cluster regions, 18 of which match a characterised cluster at 70% similarity or better: "
         "a well-studied repertoire by fungal standards, and still mostly uncharacterised in "
         "absolute terms.",
         "Two regions illustrate what a cluster inventory adds to a species-level statement. The "
         "aflatoxin region shows the arithmetic signature of a partial cluster — half the "
         "reference genes present, at essentially identical sequence — which matches the published "
         "account of a chromosome-end deletion in this lineage. And the 3-nitropropanoic acid "
         "region is present and intact, with <i>npaA</i> and <i>npaB</i> called as its core genes, "
         "in a reference strain; an industrial lineage has reported deleting precisely that region."],
        note="A third point is easy to miss: a ustiloxin-like RiPP region (68% similarity, 91% "
             "identity). Ustiloxin B is a cyclic peptide described from a rice pathogen and later "
             "shown to be produced by <i>A. flavus</i>. It is not one of the three mycotoxins "
             "routinely monitored in koji strains, which is exactly the kind of gap a genome-wide "
             "inventory is for — it looks at everything, not only at the compounds already on the "
             "panel.")
    st = species_section(
        st, "Fusarium venenatum A3/5 — a clean assembly and a well-mapped chemistry",
        "GCF_900007375.1", "Fusarium",
        ["<i>F. venenatum</i> A3/5 is the mycoprotein strain behind Quorn and the subject of a "
         "genome-scale metabolic model published in November 2026. Its chromosome-level assembly "
         "(38.6 Mb, 5 sequences) gives the cleanest cluster boundaries of the three: 45 regions, "
         "none touching a contig edge.",
         "The repertoire is the most thoroughly characterised of the three relative to its size. "
         "Eleven regions match a known cluster at 70% or better, several at 100% similarity with "
         "high identity: aurofusarin (the pigment), culmorin, W493, chrysogine and the enniatin "
         "cluster. For a food product, pigment and off-flavour pathways are as commercially "
         "relevant as toxin pathways, and both show up on the same map."],
        note="The trichothecene region is present, as the published A3/5 genome paper reports. Its "
             "numbers — 50% similarity, 89% identity against the MIBiG T-2 toxin cluster — say the "
             "cluster is there and related, not that the compound is produced. Published work on "
             "this species is unambiguous that the pathway can be functional: deleting <i>tri5</i> "
             "abolished diacetoxyscirpenol production in a strain of this species. This is the "
             "clearest illustration in the report of why a cluster inventory has to be read "
             "alongside the literature rather than on its own.")
    st = limits_section(st)
    st = sources_section(st)
    st = closing(st)
    Doc(out, FOOTER).build(st)
    print("wrote", out)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "report.pdf")
