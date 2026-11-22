"""Visual layer of the FinReason app: one stylesheet and a few small HTML components (page header,
KPI tiles, cards, chips, pipeline stepper, answer card, claim list) plus the chart style.
Page logic lives in app/views/; this file only decides how things look.

Design: a quiet, editorial "private bank" look - warm near-black surfaces, hairline borders,
a champagne accent for the interface, serif display numerals, and chart colours that are
validated for colour-blind readers (blue = Qwen3-1.7B, orange = Qwen3-8B, aqua = ours)."""
import html as _html
import re

import altair as alt
import streamlit as st

# interface colours
GOLD, INK, INK_2, MUTED, FAINT = "#d6b46a", "#eceae4", "#c4c2ba", "#9c9a92", "#6e6c66"
LINE, PANEL, BG = "#23252c", "#121419", "#0b0c0f"
# status colours (always shown together with an icon and a word, never colour alone)
GOOD, BAD, WARN = "#3ccf8e", "#ef6f6f", "#e8b04a"
# chart series colours (validated: scripts/validate_palette.js, dark surface, all pairs pass)
SERIES = ["#3987e5", "#d95926", "#199e70"]
MODEL_COLORS = {"Qwen3-1.7B": SERIES[0], "Qwen3-8B": SERIES[1]}
EVIDENCE, RETRIEVED = "#d6b46a", "#3987e5"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300..800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400..700&display=swap');
:root {
  --bg: #0b0c0f; --panel: #121419; --panel-2: #16181e; --raise: #1a1d24;
  --line: rgba(255,255,255,.075); --line-2: rgba(255,255,255,.13);
  --ink: #eceae4; --ink-2: #c4c2ba; --muted: #9c9a92; --faint: #6e6c66;
  --gold: #d6b46a; --gold-soft: rgba(214,180,106,.12); --gold-line: rgba(214,180,106,.35);
  --good: #3ccf8e; --bad: #ef6f6f; --warn: #e8b04a; --blue: #3987e5; --orange: #d95926; --aqua: #199e70;
  --serif: 'Instrument Serif', 'Times New Roman', serif;
  --sans: 'Inter', system-ui, -apple-system, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --r: 14px; --r-sm: 10px;
}
::selection {background: rgba(214,180,106,.35); color: #fff;}
html, body, .stApp {font-family: var(--sans); font-feature-settings: "cv11", "ss01", "tnum";}
.stApp {
  background:
    radial-gradient(1200px 520px at 50% -220px, rgba(214,180,106,.075), transparent 70%),
    var(--bg) !important;
}
[data-testid="stHeader"] {background: rgba(11,12,15,.82) !important; backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--line);}
[data-testid="stMainBlockContainer"], .block-container {max-width: 1320px; padding-top: 4.6rem !important;
  padding-bottom: 5rem !important;}
[data-testid="stSidebar"] {background: #0e1014 !important; border-right: 1px solid var(--line);}

/* top navigation */
[data-testid="stTopNavLink"], header a[href] {border-radius: 999px !important;}
[data-testid="stTopNavLink"] span, header nav a span {font-weight: 500; letter-spacing: .005em;}

/* typography */
h1, h2, h3, h4 {font-family: var(--sans) !important; letter-spacing: -.015em; color: var(--ink);}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {color: var(--ink-2);}
code {font-family: var(--mono) !important;}
[data-testid="stCaptionContainer"], .stCaption {color: var(--muted) !important;}

/* widgets */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
  font-size: .72rem !important; text-transform: uppercase; letter-spacing: .12em; color: var(--muted) !important;
  font-weight: 600 !important;}
