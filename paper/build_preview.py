"""Render a PDF *preview* of trace_paper.tex without a LaTeX installation.

It converts the small LaTeX subset the paper uses (sections, lists, booktabs tables, figures, citations,
simple math, the algorithm) to two-column HTML and prints it with headless Chrome. The submission
artifact is the .tex file: compile it with pdflatex + bibtex (e.g. on Overleaf) for the real layout.

    python paper/build_preview.py      # -> paper/trace_paper_preview.pdf
"""
import html
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

MATH = [  # (pattern, html) for the math the paper uses, applied inside $...$ and equations
    (r"\\mathrm\{([^}]*)\}", r"\1"), (r"\\text\{([^}]*)\}", r"\1"), (r"\\textsc\{([^}]*)\}", r"\1"),
    (r"\\underbrace\{(.*?)\}_\{(.*?)\}", r"\1"),
    (r"\\Pr", "Pr"), (r"\\in", "∈"), (r"\\neq", "≠"), (r"\\approx", "≈"), (r"\\wedge", "∧"),
    (r"\\emptyset", "∅"), (r"\\oplus", "⊕"), (r"\\gets", "←"), (r"\\pm", "±"), (r"\\times", "×"),
    (r"\\ast", "*"), (r"\\le", "≤"), (r"\\ge", "≥"), (r"\\cdot", "·"), (r"\\;", " "), (r"\\,", " "), (r"\\ ", " "),
    (r"\\!", ""), (r"\\left", ""), (r"\\right", ""), (r"\\\{", "{"), (r"\\\}", "}"),
    (r"\^\{([^}]*)\}", r"<sup>\1</sup>"), (r"_\{([^}]*)\}", r"<sub>\1</sub>"),
    (r"\^(\w)", r"<sup>\1</sup>"), (r"_(\w)", r"<sub>\1</sub>"), (r"\\Delta", "Δ"), (r"\\hat", ""), (r"\\rho", "ρ"), (r"\\tau", "τ"), (r"\\lambda", "λ"),
    (r"\\alpha", "α"), (r"\\mu", "μ"), (r"\\theta", "θ"), (r"\\sum", "Σ"), (r"\\frac1n", "1/n"),
    (r"\\tfrac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)"), (r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)"),
    (r"\\bar", ""), (r"\\mathbb", ""), (r"\\inf", "inf"), (r"\\to", "→"), (r"\\sqrt", "√"),
    (r"\\mid", "|"), (r"\\downarrow", "↓"), (r"\\Big", ""), (r"\\qquad", "  "), (r"\\quad", " "),
]


def math(s):
    for pat, rep in MATH:
        if re.fullmatch(r"\\\\[A-Za-z]+", pat):
            pat += r"(?![A-Za-z])"     # \in must not eat \inf
        s = re.sub(pat, rep, s)
    return s.replace("{", "").replace("}", "")


def bib_entries():
    text = (HERE / "refs.bib").read_text()
    entries = {}
    for chunk in re.split(r"\n(?=@)", text):
        m = re.match(r"@\w+\{(\w+),(.*)", chunk.strip(), flags=re.S)
        if not m:
            continue
        key, body = m.group(1), m.group(2)

        def field(f):
            fm = re.search(rf"\b{f}\s*=\s*\{{", body)
            if not fm:
                return ""
            depth, i = 1, fm.end()
            while i < len(body) and depth:
                depth += body[i] == "{"
                depth -= body[i] == "}"
                i += 1
            return re.sub(r"\s+", " ", body[fm.end():i - 1]).replace("{", "").replace("}", "")

        names = [a.strip() for a in field("author").split(" and ")]
        authors = ", ".join(n for n in names[:3] if n != "others")
        if len(names) > 3 or "others" in names:
            authors += " et al."
        venue = field("booktitle") or field("journal") or field("howpublished")
        entries[key] = f"{authors}, “{field('title')},” <i>{venue}</i>, {field('year')}."
    return entries


