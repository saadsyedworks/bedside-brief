import json, pathlib, sys
from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).resolve().parent
index = json.loads((D / "ipad_docs" / "_index.json").read_text())
sample_id = index["queue"][0]["id"]
sample = json.loads((D / "ipad_docs" / f"{sample_id}.json").read_text())

# Stub the viewer runtime: window.claude.use("db") -> an in-memory store holding meta/index and one record.
stub = """
window.__writes = [];
window.claude = {
  use: function (name) {
    return new Promise(function (resolve) {
      setTimeout(function () {
        if (name !== "db") return resolve(null);
        resolve({
          doc: function (path) {
            return {
              get: function () {
                return Promise.resolve({
                  exists: path === "meta/index" || path === "records/" + SAMPLE_ID,
                  data: function () { return path === "meta/index" ? INDEX : SAMPLE; }
                });
              },
              set: function (v) { window.__writes.push({path: path, value: v}); return Promise.resolve(); }
            };
          },
          collection: function () {
            return { get: function () { return Promise.resolve({docs: [], size: 0, empty: true}); } };
          }
        });
      }, 300);
    });
  }
};
"""
stub = ("const INDEX = " + json.dumps(index) + ";\n"
        "const SAMPLE = " + json.dumps(sample) + ";\n"
        "const SAMPLE_ID = " + json.dumps(sample_id) + ";\n" + stub)

errors, console = [], []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = b.new_page(viewport={"width": 820, "height": 1100})   # iPad Air portrait
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: console.append(m.type + ": " + m.text) if m.type == "error" else None)
    pg.add_init_script(stub)
    pg.goto("file://" + str(D / "ipad_verify.html"))
    pg.wait_for_timeout(1800)

    head = pg.inner_text("#count")
    rows = pg.locator("button.row").count()
    print("header:", head)
    print("queue rows rendered:", rows)
    if rows:
        pg.locator("button.row").first.click()
        pg.wait_for_timeout(900)
        print("record opened:", pg.locator("h1").count() > 0, "| packets:", pg.locator("section.pkt").count())
        print("estimates:", pg.locator(".est").count(), "| decision buttons:", pg.locator(".btn").count())
        pg.screenshot(path=str(D / "ipad_record.png"), full_page=False)
        # exclude the first estimate, then promote A
        # open the correction panel on the first estimate and fix a likelihood ratio
        pg.locator('button[data-fix]').first.click()
        pg.wait_for_timeout(400)
        print("correction panel fields:", pg.locator(".fixgrid input").count())
        lrp = pg.locator('input[data-fixfield$="|lr_positive"]').first
        lrp.fill("9.5")
        pg.locator('textarea[data-fixfield$="|note"]').first.fill("LR+ is 9.5 in Table 3, not the value shown.")
        pg.wait_for_timeout(300)
        print("edit badge:", pg.inner_text("#editcount") if pg.locator("#editcount").count() else "none")
        # exclude the second estimate if there is one
        if pg.locator('button[data-toggle]').count() > 1:
            pg.locator('button[data-toggle]').nth(1).click()
        # the action bar must be on screen without scrolling to the end
        box = pg.locator(".decide").bounding_box()
        vp = pg.viewport_size
        print("action bar visible in viewport:", bool(box) and box["y"] < vp["height"])
        pg.fill("#notes", "Checked the quoted table; kept the pooled row.")
        pg.screenshot(path=str(D / "ipad_record.png"), full_page=False)
        pg.locator('button[data-act="promote"][data-base="A"]').first.click()
        pg.wait_for_timeout(900)
        w = pg.evaluate("window.__writes")
        print("writes:", json.dumps(w, indent=1)[:800])
    else:
        pg.screenshot(path=str(D / "ipad_queue.png"))
    b.close()

print("page errors:", errors or "none")
print("console errors:", console or "none")
sys.exit(1 if errors else 0)
