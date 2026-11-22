"""Shared pieces for the review documents: team details, CSS, HTML helpers, SVG diagram helpers
and the Chrome-based HTML -> PDF renderer."""
import html
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # FinReason/
REVIEWS = ROOT / "reviews"
BUILD = REVIEWS / "build"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ---- details printed on every title page (edit GUIDE before printing) ----------------------
TITLE = "Numerical Reasoning over Financial Reports"
SUBTITLE = "Evaluating Prompting Strategies and Automated Prompt Optimization for Large Language Models"
SHORT = "FinReason"
COURSE = "UE24AM343AB5 — Prompt Engineering and Optimization for Generative AI"
PROGRAM = "B.Tech CSE (AI & ML), Semester 5, PES University"
GUIDE = ""     # e.g. "Prof. A. B. Name" — left empty, the line is omitted
TEAM = [("Gaurav Girish", "PES1UG24AM103"), ("Sunay R Hegde", "PES1UG24AM903"),
        ("Dhruvagouda", "PES1UG24AM089"), ("Hanshal Nagesh", "PES1UG24AM110")]

NAVY, TEAL, AMBER, INK, MUTED, LINE, CARD = "#13294b", "#0e7c86", "#c2610c", "#1b2433", "#5b6678", "#dde3ec", "#f4f7fb"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"

esc = html.escape

# ============================================================================================
# CSS
# ============================================================================================
BASE_CSS = f"""
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; color: {INK}; background: #fff; }}
code, .mono {{ font-family: Menlo, "SF Mono", monospace; font-size: .86em; }}
table {{ border-collapse: collapse; }}
svg text {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
"""

