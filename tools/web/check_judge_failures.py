"""Exercise the judging page's failure paths, which a happy-path stub never reaches."""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

SP = pathlib.Path(sys.argv[1])
index = json.loads((SP/"judge_docs"/"_index.json").read_text())
cases = {p.stem: json.loads(p.read_text()) for p in (SP/"judge_docs").glob("*.json") if p.stem != "_index"}

# window.__fail: "cases" rejects every queue read, "scores" rejects the scores read, "" is healthy
STUB = """
window.__writes=[];window.__reads=[];
window.claude = { use: async (n) => n !== "db" ? null : ({
  doc: (path) => ({
    get: async () => {
      window.__reads.push(path);
      if (path === "judging_meta/index") return {exists:true, data:()=>window.__index};
      if (window.__fail === "cases") { const e = new Error("rate limited"); e.code = "rate_limited"; throw e; }
      const id = path.split("/")[1];
      if (path.startsWith("judging_queue/")) return {exists:!!window.__cases[id], data:()=>window.__cases[id]};
      return {exists:false, data:()=>undefined};
    },
    set: async (d) => { window.__writes.push({path,data:d}); },
  }),
  collection: () => ({ get: async () => {
    if (window.__fail === "scores") { const e = new Error("permission denied"); e.code = "denied"; throw e; }
    return {docs:[],size:0,empty:true}; } }),
}) };
"""

def run(mode):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = b.new_page(viewport={"width":820,"height":1180}, has_touch=True, is_mobile=True)
        errs=[]
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(STUB + f'window.__fail={json.dumps(mode)};window.__index={json.dumps(index)};window.__cases={json.dumps(cases)};')
        pg.goto((SP/"judge.html").as_uri()); pg.wait_for_timeout(1400)
        out = {"mode": mode or "healthy", "pageerrors": errs,
               "notice": (pg.text_content(".notice") or "")[:120] if pg.locator(".notice").count() else None,
               "rows": pg.locator(".row").count(),
               "retry_button": pg.locator("button:has-text('Try again')").count(),
               "diag": pg.text_content("#diag"),
               "queue_reads": len([r for r in pg.evaluate("window.__reads") if "judging_queue" in r])}
        if mode == "cases":
            pg.locator("button:has-text('Try again')").first.tap(); pg.wait_for_timeout(500)
            out["reads_after_retry"] = len([r for r in pg.evaluate("window.__reads") if "judging_queue" in r])
        if not mode:
            # bulk must work with no modal at all: two taps
            pg.locator('.row').nth(0).locator('button[data-v="relevant"]').tap(); pg.wait_for_timeout(200)
            bulk = pg.locator("#bulk")
            out["bulk_label_1"] = pg.text_content("#bulk")
            bulk.tap(); pg.wait_for_timeout(250)
            out["bulk_label_2"] = pg.text_content("#bulk")
            bulk.tap(); pg.wait_for_timeout(900)
            out["prog_after_bulk"] = pg.text_content("#prog")
            out["bulk_hidden_after"] = pg.locator("#bulk").is_hidden()
            out["writes"] = len(pg.evaluate("window.__writes"))
        b.close()
        return out

for mode in ("", "cases", "scores"):
    r = run(mode)
    print(f"--- {r.pop('mode')}")
    for k, v in r.items(): print(f"    {k}: {v}")
