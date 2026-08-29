"""USDA ERS county typology: which counties depended on farming.

The 1979 edition classifies a nonmetro county as farming-dependent when farming
contributed a weighted annual average of 20% or more of total labor and
proprietor income over 1975-1979. That window closes before the farm crisis
begins, so the classification cannot have been shaped by the crisis it is being
used to study - the later 1986 and 1989 editions can, since counties that lost
their farm economies get reclassified out.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "typology"

# AGTP79R / AGTP86: 0 = other nonmetro, 1 = farming-dependent nonmetro,
# 9 = metro county (not classified under this scheme).
FARMING = 1
OTHER_NONMETRO = 0
METRO = 9

LABELS = {FARMING: "Farming-dependent", OTHER_NONMETRO: "Other nonmetro", METRO: "Metro"}


TYPE_COLS = ["AGTP79R", "MFGTP79R", "MINTP79R", "GVTTP79R", "RETTP79", "POVTP79"]


def load_typology_full() -> pd.DataFrame:
    """Every 1979 economic-type flag, one row per county."""
    df = pd.read_excel(RAW / "typ1979_1986.xls", sheet_name="Data", dtype=str,
                       header=0)
    df = df[df["FIPS"].notna() & df["FIPS"].str.strip().str.isdigit()].copy()
    df["fips"] = df["FIPS"].str.strip().str.zfill(5)
    for col in TYPE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[["fips", *TYPE_COLS]]


def load_typology() -> pd.DataFrame:
    df = pd.read_excel(RAW / "typ1979_1986.xls", sheet_name="Data", dtype=str,
                       header=0)
    df = df[df["FIPS"].notna() & df["FIPS"].str.strip().str.isdigit()].copy()
    df["fips"] = df["FIPS"].str.strip().str.zfill(5)
    for col in ("AGTP79R", "AGTP86"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df[["fips", "AGTP79R", "AGTP86"]].rename(
        columns={"AGTP79R": "farm_dep_1979", "AGTP86": "farm_dep_1986"})


if __name__ == "__main__":
    t = load_typology()
    print(f"counties classified: {len(t):,}")
    print(t["farm_dep_1979"].value_counts().rename(LABELS).to_string())
