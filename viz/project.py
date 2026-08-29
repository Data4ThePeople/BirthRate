"""TopoJSON -> projected SVG paths using a composite Albers USA projection.

Reimplements d3-geo's albersUsa (lower 48 + Alaska and Hawaii insets) so the
published page needs no external JavaScript: geometry arrives pre-projected.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

WIDTH, HEIGHT = 960.0, 600.0
K = 1070.0          # d3 albersUsa default scale
TX, TY = 480.0, 300.0
RAD = math.pi / 180.0


class ConicEqualArea:
    """d3.geoConicEqualArea with rotate([lam, 0]), center([cx, cy]), parallels."""

    def __init__(self, rotate_lon, center, parallels, scale, translate):
        self.dlam = rotate_lon
        p0, p1 = (p * RAD for p in parallels)
        self.n = (math.sin(p0) + math.sin(p1)) / 2.0
        self.C = 1.0 + math.sin(p0) * (2.0 * self.n - math.sin(p0))
        self.rho0 = math.sqrt(self.C) / self.n
        self.k = scale
        self.tx, self.ty = translate
        self.cx, self.cy = self._raw(*center)

    def _raw(self, lon, lat):
        lam = lon * RAD
        phi = lat * RAD
        r = math.sqrt(max(self.C - 2.0 * self.n * math.sin(phi), 0.0)) / self.n
        return r * math.sin(self.n * lam), self.rho0 - r * math.cos(self.n * lam)

    def __call__(self, lon, lat):
        lon += self.dlam
        while lon > 180.0:
            lon -= 360.0
        while lon < -180.0:
            lon += 360.0
        x, y = self._raw(lon, lat)
        return self.tx + self.k * (x - self.cx), self.ty - self.k * (y - self.cy)


LOWER48 = ConicEqualArea(96.0, (-0.6, 38.7), (29.5, 45.5), K, (TX, TY))
ALASKA = ConicEqualArea(154.0, (-2.0, 58.5), (55.0, 65.0), K * 0.35,
                        (TX - 0.307 * K, TY + 0.201 * K))
HAWAII = ConicEqualArea(157.0, (-3.0, 19.9), (8.0, 18.0), K,
                        (TX - 0.205 * K, TY + 0.212 * K))

# Clip windows in output pixels, matching d3's albersUsa point routing.
CLIPS = {
    "lower48": (TX - 0.455 * K, TY - 0.238 * K, TX + 0.455 * K, TY + 0.238 * K),
    "alaska": (TX - 0.425 * K, TY + 0.120 * K, TX - 0.214 * K, TY + 0.234 * K),
    "hawaii": (TX - 0.214 * K, TY + 0.166 * K, TX - 0.115 * K, TY + 0.234 * K),
}


def project(lon: float, lat: float, state: str) -> tuple[float, float]:
    if state == "02":
        return ALASKA(lon, lat)
    if state == "15":
        return HAWAII(lon, lat)
    return LOWER48(lon, lat)


def decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    """Undo TopoJSON delta encoding and quantization into lon/lat pairs."""
    sx, sy = topo["transform"]["scale"]
    ox, oy = topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + ox, y * sy + oy))
        out.append(pts)
    return out


def _ring(arcs, indices):
    pts = []
    for idx in indices:
        if idx < 0:
            seg = arcs[~idx][::-1]
        else:
            seg = arcs[idx]
        pts.extend(seg[1:] if pts else seg)
    return pts


def geometry_paths(topo: dict, precision: int = 1) -> dict[str, str]:
    """Return {fips: svg path string}, projected and rounded."""
    arcs = decode_arcs(topo)
    paths: dict[str, str] = {}
    for geom in topo["objects"]["counties"]["geometries"]:
        fips = geom["id"]
        state = fips[:2]
        polys = (
            [geom["arcs"]] if geom["type"] == "Polygon" else geom["arcs"]
        )
        parts = []
        for poly in polys:
            for ring in poly:
                pts = _ring(arcs, ring)
                if len(pts) < 3:
                    continue
                proj = [project(lon, lat, state) for lon, lat in pts]
                # Drop consecutive duplicates after rounding.
                d = []
                last = None
                for x, y in proj:
                    xy = (round(x, precision), round(y, precision))
                    if xy != last:
                        d.append(xy)
                        last = xy
                if len(d) < 3:
                    continue
                parts.append(
                    "M" + "L".join(f"{x},{y}" for x, y in d) + "Z"
                )
        if parts:
            paths[fips] = "".join(parts)
    return paths


if __name__ == "__main__":
    topo = json.loads(Path("data/raw/geo/counties-10m.json").read_text())
    paths = geometry_paths(topo)
    print(f"paths: {len(paths)}   total chars: {sum(len(v) for v in paths.values()):,}")

    # Sanity: landmark counties should land in the expected quadrants.
    import re

    def centroid(fips):
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", paths[fips])]
        xs, ys = nums[0::2], nums[1::2]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    for fips, name in [("23029", "Washington Co, ME (NE corner)"),
                       ("12087", "Monroe Co, FL (SE corner)"),
                       ("53055", "San Juan Co, WA (NW corner)"),
                       ("06073", "San Diego Co, CA (SW corner)"),
                       ("02090", "Fairbanks, AK (inset)"),
                       ("15003", "Honolulu, HI (inset)")]:
        x, y = centroid(fips)
        print(f"  {name:34s} x={x:7.1f} y={y:6.1f}")


def state_paths(topo: dict, precision: int = 1) -> dict[str, str]:
    """Projected state outlines, for map borders."""
    arcs = decode_arcs(topo)
    out: dict[str, str] = {}
    for geom in topo["objects"]["states"]["geometries"]:
        fips = geom["id"]
        polys = [geom["arcs"]] if geom["type"] == "Polygon" else geom["arcs"]
        parts = []
        for poly in polys:
            for ring in poly:
                pts = _ring(arcs, ring)
                if len(pts) < 3:
                    continue
                d, last = [], None
                for lon, lat in pts:
                    x, y = project(lon, lat, fips)
                    xy = (round(x, precision), round(y, precision))
                    if xy != last:
                        d.append(xy)
                        last = xy
                if len(d) >= 3:
                    parts.append("M" + "L".join(f"{x},{y}" for x, y in d) + "Z")
        if parts:
            out[fips] = "".join(parts)
    return out
