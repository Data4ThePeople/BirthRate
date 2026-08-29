"""National age-specific fertility rates, used as the standard schedule.

Indirect standardization needs one national rate per five-year age band per
year. Two NCHS series on data.cdc.gov cover 1991-2024 between them and agree
exactly on their 2016-2018 overlap:

    yt7u-eiyg  Birth Rates for Females by Age Group        1940-2018
    daba-4vfq  DQS Birth and fertility rates by age group  2016-2024

CDC WONDER would be the alternative but its API is national-only by policy
and the host blocks automated requests, so these curated series are used.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "asfr"

BANDS = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44"]
BAND_TO_COL = {b: f"w{b.replace('-', '_')}" for b in BANDS}

HISTORIC = (
    "https://data.cdc.gov/resource/yt7u-eiyg.json"
    "?$select=year,age_group,birth_rate&$limit=5000"
)
DQS = (
    "https://data.cdc.gov/resource/daba-4vfq.json"
    "?$select=time_period,subgroup,estimate"
    "&$where=estimate_type='Live births per 1,000 females'"
    " AND classification='Demographic Characteristic'"
    "&$limit=5000"
)

# DQS is the current series; where both cover a year, prefer it.
DQS_FROM = 2016


def _cached(name: str, url: str) -> list[dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    if not path.exists():
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        path.write_text(resp.text)
    return json.loads(path.read_text())


def load_asfr(min_year: int = 1991, max_year: int = 2024) -> pd.DataFrame:
    """Wide frame: one row per year, one column per childbearing age band."""
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
    df = df[df["year"].between(min_year, max_year)]

    wide = df.pivot(index="year", columns="band", values="rate")
    missing = [b for b in BANDS if b not in wide.columns]
    if missing:
        raise ValueError(f"missing age bands: {missing}")
    wide = wide[BANDS]

    gaps = sorted(set(range(min_year, max_year + 1)) - set(wide.index))
    if gaps:
        raise ValueError(f"no national ASFR for years: {gaps}")
    return wide.rename(columns=BAND_TO_COL).reset_index()


if __name__ == "__main__":
    a = load_asfr()
    print(a.to_string(index=False))
