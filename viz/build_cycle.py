"""Redraw the cycle-of-decline diagram to match the rest of the work.

Six stages on a ring, each feeding the next, plus the shortcut that makes the
loop vicious: when working-age people leave, the labour force falls directly,
without waiting for the slower demographic path around the circle.

Geometry is computed rather than hand-placed, so the ring stays even and the
arrows always meet the node edges.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "email" / "cycle-of-structural-decline.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1400, 1400
CX, CY = W / 2, 760
# the ring must clear the subtitle above and the credit below:
# CY - RING - NODE > subtitle baseline, CY + RING + NODE < credit baseline
RING = 424          # ring radius
NODE = 136          # node radius

INK = "#14140f"
NAVY = "#1e3050"
NAVY_EDGE = "#dfe3ea"
ARROW = "#b9b6ae"
ACCENT = "#b0062d"
SURFACE = "#fcfcfb"

# clockwise from the top; each line is a separate row of text
STAGES = [
    ["Aging population,", "falling birth rate"],
    ["Labor force", "declines"],
    ["Industrial", "exit"],
    ["Decline in city", "revenue &", "property taxes"],
    ["Services", "decline"],
    ["Working age", "population", "leaves"],
]


def polar(i: int) -> tuple[float, float]:
    angle = math.radians(-90 + i * (360 / len(STAGES)))
    return CX + RING * math.cos(angle), CY + RING * math.sin(angle)


def arc(i: int, j: int, gap: float = 15.0) -> str:
    """An arc from the edge of node i to the edge of node j, along the ring."""
    x1, y1 = polar(i)
    x2, y2 = polar(j)
    a1, a2 = math.atan2(y1 - CY, x1 - CX), math.atan2(y2 - CY, x2 - CX)
    span = (a2 - a1) % (2 * math.pi)
    pad = (NODE + gap) / RING
    sa, ea = a1 + pad, a1 + span - pad
    sx, sy = CX + RING * math.cos(sa), CY + RING * math.sin(sa)
    ex, ey = CX + RING * math.cos(ea), CY + RING * math.sin(ea)
    return (f'<path d="M{sx:.1f},{sy:.1f} A{RING},{RING} 0 0 1 {ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{ARROW}" stroke-width="12" '
            f'marker-end="url(#head)"/>')


def node(i: int) -> str:
    x, y = polar(i)
    lines = STAGES[i]
    size = 33
    start = y - (len(lines) - 1) * size * 0.62
    text = "".join(
        f'<tspan x="{x:.1f}" y="{start + n * size * 1.24:.1f}">{ln}</tspan>'
        for n, ln in enumerate(lines))
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{NODE}" fill="{NAVY}" '
            f'stroke="{NAVY_EDGE}" stroke-width="5"/>'
            f'<text x="{x:.1f}" text-anchor="middle" fill="#ffffff" '
            f'font-size="{size}" font-weight="500">{text}</text>')


def build_svg() -> str:
    ring = "".join(arc(i, (i + 1) % len(STAGES)) for i in range(len(STAGES)))
    x5, y5 = polar(5)
    x1, y1 = polar(1)
    chord = (f'<line x1="{x5 + NODE + 22:.1f}" y1="{y5:.1f}" '
             f'x2="{x1 - NODE - 30:.1f}" y2="{y1:.1f}" stroke="{ACCENT}" '
             f'stroke-width="13" marker-end="url(#head-accent)"/>'
             f'<text x="{CX:.1f}" y="{y5 - 26:.1f}" text-anchor="middle" '
             f'fill="{ACCENT}" font-size="27" font-weight="600" '
             f'letter-spacing="0.05em">AND DIRECTLY</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" font-family="'IBM Plex Sans',system-ui,sans-serif">
  <defs>
    <marker id="head" markerWidth="5" markerHeight="5" refX="3.6" refY="2.5"
            orient="auto"><path d="M0,0 L5,2.5 L0,5 z" fill="{ARROW}"/></marker>
    <marker id="head-accent" markerWidth="5" markerHeight="5" refX="3.6" refY="2.5"
            orient="auto"><path d="M0,0 L5,2.5 L0,5 z" fill="{ACCENT}"/></marker>
  </defs>
  <rect width="{W}" height="{H}" fill="{SURFACE}"/>
  <text x="{CX}" y="96" text-anchor="middle" fill="{INK}" font-size="62"
        font-weight="600" letter-spacing="-0.015em">The Cycle of Structural Decline</text>
  <text x="{CX}" y="152" text-anchor="middle" fill="#52514e" font-size="30">
    Each stage makes the next more likely, and the loop closes
  </text>
  {ring}{chord}
  {"".join(node(i) for i in range(len(STAGES)))}
  <text x="{CX}" y="{H - 34}" text-anchor="middle" fill="#88867e" font-size="25">
    Data 4 The People
  </text>
</svg>'''


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    svg = ROOT / "email" / "cycle-of-structural-decline.svg"
    svg.write_text(build_svg())
    page = ROOT / "viz" / "_cycle.html"
    page.write_text(
        f'<body style="margin:0"><link rel="stylesheet" href="https://fonts.googleapis.com/'
        f'css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap">{build_svg()}</body>')
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-color-profile=srgb",
                    "--force-device-scale-factor=2", f"--window-size={W},{H}",
                    "--virtual-time-budget=20000", f"--screenshot={OUT}",
                    f"file://{page}"], check=True, capture_output=True)
    page.unlink()
    print(f"  {OUT.relative_to(ROOT)}  and  {svg.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