SLIDE_CSS = BASE_CSS + f"""
@page {{ size: 1280px 720px; margin: 0; }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
.slide {{ width: 1280px; height: 720px; position: relative; overflow: hidden; break-after: page;
  padding: 46px 64px 58px 72px; background: #fff; }}
.slide::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 10px; background: {NAVY}; }}
.slide::after {{ content: ""; position: absolute; left: 10px; top: 0; width: 4px; height: 120px; background: {TEAL}; }}
.kicker {{ font-size: 14px; letter-spacing: .14em; text-transform: uppercase; color: {TEAL}; font-weight: 700; }}
.slide h2 {{ font-size: 40px; line-height: 1.15; margin: 4px 0 22px; color: {NAVY}; font-weight: 700; }}
.slide .lead {{ font-size: 23px; color: {MUTED}; margin: -8px 0 16px; line-height: 1.35; }}
.slide ul {{ margin: 0; padding-left: 26px; }}
.slide li {{ font-size: 24px; line-height: 1.38; margin: 0 0 13px; }}
.slide li li {{ font-size: 20px; color: #384457; margin-bottom: 4px; }}
.slide p {{ font-size: 23px; line-height: 1.4; margin: 0 0 12px; }}
.slide .small, .slide .small li {{ font-size: 20px; }}
.slide .tiny {{ font-size: 14px; color: {MUTED}; }}
.footer {{ position: absolute; left: 72px; right: 64px; bottom: 16px; display: flex; justify-content: space-between;
  font-size: 12.5px; color: #8a94a6; border-top: 1px solid {LINE}; padding-top: 7px; }}
.cols {{ display: grid; gap: 28px; }} .c2 {{ grid-template-columns: 1fr 1fr; }} .c3 {{ grid-template-columns: 1fr 1fr 1fr; }}
.c4 {{ grid-template-columns: repeat(4, 1fr); }} .c64 {{ grid-template-columns: 1.5fr 1fr; }} .c46 {{ grid-template-columns: 1fr 1.5fr; }}
.card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 12px; padding: 16px 18px; }}
.card h3 {{ margin: 0 0 10px; font-size: 23px; color: {NAVY}; }}
.card p, .card li {{ font-size: 19.5px; line-height: 1.38; }}
.card.accent {{ border-left: 5px solid {TEAL}; }} .card.warn {{ border-left: 5px solid {AMBER}; }}
.pill {{ display: inline-block; padding: 2px 10px; border-radius: 999px; background: #e3f1f2; color: {TEAL};
  font-size: 13px; font-weight: 700; margin-right: 6px; }}
.big {{ font-size: 56px; font-weight: 800; color: {NAVY}; line-height: 1; }}
.stat {{ text-align: left; }} .stat .lbl {{ font-size: 18px; color: {MUTED}; margin-top: 6px; line-height: 1.3; }}
table.t {{ width: 100%; font-size: 18.5px; }}
.dense table.t {{ font-size: 17px; }} .dense table.t td {{ padding: 5px 8px; }}
table.t th {{ background: {NAVY}; color: #fff; text-align: left; padding: 8px 10px; font-weight: 600; }}
table.t td {{ padding: 8px 10px; border-bottom: 1px solid {LINE}; vertical-align: top; }}
table.t tr:nth-child(even) td {{ background: #f8fafc; }}
table.t td.n, table.t th.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
table.t tr.hl td {{ background: #fff4e5 !important; font-weight: 700; }}
.fig {{ text-align: center; }} .fig img {{ max-width: 100%; }}
.title-slide {{ background: linear-gradient(135deg, {NAVY} 0%, #1d3d6b 60%, {TEAL} 140%); color: #fff; padding: 70px 90px; }}
.title-slide::before, .title-slide::after {{ display: none; }}
.title-slide .kicker {{ color: #9fe3e8; font-size: 16px; }}
.title-slide h1 {{ font-size: 50px; line-height: 1.1; margin: 16px 0 12px; font-weight: 800; }}
.title-slide .sub {{ font-size: 23px; color: #d6e2f3; max-width: 1000px; line-height: 1.35; }}
.title-slide .team {{ position: absolute; left: 90px; right: 90px; bottom: 60px; display: grid;
  grid-template-columns: repeat(4, 1fr); gap: 18px; }}
.title-slide .team div {{ border-top: 2px solid rgba(255,255,255,.35); padding-top: 10px; font-size: 18px; font-weight: 600; }}
.title-slide .team span {{ display: block; font-size: 14px; font-weight: 400; color: #c3d3ea; margin-top: 3px; }}
.title-slide .meta {{ margin-top: 26px; font-size: 17px; color: #c3d3ea; line-height: 1.5; }}
.section-slide {{ background: {NAVY}; color: #fff; display: flex; flex-direction: column; justify-content: center; padding-left: 110px; }}
.section-slide::before, .section-slide::after {{ display: none; }}
.section-slide h2 {{ color: #fff; font-size: 48px; }} .section-slide .kicker {{ color: #9fe3e8; }}
.section-slide p {{ color: #c3d3ea; font-size: 22px; max-width: 900px; }}
.note {{ font-size: 16px; color: {MUTED}; }}
.callout {{ background: #fff6ea; border: 1px solid #f3d3a8; border-radius: 10px; padding: 14px 18px; font-size: 20px; line-height: 1.4; }}
.qbox {{ background: #0f1b2d; color: #e6edf7; border-radius: 10px; padding: 14px 18px; font-family: Menlo, monospace; font-size: 14.5px; line-height: 1.45; white-space: pre-wrap; }}
.refs li {{ font-size: 15px !important; line-height: 1.28 !important; margin-bottom: 2px !important; }}
"""

