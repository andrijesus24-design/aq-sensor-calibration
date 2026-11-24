"""Assemble the two-page summary PDF."""
import os, sys
from reportlab.lib.units import mm
from reportlab.platypus import Image, NextPageTemplate, PageBreak, Paragraph, Spacer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import load
from make_pdf import Doc, P, S, overview_rows, table
from sources import ACCESSED

FIG = os.path.expanduser("~/work/figure1.png")
FOOTER = ("Xerabinet · two-page summary · Andri Binet, PhD (c) · modbinet@gmail.com · "
          "scientific intelligence, not regulatory advice")


def build(out):
    rows = load()
    st = [P("Secondary-metabolite gene clusters in three food-protein fungi", "title"),
          P("Two-page summary · 24 November 2026 · Xerabinet sample analysis", "subtitle"),
          Spacer(1, 3 * mm),
          P("<b>The question.</b> What else can a production organism make? For three fungi used "
            "to produce food protein — the <i>Rhizomucor pusillus</i> type strain, "
            "<i>Aspergillus oryzae</i> RIB40 and <i>Fusarium venenatum</i> A3/5, the Quorn strain "
            "— the public genome answers it in outline before any assay is run. Each was mined "
            "with antiSMASH 8 and compared with MIBiG, the reference set of characterised "
            "biosynthetic gene clusters, then read against the published literature.", "body"),
          table(["Species / strain", "Assembly", "Size (Mb)", "Seqs.", "BGC regions",
                 "MIBiG match ≥70%", "On contig edge"],
                overview_rows(rows),
                [46 * mm, 29 * mm, 17 * mm, 13 * mm, 20 * mm, 24 * mm, 21 * mm],
                align_right=(2, 3, 4, 5, 6)),
          Paragraph("All data generated and all sources read on " + ACCESSED +
                    ". Full detail in the mini-report (13 pages) and the evidence matrix "
                    "(Excel, 8 sheets).", S["cap"]),
          P("What was found", "h1"),
          P("<b>Host choice, not only strain engineering, sets the size of the characterisation "
            "job.</b> At similar genome sizes the three differ eightfold: 10 cluster regions in "
            "<i>R. pusillus</i>, 45 in <i>F. venenatum</i>, 80 in <i>A. oryzae</i>. A company whose "
            "host carries ten clusters has a tractable list; one with eighty has a programme.",
            "body"),
          P("<b><i>R. pusillus</i>: a small repertoire, and almost none of it characterised.</b> "
            "Seven terpene or terpene-precursor regions, two siderophore regions, one NRPS-like "
            "region — and no polyketide synthase or complete NRPS anywhere in the genome, the two "
            "families that produce most fungal mycotoxins of concern. Nine of the ten regions have "
            "no MIBiG match at all. That result cuts both ways: the repertoire really is small, "
            "which published work on thermophiles and Mucoromycota predicts, but “uncharacterised” "
            "is not “absent”, because Mucorales are thinly represented in the reference set. This "
            "is a genome that deserves expression data, not another sequence comparison.", "body"),
          P("<b><i>A. oryzae</i> RIB40: the numbers show which clusters are partial.</b> The "
            "aflatoxin region matches three MIBiG aflatoxin clusters at 52% similarity but 98–100% "
            "amino-acid identity — nearly identical genes over roughly half the reference cluster, "
            "the arithmetic signature of a cluster that has lost part of itself, matching the "
            "published account of a chromosome-end deletion. Meanwhile the 3-nitropropanoic acid "
            "region is present and intact, with <i>npaA</i> and <i>npaB</i> as core genes: the "
            "pathway an industrial lineage reports having deleted is still there in the reference "
            "strain. A ustiloxin-like RiPP region also appears (68% similarity, 91% identity) — a "
            "compound outside the three mycotoxins routinely monitored in koji strains.", "body"),
          P("<b><i>F. venenatum</i> A3/5: a clean assembly and a well-mapped chemistry.</b> "
            "Forty-five regions, none touching a contig edge, eleven matching a known cluster at "
            "70% or better: aurofusarin, culmorin, W493, chrysogine, enniatin. The trichothecene "
            "cluster is present, as the published A3/5 genome paper reports, matching the MIBiG "
            "T-2 toxin cluster at 50% similarity and 89% identity. Sequence says the cluster is "
            "there; published work on the species shows the pathway can be functional, since "
            "deleting <i>tri5</i> abolished diacetoxyscirpenol production in a strain of this "
            "species.", "body"),
          NextPageTemplate("body"), PageBreak(),
          Image(FIG, width=116 * mm, height=116 * mm * 0.98, kind="proportional"),
          Paragraph("Figure. Cluster types per genome. <i>A. oryzae</i> leads in every polyketide "
                    "and non-ribosomal peptide category; <i>R. pusillus</i> has neither.",
                    S["cap"]),
          P("How to read the two numbers", "h1"),
          P("<b>Similarity</b> is the share of a characterised reference cluster's genes that have "
            "a hit in the detected region: how much of a known cluster is present. <b>Mean "
            "identity</b> is how close those shared genes are. High similarity with low identity "
            "means same architecture, different chemistry. Low similarity with very high identity "
            "means part of a known cluster, unchanged, and the rest missing — which is what a "
            "deleted or partial cluster looks like from outside. Both numbers are given for every "
            "match in this analysis; neither is a measurement of what the organism produces.",
            "body"),
          P("What this does not tell you", "h1"),
          P("A detected cluster is potential, not product: expression, cultivation conditions and "
            "chemical analysis decide that. No MIBiG match means uncharacterised, not harmless. "
            "Regions on a contig edge may be truncated by the assembly rather than by biology, and "
            "are flagged individually. And these are public reference strains: strains of one "
            "species differ precisely in these clusters, so a company's own strain has to be run "
            "on its own. This is scientific intelligence, not regulatory, legal or "
            "freedom-to-operate advice.", "body"),
          P("Where this came from", "h2"),
          P("Twenty-two sources, each listed with what it supports and whether it is a primary "
            "study, a review or news reporting; eight patent families for commercial context. The "
            "whole pipeline is public and reproducible on a clean machine with one command, with "
            "the raw antiSMASH outputs committed beside it: "
            "github.com/andrijesus24-design/aq-sensor-calibration, folder "
            "<font face='DJS-B'>fungal-bgc</font>. A report of this kind is normally scoped to one "
            "company's strain and one decision question, delivered as a PDF report, an Excel "
            "evidence matrix and this two-page summary.", "body"),
          Spacer(1, 2 * mm),
          P("Andri Binet, PhD (c) — CEO, Xerabinet · modbinet@gmail.com", "h2")]
    Doc(out, FOOTER).build(st)
    print("wrote", out)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "summary.pdf")
