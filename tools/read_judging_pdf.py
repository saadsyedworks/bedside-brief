"""Read the ticked grades out of a completed judging packet PDF.

  python3 tools/read_judging_pdf.py <completed.pdf> <rows.json> [--run-dir DIR]

The marks are vector strokes drawn inside the box outlines, not form fields or annotations, so this
locates the five box rectangles on each row and asks which of them contains a stroke. With
--run-dir it also checks the alignment by text: every row's printed recommendation is compared with
the group the row is expected to hold, which is the only way to be sure an off-by-one has not
silently shifted every grade in the document.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GRADES = ["relevant", "marginal", "irrelevant", "not an item", "flag"]


def read(pdf: Path) -> list[dict]:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTChar, LTCurve, LTLine, LTRect

    rows: list[dict] = []
    for page in extract_pages(str(pdf)):
        shapes: list = []
        chars: list = []

        def walk(obj) -> None:
            if isinstance(obj, (LTRect, LTCurve, LTLine)):
                shapes.append(obj)
            if isinstance(obj, LTChar):
                chars.append(obj)
            if hasattr(obj, "__iter__"):
                for child in obj:
                    walk(child)

        for obj in page:
            walk(obj)
        boxes = [s for s in shapes
                 if isinstance(s, LTRect) and abs(s.width - s.height) < 2 and 8 < s.width < 16]
        if not boxes:
            continue
        strokes = [s for s in shapes if isinstance(s, (LTCurve, LTLine)) and not isinstance(s, LTRect)]
        by_row: dict[int, list] = collections.defaultdict(list)
        for b in boxes:
            by_row[round(b.y0)].append(b)
        for y in sorted(by_row, reverse=True):
            cols = sorted(by_row[y], key=lambda b: b.x0)
            if len(cols) != len(GRADES):
                continue
            ticked = [GRADES[i] for i, c in enumerate(cols)
                      if any(c.x0 - 1 <= (s.x0 + s.x1) / 2 <= c.x1 + 1
                             and c.y0 - 1 <= (s.y0 + s.y1) / 2 <= c.y1 + 1 for s in strokes)]
            text = "".join(ch.get_text() for ch in sorted(
                (ch for ch in chars if ch.x1 < cols[0].x0 - 2 and y - 4 <= ch.y0 <= y + 14),
                key=lambda c: (round(-c.y0), c.x0)))
            rows.append({"ticked": ticked, "text": re.sub(r"\s+", " ", text).strip()})
    return rows


def verify(rows: list[dict], run_dir: Path) -> list[str]:
    """Compare each row's printed text with the group it should hold. Catches an off-by-one."""
    import csv

    from tools.seed_judging import group_queue
    cases = group_queue(run_dir)
    order: list[str] = []
    for r in csv.DictReader((run_dir / "judging_queue.csv").open()):
        if r["case_id"] not in order:
            order.append(r["case_id"])

    def words(s: str) -> list[str]:
        # the row's printed number runs into its text ("02Allergies"), and a short item is then
        # mostly prefix -- strip a leading row number before comparing
        s = re.sub(r"^\s*\d{1,3}\*?", " ", s)
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).split()

    problems, i = [], 0
    for cid in order:
        for rank, g in enumerate(cases[cid]["groups"], 1):
            if i >= len(rows):
                problems.append(f"{cid} row {rank}: the document ran out of rows")
                return problems
            expected, got = set(words(g["text"])[:8]), set(words(rows[i]["text"])[:14])
            if expected and len(expected & got) / len(expected) < 0.4:
                problems.append(f"{cid} row {rank}: expected {g['text'][:40]!r}, found {rows[i]['text'][:40]!r}")
            i += 1
    if i != len(rows):
        problems.append(f"{len(rows)} rows in the document, {i} groups in the run")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--run-dir", default=None, help="verify row alignment against this run")
    args = ap.parse_args()

    rows = read(Path(args.pdf))
    graded = [r for r in rows if [t for t in r["ticked"] if t != "flag"]]
    multi = [r for r in rows if len([t for t in r["ticked"] if t != "flag"]) > 1]
    counts = collections.Counter(t for r in rows for t in r["ticked"] if t != "flag")
    print(f"rows: {len(rows)} · graded: {len(graded)} · ungraded: {len(rows) - len(graded)} · "
          f"more than one grade: {len(multi)} · flags: {sum(1 for r in rows if 'flag' in r['ticked'])}")
    print("distribution:", dict(counts))

    if args.run_dir:
        problems = verify(rows, Path(args.run_dir))
        for p in problems[:10]:
            print("ALIGNMENT", p)
        print(f"alignment: {'ok' if not problems else str(len(problems)) + ' problem(s)'}")
        if problems:
            return 1

    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