REPORT_CSS = BASE_CSS + f"""
@page {{ size: A4; margin: 20mm 19mm 20mm 19mm;
  @bottom-center {{ content: counter(page); font: 9pt "Helvetica Neue", Helvetica, sans-serif; color: #777; }}
  @top-right {{ content: var(--running, ""); font: 8.5pt "Helvetica Neue", Helvetica, sans-serif; color: #888; }} }}
@page cover {{ margin: 0; @bottom-center {{ content: none; }} }}
body {{ font-family: Charter, Georgia, "Times New Roman", serif; font-size: 10.6pt; line-height: 1.5; }}
.cover {{ page: cover; height: 297mm; padding: 34mm 24mm 20mm; position: relative; break-after: page;
  background: linear-gradient(160deg, {NAVY} 0%, #1d3d6b 55%, {TEAL} 130%); color: #fff;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
.cover .kicker {{ letter-spacing: .16em; text-transform: uppercase; font-size: 10.5pt; color: #9fe3e8; font-weight: 700; }}
.cover h1 {{ font-size: 28pt; line-height: 1.12; margin: 10mm 0 5mm; }}
.cover .sub {{ font-size: 14pt; color: #d6e2f3; line-height: 1.35; }}
.cover .doc {{ margin-top: 16mm; font-size: 17pt; font-weight: 700; color: #fff; border-left: 4px solid #9fe3e8; padding-left: 5mm; }}
.cover .doc span {{ display: block; font-size: 11pt; font-weight: 400; color: #c3d3ea; margin-top: 2mm; }}
.cover table {{ position: absolute; left: 24mm; right: 24mm; bottom: 34mm; width: calc(100% - 48mm); font-size: 11pt; }}
.cover td {{ padding: 2.2mm 0; border-bottom: 1px solid rgba(255,255,255,.25); }}
.cover .meta {{ position: absolute; left: 24mm; bottom: 14mm; font-size: 9.5pt; color: #c3d3ea; line-height: 1.5; }}
h1.doc-title {{ font-family: "Helvetica Neue", Helvetica, sans-serif; color: {NAVY}; font-size: 20pt; margin: 0 0 4mm; }}
h2 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: {NAVY}; font-size: 15pt; margin: 8mm 0 3mm;
  padding-bottom: 1.5mm; border-bottom: 2px solid {TEAL}; break-after: avoid; }}
h2.newpage {{ break-before: page; margin-top: 0; }}
h3 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: {NAVY}; font-size: 11.8pt; margin: 5mm 0 2mm; break-after: avoid; }}
h4 {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10.5pt; margin: 3.5mm 0 1.5mm; color: #2a3a55; break-after: avoid; }}
p {{ margin: 0 0 2.6mm; text-align: justify; hyphens: auto; }}
ul, ol {{ margin: 0 0 3mm; padding-left: 6mm; }} li {{ margin-bottom: 1.2mm; }}
table.t {{ width: 100%; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 8.6pt; margin: 2mm 0 4mm; break-inside: auto; }}
table.t th {{ background: {NAVY}; color: #fff; text-align: left; padding: 1.6mm 2mm; font-weight: 600; }}
table.t td {{ padding: 1.4mm 2mm; border-bottom: 1px solid {LINE}; vertical-align: top; }}
table.t tr {{ break-inside: avoid; }}
table.t tr:nth-child(even) td {{ background: #f7f9fc; }}
table.t td.n, table.t th.n {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
table.t tr.hl td {{ background: #fff4e5 !important; font-weight: 700; }}
.caption {{ font-family: "Helvetica Neue", Helvetica, sans-serif; font-size: 8.8pt; color: {MUTED}; margin: 1mm 0 4mm; text-align: center; }}
.tcaption {{ font-family: "Helvetica Neue", Helvetica, sans-serif; font-size: 8.8pt; color: {MUTED}; margin: 3mm 0 0; font-weight: 600; }}
figure {{ margin: 3mm 0 2mm; text-align: center; break-inside: avoid; }} figure img, figure svg {{ max-width: 100%; }}
.box {{ background: {CARD}; border: 1px solid {LINE}; border-left: 4px solid {TEAL}; border-radius: 4px; padding: 3mm 4mm; margin: 3mm 0; break-inside: avoid; }}
.box.warn {{ border-left-color: {AMBER}; background: #fffaf3; }}
.box p:last-child, .box ul:last-child {{ margin-bottom: 0; }}
.toc {{ font-family: "Helvetica Neue", Helvetica, sans-serif; font-size: 10pt; }}
.toc li {{ margin-bottom: 1mm; }}
pre {{ font-family: Menlo, monospace; font-size: 8pt; line-height: 1.4; background: #0f1b2d; color: #e6edf7; padding: 3mm 4mm;
  border-radius: 4px; white-space: pre-wrap; break-inside: avoid; }}
.refs li {{ font-size: 9pt; margin-bottom: 1.3mm; text-align: left; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }}
.kv td:first-child {{ font-weight: 600; width: 32%; }}
"""