.stButton button, .stDownloadButton button, .stFormSubmitButton button {
  border-radius: 999px !important; font-weight: 600; letter-spacing: .01em; transition: all .15s ease;}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
  background: linear-gradient(180deg, #e3c37c, #c9a456) !important; color: #17140c !important;
  border: 1px solid #e9cd8e !important; box-shadow: 0 6px 22px rgba(214,180,106,.22);}
.stButton button[kind="primary"]:hover {filter: brightness(1.06); transform: translateY(-1px);}
.stButton button[kind="primary"] *, .stFormSubmitButton button[kind="primary"] * {color: #17140c !important;}
.stButton button[kind="primary"]:disabled {opacity: .45; box-shadow: none;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: var(--r) !important;}
div[data-testid="stExpander"] details {border-radius: var(--r) !important; border-color: var(--line) !important;
  background: var(--panel);}
[data-testid="stDataFrame"], [data-testid="stTable"] {border-radius: var(--r-sm); overflow: hidden;}
.stTabs [data-baseweb="tab-list"] {gap: .25rem; border-bottom: 1px solid var(--line);}
.stTabs [data-baseweb="tab"] {height: 2.6rem; padding: 0 .9rem; font-weight: 500; color: var(--muted);}
.stTabs [aria-selected="true"] {color: var(--ink) !important;}
.stTabs [data-baseweb="tab-highlight"] {background: var(--gold) !important; height: 2px;}
[data-testid="stCode"] pre, .stCodeBlock pre {border-radius: var(--r-sm) !important; border: 1px solid var(--line);}
[data-testid="stAlert"] {border-radius: var(--r-sm) !important;}

/* ---------- components ---------- */
.fr-head {display: flex; align-items: flex-end; justify-content: space-between; gap: 2rem;
  padding: .4rem 0 1.4rem; margin-bottom: 1.4rem; border-bottom: 1px solid var(--line);}
.fr-eyebrow {font: 600 .7rem/1 var(--mono); letter-spacing: .18em; text-transform: uppercase; color: var(--gold);
  margin-bottom: .85rem; display: flex; align-items: center; gap: .55rem;}
.fr-eyebrow::before {content: ""; width: 18px; height: 1px; background: var(--gold);}
.fr-title {font-family: var(--serif) !important; font-weight: 400 !important; padding: 0 !important; font-size: clamp(2.3rem, 4.2vw, 3.5rem); line-height: 1.02;
  letter-spacing: -.01em; color: var(--ink); margin: 0;}
.fr-title em {font-style: italic; color: var(--gold);}
.fr-sub {max-width: 760px; margin: .8rem 0 0; font-size: 1.02rem; line-height: 1.6; color: var(--muted);}
.fr-head-side {display: flex; flex-direction: column; align-items: flex-end; gap: .45rem; flex-shrink: 0;}

.fr-pill {display: inline-flex; align-items: center; gap: .45rem; padding: .32rem .75rem; border-radius: 999px;
  border: 1px solid var(--line-2); background: var(--panel); font: 500 .74rem/1.2 var(--mono); color: var(--ink-2);
  white-space: nowrap;}
.fr-dot {width: 7px; height: 7px; border-radius: 50%; background: var(--faint); flex-shrink: 0;}
.fr-dot.good {background: var(--good); box-shadow: 0 0 0 3px rgba(60,207,142,.16);}
.fr-dot.warn {background: var(--warn); box-shadow: 0 0 0 3px rgba(232,176,74,.16);}
.fr-dot.bad {background: var(--bad); box-shadow: 0 0 0 3px rgba(239,111,111,.16);}

.fr-section {margin: 2.4rem 0 1rem;}
.fr-section .k {font: 600 .68rem/1 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--faint);}
.fr-section h3 {font-size: 1.35rem !important; font-weight: 600 !important; margin: .45rem 0 0 !important;
  padding: 0 !important; color: var(--ink) !important;}
.fr-section p {margin: .35rem 0 0; color: var(--muted); font-size: .93rem; max-width: 820px;}

.fr-kpis {display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .9rem; margin: .4rem 0 .6rem;}
.fr-kpi {position: relative; background: linear-gradient(180deg, var(--panel-2), var(--panel)); border: 1px solid var(--line);
  border-radius: var(--r); padding: 1.1rem 1.2rem 1.15rem; overflow: hidden;}
.fr-kpi::after {content: ""; position: absolute; left: 1.2rem; right: 1.2rem; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--tone, var(--gold)), transparent); opacity: .7;}
.fr-kpi .l {font: 600 .66rem/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--muted);}
.fr-kpi .v {font-family: var(--serif); font-size: 2.45rem; line-height: 1.05; color: var(--ink); margin-top: .55rem;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.fr-kpi .v.small {font-family: var(--sans); font-size: 1.28rem; font-weight: 600; margin-top: .75rem; letter-spacing: -.01em;}
.fr-kpi .s {font-size: .82rem; color: var(--muted); margin-top: .4rem;}

.fr-card {background: var(--panel); border: 1px solid var(--line); border-radius: var(--r); padding: 1.15rem 1.25rem;}
.fr-card h4 {margin: 0 0 .35rem !important; padding: 0 !important; font-size: 1rem !important; font-weight: 600 !important;}
.fr-card p {margin: 0; font-size: .9rem; line-height: 1.55; color: var(--muted);}
.fr-grid {display: grid; gap: .9rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));}
.fr-grid.two {grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));}
.fr-card .tag {font: 600 .64rem/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--gold);
  margin-bottom: .6rem; display: block;}
