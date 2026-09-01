"""Assemble the county-year fertility panel, 1991-2024."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from birthrate import metrics
from birthrate.geography import (HETEROGENEOUS_UNITS, UNIT_LABELS, harmonize,
                                 to_unit)
from birthrate.sources.asfr import load_asfr
from birthrate.sources import nber
from birthrate.sources.pep import CSV_VINTAGES, load_births
from birthrate.sources.rucc import MIXED_METRO_BAND, RUCC_CLASS, unit_rucc
from birthrate.sources.seer import load_denominators

OUT = Path(__file__).resolve().parents[2] / "data" / "processed"

FIRST_YEAR, LAST_YEAR = 1982, 2024
# Natality microdata identifies every county through 1988 and only counties of
# 100,000+ in 1989-90, where the rest are recovered from exact state totals.
NBER_LAST_YEAR = 1990
ALLOCATED_YEARS = [1989, 1990]
# PEP stubs each vintage's launch year, so no published county file covers the
# estimate years that straddle a decennial census. 2020 is recovered from the
# vintage-2020 release; 2000 and 2010 have no source at all. A linear
# interpolation between the neighbors would be unbiased at national level but
# carries no information - it is a deterministic function of the years either
# side - so plotting it adds nothing and invites it to be read as data. Those
# two years are dropped, not estimated. 1989-90 are different: 73% of their
# births are observed exactly and every state total is exact, so they are kept
# and flagged.
INTERPOLATED_YEARS: list[int] = []
DROPPED_YEARS = [2000, 2010]
# A vintage's final estimate year is built before NCHS natality for that year
# is final, so its county births are carried forward or projected rather than
# counted. It shows: in vintage 2024, 263 counties repeat their 2023 figure
# exactly and 41% move by under 1%, against roughly 10% in a settled year,
# while a handful swing implausibly far. The year is kept - it is the current
# reading and its national total is sound - but every cell is flagged so the
# map can say so.
PROVISIONAL_YEARS = [CSV_VINTAGES[-1][2]]

POP_COLS = ["pop_total", "women_15_44", "w15_19", "w20_24", "w25_29",
            "w30_34", "w35_39", "w40_44"]

# A unit-year whose births differ from the mean of its two neighboring years
# by more than this is flagged. Small counties swing this much naturally, so
# the flag only applies to units that normally record at least MIN_FOR_OUTLIER
# births. Flagged values are kept, never silently smoothed.
OUTLIER_TOLERANCE = 0.40
MIN_FOR_OUTLIER = 100
# The first and last year of the series, and the years either side of a
# dropped one, have only a single neighbor to be judged against. They fall
# back to that one under the same tolerance: a lone neighbor cannot separate
# an isolated spike from the start of a real level shift, but a flag is
# advisory rather than a correction, and a two-sided-only rule leaves 1982,
# 2024 and the four gap-adjacent years permanently unexaminable - which is
# exactly where the newest and least settled vintage sits.


def _assemble_births() -> pd.DataFrame:
    """Splice natality microdata (1982-1990) onto Census PEP (1991-2024).

    The two eras are on slightly different time bases: microdata counts calendar
    years, PEP counts July-June estimate years. Measured on 1995/1998/2001,
    where both sources name the same ~457 large counties, the median county
    ratio is within about 1% and its sign tracks the direction of the national
    trend in each year - the signature of a half-year offset rather than a
    difference in what is being counted.
    """
    pep = load_births()
    # The share basis and the allocation both run on stable analysis units, so
    # a county that changed FIPS between eras (Dade -> Miami-Dade) cannot be
    # counted once as a named county and again as an unnamed one.
    basis_88 = harmonize(nber.load_year(1988)[["fips", "year", "births"]],
                         ["births"]).set_index("fips")["births"]
    basis_91 = harmonize(pep[pep["year"] == 1991], ["births"]).set_index("fips")["births"]
    weights = pd.concat([basis_88, basis_91], axis=1).mean(axis=1).dropna()

    frames = []
    for year in range(FIRST_YEAR, ALLOCATED_YEARS[0]):
        part = nber.load_year(year)[["fips", "year", "births"]].copy()
        part["allocated"] = 0
        frames.append(part)
    for year in ALLOCATED_YEARS:
        part = nber.allocate_suppressed(year, weights, mapper=to_unit)
        part["allocated"] = part["births_allocated"].astype(int)
        frames.append(part[["fips", "year", "births", "allocated"]])
    pep = pep.copy()
    pep["allocated"] = 0
    frames.append(pep[["fips", "year", "births", "allocated"]])
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(["fips", "year"], as_index=False).agg(
        births=("births", "sum"), allocated=("allocated", "max"))


def _complete_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex onto every unit-year, distinguishing true zeros from gaps.

    In the microdata era a county absent from a year's file simply recorded no
    births, so those cells are zero. The only genuine gaps are the two PEP
    decade-boundary years, which are interpolated.
    """
    full = pd.MultiIndex.from_product(
        [sorted(df["fips"].unique()), range(FIRST_YEAR, LAST_YEAR + 1)],
        names=["fips", "year"],
    )
    out = df.set_index(["fips", "year"]).reindex(full)
    years = out.index.get_level_values("year")

    missing = out["births"].isna()
    out["births_interpolated"] = False
    out.loc[missing & (years <= NBER_LAST_YEAR), "births"] = 0.0
    out["births_allocated"] = out["allocated"].fillna(0).gt(0)
    return out.drop(columns="allocated").reset_index()