IEEE_CSS = BASE_CSS + """
@page { size: letter; margin: 0.75in 0.62in 0.9in 0.62in;
  @bottom-center { content: counter(page); font: 8pt "Times New Roman", serif; color: #444; } }
body { font-family: "Times New Roman", Times, serif; font-size: 9.6pt; line-height: 1.2; }
.ieee-title { text-align: center; font-size: 22pt; line-height: 1.12; margin: 0 0 9pt; font-weight: normal; }
.authors { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6pt; text-align: center; font-size: 9.5pt; margin-bottom: 14pt; }
.authors i { display: block; font-size: 8.5pt; }
.cols2 { column-count: 2; column-gap: 0.24in; text-align: justify; }
.cols2 p { margin: 0 0 4pt; text-indent: 1em; hyphens: auto; }
.cols2 p.noindent { text-indent: 0; }
.abstract { font-weight: bold; font-size: 8.8pt; } .abstract i { font-weight: bold; }
.kw { font-weight: bold; font-size: 8.8pt; font-style: italic; margin-bottom: 6pt; }
h2.ie { font-size: 9.6pt; font-variant: small-caps; text-align: center; margin: 9pt 0 4pt; font-weight: normal; letter-spacing: .02em; break-after: avoid; }
h3.ie { font-size: 9.6pt; font-style: italic; margin: 6pt 0 3pt; font-weight: normal; break-after: avoid; }
table.ie { width: 100%; font-size: 7.6pt; margin: 3pt 0 6pt; border-top: 1px solid #000; border-bottom: 1px solid #000; }
table.ie th { border-bottom: 0.6px solid #000; padding: 1.5pt 2.5pt; text-align: left; font-weight: normal; font-variant: small-caps; }
table.ie td { padding: 1.2pt 2.5pt; }
table.ie .n { text-align: right; font-variant-numeric: tabular-nums; }
table.ie tr.hl td { font-weight: bold; }
.tcap { font-size: 7.8pt; text-align: center; font-variant: small-caps; margin: 6pt 0 2pt; }
figure { margin: 4pt 0 6pt; break-inside: avoid; text-align: center; } figure img, figure svg { width: 100%; }
figcaption { font-size: 7.8pt; text-align: justify; margin-top: 2pt; }
.wide { column-span: all; }
.refs { font-size: 7.6pt; padding-left: 16pt; } .refs li { margin-bottom: 1.5pt; text-align: left; }
.eq { text-align: center; margin: 3pt 0; font-style: italic; }
pre.alg { font-family: Menlo, monospace; font-size: 6.9pt; line-height: 1.3; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 3pt 2pt; margin: 4pt 0; white-space: pre-wrap; break-inside: avoid; }
"""


# ============================================================================================
# HTML helpers
# ============================================================================================
def page(title, css, body, running=""):
    run = f':root {{ --running: "{running}"; }}' if running else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f'<style>{css}{run}</style></head><body>{body}</body></html>')


class Deck:
    """Collects slides, numbers them in the footer and records who presents each one."""

    def __init__(self, label):
        self.label = label
        self.slides = []
        self.who = None

    def by(self, name):
        """Every slide added after this call is presented by name (shown in the footer)."""
        self.who = name

    def add(self, kicker, title, body, lead=""):
        self.slides.append(("normal", kicker, title, body, lead, self.who))

    def raw(self, html_, title=""):
        self.slides.append(("raw", html_, title, self.who))

    def section(self, kicker, title, text=""):
        self.raw(f'<section class="slide section-slide"><div class="kicker">{kicker}</div><h2>{title}</h2>'
                 f'<p>{text}</p></section>', title)

    def arrange(self, plan):
        """Reorder slides and set presenters. plan = [(presenter, [title prefixes...]), ...] in presentation order.
        Slides whose title matches no prefix (e.g. results that do not exist yet) are simply absent."""
        def title(sl):
            return sl[2]
        used, out = set(), []
        for who, prefixes in plan:
            for pre in prefixes:
                for i, sl in enumerate(self.slides):
                    if i not in used and title(sl).startswith(pre):
                        used.add(i)
                        out.append(sl[:-1] + (who,))
        missing = [title(sl) for i, sl in enumerate(self.slides) if i not in used]
        if missing:
            raise ValueError(f"slides not placed in the plan: {missing}")
        self.slides = out

    def assignments(self):
        """[(slide number, title, presenter)] in slide order."""
        out = []
        for n, s in enumerate(self.slides, 1):
            out.append((n, s[2], s[-1]) if s[0] == "normal" else (n, s[2] or "Title / closing", s[-1]))
        return out

    def html(self):
        out, n = [], 0
        for s in self.slides:
            n += 1
            if s[0] == "raw":
                out.append(s[1])
                continue
            _, kicker, title, body, lead, who = s
            lead_html = f'<div class="lead">{lead}</div>' if lead else ""
            mid = f'PES University · {COURSE.split(" — ")[0]}'
            out.append(f'<section class="slide"><div class="kicker">{kicker}</div><h2>{title}</h2>{lead_html}'
                       f'{body}<div class="footer"><span>{SHORT} · {self.label}</span>'
                       f'<span>{mid}</span><span>{n}</span></div></section>')
        return "".join(out)


