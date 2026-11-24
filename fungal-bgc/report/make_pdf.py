"""Build the mini-report PDF and the two-page summary PDF."""
import os, sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import GENOMES, RES, load
from findings import FINDINGS, LIMITS
from sources import ACCESSED, PATENTS, SOURCES

L = "/usr/share/fonts/truetype/liberation"
for alias, fn in [("DJS", "LiberationSans-Regular"), ("DJS-B", "LiberationSans-Bold"),
                  ("DJS-I", "LiberationSans-Italic"), ("DJS-BI", "LiberationSans-BoldItalic"),
                  ("DJSe", "LiberationSerif-Regular"), ("DJSe-B", "LiberationSerif-Bold")]:
    pdfmetrics.registerFont(TTFont(alias, f"{L}/{fn}.ttf"))
pdfmetrics.registerFontFamily("DJS", normal="DJS", bold="DJS-B", italic="DJS-I",
                              boldItalic="DJS-BI")
pdfmetrics.registerFontFamily("DJS-B", normal="DJS-B", bold="DJS-B", italic="DJS-BI",
                              boldItalic="DJS-BI")
pdfmetrics.registerFontFamily("DJSe-B", normal="DJSe-B", bold="DJSe-B", italic="DJSe-B",
                              boldItalic="DJSe-B")

NAVY = colors.HexColor("#1F3864")
INK = colors.HexColor("#0b0b0b")
INK2 = colors.HexColor("#52514e")
RULE = colors.HexColor("#d9d8d3")
BAND = colors.HexColor("#f2f4f8")

ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", fontName="DJSe-B", fontSize=21, leading=26,
                            textColor=NAVY, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="DJS", fontSize=11.5, leading=16,
                               textColor=INK2, spaceAfter=4),
    "h1": ParagraphStyle("h1", fontName="DJSe-B", fontSize=14, leading=18, textColor=NAVY,
                         spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="DJS-B", fontSize=10.5, leading=14, textColor=INK,
                         spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DJS", fontSize=9.6, leading=14.4, textColor=INK,
                           alignment=TA_JUSTIFY, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="DJS", fontSize=8.2, leading=11.6, textColor=INK2,
                            alignment=TA_LEFT, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="DJS", fontSize=8, leading=10.6, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DJS-B", fontSize=8, leading=10.6, textColor=INK),
    "cellh": ParagraphStyle("cellh", fontName="DJS-B", fontSize=8, leading=10.6,
                            textColor=colors.white),
    "cap": ParagraphStyle("cap", fontName="DJS-I", fontSize=8.2, leading=11.4, textColor=INK2,
                          spaceBefore=4, spaceAfter=10),
    "quote": ParagraphStyle("quote", fontName="DJS", fontSize=9.4, leading=14, textColor=INK,
                            leftIndent=10, rightIndent=10, spaceBefore=4, spaceAfter=8),
}


def P(t, k="body"):
    return Paragraph(t, S[k])


def table(headers, rows, widths, align_right=()):
    data = [[Paragraph(h, S["cellh"]) for h in headers]]
    for r in rows:
        data.append([c if hasattr(c, "wrap") else Paragraph(str(c), S["cell"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    st = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND])]
    for c in align_right:
        st.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(st))
    return t


class Doc(BaseDocTemplate):
    def __init__(self, path, footer, **kw):
        super().__init__(path, pagesize=A4, leftMargin=20 * mm, rightMargin=18 * mm,
                         topMargin=18 * mm, bottomMargin=18 * mm, **kw)
        self.footer_text = footer
        fw = self.width
        self.addPageTemplates([
            PageTemplate("cover", [Frame(self.leftMargin, self.bottomMargin, fw, self.height,
                                         id="c")], onPage=self._cover),
            PageTemplate("body", [Frame(self.leftMargin, self.bottomMargin, fw, self.height,
                                        id="b")], onPage=self._page),
        ])

    def _rule_and_footer(self, canv, doc, show_page=True):
        canv.saveState()
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.5)
        y = self.bottomMargin - 6 * mm
        canv.line(self.leftMargin, y, self.leftMargin + self.width, y)
        canv.setFont("DJS", 7.4)
        canv.setFillColor(INK2)
        canv.drawString(self.leftMargin, y - 10, self.footer_text)
        if show_page:
            canv.drawRightString(self.leftMargin + self.width, y - 10, str(canv.getPageNumber()))
        canv.restoreState()

    def _cover(self, canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, stroke=0, fill=1)
        canv.restoreState()
        self._rule_and_footer(canv, doc, show_page=False)

    def _page(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.5)
        y = A4[1] - self.topMargin + 6 * mm
        canv.line(self.leftMargin, y, self.leftMargin + self.width, y)
        canv.setFont("DJS", 7.4)
        canv.setFillColor(INK2)
        canv.drawString(self.leftMargin, y + 4,
                        "Secondary-metabolite gene clusters in three food-protein fungi")
        canv.restoreState()
        self._rule_and_footer(canv, doc)


def overview_rows(rows):
    import json
    out = []
    for acc, sp in GENOMES.items():
        rs = [r for r in rows if r["accession"] == acc]
        meta = json.loads(open(f"{RES}/{acc}/assembly_report.jsonl").readline())
        st = meta["assemblyStats"]
        n = int(st.get("numberOfScaffolds") or st.get("numberOfContigs"))
        out.append([Paragraph(f"<i>{sp}</i>", S["cell"]), acc,
                    f"{int(st['totalSequenceLength'])/1e6:.1f}", n, len(rs),
                    sum(1 for r in rs if r["hits"] and r["hits"][0]["similarity"] >= 70),
                    sum(1 for r in rs if r["contig_edge"] == "True")])
    return out


def findings_for(prefix, rows=None):
    out = []
    for f in FINDINGS:
        if f[1].startswith(prefix):
            out.append([Paragraph(f"<b>{f[0]}</b>", S["cell"]), f[2],
                        f"{f[3]}<br/><font size=7 color='#52514e'>{f[6]}</font>",
                        f[5]])
    return out


FTAB = ["ID", "Finding", "Basis and confidence", "Sources"]
FW = [12 * mm, 84 * mm, 42 * mm, 24 * mm]


def hits_table(acc, minimum=40, limit=None):
    rows = [r for r in load() if r["accession"] == acc]
    sel = [r for r in rows if r["hits"] and r["hits"][0]["similarity"] >= minimum]
    sel.sort(key=lambda r: -r["hits"][0]["similarity"])
    if limit:
        sel = sel[:limit]
    body = []
    for r in sel:
        h = r["hits"][0]
        body.append([Paragraph(r["region"].replace(".region", " r"), S["cell"]),
                     r["products"],
                     Paragraph(h["compound"][:60] + (" …" if len(h["compound"]) > 60 else ""),
                               S["cell"]),
                     h["mibig"], h["similarity"], h["mean_identity"],
                     "yes" if r["contig_edge"] == "True" else ""])
    return table(["Region", "Cluster type(s)", "Closest characterised cluster (MIBiG)",
                  "MIBiG ID", "Sim. %", "Ident. %", "Edge"],
                 body, [31 * mm, 28 * mm, 50 * mm, 23 * mm, 12 * mm, 13 * mm, 11 * mm],
                 align_right=(4, 5))
