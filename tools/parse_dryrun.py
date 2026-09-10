"""Dev check only (nothing rendered, nothing promoted): run the LLM parser over every frozen input and
report vocab validity, presentation agreement with the case, differential overlap with the author's
intended differential, and ask-first (missing_features) behaviour vs the underspecified flag.
  python3 tools/parse_dryrun.py <out.json>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bedside_brief.llm import LLMClient  # noqa: E402
from bedside_brief.parser import ParserError, parse_oneliner  # noqa: E402
from eval.cases import load_cases  # noqa: E402


def main(out: Path, only: set[str] | None = None) -> None:
    llm = LLMClient()
    rows = []
    for ci in load_cases():
        if only and ci.case_id not in only:
            continue
        t0 = time.time()
        try:
            p = parse_oneliner(ci.oneliner, llm)
            err = None
        except ParserError as e:  # includes vocab errors
            p, err = None, f"{type(e).__name__}: {e}"
        except Exception as e:  # noqa: BLE001
            p, err = None, f"{type(e).__name__}: {e}"
        row = {
            "case_id": ci.case_id, "presentation": ci.presentation, "variant": ci.variant,
            "underspecified_expected": ci.underspecified_expected, "error": err,
            "latency_s": round(time.time() - t0, 2),
        }
        if p:
            dx = [d["dx"] for d in p["differentials"]]
            intended = set(json.loads(Path(ci.source_file).read_text())["intended_bedside_differential"])
            row.update({
                "parsed_presentation": p["presentation"],
                "presentation_ok": p["presentation"] == ci.presentation,
                "differentials": dx,
                "overlap_with_intended": len(intended & set(dx)),
                "n_intended": len(intended),
                "tags": p["indication_tags"],
                "missing_features": p["missing_features"],
                "ask_first": bool(p["missing_features"]),
            })
        rows.append(row)
        if err:
            status = "ERR " + err[:60]
        else:
            status = "ok  " + ("" if row["presentation_ok"] else "PRES-MISMATCH ") + f"overlap {row['overlap_with_intended']}/{row['n_intended']}" + (" ask-first" if row["ask_first"] else "")
        print(f"{ci.case_id:<22} {status}", flush=True)
    out.write_text(json.dumps(rows, indent=1))
    ok = [r for r in rows if not r["error"]]
    print(f"\n{len(ok)}/{len(rows)} parsed; presentation ok {sum(r['presentation_ok'] for r in ok)}/{len(ok)}; "
          f"mean overlap {sum(r['overlap_with_intended'] for r in ok)/max(len(ok),1):.2f}; "
          f"ask-first on underspecified {sum(r['ask_first'] for r in ok if r['underspecified_expected'])}/{sum(r['underspecified_expected'] for r in ok)}, "
          f"on others {sum(r['ask_first'] for r in ok if not r['underspecified_expected'])}/{sum(not r['underspecified_expected'] for r in ok)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None)
