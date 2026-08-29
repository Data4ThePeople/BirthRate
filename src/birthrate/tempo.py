"""Timing versus quantum: is fertility falling, or just moving later?

A period total fertility rate is synthetic. It asks what a woman would bear if
she spent her whole life under one calendar year's age-specific rates. When
women postpone childbearing, births that will still happen simply are not
happening *yet*, and the period TFR reads low even if no one ends up with fewer
children. That is tempo distortion, and it makes a postponement and a genuine
decline look identical in the headline number.

Two ways to separate them are used here.

Cohort completed fertility follows real women through their whole reproductive
span and counts what they actually had. It assumes nothing - but it can only be
computed once a cohort has finished, so it is silent about anyone still of
childbearing age.

The Bongaarts-Feeney adjustment removes the distortion from a period measure by
inflating the TFR in proportion to how fast the mean age of childbearing is
rising, giving a reading for years no cohort has yet completed. The version here
is the aggregate one; the order-specific form is better behaved but needs birth
order, which public data does not carry for the modern era.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "asfr"

# Five-year bands and their midpoints. TFR is computed over 15-44: both sources
# cover exactly these, whereas the 45+ band is reported on a 45-49 denominator
# by one and 45-54 by the other. The bands left out contribute under half a
# percent of TFR and their omission is constant across the series.
BANDS = {"15-19": 17.5, "20-24": 22.5, "25-29": 27.5,
         "30-34": 32.5, "35-39": 37.5, "40-44": 42.5}
WIDTH = 5

HISTORIC = ("https://data.cdc.gov/resource/yt7u-eiyg.json"
            "?$select=year,age_group,birth_rate&$limit=5000")
DQS = ("https://data.cdc.gov/resource/daba-4vfq.json"
       "?$select=time_period,subgroup,estimate"
       "&$where=estimate_type='Live births per 1,000 females'"
       " AND classification='Demographic Characteristic'&$limit=5000")
DQS_FROM = 2016


def _cached(name: str, url: str) -> list[dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    if not path.exists():
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        path.write_text(resp.text)
    return json.loads(path.read_text())


def national_asfr(first: int = 1940, last: int = 2024) -> pd.DataFrame:
    """Age-specific fertility rates per 1,000 women, one row per year."""
    hist = pd.DataFrame(_cached("nchs_birth_rates_by_age.json", HISTORIC))
    hist["year"] = hist["year"].astype(int)
    hist["band"] = hist["age_group"].str.replace(" Years", "", regex=False).str.strip()
    hist["rate"] = hist["birth_rate"].astype(float)
    hist = hist[hist["band"].isin(BANDS) & (hist["year"] < DQS_FROM)]

    dqs = pd.DataFrame(_cached("nchs_dqs_birth_rates_by_age.json", DQS))
    dqs["year"] = dqs["time_period"].astype(int)
    dqs["band"] = dqs["subgroup"].str.replace(" years", "", regex=False).str.strip()
    dqs["rate"] = dqs["estimate"].astype(float)
    dqs = dqs[dqs["band"].isin(BANDS) & (dqs["year"] >= DQS_FROM)]

    df = pd.concat([hist[["year", "band", "rate"]], dqs[["year", "band", "rate"]]])
    df = df[df["year"].between(first, last)]
    wide = df.pivot(index="year", columns="band", values="rate")[list(BANDS)]
    gaps = sorted(set(range(first, last + 1)) - set(wide.index))
    if gaps:
        raise ValueError(f"no national ASFR for {gaps}")
    return wide


def period_tfr(asfr: pd.DataFrame) -> pd.Series:
    """Children per woman implied by one year's rates."""
    return (asfr.sum(axis=1) * WIDTH / 1000).rename("tfr")


def mean_age_childbearing(asfr: pd.DataFrame) -> pd.Series:
    """Fertility-weighted mean age of the mother, in years."""
    mids = np.array(list(BANDS.values()))
    return pd.Series((asfr.values * mids).sum(axis=1) / asfr.values.sum(axis=1),
                     index=asfr.index, name="mac")


def bongaarts_feeney(asfr: pd.DataFrame, smooth: int = 5) -> pd.DataFrame:
    """Tempo-adjusted TFR: TFR / (1 - r), r the annual rise in mean age.

    The mean-age change is smoothed, because a single year's wobble in r
    produces a wild swing in the adjustment.
    """
    tfr, mac = period_tfr(asfr), mean_age_childbearing(asfr)
    r = mac.diff().rolling(smooth, center=True, min_periods=2).mean()
    adjusted = (tfr / (1 - r)).rename("tfr_adjusted")
    return pd.concat([tfr, mac, r.rename("r"), adjusted], axis=1)


def cohort_completed_fertility(asfr: pd.DataFrame) -> pd.DataFrame:
    """Children actually borne by each birth cohort, summed along its diagonal.

    A cohort born in year c passes through band [lo, hi] during calendar years
    c+lo to c+hi. Only cohorts observed across every band are returned, so the
    result stops well short of the present - which is the price of measuring
    quantum without assumptions.
    """
    years = set(asfr.index)
    rows = []
    for cohort in range(int(asfr.index.min()) - 45, int(asfr.index.max()) + 1):
        total, complete = 0.0, True
        for band, mid in BANDS.items():
            lo, hi = (int(x) for x in band.split("-"))
            span = [c for c in range(cohort + lo, cohort + hi + 1) if c in years]
            if len(span) < WIDTH:
                complete = False
                break
            total += asfr.loc[span, band].mean() * WIDTH / 1000
        if complete:
            rows.append({"cohort": cohort, "ccf": total,
                         "mean_year": cohort + float(np.mean(list(BANDS.values())))})
    return pd.DataFrame(rows).set_index("cohort")


def cumulative_by_age(asfr: pd.DataFrame, cohorts: list[int]) -> dict[int, dict[int, float]]:
    """Children borne per woman by each exact age, for real birth cohorts.

    This is the assumption-free view. It uses only each cohort's own recorded
    rates, so a cohort that is merely postponing shows up as running below its
    predecessors early and closing the gap later, while one that will end up
    with fewer children never closes it.
    """
    out: dict[int, dict[int, float]] = {}
    for cohort in cohorts:
        running, reached = 0.0, {}
        for band in BANDS:
            lo, hi = (int(x) for x in band.split("-"))
            years = [y for y in range(cohort + lo, cohort + hi + 1) if y in asfr.index]
            if len(years) < WIDTH:
                break
            running += asfr.loc[years, band].mean() * WIDTH / 1000
            reached[hi + 1] = round(running, 4)
        out[cohort] = reached
    return out
