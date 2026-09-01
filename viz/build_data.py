"""Compile the panel + geometry into one compact JSON payload for the artifact."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from birthrate.analysis import (by_county_type, by_metro, load,  # noqa: E402
                                shift_share)
from birthrate.panel import ALLOCATED_YEARS, PROVISIONAL_YEARS  # noqa: E402
from birthrate.geography import UNIT_LABELS, to_unit  # noqa: E402
from birthrate.tempo import (bongaarts_feeney, cohort_completed_fertility,  # noqa: E402
                             cumulative_by_age, national_asfr)
from birthrate.sources.rucc import RUCC_CLASS  # noqa: E402
from project import geometry_paths, state_paths  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASELINE = [1982, 1983, 1984]
SMOOTH = 3  # centered rolling window, pooled births over pooled women


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
    """Centered 3-year pooled GFR, which damps small-county sampling noise.

    Two years carry no published source and are absent from the panel. The
    window is taken over a complete year index so a gap is spanned rather
    than silently pulling in a year further away, then the gaps are dropped
    again.
    """
    years = range(int(panel["year"].min()), int(panel["year"].max()) + 1)
    full = pd.MultiIndex.from_product(
        [sorted(panel["fips"].unique()), years], names=["fips", "year"])
    p = panel.set_index(["fips", "year"]).reindex(full).reset_index()
    g = p.groupby("fips")
    b = g["births"].transform(lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    w = g["women_15_44"].transform(lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    p["gfr_smooth"] = 1000 * b / w
    return p[p["births"].notna()]


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

    state_names = {
        "01":"Alabama","02":"Alaska","04":"Arizona","05":"Arkansas","06":"California",
        "08":"Colorado","09":"Connecticut","10":"Delaware","11":"District of Columbia",
        "12":"Florida","13":"Georgia","15":"Hawaii","16":"Idaho","17":"Illinois",
        "18":"Indiana","19":"Iowa","20":"Kansas","21":"Kentucky","22":"Louisiana",
        "23":"Maine","24":"Maryland","25":"Massachusetts","26":"Michigan","27":"Minnesota",
        "28":"Mississippi","29":"Missouri","30":"Montana","31":"Nebraska","32":"Nevada",
        "33":"New Hampshire","34":"New Jersey","35":"New Mexico","36":"New York",
        "37":"North Carolina","38":"North Dakota","39":"Ohio","40":"Oklahoma","41":"Oregon",
        "42":"Pennsylvania","44":"Rhode Island","45":"South Carolina","46":"South Dakota",
        "47":"Tennessee","48":"Texas","49":"Utah","50":"Vermont","51":"Virginia",
        "53":"Washington","54":"West Virginia","55":"Wisconsin","56":"Wyoming",
    }

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

    # Per-state series and map extents, for the state selector.
    panel_state = panel.assign(st=panel["fips"].str[:2])
    st_year = panel_state.groupby(["st", "year"], as_index=False).agg(
        births=("births", "sum"), women=("women_15_44", "sum"))
    st_year = st_year.sort_values(["st", "year"])
    grp = st_year.groupby("st")
    pooled_b = grp["births"].transform(
        lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    pooled_w = grp["women"].transform(
        lambda s: s.rolling(SMOOTH, center=True, min_periods=1).sum())
    st_year["gfr"] = 1000 * pooled_b / pooled_w
    state_series = {
        st: [round(v, 2) for v in g.sort_values("year")["gfr"]]
        for st, g in st_year.groupby("st")
    }
    st_base = st_year[st_year["year"].isin(BASELINE)].groupby("st").apply(
        lambda g: 1000 * g["births"].sum() / g["women"].sum(), include_groups=False)
    state_units = (panel_state[panel_state["year"] == years[-1]]
                   .groupby("st")["fips"].nunique().to_dict())

    bounds: dict[str, list[float]] = {}
    for fips, path_d in geo.items():
        st = fips[:2]
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", path_d)]
        xs, ys = nums[0::2], nums[1::2]
        box = bounds.setdefault(st, [min(xs), min(ys), max(xs), max(ys)])
        box[0] = min(box[0], min(xs)); box[1] = min(box[1], min(ys))
        box[2] = max(box[2], max(xs)); box[3] = max(box[3], max(ys))

    states_meta = {
        st: {"name": state_names.get(st, st), "box": [round(v, 1) for v in box],
             "gfr": state_series.get(st, []), "units": state_units.get(st, 0),
             "baseline": round(float(st_base.get(st, float("nan"))), 2)}
        for st, box in sorted(bounds.items()) if st in state_names
    }

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

    # The metro/rural gap collapses through the 1980s and re-opens after the
    # mid-1990s, so a single start-to-end change would hide two opposite
    # regimes. Report both eras, split at the year the gap bottoms out.
    PIVOT_YEAR = 1994
    rucc_rows = []
    ss = shift_share(panel, years[0], years[-1])
    era1 = shift_share(panel, years[0], PIVOT_YEAR)
    era2 = shift_share(panel, PIVOT_YEAR, years[-1])
    for cls in [RUCC_CLASS[i] for i in range(1, 10)]:
        if cls not in ss.index:
            continue
        r = ss.loc[cls]
        a, b = era1.loc[cls], era2.loc[cls]
        rucc_rows.append({
            "cls": cls,
            "start": round(r["gfr_start"], 1),
            "end": round(r["gfr_end"], 1),
            "change": round(100 * (r["gfr_end"] / r["gfr_start"] - 1), 1),
            "mid": round(a["gfr_end"], 1),
            "change_era1": round(100 * (a["gfr_end"] / a["gfr_start"] - 1), 1),
            "change_era2": round(100 * (b["gfr_end"] / b["gfr_start"] - 1), 1),
            "share_start": round(r["share_start"] * 100, 2),
            "share_end": round(r["share_end"] * 100, 2),
        })

    ctypes = by_county_type(panel)
    county_types = {
        label: {
            "units": v["units"],
            "gfr": [round(x, 1) for x in v["gfr"].reindex(years)],
            "change8287": round(100 * (v["gfr"][1987] / v["gfr"][1982] - 1), 1),
        }
        for label, v in ctypes.items()
    }

    asfr = national_asfr(1940, years[-1])
    bf = bongaarts_feeney(asfr)
    ccf = cohort_completed_fertility(asfr)
    COHORTS = [1950, 1960, 1970, 1980, 1990]
    tempo = {
        "years": [int(y) for y in bf.index],
        "tfr": [round(v, 3) for v in bf["tfr"]],
        "adjusted": [None if pd.isna(v) else round(v, 3) for v in bf["tfr_adjusted"]],
        "meanAge": [round(v, 2) for v in bf["mac"]],
        "ccf": [{"cohort": int(c), "ccf": round(r.ccf, 3),
                 "meanYear": round(r.mean_year, 1)} for c, r in ccf.iterrows()],
        "cumulative": {str(c): v for c, v in cumulative_by_age(asfr, COHORTS).items()},
        "cohorts": COHORTS,
    }

    pooled_with_modeled = sorted(
        y for y in years
        if y not in ALLOCATED_YEARS
        and any(n in ALLOCATED_YEARS for n in (y - 1, y + 1))
    )
    short_window = sorted(
        y for y in years
        if sum(1 for n in (y - 1, y, y + 1) if n in set(years)) < SMOOTH
    )
    flagged = sorted(
        [idx[r.fips], years.index(int(r.year))]
        for r in panel[panel["births_outlier"]].itertuples()
        if r.fips in idx and int(r.year) in years
    )

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
        "stateMeta": states_meta,
        "gfr": gfr_rows,
        "chg": chg_rows,
        "births": birth_rows,
        "baseline": [round(v, 1) for v in base.reindex(units)],
        "national": [round(v, 1) for v in national.reindex(years)],
        "metro": metro_series,
        "rucc": rucc_rows,
        "countyTypes": county_types,
        "tempo": tempo,
        "decomposition": {
            "within": round(ss["within"].sum(), 2),
            "between": round(ss["between"].sum(), 2),
            "interaction": round(ss["interaction"].sum(), 2),
        },
        "pivotYear": PIVOT_YEAR,
        "allocatedYears": ALLOCATED_YEARS,
        # A displayed rate is a three-year pool, so the years either side of a
        # modeled one carry modeled births too - a third of their window
        # against two thirds for 1989-90. Flagging only the modeled years
        # themselves would understate how far the estimate reaches.
        "pooledWithModeled": pooled_with_modeled,
        "provisionalYears": [y for y in PROVISIONAL_YEARS if y in years],
        # Years whose pooling window is short a year, because they sit at the
        # end of the series or beside a dropped one. Their rate is pooled over
        # two years rather than three, so it carries more sampling noise.
        "shortWindowYears": short_window,
        "outliers": int(panel["births_outlier"].sum()),
        # [unit index, year index] for every cell the surrounding years do not
        # support, so the tooltip can say so rather than presenting the value
        # as though nothing were wrong with it.
        "flagged": flagged,
    }

    out = ROOT / "viz" / "fertility_data.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"wrote {out}  {out.stat().st_size/1e6:.2f} MB")
    print(f"  years {years[0]}-{years[-1]}  units {len(units)}  geometries {len(geo)}")
    print(f"  decomposition {payload['decomposition']}")


if __name__ == "__main__":
    main()
