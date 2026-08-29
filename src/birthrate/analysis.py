"""Metro/nonmetro fertility series from the county-year panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from birthrate.sources.rucc import RUCC_CLASS

PANEL = Path("data/processed/county_year_fertility.parquet")
VINTAGE_FOR_YEAR = {1993: range(1982, 1999), 2003: range(1999, 2009),
                    2013: range(2009, 2019), 2023: range(2019, 2025)}


def load() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def _aggregate(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Births-weighted group series: a group's GFR is its pooled rate."""
    g = df.groupby([key, "year"], as_index=False).agg(
        births=("births", "sum"),
        women_15_44=("women_15_44", "sum"),
        expected_births=("expected_births", "sum"),
        pop_total=("pop_total", "sum"),
        units=("fips", "nunique"),
    )
    g["gfr"] = 1000 * g["births"] / g["women_15_44"]
    g["women_15_44_share"] = g["women_15_44"] / g["pop_total"]
    # Rescale expected births so the national CFR is 1.0 in every year, then
    # the group CFR reads as "fertility relative to the nation, net of age".
    nat = df.groupby("year").agg(b=("births", "sum"), e=("expected_births", "sum"))
    scale = (nat["b"] / nat["e"]).rename("scale")
    g = g.merge(scale, left_on="year", right_index=True)
    g["cfr"] = g["births"] / (g["expected_births"] * g["scale"])
    return g.drop(columns="scale")


def by_rucc_class(df: pd.DataFrame | None = None,
                  reliable_only: bool = True) -> pd.DataFrame:
    df = load() if df is None else df
    if reliable_only:
        df = df[df["rucc_reliable"]]
    df = df.assign(rucc_class=df["rucc_2013"].map(RUCC_CLASS))
    return _aggregate(df, "rucc_class")


def by_metro(df: pd.DataFrame | None = None, vintage: str = "fixed") -> pd.DataFrame:
    """Metro vs nonmetro, under a frozen or contemporaneous RUCC vintage."""
    df = load() if df is None else df
    df = df[df["rucc_reliable"]].copy()
    if vintage == "fixed":
        code = df["rucc_2013"]
    else:
        code = pd.Series(pd.NA, index=df.index, dtype="Int64")
        for v, years in VINTAGE_FOR_YEAR.items():
            mask = df["year"].isin(years)
            code = code.mask(mask, df.loc[:, f"rucc_{v}"])
    df["metro_label"] = code.le(3).map({True: "Metro", False: "Nonmetro"})
    return _aggregate(df, "metro_label")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, "src")
    panel = load()

    print("=== Metro vs nonmetro GFR (frozen 2013 classification) ===")
    m = by_metro(panel, "fixed")
    piv = m.pivot(index="year", columns="metro_label", values="gfr").round(1)
    piv["gap"] = (piv["Nonmetro"] - piv["Metro"]).round(1)
    print(piv.loc[[1991, 1995, 2000, 2005, 2010, 2015, 2019, 2024]].to_string())

    print("\n=== Same, age-standardized (CFR, national = 1.00) ===")
    pc = m.pivot(index="year", columns="metro_label", values="cfr").round(3)
    pc["gap"] = (pc["Nonmetro"] - pc["Metro"]).round(3)
    print(pc.loc[[1991, 1995, 2000, 2005, 2010, 2015, 2019, 2024]].to_string())

    print("\n=== Contemporaneous vintage (robustness) ===")
    mc = by_metro(panel, "contemporaneous")
    pv = mc.pivot(index="year", columns="metro_label", values="gfr").round(1)
    pv["gap"] = (pv["Nonmetro"] - pv["Metro"]).round(1)
    print(pv.loc[[1991, 2000, 2010, 2019, 2024]].to_string())

    print("\n=== Women 15-44 as a share of population ===")
    ps = m.pivot(index="year", columns="metro_label", values="women_15_44_share")
    print((ps * 100).round(2).loc[[1991, 2000, 2010, 2019, 2024]].to_string())

    print("\n=== GFR by RUCC class, 1991 vs 2024 ===")
    r = by_rucc_class(panel)
    wide = r.pivot(index="rucc_class", columns="year", values="gfr")[[1991, 2024]]
    wide["change_%"] = (100 * (wide[2024] / wide[1991] - 1)).round(1)
    order = [RUCC_CLASS[i] for i in range(1, 10) if RUCC_CLASS[i] in wide.index]
    print(wide.loc[order].round(1).to_string())


def shift_share(df: pd.DataFrame | None = None, start: int = 1991,
                end: int = 2024) -> pd.DataFrame:
    """Decompose the national GFR change into within-group and composition parts.

    National GFR is the female-population-weighted mean of group GFRs, so the
    change from `start` to `end` splits into a within effect (group rates moved),
    a between effect (women redistributed across groups) and their interaction.
    """
    df = load() if df is None else df
    df = df[df["rucc_reliable"]].copy()
    df["rucc_class"] = df["rucc_2013"].map(RUCC_CLASS)
    g = _aggregate(df, "rucc_class")

    wide = g[g["year"].isin([start, end])].pivot(
        index="rucc_class", columns="year", values=["gfr", "women_15_44"]
    )
    gfr0, gfr1 = wide[("gfr", start)], wide[("gfr", end)]
    w0 = wide[("women_15_44", start)] / wide[("women_15_44", start)].sum()
    w1 = wide[("women_15_44", end)] / wide[("women_15_44", end)].sum()

    out = pd.DataFrame({
        "within": w0 * (gfr1 - gfr0),
        "between": (w1 - w0) * gfr0,
        "interaction": (w1 - w0) * (gfr1 - gfr0),
        "share_start": w0, "share_end": w1,
        "gfr_start": gfr0, "gfr_end": gfr1,
    })
    order = [RUCC_CLASS[i] for i in range(1, 10) if RUCC_CLASS[i] in out.index]
    return out.loc[order]
