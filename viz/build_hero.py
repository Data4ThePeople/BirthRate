"""Render the county map as a hero / social card at a fixed size.

Built from the embed page rather than the analysis page: the embed fills its
frame, while the analysis page caps the map at 700px tall and would leave a
1680x1080 canvas mostly empty. Controls are hidden, the legend is scaled for
the larger canvas, and the coverage note is dropped - it is guidance for a
reader using the map, not something a shared image needs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SIZE = (1680, 1080)
OUT = ROOT / "posts" / "images" / "hero-fertility-map-1680x1080.png"

TWEAK = """
<style>
  .controls, .embed-foot { display: none !important; }
  .legend .ramp:nth-of-type(2) { display: none !important; }
  .legend { padding: 20px 46px 30px !important; gap: 26px !important; }
  .ramp .cap { font-size: 15px !important; letter-spacing: .12em !important; }
  .ramp .sw { width: 84px !important; height: 22px !important; }
  .ramp .ticks span { width: 84px !important; font-size: 13px !important; }
  .mapbox { padding: 14px 30px 0 !important; }
</style>
"""


def main() -> None:
    src = ROOT / "viz" / "dist" / "map.html"
    if not src.exists():
        sys.exit(f"{src} missing; run build_map.py then wrap_standalone.py")
    w, h = SIZE
    tmp = ROOT / "viz" / "_hero.html"
    tmp.write_text(src.read_text().replace("</body>", TWEAK + "</body>"))
    try:
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--force-color-profile=srgb", "--force-device-scale-factor=2",
             f"--window-size={w},{h}", "--virtual-time-budget=45000",
             f"--screenshot={OUT}", f"file://{tmp}"], check=True, capture_output=True)
    finally:
        tmp.unlink(missing_ok=True)
    # rendered at 2x for sharpness, then resampled down to the requested size
    Image.open(OUT).resize(SIZE, Image.LANCZOS).save(OUT, optimize=True)
    print(f"  {OUT.relative_to(ROOT)}  {Image.open(OUT).size}  "
          f"{OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
