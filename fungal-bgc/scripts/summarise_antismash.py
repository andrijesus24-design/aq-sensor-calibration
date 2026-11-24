"""Summarise an antiSMASH output directory into small, reviewable tables.

Usage: python summarise_antismash.py <antismash_out_dir> <basename> <dest_dir>

Writes to <dest_dir>:
  regions.tsv          one row per BGC region, with its core biosynthetic genes and
                       the best KnownClusterBlast (MIBiG) match
  mibig_hits.tsv       up to 5 MIBiG matches per region, with similarity
  core_genes.tsv       one row per core biosynthetic gene
  regions/*.gbk        antiSMASH region GenBank files (open in any genome viewer)
  compact.json.gz      region areas and comparison results, without sequences

"MIBiG similarity" is computed as antiSMASH's web report does: the share of the
reference cluster's proteins with a significant BLAST hit in the query region.
It says how much of a known cluster is present, not that the compound is made.
"""
import csv
import glob
import gzip
import json
import os
import shutil
import sys

from Bio import SeqIO

KCB = "antismash.modules.clusterblast"
CC = "antismash.modules.cluster_compare"


def region_core_genes(gbk_path):
    """Return region-level info and core biosynthetic genes from a region GenBank file."""
    rec = SeqIO.read(gbk_path, "genbank")
    info = {"contig_edge": "", "products": "", "n_cds": 0}
    core = []
    for f in rec.features:
        if f.type == "region":
            info["contig_edge"] = f.qualifiers.get("contig_edge", [""])[0]
            info["products"] = ";".join(f.qualifiers.get("product", []))
        elif f.type == "CDS":
            info["n_cds"] += 1
            if "biosynthetic" in f.qualifiers.get("gene_kind", []):
                q = f.qualifiers
                core.append({
                    "locus_tag": q.get("locus_tag", [""])[0],
                    "protein_id": q.get("protein_id", [""])[0],
                    "ncbi_product": q.get("product", [""])[0],
                    "gene_functions": " | ".join(q.get("gene_functions", []))[:300],
                    "domains": ";".join(q.get("NRPS_PKS", []))[:300],
                })
    return info, core


def main(out_dir, base, dest):
    os.makedirs(os.path.join(dest, "regions"), exist_ok=True)
    data = json.load(open(os.path.join(out_dir, base + ".json")))
    region_rows, hit_rows, core_rows, compact = [], [], [], []
    for rec in data["records"]:
        rid = rec["id"]
        mods = rec.get("modules", {})
        kcb = {}
        known = mods.get(KCB, {}).get("knowncluster", {})
        for res in known.get("results", []):
            kcb[res["region_number"]] = res["ranking"]
        compact.append({"id": rid,
                        "areas": rec.get("areas", []),
                        "knowncluster": known.get("results", []),
                        "cluster_compare": mods.get(CC, {})})
        for i, area in enumerate(rec.get("areas", []), start=1):
            gbk = os.path.join(out_dir, f"{rid}.region{i:03d}.gbk")
            info, core = region_core_genes(gbk) if os.path.exists(gbk) else ({}, [])
            if os.path.exists(gbk):
                shutil.copy(gbk, os.path.join(dest, "regions"))
            hits = []
            for cluster, score in kcb.get(i, [])[:5]:
                n_prot = len(cluster.get("proteins", [])) or 1
                hits.append({
                    "mibig": cluster.get("accession", ""),
                    "compound": cluster.get("description", ""),
                    "mibig_type": cluster.get("cluster_type", ""),
                    "proteins_hit": score.get("hits", 0),
                    "proteins_total": n_prot,
                    "similarity_pct": round(100 * score.get("hits", 0) / n_prot),
                    "core_gene_hits": score.get("core_gene_hits", ""),
                })
            top = hits[0] if hits else {}
            region_id = f"{rid}.region{i:03d}"
            region_rows.append({
                "accession": base, "record": rid, "region": region_id,
                "start": area["start"], "end": area["end"], "length_bp": area["end"] - area["start"],
                "products": ";".join(area.get("products", [])),
                "contig_edge": info.get("contig_edge", ""), "n_cds": info.get("n_cds", ""),
                "n_core_genes": len(core),
                "core_genes": "; ".join(f"{c['locus_tag'] or c['protein_id']} ({c['ncbi_product']})" for c in core),
                "top_mibig": top.get("mibig", ""), "top_compound": top.get("compound", ""),
                "top_similarity_pct": top.get("similarity_pct", ""),
            })
            for rank, h in enumerate(hits, start=1):
                hit_rows.append({"accession": base, "region": region_id, "rank": rank, **h})
            for c in core:
                core_rows.append({"accession": base, "region": region_id,
                                  "products": ";".join(area.get("products", [])), **c})

    def write(name, rows):
        if not rows:
            open(os.path.join(dest, name), "w").write("")
            return
        with open(os.path.join(dest, name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(rows)

    write("regions.tsv", region_rows)
    write("mibig_hits.tsv", hit_rows)
    write("core_genes.tsv", core_rows)
    with gzip.open(os.path.join(dest, "compact.json.gz"), "wt") as fh:
        json.dump({"antismash_version": data.get("version"), "taxon": data.get("taxon"),
                   "records": compact}, fh)
    print(f"{base}: {len(region_rows)} regions, {len(core_rows)} core genes")


if __name__ == "__main__":
    main(*sys.argv[1:4])
