"""Headless check of the judging page against a stubbed db serving the real seeded docs."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

SP = pathlib.Path(sys.argv[1]); PAGE = SP / "judge.html"; DOCS = SP / "judge_docs"
index = json.loads((DOCS / "_index.json").read_text())
cases = {p.stem: json.loads(p.read_text()) for p in DOCS.glob("*.json") if p.stem != "_index"}

STUB = """
window.__writes = [];
window.claude = { use: async (n) => n !== "db" ? null : ({
  doc: (path) => ({
    get: async () => {
      if (path === "judging_meta/index") return {exists: true, data: () => window.__index};
      const id = path.split("/")[1];
      if (path.startsWith("judging_queue/")) return {exists: !!window.__cases[id], data: () => window.__cases[id]};
      return {exists: false, data: () => undefined};
    },
    set: async (d) => { window.__writes.push({path, data: d}); },
  }),
  collection: () => ({ get: async () => ({docs: (window.__scoreDocs||[]).map(d => ({id: d.id, exists: true, data: () => d.body})), size: 0, empty: true}) }),
}) };
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = b.new_page(viewport={"width": 820, "height": 1180})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.add_init_script(STUB + f"window.__index={json.dumps(index)};window.__cases={json.dumps(cases)};")
    pg.goto(PAGE.as_uri())
    pg.wait_for_timeout(900)

    print("page errors:", errs or "none")
    print("totals:", pg.text_content("#totals"))
    print("case chips:", pg.locator(".chip").count())
    print("rows rendered:", pg.locator(".row").count())
    print("groups with variants:", pg.locator(".variants").count())
    print("bulk in bar visible:", pg.locator("#bulk").is_visible(), "| label:", pg.text_content("#bulk"))
    print("rubric panel:", pg.locator("details.rubric").count())
    print("one-liner:", (pg.text_content(".oneliner p") or "")[:78])
    print("bar visible:", pg.locator("#bar").is_visible())

    # score the first three items, flag one
    for i, v in enumerate(["relevant", "marginal", "irrelevant", "not an item"]):
        pg.locator(".row").nth(i).locator(f'button[data-v="{v}"]').click()
        pg.wait_for_timeout(60)
    pg.locator(".row").nth(0).locator("button.flag").click()
    pg.wait_for_timeout(1200)

    print("progress:", pg.text_content("#prog"))
    print("save state:", pg.text_content("#save"))
    writes = pg.evaluate("window.__writes")
    print("db writes:", len(writes), "| last path:", writes[-1]["path"] if writes else None)
    if writes:
        s = writes[-1]["data"]["scores"]
        scored = {k: v for k, v in s.items() if v.get("r")}
        print("scores persisted:", len(scored), "| sample:", list(scored.items())[:2])
    pg.on("dialog", lambda d: d.accept())
    pg.locator("button.bulk").click(); pg.wait_for_timeout(1200)
    print("after bulk, progress:", pg.text_content("#prog"))
    print("after bulk, bulk hidden:", pg.locator("#bulk").is_hidden())
    w = pg.evaluate("window.__writes")
    print("after bulk, scores in last write:", len(w[-1]["data"]["scores"]))
    pg.locator("#next").click(); pg.wait_for_timeout(500)
    print("after Next, one-liner:", (pg.text_content(".oneliner p") or "")[:60])
    print("horizontal overflow:", pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
    pg.set_viewport_size({"width": 390, "height": 844}); pg.wait_for_timeout(300)
    print("phone-width overflow:", pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
    pg.set_viewport_size({"width": 834, "height": 1194})
    pg.evaluate("document.querySelector('details.rubric').open = true")
    pg.wait_for_timeout(200)
    pg.screenshot(path=str(SP / "judge_check.png"), full_page=False)
    b.close()
