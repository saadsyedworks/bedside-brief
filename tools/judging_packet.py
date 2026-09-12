"""Build a standalone, blinded judging packet as a PDF (gate 3, second rater).

  python3 tools/judging_packet.py <run_dir> <out.pdf>

Everything a second rater needs and nothing that would unblind them: the rubric, each case's
one-liner, and every grouped recommendation with boxes to tick. Which arm produced an item appears
nowhere -- it lives only in the run's judging_key.json, which this tool never reads.

A second independent rater is worth more than convenience here: the study's stated limitation is a
single author who is also the sole verifier and judge, and two raters on the same blinded queue
turn that into a reported agreement figure.

Rendered by printing HTML through the headless Chromium already installed for the browser checks,
which gives real typographic control over the page; reportlab would fight us for the same result.
"""
from __future__ import annotations

import html
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.seed_judging import THRESHOLD, group_queue  # noqa: E402

CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

CSS = """
@page { size: A4; margin: 17mm 15mm 16mm; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.42 "DejaVu Serif", Georgia, serif; color: #14201d; margin: 0; }
h1 { font-family: "DejaVu Sans", sans-serif; font-size: 20pt; line-height: 1.12; margin: 0 0 6pt;
     font-weight: 600; letter-spacing: -.2pt; }
h2 { font-family: "DejaVu Sans", sans-serif; font-size: 12pt; margin: 0 0 3pt; font-weight: 600; }
.eyebrow { font-family: "DejaVu Sans Mono", monospace; font-size: 7.5pt; letter-spacing: 1.4pt;
           text-transform: uppercase; color: #0d5c63; margin-bottom: 7pt; }
.stand { font-size: 11pt; color: #4a5a55; margin: 0 0 14pt; }
p { margin: 0 0 7pt; }
.cover section { margin-bottom: 13pt; }
.cover h2 { border-bottom: .6pt solid #14201d; padding-bottom: 2pt; margin-bottom: 5pt; }
.meta { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; color: #6b7c77; }
ol { margin: 0 0 7pt; padding-left: 15pt; }
li { margin-bottom: 4pt; }
.scale { background: #eef1f0; padding: 8pt 10pt; font-size: 9.5pt; }
.scale div { margin-bottom: 3pt; }
.scale div:last-child { margin-bottom: 0; }
.scale b { font-family: "DejaVu Sans", sans-serif; }

.case { page-break-before: always; }
.case-head { border-bottom: 1.2pt solid #14201d; padding-bottom: 4pt; margin-bottom: 9pt; }
.case-head .n { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; color: #6b7c77; }
.oneliner { border-left: 2.4pt solid #0d5c63; background: #f4f6f5; padding: 7pt 9pt; margin: 0 0 10pt;
            font-size: 10.5pt; }
.oneliner .lbl { font-family: "DejaVu Sans Mono", monospace; font-size: 7pt; letter-spacing: 1.1pt;
                 text-transform: uppercase; color: #6b7c77; margin-bottom: 3pt; }

table.items { width: 100%; border-collapse: collapse; }
table.items th { font-family: "DejaVu Sans Mono", monospace; font-size: 6.8pt; letter-spacing: .7pt;
                 text-transform: uppercase; color: #6b7c77; font-weight: normal; text-align: center;
                 padding: 0 0 3pt; border-bottom: .6pt solid #14201d; }
table.items th.t { text-align: left; }
table.items td { padding: 4.5pt 0; border-bottom: .5pt solid #dfe4e2; vertical-align: top;
                 page-break-inside: avoid; }
td.num { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; color: #6b7c77; width: 20pt; }
td.txt { padding-right: 8pt; }
td.box { width: 26pt; text-align: center; }
td.box.gap { width: 32pt; }
.bx { display: inline-block; width: 10pt; height: 10pt; border: .7pt solid #6b7c77; }
.var { font-size: 8.5pt; color: #77877f; margin-top: 2pt; }
tr.grouped td.num::after { content: "*"; color: #0d5c63; }
.foot { font-family: "DejaVu Sans Mono", monospace; font-size: 7.5pt; color: #6b7c77;
        margin-top: 9pt; padding-top: 4pt; border-top: .5pt solid #dfe4e2; }
"""

