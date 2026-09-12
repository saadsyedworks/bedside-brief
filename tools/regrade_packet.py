"""Build the off-bedside re-grade sheet: only the rows a rubric correction touches.

  python3 tools/regrade_packet.py <rows.json> <run_dir> <out.pdf>

`rows.json` is the per-row grade extracted from the completed judging packet (see
tools/read_judging_pdf.py). This selects the groups whose items are ALL in off-bedside categories
by the deterministic classifier -- lab, imaging, ecg, monitoring, treatment, mar, consult -- and
which carry a grade of marginal or irrelevant. That is exactly the population affected by grading
relevance bedside-blind rather than bedside-only (DECISIONS #56), and the selection contains no
judgement: it is a category filter plus the grade already recorded.

Each row states its current grade and offers the alternatives. Keep is the default, so the reader
ticks only what changes.
"""
from __future__ import annotations

import csv
import glob
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.seed_judging import group_queue  # noqa: E402

CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OFF_BEDSIDE = {"lab", "imaging", "ecg", "monitoring", "treatment", "consult", "disposition", "mar"}
CHOICES = ["relevant", "marginal", "irrelevant", "not an item"]

CSS = """
@page { size: A4; margin: 16mm 15mm; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.45 "DejaVu Serif", Georgia, serif; color: #14201d; margin: 0; }
h1 { font-family: "DejaVu Sans", sans-serif; font-size: 19pt; margin: 0 0 5pt; font-weight: 600; }
h2 { font-family: "DejaVu Sans", sans-serif; font-size: 11.5pt; margin: 0; font-weight: 600; }
.eyebrow { font-family: "DejaVu Sans Mono", monospace; font-size: 7.5pt; letter-spacing: 1.4pt;
           text-transform: uppercase; color: #0d5c63; margin-bottom: 6pt; }
.stand { font-size: 10.5pt; color: #4a5a55; margin: 0 0 10pt; }
.how { background: #eef1f0; padding: 9pt 11pt; margin: 0 0 4pt; font-size: 10pt; }
.how p { margin: 0 0 5pt; } .how p:last-child { margin: 0; }
.how b { font-family: "DejaVu Sans", sans-serif; }
.case { margin-top: 15pt; page-break-inside: avoid; }
.case-head { border-bottom: 1pt solid #14201d; padding-bottom: 3pt; margin-bottom: 7pt;
             display: flex; justify-content: space-between; align-items: baseline; }
.case-head .n { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; color: #6b7c77; }
.oneliner { border-left: 2.4pt solid #0d5c63; background: #f4f6f5; padding: 6pt 9pt; margin: 0 0 8pt;
            font-size: 10pt; }
.item { border-bottom: .5pt solid #dfe4e2; padding: 6pt 0 7pt; page-break-inside: avoid; }
.item .top { display: flex; gap: 7pt; align-items: baseline; }
.item .rn { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; color: #6b7c77; min-width: 20pt; }
.item .txt { flex: 1; }
.item .cat { font-family: "DejaVu Sans Mono", monospace; font-size: 7pt; letter-spacing: .6pt;
             text-transform: uppercase; color: #6b7c77; }
.choices { display: flex; gap: 13pt; margin: 5pt 0 0 27pt; font-size: 9.5pt; align-items: center; }
.choices span { white-space: nowrap; }
.bx { display: inline-block; width: 10pt; height: 10pt; border: .7pt solid #6b7c77;
      vertical-align: -1pt; margin-right: 3pt; }
.keep { font-family: "DejaVu Sans", sans-serif; }
.keep .bx { border-width: 1.4pt; border-color: #14201d; background: #dfe4e2; }
.foot { font-family: "DejaVu Sans Mono", monospace; font-size: 7.5pt; color: #6b7c77;
        margin-top: 12pt; padding-top: 5pt; border-top: .5pt solid #dfe4e2; }
"""


