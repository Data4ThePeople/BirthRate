"""End-to-end validation of the county-year fertility panel.

Run: PYTHONPATH=src .venv/bin/python tests/validate.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from birthrate.panel import (ALLOCATED_YEARS, DROPPED_YEARS,  # noqa: E402
                             FIRST_YEAR, INTERPOLATED_YEARS, LAST_YEAR,
                             NBER_LAST_YEAR, PROVISIONAL_YEARS)
from birthrate.sources.asfr import BAND_TO_COL, load_asfr  # noqa: E402

PANEL = Path("data/processed/county_year_fertility.parquet")

# NCHS published national live births for the microdata era. These are
# calendar-year totals published by NCHS, not derived from our files, so
# reproducing them exactly validates the record weighting and residence filter.
NCHS_MICRODATA_BIRTHS = {
    1982: 3_680_537, 1983: 3_638_933, 1984: 3_669_141, 1985: 3_760_561,
    1986: 3_756_547, 1987: 3_809_394, 1988: 3_909_510, 1989: 4_040_958,
    1990: 4_158_212,
}

# NCHS published national live births, calendar year, final data.
NCHS_BIRTHS = {
    1991: 4_110_907, 1992: 4_065_014, 1993: 4_000_240, 1994: 3_952_767,
    1995: 3_899_589, 1996: 3_891_494, 1997: 3_880_894, 1998: 3_941_553,
    1999: 3_959_417, 2000: 4_058_814, 2001: 4_025_933, 2002: 4_021_726,
    2003: 4_089_950, 2004: 4_112_052, 2005: 4_138_349, 2006: 4_265_555,
    2007: 4_316_233, 2008: 4_247_694, 2009: 4_130_665, 2010: 3_999_386,
    2011: 3_953_590, 2012: 3_952_841, 2013: 3_932_181, 2014: 3_988_076,
    2015: 3_978_497, 2016: 3_945_875, 2017: 3_855_500, 2018: 3_791_712,
    2019: 3_747_540, 2020: 3_613_647, 2021: 3_664_292, 2022: 3_667_758,
    2023: 3_596_017,
}

# Orleans and St Bernard Parish after Hurricane Katrina: a real population
# event, not a data defect, and the only legitimate large discontinuity.
KATRINA_UNITS = {"22071", "22087"}

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((bool(ok), f"{name}{': ' + detail if detail else ''}"))


def main() -> int:
    p = pd.read_parquet(PANEL)
    nat = p.groupby("year").agg(births=("births", "sum"),
                                women=("women_15_44", "sum"))
    nat["gfr"] = 1000 * nat["births"] / nat["women"]

    # --- 1. National births track published NCHS totals -------------------
    present = set(nat.index)
    cal = {y: abs(nat.loc[y, "births"] - v) / v * 100
           for y, v in NCHS_BIRTHS.items() if y in present}
    check("national births track NCHS (median <1%, max <4%)",
          statistics.median(cal.values()) < 1.0 and max(cal.values()) < 4.0,
          f"median {statistics.median(cal.values()):.2f}%, "
          f"max {max(cal.values()):.2f}% ({max(cal, key=cal.get)})")

    # --- 1b. The microdata era must reproduce published totals exactly ----
    micro = {y: abs(nat.loc[y, "births"] - v) / v * 100
             for y, v in NCHS_MICRODATA_BIRTHS.items() if y in set(nat.index)}
    check("microdata era reproduces NCHS totals exactly (<0.05%)",
          max(micro.values()) < 0.05,
          f"max {max(micro.values()):.4f}% ({max(micro, key=micro.get)})")

    # --- 2. The residual is the July-June estimate-year window ------------
    # PEP estimate year t spans Jul t-1 to Jun t, so it should sit closer to
    # the mean of calendar years t-1 and t than to calendar year t alone.
    blend = {}
    for y in NCHS_BIRTHS:
        if y - 1 in NCHS_BIRTHS and y in present:
            mid = (NCHS_BIRTHS[y - 1] + NCHS_BIRTHS[y]) / 2
            blend[y] = abs(nat.loc[y, "births"] - mid) / mid * 100
    shared = [y for y in blend if y in cal]
    check("estimate-year window explains the residual",
          statistics.median(blend[y] for y in shared)
          < statistics.median(cal[y] for y in shared)
          and max(blend.values()) < max(cal.values()),
          f"median {statistics.median(blend.values()):.2f}% vs "
          f"{statistics.median(cal[y] for y in shared):.2f}% unaligned")

    # --- 3. Denominators validated against the national rate schedule -----
    band_cols = list(BAND_TO_COL.values())
    asfr = load_asfr(FIRST_YEAR, LAST_YEAR).set_index("year")
    expected = (p.groupby("year")[band_cols].sum() * asfr / 1000.0).sum(axis=1)
    dev = {y: abs(expected[y] - v) / v * 100
           for y, v in NCHS_BIRTHS.items() if y in present}
    check("SEER age structure x NCHS rates reproduces NCHS births (<1%)",
          max(dev.values()) < 1.0,
          f"median {statistics.median(dev.values()):.2f}%, max {max(dev.values()):.2f}%")

    # --- 3b. Every year, including the ones NCHS_BIRTHS does not reach ------
    # The table above stops where NCHS final natality stops, which would leave
    # the newest year - the one the map opens on - with no external check at
    # all. SEER denominators and the NCHS rate schedule are both independent
    # of PEP, so their product is a check the latest year can also be held to.
    own = (100 * (nat["births"] / expected - 1)).dropna()
    check("panel births reconcile with SEER x NCHS rates in every year",
          own.abs().max() < 5.0 and own.abs().median() < 1.5,
          f"median |dev| {own.abs().median():.2f}%, max {own.abs().max():.2f}% "
          f"({own.abs().idxmax()}), {LAST_YEAR} {own[LAST_YEAR]:+.2f}%")

    # --- 4-5. Boundary integrity ------------------------------------------
    per_year = p.groupby("year")["fips"].apply(frozenset)
    check("unit set identical across all years", per_year.nunique() == 1,
          f"{p.fips.nunique():,} units")
    n_years = LAST_YEAR - FIRST_YEAR + 1 - len(DROPPED_YEARS)
    counts = p.groupby("fips")["year"].count()
    check("every unit has every year", bool((counts == n_years).all()),
          f"{n_years} years each")

    # --- 6. No partial-year stub survived ---------------------------------
    low = nat[nat["births"] < 2_000_000]
    check("no partial-year stub in the series", low.empty,
          "none" if low.empty else f"years {list(low.index)}")

    # --- 7. Estimated values confined to documented years ------------------
    interp = sorted(int(y) for y in p.loc[p["births_interpolated"], "year"].unique())
    check("no interpolated values anywhere in the panel",
          interp == INTERPOLATED_YEARS, str(interp) or "none")
    present = sorted(int(y) for y in p["year"].unique())
    check("years with no published source are absent, not estimated",
          all(y not in present for y in DROPPED_YEARS),
          f"{DROPPED_YEARS} dropped, {len(present)} years kept")
    alloc = sorted(int(y) for y in p.loc[p["births_allocated"], "year"].unique())
    check("state-constrained allocation only in 1989-90",
          alloc == ALLOCATED_YEARS, str(alloc))
    alloc_share = (p.loc[p["births_allocated"], "births"].sum()
                   / p.loc[p["year"].isin(ALLOCATED_YEARS), "births"].sum())
    check("allocated births are a minority of those two years",
          alloc_share < 0.35, f"{alloc_share*100:.1f}% of 1989-90 births")

    prov = sorted(int(y) for y in p.loc[p["births_provisional"], "year"].unique())
    check("provisional flag marks the newest vintage's final year",
          prov == PROVISIONAL_YEARS, str(prov))

    # --- 7d. The carried-forward signature must stay inside that flag ------
    # A vintage's last estimate year is produced before NCHS natality for it is
    # final, so many counties simply repeat the prior year. That is tolerable
    # once it is labeled; what must not happen is a later year quietly
    # acquiring the same signature while PROVISIONAL_YEARS still points at an
    # older one. Repeated-to-the-birth is rare in a settled year (under 4%,
    # and under 2.5% outside the pandemic) and common in a provisional one.
    wide = p.pivot(index="fips", columns="year", values="births")
    span = list(wide.columns)
    repeat = {}
    for a, b in zip(span, span[1:]):
        if b - a != 1:
            continue
        big = wide[a] >= 50
        repeat[int(b)] = 100 * (wide[b][big] == wide[a][big]).mean()
    settled = {y: v for y, v in repeat.items() if y not in PROVISIONAL_YEARS}
    worst = max(settled, key=settled.get)
    check("carried-forward births confined to the provisional year",
          max(settled.values()) < 5.0,
          f"settled max {settled[worst]:.1f}% ({worst}), "
          + ", ".join(f"{y} {repeat[y]:.1f}%" for y in PROVISIONAL_YEARS
                      if y in repeat))

    # --- 7b. The 1990/1991 source splice must not show as a step ----------
    span = nat.loc[1986:1995, "gfr"]
    steps = span.diff().abs().dropna()
    splice = abs(nat.loc[1991, "gfr"] - nat.loc[1990, "gfr"])
    check("no step artifact at the 1990/1991 source splice",
          splice <= steps.max(),
          f"splice {splice:.2f} vs largest nearby year-step {steps.max():.2f}")

    # --- 7c. The splice must not bias one kind of county against another ---
    # Small counties genuinely move differently from large ones - through the
    # 1980s they were shedding births far faster - so comparing the two groups
    # in the splice year alone finds a gap that has nothing to do with the
    # sources. The test is whether the splice year's gap is unusual for its era.
    import numpy as np

    seq = p.sort_values(["fips", "year"]).copy()
    seq["prev"] = seq.groupby("fips")["births"].shift()
    seq["prev_year"] = seq.groupby("fips")["year"].shift()
    seq = seq[(seq["prev"] >= 100) & (seq["year"] == seq["prev_year"] + 1)].copy()
    seq["chg"] = np.log(seq["births"] / seq["prev"]) * 100
    modeled = set(p.loc[p["births_allocated"], "fips"].unique())

    gaps = {}
    for year in range(1985, 2000):
        s = seq[seq["year"] == year]
        a = s[s["fips"].isin(modeled)]["chg"]
        b = s[~s["fips"].isin(modeled)]["chg"]
        if len(a) >= 50 and len(b) >= 50:
            gaps[year] = a.mean() - b.mean()
    ordinary = [g for y, g in gaps.items() if y not in (1989, 1990, 1991)]
    z = (gaps[1991] - np.mean(ordinary)) / np.std(ordinary)
    check("splice year is unremarkable for its era", abs(z) < 2,
          f"small-vs-large gap {gaps[1991]:+.2f} pts, {z:+.1f} sd from normal")

    # --- 8. Discontinuities ------------------------------------------------
    ordered = p.sort_values(["fips", "year"]).copy()
    prev = ordered.groupby("fips")["births"].shift()
    jump = (ordered["births"] - prev).abs() / prev.where(prev > 0)
    ordered["prev_year"] = ordered.groupby("fips")["year"].shift()
    material = ordered.loc[
        (jump > 0.5)
        & (prev > 1000)
        & (ordered["year"] == ordered["prev_year"] + 1)   # skip across the gaps
        & ~ordered["fips"].isin(KATRINA_UNITS)
    ]
    check("no unexplained jumps in units with >1,000 births", material.empty,
          "none" if material.empty
          else str(material[["fips", "year"]].to_dict("records")))

    flagged = int(p["births_outlier"].sum())
    check("isolated source anomalies stay rare (<0.1% of rows)",
          flagged / len(p) < 0.001, f"{flagged} of {len(p):,} rows")

    # A rule that needs both neighbors can never judge the first or last year,
    # or either side of a dropped one - six years, and the newest of them is
    # the least settled. Those years must remain reachable.
    one_sided = [FIRST_YEAR, LAST_YEAR]
    one_sided += [y for d in DROPPED_YEARS for y in (d - 1, d + 1)]
    reach = sorted(set(p.loc[p["births_outlier"], "year"]) & set(one_sided))
    check("the outlier rule reaches the ends of the series and the gaps",
          bool(reach), f"flags in {reach or 'none'} of {sorted(one_sided)}")

    # --- 9-10. Metric integrity -------------------------------------------
    nat_cfr = p.groupby("year").apply(
        lambda g: (g["births"] / g["cfr"]).sum() / g["births"].sum(),
        include_groups=False,
    )
    ratio = p.groupby("year")["births"].sum() / p.groupby("year")["expected_births"].sum()
    implied = p.groupby("year").apply(
        lambda g: g["births"].sum() / g["expected_births"].sum(), include_groups=False
    )
    check("national CFR normalized to 1.0",
          bool(((implied / ratio) - 1.0).abs().max() < 1e-9))
    for col in ["gfr", "cfr", "rucc_2013", "expected_births"]:
        check(f"no missing {col}", int(p[col].isna().sum()) == 0)

    passed = sum(ok for ok, _ in results)
    print(f"{'PASS' if passed == len(results) else 'FAIL'}  "
          f"({passed}/{len(results)} checks)\n")
    for ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {msg}")

    print("\nnational series:")
    show = nat.loc[[1982, 1985, 1988, 1990, 1991, 1995, 1999, 2007, 2019, 2024]]
    print(show.assign(births=lambda d: d.births.map("{:,.0f}".format),
                      women=lambda d: d.women.map("{:,.0f}".format),
                      gfr=lambda d: d.gfr.round(1)).to_string())
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
