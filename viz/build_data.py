"""Compile the panel + geometry into one compact JSON payload for the artifact."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from birthrate.analysis import by_metro, load, shift_share  # noqa: E402
from birthrate.geography import UNIT_LABELS, to_unit  # noqa: E402
from birthrate.sources.rucc import RUCC_CLASS  # noqa: E402
from project import geometry_paths, state_paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASELINE = [1991, 1992, 1993]
SMOOTH = 3  # centred rolling window, pooled births over pooled women


def county_names() -> dict[str, str]:
    rucc = pd.read_csv(ROOT / "data/raw/rucc/rucc2023.csv", dtype=str,
                       encoding="latin-1").drop_duplicates("FIPS")
    names = {
        r.FIPS: f"{r.County_Name}, {r.State}"
        for r in rucc.itertuples()
        if r.FIPS and r.County_Name
    }
    out = {}
    for fips, name in names.items():
        unit = to_unit(fips)
        if unit and unit not in out:
            out[unit] = name
    out.update(UNIT_LABELS)
    return out


def rolling_rate(panel: pd.DataFrame) -> pd.DataFrame:
    """Centred 3-year pooled GFR, which damps small-county sampling noise."""
    p = panel.sort_values(["fips", "year"]).copy()
    g = p.groupby("fips")
    b = g["births"].transform(lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    w = g["women_15_44"].transform(lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    p["gfr_smooth"] = 1000 * b / w
    return p


def main() -> None:
    panel = rolling_rate(load())
    years = sorted(panel["year"].unique().tolist())
    units = sorted(panel["fips"].unique().tolist())
    idx = {u: i for i, u in enumerate(units)}

    base = (
        panel[panel["year"].isin(BASELINE)]
        .groupby("fips")
        .apply(lambda g: 1000 * g["births"].sum() / g["women_15_44"].sum(),
               include_groups=False)
    )

    gfr_rows, chg_rows, birth_rows = [], [], []
    for year in years:
        sub = panel[panel["year"] == year].set_index("fips")
        gfr = sub["gfr_smooth"].reindex(units)
        gfr_rows.append([round(v, 1) if pd.notna(v) else None for v in gfr])
        chg = 100 * (gfr / base.reindex(units) - 1)
        chg_rows.append([round(v, 1) if pd.notna(v) else None for v in chg])
        birth_rows.append([int(v) if pd.notna(v) else None
                           for v in sub["births"].reindex(units)])

    topo = json.loads((ROOT / "data/raw/geo/counties-10m.json").read_text())
    paths = geometry_paths(topo)
    geo, geo2unit = {}, {}
    for fips, d in paths.items():
        unit = to_unit(fips)
        if unit in idx:
            geo[fips] = d
            geo2unit[fips] = idx[unit]

    states = {k: v for k, v in state_paths(topo).items()
              if not k.startswith(("60", "66", "69", "72", "78"))}

    metro = by_metro(panel, "fixed")
    metro_series = {
        label: {
            "gfr": [round(v, 2) for v in grp.sort_values("year")["gfr"]],
            "cfr": [round(v, 4) for v in grp.sort_values("year")["cfr"]],
            "share": [round(v * 100, 2)
                      for v in grp.sort_values("year")["women_15_44_share"]],
        }
        for label, grp in metro.groupby("metro_label")
    }

    rucc_rows = []
    ss = shift_share(panel)
    for cls in [RUCC_CLASS[i] for i in range(1, 10)]:
        if cls not in ss.index:
            continue
        r = ss.loc[cls]
        rucc_rows.append({
            "cls": cls,
            "start": round(r["gfr_start"], 1),
            "end": round(r["gfr_end"], 1),
            "change": round(100 * (r["gfr_end"] / r["gfr_start"] - 1), 1),
            "share_start": round(r["share_start"] * 100, 2),
            "share_end": round(r["share_end"] * 100, 2),
        })

    national = panel.groupby("year").apply(
        lambda g: 1000 * g["births"].sum() / g["women_15_44"].sum(),
        include_groups=False,
    )

    payload = {
        "years": years,
        "units": units,
        "names": {u: county_names().get(u, u) for u in units},
        "geo": geo,
        "geoUnit": geo2unit,
        "states": states,
        "gfr": gfr_rows,
        "chg": chg_rows,
        "births": birth_rows,
        "baseline": [round(v, 1) for v in base.reindex(units)],
        "national": [round(v, 1) for v in national.reindex(years)],
        "metro": metro_series,
        "rucc": rucc_rows,
        "decomposition": {
            "within": round(ss["within"].sum(), 2),
            "between": round(ss["between"].sum(), 2),
            "interaction": round(ss["interaction"].sum(), 2),
        },
        "interpolatedYears": [2000, 2010],
        "outliers": int(panel["births_outlier"].sum()),
    }

    out = ROOT / "viz" / "fertility_data.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"wrote {out}  {out.stat().st_size/1e6:.2f} MB")
    print(f"  years {years[0]}-{years[-1]}  units {len(units)}  geometries {len(geo)}")
    print(f"  decomposition {payload['decomposition']}")


if __name__ == "__main__":
    main()