def affected(rows: list[dict], run_dir: Path, order: list[str]) -> dict[str, list[dict]]:
    cases = group_queue(run_dir)
    uid_where = {r["item_uid"]: (r["case_id"], r["item_text"])
                 for r in csv.DictReader((run_dir / "judging_queue.csv").open())}
    category: dict[tuple[str, str], str] = {}
    for arm in ("A", "B", "C"):
        for f in glob.glob(f"{run_dir}/{arm}/*.json"):
            out = json.load(open(f))
            for item in out["items"]:
                category[(out["case_id"], item["text"])] = item.get("category")

    picked: dict[str, list[dict]] = {}
    i = 0
    for cid in order:
        for rank, g in enumerate(cases[cid]["groups"], 1):
            grade = next((t for t in rows[i]["ticked"] if t != "flag"), None)
            i += 1
            cats = {category.get(uid_where.get(u, (None, None))) for u in g["uids"]}
            cats.discard(None)
            if cats and cats <= OFF_BEDSIDE and grade in ("marginal", "irrelevant"):
                picked.setdefault(cid, []).append(
                    {"rank": rank, "grade": grade, "cats": "/".join(sorted(cats)), "text": g["text"]})
    if i != len(rows):
        raise SystemExit(f"alignment error: consumed {i} of {len(rows)} rows")
    return {cid: picked[cid] for cid in order if cid in picked}


def build_html(picked: dict[str, list[dict]], run_dir: Path) -> str:
    cases = group_queue(run_dir)
    e = html.escape
    total = sum(len(v) for v in picked.values())
    out = [f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"]
    out.append('<div class="eyebrow">Bedside Brief · rubric correction · blinded</div>')
    out.append("<h1>Off-bedside rows to re-grade</h1>")
    out.append(f'<p class="stand">{total} of 427 rows &mdash; every one where the recommendation is a '
               "lab, an ECG, imaging, monitoring, a medication review or a consult, and it was graded "
               "marginal or irrelevant under the bedside-only rubric.</p>")
    out.append('<div class="how">'
               "<p><b>Grade the medicine, not the format.</b> Ignore whether the recommendation happens "
               "at the bedside. Would you want this done for this patient today?</p>"
               "<p><b>Tick only what changes.</b> Every row shows the grade you gave it, already marked "
               "as <i>keep</i>. Leave it alone and it stays as it is.</p>"
               "<p>Nothing else from your packet is affected: the other 383 rows, including all 71 "
               "&ldquo;not an item&rdquo; calls, stand as graded.</p></div>")

    for cid, items in picked.items():
        out.append('<div class="case"><div class="case-head">')
        out.append(f'<h2>{e(cid.replace("_", " "))}</h2>'
                   f'<div class="n">{len(items)} row{"s" if len(items) > 1 else ""} to review</div>')
        out.append("</div>")
        out.append('<div class="oneliner">' + e(cases[cid]["oneliner"]) + "</div>")
        for it in items:
            out.append('<div class="item"><div class="top">'
                       f'<div class="rn">{it["rank"]:02d}</div>'
                       f'<div class="txt">{e(it["text"])} <span class="cat">[{e(it["cats"])}]</span></div>'
                       "</div>")
            out.append('<div class="choices">'
                       f'<span class="keep"><span class="bx"></span>keep <i>{it["grade"]}</i></span>')
            for c in CHOICES:
                if c != it["grade"]:
                    out.append(f'<span><span class="bx"></span>{c}</span>')
            out.append("</div></div>")
        out.append("</div>")
    out.append('<div class="foot">Case name and row number identify a row uniquely; the numbers match '
               "the judging packet. Replying in plain text is equally fine &mdash; only the changes.</div>")
    return "\n".join(out)


def main(rows_path: Path, run_dir: Path, out_pdf: Path) -> int:
    rows = json.loads(rows_path.read_text())
    # The packet's case order is the order the cases first appear in the queue, which is what
    # group_queue and the seeded index both preserve.
    order: list[str] = []
    for r in csv.DictReader((run_dir / "judging_queue.csv").open()):
        if r["case_id"] not in order:
            order.append(r["case_id"])
    picked = affected(rows, run_dir, order)
    page = out_pdf.with_suffix(".html")
    page.write_text(build_html(picked, run_dir))
    subprocess.run([CHROMIUM, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    f"--print-to-pdf={out_pdf}", page.as_uri()], capture_output=True, text=True)
    if not out_pdf.exists():
        return 1
    print(f"wrote {out_pdf} ({out_pdf.stat().st_size // 1024} KB) — "
          f"{sum(len(v) for v in picked.values())} rows over {len(picked)} cases")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(args[0]), Path(args[1]), Path(args[2])))
