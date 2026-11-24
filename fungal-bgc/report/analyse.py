"""Consolidate antiSMASH results of the three genomes into one table.
MIBiG similarity = antiSMASH's own KnownClusterBlast 'similarity' score (% of the
reference cluster's genes with a BLAST hit). Mean identity = mean % amino-acid
identity of the best hit pairs between query and reference proteins."""
import csv, gzip, json, statistics, os
RES = os.path.expanduser("~/repo/fungal-bgc/results")
GENOMES = {"GCF_041956525.1": "Rhizomucor pusillus CBS 183.67",
           "GCF_000184455.2": "Aspergillus oryzae RIB40",
           "GCF_900007375.1": "Fusarium venenatum A3/5"}

def load():
    rows = []
    for acc, sp in GENOMES.items():
        regions = {r["region"]: r for r in csv.DictReader(open(f"{RES}/{acc}/regions.tsv"), delimiter="\t")}
        d = json.load(gzip.open(f"{RES}/{acc}/compact.json.gz", "rt"))
        kcb = {}
        for rec in d["records"]:
            for res in rec["knowncluster"]:
                kcb[f"{rec['id']}.region{res['region_number']:03d}"] = res["ranking"]
        for rid, r in regions.items():
            hits = []
            for c, s in kcb.get(rid, [])[:3]:
                idents = [p[2]["perc_ident"] for p in s.get("pairings", [])]
                hits.append({"mibig": c["accession"], "compound": c["description"],
                             "mibig_class": c["cluster_type"], "similarity": s.get("similarity", 0),
                             "mean_identity": round(statistics.mean(idents)) if idents else None})
            rows.append({"species": sp, "accession": acc, **r, "hits": hits})
    return rows

if __name__ == "__main__":
    rows = load()
    for sp in GENOMES.values():
        rs = [r for r in rows if r["species"] == sp]
        hi = [r for r in rs if r["hits"] and r["hits"][0]["similarity"] >= 70]
        print(f"\n== {sp}: {len(rs)} regions; {len(hi)} with a MIBiG match >=70%; contig-edge {sum(r['contig_edge']=='True' for r in rs)}")
        for r in rs:
            h = r["hits"][0] if r["hits"] else None
            if h and h["similarity"] >= 40:
                print(f"  {r['region']:28s} {r['products']:28s} {h['mibig']:14s} {h['compound'][:45]:45s} sim={h['similarity']:3d} id={h['mean_identity']}")
