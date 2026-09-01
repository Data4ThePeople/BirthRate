"""Fertility measures for the county-year panel.

GFR is the intuitive headline but confounds fertility behavior with the age
structure of the local female population: a county whose women skew older
within 15-44 posts a lower GFR even if nobody's behavior changed. That is
exactly the confound a migration story turns on, so the panel also carries an
indirectly standardized measure.

Indirect standardization applies the national age schedule to each county's
own female age distribution to get expected births; the ratio of observed to
expected is the comparative fertility ratio (CFR). It needs only total births
per county, which is all the unsuppressed data provides.
"""
from __future__ import annotations

import pandas as pd

from birthrate.sources.asfr import BAND_TO_COL

BAND_COLS = list(BAND_TO_COL.values())


def add_gfr(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["gfr"] = 1000.0 * out["births"] / out["women_15_44"].where(out["women_15_44"] > 0)
    return out


def add_expected_births(df: pd.DataFrame, asfr: pd.DataFrame) -> pd.DataFrame:
    """Expected births under the national age schedule for each county-year."""
    out = df.merge(asfr, on="year", how="left", suffixes=("", "_rate"))
    expected = sum(
        out[col] * out[f"{col}_rate"] / 1000.0 for col in BAND_COLS
    )
    out["expected_births"] = expected
    return out.drop(columns=[f"{c}_rate" for c in BAND_COLS])


def add_cfr(df: pd.DataFrame) -> pd.DataFrame:
    """Observed/expected births, renormalized so the national CFR is 1.0.

    Renormalizing absorbs the level mismatch between PEP births (July-June
    estimate years, county-of-residence) and the calendar-year national rate
    schedule, leaving CFR to express only how a county compares with the
    nation once its age structure is accounted for.
    """
    out = df.copy()
    national = out.groupby("year")[["births", "expected_births"]].sum()
    scale = (national["births"] / national["expected_births"]).rename("_scale")
    out = out.merge(scale, left_on="year", right_index=True, how="left")
    denom = (out["expected_births"] * out["_scale"]).where(out["expected_births"] > 0)
    out["cfr"] = out["births"] / denom
    return out.drop(columns="_scale")


def add_age_structure(df: pd.DataFrame) -> pd.DataFrame:
    """Share of the population that is female 15-44, and the mean age within it."""
    out = df.copy()
    out["women_15_44_share"] = out["women_15_44"] / out["pop_total"].where(
        out["pop_total"] > 0
    )
    midpoints = {"w15_19": 17.5, "w20_24": 22.5, "w25_29": 27.5,
                 "w30_34": 32.5, "w35_39": 37.5, "w40_44": 42.5}
    weighted = sum(out[col] * mid for col, mid in midpoints.items())
    out["mean_age_15_44"] = weighted / out["women_15_44"].where(out["women_15_44"] > 0)
    return out