def inline(s, cites):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = s.replace("\\ours{}", "<span class=sc>Trace</span>").replace("\\ours", "<span class=sc>Trace</span>")
    s = re.sub(r"\\cite\{([^}]*)\}", lambda m: "[" + ", ".join(str(cites.setdefault(k.strip(), len(cites) + 1))
                                                              for k in m.group(1).split(",")) + "]", s)
    s = re.sub(r"\$(.+?)\$", lambda m: "<i>" + math(m.group(1)) + "</i>", s)
    for cmd, tag in [("textbf", "b"), ("emph", "i"), ("textit", "i"), ("texttt", "code"), ("textsc", "span class=sc")]:
        for _ in range(3):
            s = re.sub(rf"\\{cmd}\{{([^{{}}]*)\}}", lambda m: f"<{tag}>{m.group(1)}</{tag.split()[0]}>", s)
    s = re.sub(r"\\S\\ref\{[^}]*\}", "§", s)
    s = re.sub(r"(Table|Fig\.|Algorithm|Eq\.)~?\\ref\{[^}]*\}", r"\1", s)
    s = re.sub(r"\\(ref|label)\{[^}]*\}", "", s)
    s = re.sub(r"\\num\{([^}]*)\}", r"\1", s)
    for a, b in [("~", " "), ("---", "—"), ("--", "–"), ("``", "“"), ("''", "”"), ("\\&", "&amp;"), ("\\%", "%"),
                 ("\\_", "_"), ("\\#", "#"), ("\\ldots", "…"), ("\\textasciitilde", "~"), ("\\\\", "<br>"),
                 ("\\checkmark", "✓"), ("\\quad", " "), ("\\small", ""), ("\\footnotesize", ""),
                 ("\\centering", ""), ("\\midrule", ""), ("\\toprule", ""), ("\\bottomrule", ""), ("$", "")]:
        s = s.replace(a, b)
    s = re.sub(r"\\(cmidrule|addlinespace)(\([^)]*\))?(\{[^}]*\})?", "", s)
    return s


def table_html(body, cites):
    body = re.sub(r"\\begin\{tabular\}\{[^}]*\}|\\end\{tabular\}", "", body)
    rows = [r for r in re.split(r"\\\\", body) if r.strip() and not r.strip().startswith("\\caption")]
    out = ["<table>"]
    for i, r in enumerate(rows):
        r = re.sub(r"\\(toprule|midrule|bottomrule|hline)", "", r)
        r = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", r)
        if not r.strip():
            continue
        cells = []
        for c in r.split("&"):
            m = re.match(r"\s*\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}\s*$", c, flags=re.S)
            span, c = (int(m.group(1)), m.group(2)) if m else (1, c)
            c = re.sub(r"\\multirow\{[^}]*\}\{[^}]*\}\{(.*)\}", r"\1", c)
            cells.append(f"<td colspan={span}>{inline(c.strip(), cites)}</td>")
        out.append(f"<tr class={'h' if i == 0 else ''}>{''.join(cells)}</tr>")
    out.append("</table>")
    return "".join(out)