def _flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Mark birth counts that the surrounding years do not support.

    Where both neighbors exist the reference is their mean, which isolates a
    one-year spike. At the ends of the series and either side of a dropped
    year only one neighbor exists; those cells fall back to it rather than
    going unchecked, since a two-sided-only rule leaves 1982, 2024 and the
    four gap-adjacent years permanently unexaminable.
    """
    out = df.sort_values(["fips", "year"]).copy()
    grp = out.groupby("fips")["births"]
    prev, nxt = grp.shift(1), grp.shift(-1)

    both = (prev + nxt) / 2.0
    lone = prev.where(prev.notna(), nxt)          # whichever single one exists
    reference = both.where(both.notna(), lone)

    deviation = (out["births"] - reference).abs() / reference.where(reference > 0)
    typical = grp.transform("median")
    out["births_outlier"] = (
        (deviation > OUTLIER_TOLERANCE) & (typical >= MIN_FOR_OUTLIER)
    ).fillna(False)
    return out


def build() -> pd.DataFrame:
    births = harmonize(_assemble_births(), ["births", "allocated"])
    births = _complete_grid(births)

    pop = harmonize(load_denominators(FIRST_YEAR, LAST_YEAR), POP_COLS)
    panel = births.merge(pop, on=["fips", "year"], how="inner")

    panel = metrics.add_gfr(panel)
    panel = metrics.add_expected_births(panel, load_asfr(FIRST_YEAR, LAST_YEAR))
    panel = metrics.add_cfr(panel)
    panel = metrics.add_age_structure(panel)

    rucc = unit_rucc()
    panel = panel.merge(rucc, on="fips", how="left")
    panel["rucc_class"] = panel["rucc_2013"].map(RUCC_CLASS)
    panel["metro"] = panel["rucc_2013"].le(3)

    lo, hi = MIXED_METRO_BAND
    mixed = panel["metro_share_2013"].between(lo, hi, inclusive="neither")
    panel["rucc_reliable"] = ~(mixed | panel["fips"].isin(HETEROGENEOUS_UNITS))
    panel["merged_unit"] = panel["fips"].map(UNIT_LABELS)
    panel["births_provisional"] = panel["year"].isin(PROVISIONAL_YEARS)
    panel = _flag_outliers(panel)
    panel = panel[~panel["year"].isin(DROPPED_YEARS)]

    return panel.sort_values(["fips", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    p = build()
    path = OUT / "county_year_fertility.parquet"
    p.to_parquet(path, index=False)
    print(f"wrote {path}  rows={len(p):,}  units={p.fips.nunique():,}  "
          f"years={p.year.min()}-{p.year.max()}")
    print(p[["fips", "year", "births", "women_15_44", "gfr", "cfr",
             "rucc_2013"]].head(6).to_string(index=False))