RUBRIC = """
<section>
  <h2>How to score</h2>
  <p>For each numbered recommendation, tick one grade. Judge it against that case's one-liner and
  nothing else &mdash; not against the other items, and not against what you would have written.</p>
  <div class="scale">
    <div><b>Relevant</b> &mdash; you would spend bedside seconds on this, for this patient, today.</div>
    <div><b>Marginal</b> &mdash; right medicine, wrong moment. You would do it, just not in the first
      twenty seconds.</div>
    <div><b>Irrelevant</b> &mdash; no.</div>
    <div><b>Not an item</b> &mdash; a heading, citation or aside with no clinical instruction in it.
      These leave the relevance denominator rather than counting as an irrelevant recommendation.</div>
    <div><b>Flag</b> &mdash; tick as well as a grade when you would stop a colleague from doing it.
      Expect very few.</div>
  </div>
</section>
<section>
  <h2>One question to settle before you start</h2>
  <p>A recommendation that is correct medicine but not a bedside act &mdash; send a troponin, get a CT,
  start telemetry &mdash; is it <i>Irrelevant</i> or <i>Marginal</i>? It comes up often enough that
  changing your mind halfway is the largest avoidable risk to the result. This is a bedside card, so
  <i>Irrelevant</i> is the defensible answer; either way, decide now and hold it.</p>
  <p>Finish a case before you stop. Being systematically strict or lenient cancels out, because this
  is a comparison; drifting mid-case does not.</p>
</section>
<section>
  <h2>What you are looking at, and what is hidden</h2>
  <p>Each case is one synthetic inpatient one-liner, put to three different systems that each returned
  a list of bedside recommendations. Their outputs are pooled and ordered by a hash of the item, so
  <b>which system produced any given item is not recoverable from this document</b>. That is
  deliberate: the comparison is only worth anything if the grader cannot tell.</p>
  <p>Items marked <b>*</b> are ones where more than one system recommended essentially the same thing.
  They are merged into a single row so you grade the recommendation once, and the wording variants are
  printed underneath. Merging uses the same text-similarity threshold the analysis already uses to
  decide whether two items are the same recommendation.</p>
</section>
<section>
  <h2>Returning your scores</h2>
  <p>Case name and item number identify a row uniquely &mdash; &ldquo;syncope_001 item 14, marginal&rdquo;
  is enough. Ticked boxes on the PDF, a photo of the pages, or a plain list all work equally well.</p>
</section>
"""


def build_html(run_dir: Path) -> str:
    cases = group_queue(run_dir)
    n_groups = sum(c["n_groups"] for c in cases.values())
    n_items = sum(c["n_items"] for c in cases.values())
    e = html.escape

    out = [f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"]
    out.append('<div class="cover">')
    out.append('<div class="eyebrow">Bedside Brief &middot; blinded judging packet</div>')
    out.append("<h1>Score each bedside recommendation</h1>")
    out.append('<p class="stand">Twelve inpatient one-liners, and every bedside recommendation three '
               "systems made for them, pooled and stripped of any sign of which system said what.</p>")
    out.append(f'<p class="meta">{len(cases)} cases &middot; {n_items} recommendations merged into '
               f"{n_groups} judgements &middot; run {e(run_dir.name)} &middot; "
               f"prepared {date.today().isoformat()}</p>")
    out.append(RUBRIC)
    out.append("</div>")

    for c in cases.values():
        out.append('<div class="case">')
        out.append('<div class="case-head">')
        out.append(f'<h2>{e(c["case_id"].replace("_", " "))}</h2>')
        out.append(f'<div class="n">{c["presentation"].replace("_", " ")} &middot; '
                   f'{c["n_groups"]} judgements &middot; {c["n_items"]} pooled recommendations</div>')
        out.append("</div>")
        out.append('<div class="oneliner"><div class="lbl">The one-liner you are judging against</div>'
                   f'{e(c["oneliner"])}</div>')
        out.append('<table class="items"><thead><tr><th></th><th class="t">Recommendation</th>'
                   '<th>Rel</th><th>Marg</th><th>Irrel</th><th>Not an<br>item</th>'
                   '<th class="gap">Flag</th></tr></thead><tbody>')
        for i, g in enumerate(c["groups"], 1):
            klass = ' class="grouped"' if g.get("merged", 1) > 1 else ""
            var = ('<div class="var">also worded as: '
                   + e("  ·  ".join(g["variants"])) + "</div>") if g["variants"] else ""
            out.append(f'<tr{klass}><td class="num">{i:02d}</td>'
                       f'<td class="txt">{e(g["text"])}{var}</td>'
                       + '<td class="box"><span class="bx"></span></td>' * 4
                       + '<td class="box gap"><span class="bx"></span></td></tr>')
        out.append("</tbody></table>")
        out.append(f'<div class="foot">{e(c["case_id"])} &middot; items 01&ndash;{c["n_groups"]} '
                   f"&middot; * = more than one system recommended this</div>")
        out.append("</div>")
    return "\n".join(out)


def main(run_dir: Path, out_pdf: Path) -> int:
    page = out_pdf.with_suffix(".html")
    page.write_text(build_html(run_dir))
    cmd = [CHROMIUM, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
           f"--print-to-pdf={out_pdf}", page.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not out_pdf.exists():
        print(r.stderr[-1500:])
        return 1
    print(f"wrote {out_pdf} ({out_pdf.stat().st_size // 1024} KB) from {page.name}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(args[0]), Path(args[1])))
