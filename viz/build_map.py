"""Build the standalone, embeddable county map.

The map page is produced from the same template as the full analysis, with the
analysis sections stripped between explicit markers, so the two cannot drift
apart. The payload is trimmed to only what the map reads, which keeps the
embed light.

The page carries no title or method text of its own: it is meant to sit in an
iframe under the host page's own heading, with the methodology beside it. It
posts its height to the parent on load and on resize so the frame can be sized
without guessing.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Only these keys are read by the map, its tooltip and the state selector.
MAP_KEYS = ["years", "units", "names", "geo", "geoUnit", "states", "stateMeta",
            "gfr", "chg", "births", "baseline", "interpolatedYears"]

EMBED_CSS = """
<style>
/* embed mode: no page furniture, the host page supplies the heading */
body{background:var(--surface)}
.wrap{max-width:none; padding:0}
.panel{border:0; border-radius:0; box-shadow:none}
.controls{padding:14px 18px}
.legend{padding:14px 18px 16px}
.statebar{padding:12px 18px}
.embed-foot{display:flex; flex-wrap:wrap; gap:6px 18px; align-items:baseline;
  padding:12px 18px 16px; border-top:1px solid var(--rule); color:var(--muted);
  font-size:.76rem; line-height:1.5}
.embed-foot a{color:var(--muted); text-decoration:underline}
.embed-foot b{font-family:"IBM Plex Mono",monospace; font-weight:500;
  letter-spacing:.04em; text-transform:uppercase; font-size:.68rem; color:var(--ink-2)}
</style>
"""

FOOT = """
<div class="embed-foot">
  <b>Fertility rate</b>
  <span>Births per 1,000 women aged 15&ndash;44, three-year pooled. 3,098 county
  units held stable across all 43 years.</span>
  <span>Census Population Estimates &middot; NCHS natality microdata &middot; SEER</span>
</div>
"""

RESIZE = """
<script>
(function(){
  function report(){
    const h = document.documentElement.scrollHeight;
    if (window.parent !== window){
      window.parent.postMessage({ type: "birthrate-map-height", height: h }, "*");
    }
  }
  window.addEventListener("load", report);
  window.addEventListener("resize", report);
  if (window.ResizeObserver) new ResizeObserver(report).observe(document.body);
})();
</script>
"""


def cut(text: str, start: str, end: str, keep_end: bool = False) -> str:
    """Remove start..end. The end marker is searched for *after* start, which a
    global search does not guarantee - that mistake silently ate the map."""
    if start not in text:
        raise SystemExit(f"marker not found: {start!r}")
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + (text[b:] if keep_end else text[b + len(end):])


def strip_between(text: str, start: str, end: str) -> str:
    while start in text:
        text = cut(text, start, end)
    return text


def main() -> None:
    tpl = (HERE / "template.html").read_text()

    for a, b in [("<!--ANALYSIS-START-->", "<!--ANALYSIS-END-->"),
                 ("<!--TILES-HTML-START-->", "<!--TILES-HTML-END-->"),
                 ("/*ANALYSIS-JS-START*/", "/*ANALYSIS-JS-END*/"),
                 ("/*TILES-START*/", "/*TILES-END*/")]:
        tpl = strip_between(tpl, a, b)

    # drop the masthead and the method essay; the host page carries both
    tpl = cut(tpl, '<header class="masthead">', "</header>")
    tpl = cut(tpl, '<section id="notes">', "</section>")

    # the map section's heading and standfirst are page furniture too; cut up to
    # the panel and keep the panel itself
    tpl = cut(tpl, '<div class="section-head">', '<div class="panel">', keep_end=True)

    tpl = tpl.replace('<section id="map">', '<section id="map" style="padding-top:0">')
    tpl = tpl.replace("<title>The Rural Fertility Gap</title>",
                      "<title>County Fertility Map</title>")
    tpl = tpl.replace("</style>", "</style>" + EMBED_CSS, 1)

    # the source line belongs inside the panel, under the legend
    tpl = tpl.replace("</section>", FOOT + "</section>", 1)

    for required in ('id="usmap"', 'id="counties"', 'id="statesel"',
                     'id="payload"', 'id="tip"', "buildLegend();"):
        if required not in tpl:
            raise SystemExit(f"map build dropped something it needs: {required}")
    for tag in ("div", "section"):
        opened, closed = tpl.count(f"<{tag}"), tpl.count(f"</{tag}>")
        if opened != closed:
            raise SystemExit(f"unbalanced <{tag}>: {opened - closed}")
    if "<header" in tpl:
        raise SystemExit("masthead survived the strip")

    data = json.loads((HERE / "fertility_data.json").read_text())
    trimmed = {k: data[k] for k in MAP_KEYS if k in data}
    payload = json.dumps(trimmed, separators=(",", ":"))
    page = tpl.replace("__DATA__", payload) + RESIZE

    leftover = re.findall(r"\bD\.(\w+)", page)
    unknown = sorted({k for k in leftover if k not in trimmed})
    if unknown:
        raise SystemExit(f"map page still reads missing payload keys: {unknown}")

    out = HERE / "map.html"
    out.write_text(page)
    print(f"wrote {out}  {out.stat().st_size/1e6:.2f} MB "
          f"(full page {(HERE/'fertility.html').stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