.fr-card .file {font: 500 .72rem/1 var(--mono); color: var(--faint); margin-top: .8rem; display: block;}

.fr-chips {display: flex; flex-wrap: wrap; gap: .4rem;}
.fr-chip {display: inline-flex; align-items: center; gap: .35rem; padding: .26rem .62rem; border-radius: 999px;
  font: 500 .74rem/1.2 var(--sans); border: 1px solid var(--line-2); color: var(--ink-2); background: rgba(255,255,255,.02);}
.fr-chip.gold {border-color: var(--gold-line); color: #ecd49c; background: var(--gold-soft);}
.fr-chip.good {border-color: rgba(60,207,142,.35); color: #8fe6bd; background: rgba(60,207,142,.08);}
.fr-chip.bad {border-color: rgba(239,111,111,.35); color: #f5a3a3; background: rgba(239,111,111,.08);}
.fr-chip.warn {border-color: rgba(232,176,74,.35); color: #f0cb85; background: rgba(232,176,74,.08);}
.fr-chip.blue {border-color: rgba(57,135,229,.4); color: #9cc3f3; background: rgba(57,135,229,.08);}

/* pipeline stepper */
.fr-steps {display: grid; grid-template-columns: repeat(7, 1fr); gap: 0; background: var(--panel);
  border: 1px solid var(--line); border-radius: var(--r); padding: 1rem .6rem; margin: .6rem 0 1.2rem;}
.fr-stp {position: relative; text-align: center; padding: 0 .35rem;}
.fr-stp::before {content: ""; position: absolute; top: 15px; left: -50%; width: 100%; height: 1px; background: var(--line-2);}
.fr-stp:first-child::before {display: none;}
.fr-stp .n {position: relative; z-index: 1; width: 30px; height: 30px; margin: 0 auto; border-radius: 50%;
  display: grid; place-items: center; font: 600 .72rem/1 var(--mono); background: var(--raise); color: var(--faint);
  border: 1px solid var(--line-2);}
.fr-stp.on .n {background: var(--gold-soft); color: var(--gold); border-color: var(--gold-line);}
.fr-stp.good .n {background: rgba(60,207,142,.12); color: var(--good); border-color: rgba(60,207,142,.4);}
.fr-stp.warn .n {background: rgba(232,176,74,.12); color: var(--warn); border-color: rgba(232,176,74,.4);}
.fr-stp.bad .n {background: rgba(239,111,111,.12); color: var(--bad); border-color: rgba(239,111,111,.4);}
.fr-stp .t {font-weight: 600; font-size: .82rem; color: var(--ink); margin-top: .55rem;}
.fr-stp .d {font: 400 .7rem/1.35 var(--mono); color: var(--muted); margin-top: .2rem;}
.fr-stp.off .t {color: var(--faint);}

/* answer card */
.fr-answer {background: radial-gradient(500px 200px at 0% 0%, rgba(214,180,106,.10), transparent 70%), var(--panel);
  border: 1px solid var(--gold-line); border-radius: 18px; padding: 1.5rem 1.6rem 1.3rem;}
.fr-answer .l {font: 600 .68rem/1 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--gold);}
.fr-answer .v {font-family: var(--serif); font-size: clamp(3rem, 5.4vw, 4.6rem); line-height: 1; color: var(--ink);
  margin: .7rem 0 .2rem; word-break: break-all;}
.fr-answer .exact {font: 400 .75rem/1 var(--mono); color: var(--faint);}
.fr-answer .row {display: flex; flex-wrap: wrap; gap: .45rem; margin: 1rem 0 0;}
.fr-answer .meta {display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; margin-top: 1.2rem; padding-top: 1rem;
  border-top: 1px solid var(--line);}
.fr-answer .meta b {display: block; font-family: var(--serif); font-weight: 400; font-size: 1.65rem; color: var(--ink);}
.fr-answer .meta span {font: 600 .62rem/1 var(--mono); letter-spacing: .13em; text-transform: uppercase; color: var(--faint);}
.fr-conf {height: 6px; border-radius: 6px; background: var(--raise); overflow: hidden; margin-top: 1rem;}
.fr-conf i {display: block; height: 100%; border-radius: 6px; background: linear-gradient(90deg, #b89448, #e6c98a);}
.fr-flag {margin-top: 1rem; padding: .75rem .9rem; border-radius: var(--r-sm); font-size: .86rem; line-height: 1.45;
  border: 1px solid rgba(232,176,74,.35); background: rgba(232,176,74,.07); color: #f0cb85;}
.fr-flag.ok {border-color: rgba(60,207,142,.3); background: rgba(60,207,142,.06); color: #9fe5c4;}

/* question / quote */
.fr-q {background: var(--panel); border: 1px solid var(--line); border-left: 2px solid var(--gold); border-radius: var(--r-sm);
  padding: 1rem 1.15rem; margin: .4rem 0 1rem;}
.fr-q .id {font: 500 .7rem/1 var(--mono); color: var(--faint); margin-bottom: .45rem;}
.fr-q .txt {font-size: 1.04rem; line-height: 1.5; color: var(--ink);}
.fr-q .fr-chips {margin-top: .7rem;}

/* claims */
.fr-claims {display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: .55rem;}
.fr-claim {display: grid; grid-template-columns: 22px 1fr; gap: .7rem; align-items: start; padding: .8rem .95rem;
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-sm);}
.fr-claim .ic {width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center; font-size: .72rem;
  font-weight: 700; margin-top: .05rem;}
.fr-claim .ic.good {background: rgba(60,207,142,.13); color: var(--good);}
.fr-claim .ic.warn {background: rgba(232,176,74,.13); color: var(--warn);}
.fr-claim .c {font-size: .88rem; color: var(--ink); line-height: 1.4;}
.fr-claim .w {font: 400 .72rem/1.4 var(--mono); color: var(--muted); margin-top: .25rem;}

/* tables written in HTML */
.fr-table {width: 100%; border-collapse: separate; border-spacing: 0; font-size: .86rem; background: var(--panel);
  border: 1px solid var(--line); border-radius: var(--r); overflow: hidden;}
.fr-table th {text-align: left; font: 600 .64rem/1.2 var(--mono); letter-spacing: .12em; text-transform: uppercase;
  color: var(--muted); padding: .8rem .9rem; border-bottom: 1px solid var(--line-2); background: var(--panel-2);}
.fr-table td {padding: .75rem .9rem; border-bottom: 1px solid var(--line); color: var(--ink-2); vertical-align: top;
  line-height: 1.45;}
.fr-table tr:last-child td {border-bottom: none;}
.fr-table td b {color: var(--ink); font-weight: 600;}
.fr-table td .m {font: 400 .72rem/1.3 var(--mono); color: var(--faint); display: block; margin-top: .2rem;}
.fr-table tr.group td {background: var(--panel-2); font: 600 .64rem/1 var(--mono); letter-spacing: .14em;
  text-transform: uppercase; color: var(--gold); padding: .6rem .9rem;}

.fr-legend {display: flex; flex-wrap: wrap; gap: 1.1rem; font-size: .8rem; color: var(--muted); margin: .2rem 0 .7rem;}
.fr-legend i {display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: .4rem; vertical-align: -1px;}

.fr-flow {display: grid; grid-template-columns: repeat(4, 1fr); gap: .7rem;}
.fr-flow .fr-card {padding: 1rem 1.05rem;}
.fr-flow .no {font: 600 .64rem/1 var(--mono); color: var(--gold); letter-spacing: .14em;}
.fr-flow h4 {margin-top: .5rem !important;}

.fr-timer {display: flex; align-items: center; gap: .9rem; padding: .95rem 1.1rem; border-radius: var(--r);
  background: var(--panel); border: 1px solid var(--gold-line);}
.fr-timer .spin {width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--gold-soft);
  border-top-color: var(--gold); animation: fr-spin .8s linear infinite;}
.fr-timer b {color: var(--ink); font-weight: 600;}
.fr-timer span {color: var(--muted); font-size: .85rem;}
.fr-timer .t {margin-left: auto; font: 500 1.05rem/1 var(--mono); color: var(--gold);}
@keyframes fr-spin {to {transform: rotate(360deg);}}

.fr-foot {margin-top: 4rem; padding-top: 1.2rem; border-top: 1px solid var(--line); font: 400 .74rem/1.5 var(--mono);
  color: var(--faint); display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem;}

@media (max-width: 900px) {
  .fr-head {flex-direction: column; align-items: flex-start;}
  .fr-head-side {align-items: flex-start;}
  .fr-steps {grid-template-columns: repeat(4, 1fr); row-gap: 1rem;}
  .fr-flow {grid-template-columns: repeat(2, 1fr);}
  .fr-grid.two {grid-template-columns: 1fr;}
}
"""


def inject_css():
    # st.html keeps a <style> block only when the CSS itself contains no "<" character
    st.html(f"<style>{CSS}</style>")


def esc(text):
    return _html.escape(str(text), quote=True)


def render(markup):
    """Render trusted HTML. Lines are flattened so Markdown never mistakes indentation for code."""
    st.markdown(re.sub(r"\n\s*", " ", markup.strip()), unsafe_allow_html=True)


def chip(text, tone="", icon=""):
    return f"<span class='fr-chip {tone}'>{esc(icon) + ' ' if icon else ''}{esc(text)}</span>"


def pill(text, state=""):
    return f"<span class='fr-pill'><span class='fr-dot {state}'></span>{esc(text)}</span>"


def page_header(eyebrow, title, subtitle="", side=()):
    """Page title. `title` may contain one *emphasised* phrase, shown in gold italics."""
    title_html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", esc(title))
    side_html = "".join(side)
    render(f"""<div class="fr-head"><div><div class="fr-eyebrow">{esc(eyebrow)}</div>
      <h1 class="fr-title">{title_html}</h1>{f'<p class="fr-sub">{esc(subtitle)}</p>' if subtitle else ''}</div>
      <div class="fr-head-side">{side_html}</div></div>""")


def section(title, subtitle="", kicker=""):
    render(f"""<div class="fr-section">{f'<div class="k">{esc(kicker)}</div>' if kicker else ''}
      <h3>{esc(title)}</h3>{f'<p>{esc(subtitle)}</p>' if subtitle else ''}</div>""")


def kpis(tiles):
    """tiles: (label, value, sub, tone colour or None[, small]) - small=True for word values."""
    out = []
    for tile in tiles:
        label, value, sub, tone = tile[:4]
        small = tile[4] if len(tile) > 4 else False
        out.append(f"<div class='fr-kpi' style='--tone:{tone or GOLD}'><div class='l'>{esc(label)}</div>"
                   f"<div class='v{' small' if small else ''}' title='{esc(value)}'>{esc(value)}</div>"
                   f"<div class='s'>{esc(sub)}</div></div>")
    render(f"<div class='fr-kpis'>{''.join(out)}</div>")


def cards(items, cls=""):
    """items: (tag, title, body, file) - file may be ''."""
    out = "".join(
        f"<div class='fr-card'>{f'<span class=tag>{esc(tag)}</span>' if tag else ''}<h4>{esc(title)}</h4>"
        f"<p>{esc(body)}</p>{f'<span class=file>{esc(f)}</span>' if f else ''}</div>"
        for tag, title, body, f in items)
    render(f"<div class='fr-grid {cls}'>{out}</div>")


def stepper(stages):
    """stages: (title, detail, state) with state in on / good / warn / bad / off."""
    out = "".join(f"<div class='fr-stp {state}'><div class='n'>{i:02d}</div><div class='t'>{esc(t)}</div>"
                  f"<div class='d'>{esc(d)}</div></div>" for i, (t, d, state) in enumerate(stages, 1))
    render(f"<div class='fr-steps'>{out}</div>")


def answer_card(value, exact, chips_html, confidence, calls, tokens, seconds, flag=None):
    conf = ""
    if confidence is not None:
        conf = (f"<div class='fr-conf' title='share of samples that agree'><i style='width:{100 * confidence:.0f}%'></i></div>"
                f"<div class='exact' style='margin-top:.45rem'>{100 * confidence:.0f}% of samples agree on this answer</div>")
    flag_html = ""
    if flag is not None:
        ok, text = flag
        flag_html = f"<div class='fr-flag {'ok' if ok else ''}'>{'✓' if ok else '⚠'} {esc(text)}</div>"
    render(f"""<div class="fr-answer"><div class="l">Computed answer</div><div class="v">{esc(value)}</div>
      <div class="exact">{esc(exact)}</div><div class="row">{chips_html}</div>{conf}{flag_html}
      <div class="meta"><div><b>{calls}</b><span>model calls</span></div><div><b>{tokens:,}</b><span>tokens</span></div>
      <div><b>{seconds:.1f}s</b><span>model time</span></div></div></div>""")


def question(uid, text, chips_html=""):
    render(f"<div class='fr-q'><div class='id'>{esc(uid)}</div><div class='txt'>{esc(text)}</div>"
           f"{f'<div class=fr-chips>{chips_html}</div>' if chips_html else ''}</div>")


def claims(items):
    """items: (done, claim, where)."""
    out = "".join(f"<div class='fr-claim'><div class='ic {'good' if done else 'warn'}'>{'✓' if done else '…'}</div>"
                  f"<div><div class='c'>{esc(c)}</div><div class='w'>{esc(w)}</div></div></div>"
                  for done, c, w in items)
    render(f"<div class='fr-claims'>{out}</div>")


def legend(items):
    render("<div class='fr-legend'>" + "".join(f"<span><i style='background:{c}'></i>{esc(t)}</span>"
                                             for t, c in items) + "</div>")


def timer(label, sub, elapsed):
    return (f"<div class='fr-timer'><div class='spin'></div><div><b>{esc(label)}</b><br><span>{esc(sub)}</span></div>"
            f"<div class='t'>{elapsed:5.1f}s</div></div>")


def html_table(header, rows, groups=None):
    """Small static table. rows: lists of HTML-safe cell strings; groups: {row index: group title}."""
    groups = groups or {}
    body = ""
    for i, row in enumerate(rows):
        if i in groups:
            body += f"<tr class='group'><td colspan='{len(header)}'>{esc(groups[i])}</td></tr>"
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    head = "".join(f"<th>{esc(h)}</th>" for h in header)
    render(f"<table class='fr-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")


def footer():
    render("<div class='fr-foot'><span>FinReason · numerical reasoning over financial reports</span>"
           "<span>UE24AM343AB5 · Prompt Engineering and Optimization for Generative AI · PES University</span></div>")


def style_chart(chart, height=None):
    """Apply the app's chart style: transparent surface, recessive grid, muted axes, Inter."""
    if height:
        chart = chart.properties(height=height)
    return (chart.configure(background="transparent", font="Inter", padding={"left": 18, "right": 14, "top": 8, "bottom": 4},
                            autosize=alt.AutoSizeParams(type="fit", contains="padding"))
            .configure_view(stroke=None)
            .configure_axis(gridColor="#20232a", domainColor="#2a2d35", tickColor="#2a2d35", labelColor=MUTED,
                            titleColor=FAINT, labelFontSize=11, titleFontSize=10, titleFontWeight=600,
                            titlePadding=10, labelPadding=6)
            .configure_legend(labelColor=INK_2, titleColor=FAINT, labelFontSize=11, titleFontSize=10,
                              orient="top", symbolType="circle", titleFontWeight=600)
            .configure_header(labelColor=INK_2, titleColor=FAINT, labelFontSize=12)
            .configure_title(color=INK, fontSize=13, anchor="start"))
