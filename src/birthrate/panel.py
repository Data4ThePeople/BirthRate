"""Assemble the county-year fertility panel, 1991-2024."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from birthrate import metrics
from birthrate.geography import HETEROGENEOUS_UNITS, UNIT_LABELS, harmonize
from birthrate.sources.asfr import load_asfr
from birthrate.sources.pep import load_births
from birthrate.sources.rucc import MIXED_METRO_BAND, RUCC_CLASS, unit_rucc
from birthrate.sources.seer import load_denominators

OUT = Path(__file__).resolve().parents[2] / "data" / "processed"

FIRST_YEAR, LAST_YEAR = 1991, 2024
# PEP stubs each vintage's launch year, so no published county file covers the
# estimate years that straddle a decennial census. 2020 is recovered from the
# vintage-2020 release; 2000 and 2010 have no source and are interpolated.
INTERPOLATED_YEARS = [2000, 2010]

POP_COLS = ["pop_total", "women_15_44", "w15_19", "w20_24", "w25_29",
            "w30_34", "w35_39", "w40_44"]

# A unit-year whose births differ from the mean of its two neighbouring years
# by more than this is flagged. Small counties swing this much naturally, so
# the flag only applies to units that normally record at least MIN_FOR_OUTLIER
# births. Flagged values are kept, never silently smoothed.
OUTLIER_TOLERANCE = 0.40
MIN_FOR_OUTLIER = 100


def _interpolate_missing_births(df: pd.DataFrame) -> pd.DataFrame:
    """Fill the decade-boundary gaps by linear interpolation within each unit."""
    full = pd.MultiIndex.from_product(
        [sorted(df["fips"].unique()), range(FIRST_YEAR, LAST_YEAR + 1)],
        names=["fips", "year"],
    )
    out = df.set_index(["fips", "year"]).reindex(full)
    out["births_interpolated"] = out["births"].isna()
    out["births"] = (
        out.groupby(level="fips")["births"]
        .transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
        .round()
    )
    return out.reset_index()


def _flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Mark isolated birth counts that neither neighbouring year supports."""
    out = df.sort_values(["fips", "year"]).copy()
    grp = out.groupby("fips")["births"]
    neighbours = (grp.shift(1) + grp.shift(-1)) / 2.0
    deviation = (out["births"] - neighbours).abs() / neighbours.where(neighbours > 0)
    typical = out.groupby("fips")["births"].transform("median")
    out["births_outlier"] = (
        (deviation > OUTLIER_TOLERANCE) & (typical >= MIN_FOR_OUTLIER)
    ).fillna(False)
    return out


def build() -> pd.DataFrame:
    births = harmonize(load_births(), ["births"])
    births = _interpolate_missing_births(births)

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
    panel = _flag_outliers(panel)

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
