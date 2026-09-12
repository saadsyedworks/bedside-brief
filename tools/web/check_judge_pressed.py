"""Every grade must visibly change the button, in both themes.

Written after three rounds of failing to fix a report of "I tap it and nothing happens". The
earlier checks asserted aria-pressed, which was correctly "true" the whole time, while the fourth
grade had no pressed background rule at all -- so the button was dead to look at and passing tests.
An assertion about the DOM is not an assertion about what a reader sees.
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

GRADES = ["relevant", "marginal", "irrelevant", "not an item"]
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
STUB = """window.claude={use:async(n)=>n!=="db"?null:({doc:(path)=>({get:async()=>{
 if(path==="judging_meta/index")return{exists:true,data:()=>window.__index};
 const id=path.split("/")[1];
 if(path.startsWith("judging_queue/"))return{exists:!!window.__cases[id],data:()=>window.__cases[id]};
 return{exists:false,data:()=>undefined};},set:async()=>{}}),
 collection:()=>({get:async()=>({docs:[],size:0,empty:true})})})};"""


def _luminance(rgb):
    def channel(value):
        v = value / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def parse(css):
    return tuple(int(x) for x in css[css.index("(") + 1:css.index(")")].split(",")[:3])


def main(scratch: pathlib.Path) -> int:
    docs = scratch / "judge_docs"
    index = json.loads((docs / "_index.json").read_text())
    cases = {p.stem: json.loads(p.read_text()) for p in docs.glob("*.json") if p.stem != "_index"}
    failures = []
    for scheme in ("light", "dark"):
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROMIUM)
            page = browser.new_page(viewport={"width": 1590, "height": 975}, color_scheme=scheme)
            page.add_init_script(STUB + "window.__index=" + json.dumps(index)
                                 + ";window.__cases=" + json.dumps(cases) + ";")
            page.goto((scratch / "judge.html").as_uri())
            page.wait_for_timeout(700)
            for i, grade in enumerate(GRADES):
                button = page.locator(".row").nth(i).locator(f'button[data-v="{grade}"]')
                before = button.evaluate("el => getComputedStyle(el).backgroundColor")
                button.click()
                page.wait_for_timeout(120)
                after = button.evaluate(
                    "el => { const c = getComputedStyle(el);"
                    "        return {bg: c.backgroundColor, fg: c.color}; }")
                if after["bg"] == before:
                    failures.append(f"{scheme}/{grade}: tapping changed no background")
                ratio = contrast(parse(after["bg"]), parse(after["fg"]))
                if ratio < 4.5:
                    failures.append(f"{scheme}/{grade}: label contrast {ratio:.2f}:1 below 4.5:1")
                print(f"{scheme:5s} {grade:12s} bg {before} -> {after['bg']}  contrast {ratio:.2f}:1")
            browser.close()
    for f in failures:
        print("FAIL", f)
    print("ok" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(pathlib.Path(sys.argv[1])))
