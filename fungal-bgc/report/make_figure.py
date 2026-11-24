"""Figure 1: BGC cluster types per genome.

Form: grouped horizontal bars - the job is comparing magnitude across one
category axis (cluster type) for three named entities, so bars, one axis, and a
legend plus direct value labels (the aqua series is below 3:1 on the surface, and
the palette validator requires visible labels as relief).
Palette: categorical slots 1-3 of the default theme, validated with
scripts/validate_palette.js (all checks pass, contrast WARN relieved by labels).
"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import GENOMES, RES

SERIES = {"Rhizomucor pusillus CBS 183.67": "#2a78d6",
          "Fusarium venenatum A3/5": "#eb6834",
          "Aspergillus oryzae RIB40": "#1baf7a"}
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
# Keep related types together rather than ordering by count, so the reader can
# compare families (PKS, NRPS, terpene, other) across the three genomes.
ORDER = ["T1PKS", "T3PKS", "NRPS", "NRPS-like", "terpene", "terpene-precursor",
         "indole", "NI-siderophore", "NRP-metallophore", "fungal-RiPP",
         "isocyanide", "isocyanide-nrp", "betalactone", "nitropropanoic_acid"]


def counts():
    out = {}
    for acc, sp in GENOMES.items():
        c = {}
        with open(f"{RES}/{acc}/regions.tsv") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                for p in r["products"].split(";"):
                    c[p] = c.get(p, 0) + 1
        out[sp] = c
    return out


def main(out_path):
    data = counts()
    seen = [t for t in ORDER if any(t in c for c in data.values())]
    extra = sorted({t for c in data.values() for t in c} - set(ORDER))
    types = seen + extra
    n = len(types)
    fig, ax = plt.subplots(figsize=(7.1, 0.42 * n + 1.1), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    h = 0.24
    ys = range(n)
    for i, (sp, color) in enumerate(SERIES.items()):
        offs = (1 - i) * (h + 0.02)  # 2px-equivalent gap between adjacent bars
        vals = [data[sp].get(t, 0) for t in types]
        bars = ax.barh([y + offs for y in ys], vals, height=h, color=color,
                       label=sp, zorder=3)
        for b, v in zip(bars, vals):
            if v:
                ax.text(b.get_width() + 0.35, b.get_y() + h / 2, str(v),
                        va="center", ha="left", fontsize=7, color=INK2, zorder=4)

    ax.set_yticks(list(ys))
    ax.set_yticklabels([t.replace("_", " ") for t in types], fontsize=8, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Biosynthetic gene cluster regions detected", fontsize=8, color=INK2)
    ax.tick_params(axis="x", labelsize=7, colors=INK2, length=0)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(max(c.values()) for c in data.values()) + 3)
    ax.xaxis.grid(True, color="#e6e5e1", linewidth=0.6, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    leg = ax.legend(fontsize=7.5, frameon=False, loc="lower right",
                    labelcolor=INK, handlelength=1.1, handleheight=0.8)
    for t in leg.get_texts():
        t.set_fontstyle("italic")
    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, facecolor=SURFACE)
    print("wrote", out_path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "figure1.png")