def title_slide(review_label, review_title):
    team = "".join(f"<div>{esc(n)}<span>{u}</span></div>" for n, u in TEAM)
    guide = f"<br>Project guide: {esc(GUIDE)}" if GUIDE else ""
    return (f'<section class="slide title-slide"><div class="kicker">{esc(review_label)} · {esc(review_title)}</div>'
            f'<h1>{TITLE}</h1><div class="sub">{SUBTITLE}</div>'
            f'<div class="meta">{COURSE}<br>{PROGRAM}{guide}</div><div class="team">{team}</div></section>')


def cover(review_label, doc_title, doc_sub):
    rows = "".join(f"<tr><td>{esc(n)}</td><td style='text-align:right'>{u}</td></tr>" for n, u in TEAM)
    guide = f"<br>Project guide: {esc(GUIDE)}" if GUIDE else ""
    return (f'<div class="cover"><div class="kicker">Mini Project · {esc(review_label)}</div><h1>{TITLE}</h1>'
            f'<div class="sub">{SUBTITLE}</div><div class="doc">{doc_title}<span>{doc_sub}</span></div>'
            f'<table>{rows}</table><div class="meta">{COURSE}<br>{PROGRAM}{guide}</div></div>')


def table(headers, rows, num_cols=(), cls="t", highlight=None, widths=None):
    """headers: list of str; rows: list of lists (already formatted strings, HTML allowed)."""
    head = "".join(f'<th class="{"n" if i in num_cols else ""}">{h}</th>' for i, h in enumerate(headers))
    body = []
    for r_i, r in enumerate(rows):
        cls_row = ' class="hl"' if highlight and highlight(r_i, r) else ""
        body.append(f"<tr{cls_row}>" + "".join(
            f'<td class="{"n" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>")
    cols = "<colgroup>" + "".join(f'<col style="width:{w}%">' for w in widths) + "</colgroup>" if widths else ""
    return f'<table class="{cls}">{cols}<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def ul(items, cls=""):
    def item(x):
        if isinstance(x, (list, tuple)):
            return f"<li>{x[0]}{ul(x[1])}</li>"
        return f"<li>{x}</li>"
    return f'<ul class="{cls}">' + "".join(item(i) for i in items) + "</ul>"


def img(path, style=""):
    path = Path(path)
    path = path if path.is_absolute() else REVIEWS / path
    return f'<img src="{path.resolve().as_uri()}" style="{style}">'


# ============================================================================================
# SVG helpers for hand-drawn diagrams
# ============================================================================================
def svg(w, h, inner, style=""):
    defs = (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{NAVY}"/></marker>'
            f'<marker id="aht" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{TEAL}"/></marker></defs>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" style="{style}">{defs}{inner}</svg>'


def box(x, y, w, h, title, lines=(), fill=CARD, stroke=NAVY, title_color=NAVY, fs=15, lfs=12.5, rx=10, sw=1.5, align="middle"):
    tx = x + w / 2 if align == "middle" else x + 12
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>']
    n = len(lines)
    total = fs + (n * (lfs + 4)) + (6 if n else 0)
    ty = y + (h - total) / 2 + fs - 2
    if title:
        out.append(f'<text x="{tx}" y="{ty}" text-anchor="{align}" font-size="{fs}" font-weight="700" fill="{title_color}">{esc(title)}</text>')
    else:
        ty -= fs
    for i, line in enumerate(lines):
        out.append(f'<text x="{tx}" y="{ty + 6 + (i + 1) * (lfs + 4)}" text-anchor="{align}" font-size="{lfs}" fill="#33415a">{esc(line)}</text>')
    return "".join(out)


def arrow(x1, y1, x2, y2, color=NAVY, sw=1.8, dash="", label="", lfs=11.5, marker="ah", lx=None, ly=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#{marker})"/>'
    if label:
        lx = (x1 + x2) / 2 if lx is None else lx
        ly = (y1 + y2) / 2 - 6 if ly is None else ly
        out += f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="{lfs}" fill="{MUTED}">{esc(label)}</text>'
    return out


def path_arrow(d, color=NAVY, sw=1.8, dash="", marker="ah"):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da} marker-end="url(#{marker})"/>'


def text(x, y, s, fs=12, color=MUTED, anchor="middle", weight="400", italic=False):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}" fill="{color}" font-weight="{weight}"{st}>{esc(s)}</text>'


# ============================================================================================
# Rendering
# ============================================================================================
def render_pdf(html_text, out_pdf, name):
    BUILD.mkdir(parents=True, exist_ok=True)
    src = BUILD / f"{name}.html"
    src.write_text(html_text, encoding="utf-8")
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
           "--virtual-time-budget=4000", f"--print-to-pdf={out_pdf}", src.resolve().as_uri()]
    for attempt in range(3):   # headless Chrome occasionally hangs when the machine is busy: retry
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            return out_pdf
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise


# ---- concise versions ----------------------------------------------------------------------
SLIDE_CSS_CONCISE = SLIDE_CSS + f"""
.takeaway {{ position: absolute; left: 72px; right: 64px; bottom: 50px; background: #e3f1f2; border-left: 6px solid {TEAL};
  border-radius: 8px; padding: 12px 18px; font-size: 21px; font-weight: 600; color: {NAVY}; line-height: 1.35; }}
.takeaway::before {{ content: "Key point  "; color: {TEAL}; font-size: 13px; letter-spacing: .12em; text-transform: uppercase; font-weight: 800; margin-right: 8px; }}
.slide li {{ font-size: 26px; margin-bottom: 16px; }}
table.t {{ font-size: 21px; }} table.t td, table.t th {{ padding: 11px 12px; }}
.dense table.t {{ font-size: 18px; }} .dense table.t td, .dense table.t th {{ padding: 7px 10px; }}
.card p, .card li {{ font-size: 20px; }} .slide .small, .slide .small li {{ font-size: 22px; }}
"""

NOTES_CSS = REPORT_CSS + f"""
@page {{ margin: 15mm 16mm 15mm 16mm; }}
body {{ font-size: 10.4pt; line-height: 1.42; }}
.nhead {{ border-bottom: 3px solid {TEAL}; padding-bottom: 3mm; margin-bottom: 4mm; font-family: "Helvetica Neue", Helvetica, sans-serif; }}
.nhead .k {{ color: {TEAL}; font-size: 8.5pt; letter-spacing: .14em; text-transform: uppercase; font-weight: 800; }}
.nhead h1 {{ margin: 1mm 0 1mm; color: {NAVY}; font-size: 17pt; }}
.nhead .t {{ color: {MUTED}; font-size: 8.8pt; }}
h2 {{ font-size: 12.5pt; margin: 5mm 0 2mm; padding-bottom: 1mm; }}
p, li {{ text-align: left; }}
li {{ margin-bottom: 0.8mm; }}
.oneline {{ background: #fff4e5; border-left: 4px solid {AMBER}; padding: 2.5mm 4mm; font-size: 11pt; font-weight: 600; color: {NAVY}; margin: 2mm 0 3mm; }}
.qa dt {{ font-weight: 700; font-family: "Helvetica Neue", Helvetica, sans-serif; font-size: 9.8pt; margin-top: 2mm; color: {NAVY}; }}
.qa dd {{ margin: 0.5mm 0 0 0; }}
.nums {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 2mm 0 3mm; }}
.nums div {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 4px; padding: 2.5mm 3mm; font-family: "Helvetica Neue", Helvetica, sans-serif; font-size: 8.3pt; color: {MUTED}; line-height: 1.3; }}
.nums b {{ display: block; font-size: 15pt; color: {NAVY}; margin-bottom: 1mm; }}
"""


def notes_head(review, title, kind="study notes"):
    team = " · ".join(f"{n} ({u})" for n, u in TEAM)
    return (f'<div class="nhead"><div class="k">{review} · {kind}</div><h1>{title}</h1>'
            f'<div class="t">{TITLE} — {COURSE}<br>{team}</div></div>')
