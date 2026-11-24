"""Key findings of the mini-report.

`basis` records where each claim comes from:
  COMPUTED    - produced by this analysis (antiSMASH regions, MIBiG similarity)
  LITERATURE  - stated in a cited published source
  INFERENCE   - our reading of the two above, offered as a hypothesis to test

Each row ends with the open question a client would need answered next, so the
sample shows the limits of the method as plainly as its results.
"""

FINDINGS = [
    # id, species, finding, basis, data pointer, sources, confidence, open question
    ("F1", "Rhizomucor pusillus CBS 183.67",
     "Smallest repertoire of the three genomes: 10 BGC regions, of which 7 are terpene or "
     "terpene-precursor, 2 are NIS-type siderophore clusters and 1 is NRPS-like. No polyketide "
     "synthase and no complete NRPS core gene were detected. One of the siderophore regions sits "
     "on a contig edge of this scaffold-level assembly.",
     "COMPUTED", "results/GCF_041956525.1/regions.tsv (10 rows)", "S20, S22",
     "High for this assembly as annotated",
     "Does the production strain carry the same 10 regions, or additional ones?"),

    ("F2", "Rhizomucor pusillus CBS 183.67",
     "No region matches a characterised mycotoxin cluster in MIBiG. Nine of the ten have no MIBiG "
     "match at all; the tenth matches a terpene cyclase at 54% mean amino-acid identity, which at "
     "that distance is as consistent with primary sterol metabolism as with a toxin pathway.",
     "COMPUTED + INFERENCE", "NW_027192145.1.region001; mibig_hits.tsv", "S20, S21",
     "Medium: MIBiG contains few Mucorales clusters, so 'no match' means 'uncharacterised', not 'absent'",
     "Which of the nine uncharacterised regions are transcribed under production conditions?"),

    ("F3", "Rhizomucor pusillus",
     "The small count agrees with published comparative genomics: thermophilic fungi and "
     "Mucoromycota carry fewer secondary-metabolism genes than Ascomycota.",
     "LITERATURE", "n/a", "S15, S16", "High (two independent studies)",
     ""),

    ("F4", "Rhizomucor pusillus",
     "Published safety work on the food strain CBS 143028 screened for protein toxins, virulence "
     "factors and resistance determinants and found none, and found no clinically relevant "
     "mycotoxins in vitro. A genome-wide inventory of biosynthetic gene clusters is not part of "
     "that published work.",
     "LITERATURE", "n/a", "S13, S14", "High for what the papers report",
     "A cluster-level inventory is the gap this kind of analysis fills."),

    ("F5", "Aspergillus oryzae RIB40",
     "Largest repertoire: 80 BGC regions (25 T1PKS, 23 terpene, 17 NRPS, 14 NRPS-like, 7 indole, "
     "4 T3PKS and others). Eighteen regions match a characterised MIBiG cluster at 70% similarity "
     "or more, so a large share of this repertoire is already described in the literature.",
     "COMPUTED", "results/GCF_000184455.2/regions.tsv, mibig_hits.tsv", "S20, S21, S22",
     "High", "Which of the 62 weaker-match regions are relevant to the client's product?"),

    ("F6", "Aspergillus oryzae RIB40",
     "The aflatoxin region (NC_036437.1.region010, T1PKS plus indole) matches three MIBiG aflatoxin "
     "clusters at 52% similarity with 98-100% amino-acid identity in the genes that are present. "
     "Very high identity over roughly half the reference cluster is the signature of a partial "
     "cluster, which matches the published account of a large deletion at the end of chromosome 3. "
     "antiSMASH flags this region as touching a contig edge, so its true extent cannot be settled "
     "from this assembly alone.",
     "COMPUTED + LITERATURE", "NC_036437.1.region010; mibig_hits.tsv", "S07, S09, S21",
     "Medium-high: the pattern is clear, the exact breakpoint is not",
     "Mapping the breakpoint needs read-level or long-read data, not this assembly."),

    ("F7", "Aspergillus oryzae RIB40",
     "A 3-nitropropanoic acid region is detected (NC_036440.1.region011, 18 kb, 5 genes), with "
     "npaA and npaB as its core genes. This is the pathway that 21st.BIO's published strain lineage "
     "reports as removed by a 390 kb deletion, so the reference strain carries what their lineage "
     "has lost.",
     "COMPUTED + LITERATURE", "NC_036440.1.region011; core_genes.tsv", "S07, S20",
     "High for the gene calls; the functional claim rests on the cited work",
     "A side-by-side run on the client's own strain would show the deletion directly."),

    ("F8", "Aspergillus oryzae RIB40",
     "Only a weak penicillin signal is seen: region NC_036440.1.region005 matches the MIBiG "
     "penicillin clusters at 18% similarity. A low share of matched genes at 85% identity points to "
     "a few shared genes rather than a complete pathway.",
     "COMPUTED", "NC_036440.1.region005; mibig_hits.tsv", "S20, S21",
     "Medium", "Whether the penicillin cluster is intact needs gene-by-gene inspection."),

    ("F9", "Aspergillus oryzae RIB40",
     "No cyclopiazonic acid cluster is detected. Published work explains this for RIB40 "
     "specifically: its cpaA gene is truncated by a chromosome-end deletion. The absence here is "
     "therefore expected and strain-specific, not a property of the species.",
     "COMPUTED + LITERATURE", "mibig_hits.tsv (no CPA match)", "S07, S09",
     "High", "Any new isolate has to be checked individually."),

    ("F10", "Aspergillus oryzae RIB40",
     "A ustiloxin-like RiPP region is detected (NC_036439.1.region010, 68% similarity, 91% "
     "identity). Ustiloxin B is a cyclic peptide first described from a rice pathogen and later "
     "shown to be made by A. flavus; it is not among the three mycotoxins usually monitored in koji "
     "strains.",
     "COMPUTED + LITERATURE", "NC_036439.1.region010", "S19, S20, S21",
     "Medium-high for the cluster match; production is not shown by sequence alone",
     "Worth checking in any strain intended for food, since routine panels do not cover it."),

    ("F11", "Fusarium venenatum A3/5",
     "Intermediate repertoire: 45 BGC regions (16 terpene, 13 NRPS, 10 T1PKS, 6 NRPS-like and "
     "others). Eleven match a characterised MIBiG cluster at 70% similarity or more. No region "
     "touches a contig edge, so the chromosome-level assembly gives clean cluster boundaries.",
     "COMPUTED", "results/GCF_900007375.1/regions.tsv", "S20, S21, S22",
     "High", ""),

    ("F12", "Fusarium venenatum A3/5",
     "A trichothecene region is detected (NC_038013.1.region010, terpene), matching the MIBiG T-2 "
     "toxin cluster at 50% similarity and 89% identity, and the 15-acetyl-deoxynivalenol cluster at "
     "45%. This is the TRI cluster described in the published A3/5 genome as the type A "
     "trichothecene TRI5 cluster, and a tri5 deletion in F. venenatum was shown to abolish "
     "diacetoxyscirpenol production, so the pathway is functional in at least some strains of the "
     "species.",
     "COMPUTED + LITERATURE", "NC_038013.1.region010", "S01, S03, S20, S21",
     "High that the cluster is present; production depends on strain and conditions",
     "The commercial Quorn process addresses this; any new F. venenatum strain should be checked."),

    ("F13", "Fusarium venenatum A3/5",
     "Several regions match well-characterised Fusarium metabolite clusters at 100% similarity: "
     "aurofusarin (a pigment, 90% identity), culmorin (77%), W493 (89%), chrysogine (85%), "
     "ilicicolin H (56%) and the enniatin cluster (100% similarity, 62% identity).",
     "COMPUTED", "mibig_hits.tsv, GCF_900007375.1", "S20, S21",
     "High for the matches; identity varies, so compound identity is not implied for the weaker ones",
     "Which of these matter for product colour, taste or regulatory dossiers?"),

    ("F14", "Fusarium venenatum A3/5",
     "The genome-scale metabolic model published for A3/5 in November 2026 (iJL1143) is built around "
     "growth and batch fermentation; its abstract does not cover secondary metabolism. Cluster "
     "inventory and flux model answer different questions and are complementary.",
     "LITERATURE + INFERENCE", "n/a", "S04",
     "Medium: only the abstract was read, through an aggregator page",
     "Reading the full preprint would confirm whether any SM reactions are included."),

    ("F15", "Cross-species",
     "The three genomes span a 8-fold range in cluster count (10, 45 and 80) for similar genome "
     "sizes (25-39 Mb). Host choice, not only strain engineering, sets how much secondary-metabolite "
     "characterisation a food or precision-fermentation dossier will require.",
     "COMPUTED + INFERENCE", "all three regions.tsv", "S20, S22",
     "High for the counts; the regulatory reading is ours",
     "What does the relevant authority ask for in each case?"),

    ("F16", "Cross-species",
     "A clavaric-acid-like terpene region appears in all three genomes at 100% similarity but only "
     "47-54% amino-acid identity. Identical similarity scores with low identity illustrate why the "
     "two numbers must be read together: the gene set lines up, the proteins are distant.",
     "COMPUTED", "three regions, one per genome", "S20, S21",
     "High", "A worked example of how these matches should and should not be read."),
]

# Claims we deliberately do not make, listed in the report itself.
LIMITS = [
    "A detected cluster is not a produced compound. Expression, cultivation conditions and "
    "chemical analysis decide that, and none of them is part of this analysis.",
    "A MIBiG match names the closest characterised cluster, not the compound made. Similarity is "
    "the share of the reference cluster's genes with a hit; mean identity says how close those "
    "genes are. Both are given for every match.",
    "No MIBiG match means uncharacterised, not harmless. This matters most for Rhizomucor pusillus, "
    "since Mucorales are thinly represented in the reference set.",
    "Regions touching a contig edge may be truncated by the assembly rather than by biology. Each "
    "one is flagged in the Excel matrix.",
    "Results describe the public reference strains named here, not any company's production strain. "
    "Strains of one species differ precisely in these clusters.",
    "This is scientific intelligence, not regulatory, legal or freedom-to-operate advice.",
]