def convert(tex):
    cites = {}
    tex = re.sub(r"\\input\{([^}]*)\}", lambda m: (HERE / (m.group(1) + ("" if m.group(1).endswith(".tex") else ".tex"))).read_text()
                 if (HERE / (m.group(1) + ("" if m.group(1).endswith(".tex") else ".tex"))).exists()
                 else "\\begin{tabular}{l}(pending)\\end{tabular}", tex)
    tex = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", "", tex)
    tex = tex.replace("\\ours{}", "<span class=sc>Trace-PG</span>").replace("\\trace{}", "<span class=sc>Trace</span>")
    tex = re.sub(r"\\begin\{(proposition|theorem)\}(?:\[([^\]]*)\])?",
                 lambda m: f"<b>{m.group(1).capitalize()}{' (' + m.group(2) + ')' if m.group(2) else ''}.</b> <i>", tex)
    tex = re.sub(r"\\end\{(proposition|theorem)\}", "</i>", tex)
    tex = tex.replace("$\\square$", "□")
    tex = re.sub(r"\\TBD\{([^}]*)\}", r"<span class=tbd>\1</span>", tex)
    tex = re.sub(r"\\textsuperscript\{([^}]*)\}", r"<sup>\1</sup>", tex)
    tex = re.sub(r"\{\\scriptsize(\[[^]]*\])\}", r"<small>\1</small>", tex)
    tex = tex.replace("$^{\\ast}$", "<sup>*</sup>").replace("e.g.\\ ", "e.g. ")
    tex = re.sub(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}",
                 lambda m: "<p class=kw><b><i>Index Terms</i>—</b>" + m.group(1).strip() + "</p>", tex, flags=re.S)
    title = re.search(r"\\title\{(.*?)\}\n", tex, flags=re.S).group(1)
    authors = re.search(r"\\IEEEauthorblockN\{(.*?)\}", tex).group(1)
    affil = re.search(r"\\IEEEauthorblockA\{(.*?)\}", tex).group(1)
    body = tex.split("\\maketitle", 1)[1].split("\\bibliographystyle", 1)[0]
    parts = []
    tokens = re.split(r"(\\begin\{(?:abstract|itemize|enumerate|table\*?|figure\*?|equation|algorithm)\}.*?"
                      r"\\end\{(?:abstract|itemize|enumerate|table\*?|figure\*?|equation|algorithm)\})", body, flags=re.S)
    for tok in tokens:
        if tok.startswith("\\begin{abstract}"):
            inner = tok.split("}", 1)[1].rsplit("\\end", 1)[0]
            parts.append(f"<div class=abs><b><i>Abstract</i>—</b>{inline(inner, cites)}</div>")
        elif tok.startswith(("\\begin{itemize}", "\\begin{enumerate}")):
            tag = "ul" if "itemize" in tok[:20] else "ol"
            items = re.split(r"\\item\s*", tok.split("}", 1)[1].rsplit("\\end", 1)[0])[1:]
            parts.append(f"<{tag}>" + "".join(f"<li>{inline(i, cites)}</li>" for i in items) + f"</{tag}>")
        elif tok.startswith("\\begin{table"):
            cap = re.search(r"\\caption\{(.*?)\}\s*(\\label|\n)", tok, flags=re.S)
            wide = "wide" if tok.startswith("\\begin{table*}") else ""
            parts.append(f"<div class='tbl {wide}'><div class=cap>TABLE. {inline(cap.group(1), cites) if cap else ''}</div>"
                         f"{table_html(re.search(r'\\begin\{tabular\}.*?\\end\{tabular\}', tok, flags=re.S).group(0), cites)}</div>")
        elif tok.startswith("\\begin{figure"):
            img = re.search(r"\\includegraphics(\[[^]]*\])?\{([^}]*)\}", tok).group(2)
            img = img.replace(".pdf", ".png")
            cap = re.search(r"\\caption\{(.*?)\}\s*(\\label|\n|\\end)", tok, flags=re.S)
            wide = "wide" if tok.startswith("\\begin{figure*}") else ""
            parts.append(f"<figure class='{wide}'><img src='{img}'><figcaption>Fig. {inline(cap.group(1), cites) if cap else ''}"
                         "</figcaption></figure>")
        elif tok.startswith("\\begin{equation}"):
            inner = tok.split("}", 1)[1].rsplit("\\end", 1)[0]
            inner = re.sub(r"\\label\{[^}]*\}", "", inner)
            inner = re.sub(r"\\underbrace\{(.*?)\}_\{\\text\{(.*?)\}\s*(.*?)\}",
                           lambda m: f"<span class=ub>{math(m.group(1))}<small>{m.group(2)} {math(m.group(3))}</small></span>", inner)
            parts.append(f"<div class=eq><i>{math(inner)}</i><span>(1)</span></div>")
        elif tok.startswith("\\begin{algorithm}"):
            cap = re.search(r"\\caption\{(.*?)\}", tok).group(1)
            lines = re.findall(r"\\(State|If|For|EndIf|EndFor|Return)\b(.*)", tok)
            out = [f"<div class=alg><div class=cap><b>Algorithm 1:</b> {inline(cap, cites)}</div><ol>"]
            for kw, rest in lines:
                rest = rest.replace("\\EndIf", "").replace("\\Return", "<b>return</b>")
                text = {"If": "<b>if</b> ", "For": "<b>for</b> ", "Return": "<b>return</b> "}.get(kw, "")
                if kw in ("EndIf", "EndFor"):
                    continue
                if kw in ("If", "For"):
                    depth, end = 0, 0
                    for i, ch in enumerate(rest):
                        depth += ch == "{"
                        depth -= ch == "}"
                        if depth == 0 and ch == "}":
                            end = i
                            break
                    rest = rest[1:end] + (" " + rest[end + 1:] if end else "")
                out.append(f"<li>{text}{inline(rest, cites)}</li>")
            parts.append("".join(out) + "</ol></div>")
        else:
            tok = re.sub(r"\\section\*?\{(.*?)\}", lambda m: f"\n\n<h2>{m.group(1)}</h2>\n\n", tok)
            tok = re.sub(r"\\subsection\*?\{(.*?)\}", lambda m: f"\n\n<h3>{m.group(1)}</h3>\n\n", tok)
            for para in re.split(r"\n\s*\n", tok):
                para = para.strip()
                if not para or para.startswith("%"):
                    continue
                p = inline(para, cites)
                parts.append(p if p.startswith("<h") else f"<p>{p}</p>")
    entries = bib_entries()
    refs = "".join(f"<li value={n}>{entries.get(k, k)}</li>" for k, n in sorted(cites.items(), key=lambda x: x[1]))
    # number sections like IEEE (I, II, ...)
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    k = iter(roman)
    doc = "\n".join(parts)
    doc = re.sub(r"<h2>(.*?)</h2>", lambda m: f"<h2>{next(k)}. {m.group(1).upper()}</h2>", doc)
    return f"""<!doctype html><html><head><meta charset=utf-8><style>
@page {{ size: Letter; margin: 0.75in 0.62in; }}
body {{ font-family: 'Times New Roman', Times, serif; font-size: 9.6pt; line-height: 1.22; color: #000; margin: 0; }}
.title {{ text-align: center; font-size: 21pt; line-height: 1.15; margin: 0 0 10px; }}
.auth {{ text-align: center; font-size: 10.5pt; margin-bottom: 2px; }} .aff {{ text-align: center; font-size: 9.5pt; font-style: italic; margin-bottom: 14px; }}
.cols {{ column-count: 2; column-gap: 0.24in; text-align: justify; hyphens: auto; }}
h2 {{ font-size: 9.6pt; text-align: center; font-weight: normal; letter-spacing: .04em; margin: 10px 0 5px; break-after: avoid; }}
h3 {{ font-size: 9.6pt; font-style: italic; font-weight: normal; margin: 8px 0 3px; break-after: avoid; }}
p {{ margin: 0 0 5px; text-indent: 1em; }} .abs {{ font-weight: bold; font-size: 9pt; margin-bottom: 8px; }}
.abs b {{ font-weight: bold; }} ul, ol {{ margin: 3px 0 6px 0; padding-left: 16px; }} li {{ margin-bottom: 2px; }}
.sc {{ font-variant: small-caps; }} code {{ font-family: Menlo, monospace; font-size: 7.8pt; }}
.tbl, figure, .alg, .eq {{ break-inside: avoid; margin: 7px 0; }} .wide {{ column-span: all; }}
.cap {{ font-size: 8pt; text-align: center; margin-bottom: 3px; font-variant: small-caps; }}
table {{ border-collapse: collapse; width: 100%; font-size: 7.6pt; border-top: 1px solid #000; border-bottom: 1px solid #000; }}
td {{ padding: 1.5px 3px; text-align: center; }} td:first-child {{ text-align: left; }} tr.h td {{ border-bottom: 0.6px solid #000; font-weight: bold; }}
figure img {{ width: 100%; }} figcaption {{ font-size: 8pt; text-align: justify; }}
.eq {{ display: flex; justify-content: space-between; align-items: center; padding: 0 6px; font-size: 9.4pt; }}
.ub {{ display: inline-flex; flex-direction: column; align-items: center; border-bottom: 0; }} .ub small {{ font-size: 7pt; border-top: 1px solid #000; }}
.alg {{ border-top: 1px solid #000; border-bottom: 1px solid #000; font-size: 8.4pt; }} .alg .cap {{ text-align: left; font-variant: normal; border-bottom: .6px solid #000; padding: 2px 0; }}
.tbd {{ color: #c00; font-weight: bold; }} .kw {{ font-size: 9pt; text-indent: 0; }} .refs {{ font-size: 7.8pt; padding-left: 18px; }} .note {{ font-size: 7.5pt; color: #666; text-align: center; margin-top: 10px; }}
</style></head><body>
<div class=title>{inline(title, cites)}</div><div class=auth>{inline(authors, cites)}</div><div class=aff>{inline(affil, cites)}</div>
<div class=cols>{doc}<h2>REFERENCES</h2><ol class=refs>{refs}</ol>
<div class=note>Preview rendered from trace_paper.tex without LaTeX; compile the .tex for the camera-ready layout.</div></div>
</body></html>"""


def main():
    tex = (HERE / "trace_paper.tex").read_text()
    out_html = HERE / "trace_paper_preview.html"
    out_html.write_text(convert(tex), encoding="utf-8")
    pdf = HERE / "trace_paper_preview.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", f"--print-to-pdf={pdf}", out_html.resolve().as_uri()],
                   check=True, capture_output=True, timeout=120)
    print(pdf)


if __name__ == "__main__":
    main()
