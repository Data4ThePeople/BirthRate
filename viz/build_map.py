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
/* Embed mode. The host frame is a fixed height set by oEmbed, and viewport
   media queries do not see the frame's width, so all responsive behaviour is
   driven by container queries on .wrap instead. */
/* The frame height is fixed by oEmbed, so the page fills it exactly: the
   controls, legend and footer take what they need and the map absorbs the
   rest. That keeps one fixed height correct at every width, with no dead
   space on a phone and no clipping on a desktop. */
html,body{height:100%}
body{background:var(--surface); margin:0; overflow:hidden}
.wrap{max-width:none; padding:0; height:100%; display:flex; flex-direction:column;
  container-type:inline-size; container-name:embed}
#map{flex:1 1 auto; min-height:0; display:flex; flex-direction:column}
.panel{border:0; border-radius:0; box-shadow:none; flex:1 1 auto; min-height:0;
  display:flex; flex-direction:column; width:100%}
.controls,.legend,.statebar,.embed-foot{flex:0 0 auto; min-width:0}
.mapbox{flex:1 1 auto; min-height:0; display:flex; overflow:hidden}
.mapbox svg{width:100%; height:100%; min-width:0; max-height:none}
.controls{padding:12px 16px; gap:14px}
.legend{padding:12px 16px 14px; gap:18px}
.statebar{padding:10px 16px; gap:18px}
.mapbox svg{max-height:none}
.embed-foot{display:flex; flex-wrap:wrap; gap:5px 16px; align-items:baseline;
  padding:11px 16px 14px; border-top:1px solid var(--rule); color:var(--muted);
  font-size:.74rem; line-height:1.5}
.embed-foot a{color:var(--muted); text-decoration:underline}
.embed-foot b{font-family:"IBM Plex Mono",monospace; font-weight:500;
  letter-spacing:.04em; text-transform:uppercase; font-size:.66rem; color:var(--ink-2)}

@container embed (max-width: 830px){
  .controls{gap:10px; padding:10px 12px}
  .segmented button{padding:6px 10px; font-size:.78rem}
  .statepick select{font-size:.78rem; padding:6px 8px}
  /* the range input and playbar both carry minimum widths that would
     otherwise hold the whole panel wider than a phone frame, clipping the map */
  .playbar{flex:1 1 100%; min-width:0; gap:10px}
  .playbar input[type=range]{min-width:0}
  .segmented{flex:0 1 auto; min-width:0}
  .statepick{flex:0 1 auto; min-width:0}
  .statepick select{max-width:38vw}
  .play{width:34px; height:34px}
  .yearout{font-size:1.15rem; min-width:3.6ch}
  .yearnote{display:none}
  .legend{flex-direction:column; align-items:flex-start; gap:10px}
  /* the coverage note is reassurance, not instruction; on a phone the space is
     better spent on the map itself */
  .legend .ramp:nth-of-type(2){display:none}
  .ramp .sw{width:32px; height:11px}
  .ramp .ticks span{width:32px; font-size:.6rem}
  .statebar{gap:12px; padding:9px 12px}
  .statebar .nm{font-size:1.1rem}
  .statebar dl{gap:14px}
  .statebar .unit{display:none}
  .embed-foot{padding:10px 12px 12px; font-size:.7rem}
}
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
