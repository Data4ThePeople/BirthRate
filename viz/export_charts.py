"""Export each chart from the built page as a standalone PNG for the posts.

Rather than cropping a screenshot of the full page - which breaks the moment
the layout shifts - this reuses the page's own rendering and then reparents a
single chart into a frame of known size. The browser window is set to that
frame, so the capture needs no cropping at all.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "viz" / "fertility.html"
OUT = ROOT / "posts" / "images"
CHROME = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SCALE = 2  # retina; halves cleanly for a 1x asset

# id, output name, frame size, and whether to strip the map's controls
CHARTS = [
    ("__map__", "01-map-change-since-1982", (1180, 760)),
    ("chart-gfr", "01-metro-vs-nonmetro-rate", (720, 400)),
    ("chart-cfr", "01-age-standardised", (720, 400)),
    ("chart-national", "01-national-level", (720, 400)),
    ("chart-gap", "01-the-gap", (720, 400)),
    ("chart-sector", "02-fall-by-county-type", (720, 430)),
    ("chart-sectorline", "02-sector-trajectories", (720, 400)),
    ("chart-rucc", "02-gradient-by-era", (1000, 480)),
    ("chart-cohort", "03-children-by-age", (720, 430)),
    ("chart-tempo", "03-period-vs-adjusted", (720, 400)),
    ("__table__", "03-cohort-table", (760, 300)),
]

BOOTSTRAP = """
<script>
(function(){
  const params = new URLSearchParams(location.search);
  const want = params.get("chart");
  const W = +params.get("w"), H = +params.get("h");
  setPlaying(false);
  setYear(YEARS.length - 1, true);

  const frame = document.createElement("div");
  frame.id = "export-frame";
  frame.style.cssText =
    `position:fixed;inset:0;width:${W}px;height:${H}px;background:var(--surface);`
    + "display:flex;flex-direction:column;justify-content:center;"
    + "padding:18px 22px;box-sizing:border-box;overflow:hidden;z-index:9999";

  let node;
  if (want === "__map__"){
    node = document.querySelector("#map .panel");
    node.querySelector(".controls").remove();
    node.style.border = "0"; node.style.boxShadow = "none";
    frame.style.padding = "0";
  } else if (want === "__table__"){
    const T = D.tempo, rows = [1950, 1970, 1980, 1990];
    const ages = [25, 30, 35, 45];
    node = document.createElement("table");
    node.innerHTML =
      "<thead><tr><th>Cohort</th>" + ages.map(a => `<th>by ${a}</th>`).join("") +
      "</tr></thead><tbody>" +
      rows.map(c => {
        const cum = T.cumulative[String(c)];
        const cells = ages.map(a => cum[String(a)] == null ? "&mdash;"
                                 : cum[String(a)].toFixed(2));
        const strong = c === 1990;
        return `<tr>${[c, ...cells].map((v, i) =>
          `<td${strong ? ' style="font-weight:600"' : ""}>${v}</td>`).join("")}</tr>`;
      }).join("") + "</tbody>";
    node.style.fontSize = "15px";
  } else {
    node = document.getElementById(want);
    const legend = node.previousElementSibling;
    if (legend && legend.classList.contains("legend-inline")){
      frame.appendChild(legend);
    }
  }
  frame.appendChild(node);
  document.body.innerHTML = "";
  document.body.style.cssText = "margin:0;background:var(--surface)";
  document.body.appendChild(frame);
})();
</script>
"""


def main() -> None:
    if not PAGE.exists():
        sys.exit(f"{PAGE} missing; run build_page.py first")
    OUT.mkdir(parents=True, exist_ok=True)
    src = PAGE.read_text()
    export_page = ROOT / "viz" / "_export.html"
    export_page.write_text(src + BOOTSTRAP)

    for chart_id, name, (w, h) in CHARTS:
        dest = OUT / f"{name}.png"
        url = f"file://{export_page}?chart={chart_id}&w={w}&h={h}"
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--force-color-profile=srgb", f"--force-device-scale-factor={SCALE}",
             f"--window-size={w},{h}", "--virtual-time-budget=25000",
             f"--screenshot={dest}", url],
            check=True, capture_output=True)
        size = dest.stat().st_size
        print(f"  {name:34s} {w}x{h} @{SCALE}x  {size/1024:6.0f} KB")

    export_page.unlink()


if __name__ == "__main__":
    main()
