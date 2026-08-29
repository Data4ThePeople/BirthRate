"""USDA ERS Rural-Urban Continuum Codes, all published vintages.

RUCC is a 1-9 scale: 1-3 are metropolitan counties (by metro area size),
4-9 are nonmetropolitan (by urban population and metro adjacency). The 2003
release carries the 1993 codes alongside its own, so four vintages cover the
1991-2024 panel: 1993, 2003, 2013, 2023.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "rucc"

# Analysis classes collapsing the 1-9 scale. Ordered rural-ward.
RUCC_CLASS = {
    1: "Large metro (1M+)",
    2: "Metro 250K-1M",
    3: "Small metro (<250K)",
    4: "Micropolitan, adjacent",
    5: "Micropolitan, remote",
    6: "Small town, adjacent",
    7: "Small town, remote",
    8: "Rural, adjacent",
    9: "Rural, remote",
}
CLASS_ORDER = [RUCC_CLASS[i] for i in range(1, 10)]

VINTAGES = ["rucc_1993", "rucc_2003", "rucc_2013", "rucc_2023"]

# A merged unit whose population straddles the metro/nonmetro line cannot be
# given one honest code; these are dropped from the metro/nonmetro series.
MIXED_METRO_BAND = (0.10, 0.90)


def load_rucc() -> pd.DataFrame:
    """Source-FIPS level table of RUCC codes for every vintage."""
    v2003 = pd.read_excel(RAW / "ruralurbancodes2003.xls", dtype=str)
    v2003 = v2003.rename(
        columns={
            "FIPS Code": "fips",
            "1993 Rural-urban Continuum Code": "rucc_1993",
            "2003 Rural-urban Continuum Code": "rucc_2003",
            "2000 Population ": "pop_2000",
        }
    )[["fips", "rucc_1993", "rucc_2003", "pop_2000"]]

    v2013 = pd.read_excel(RAW / "ruralurbancodes2013.xls", dtype=str)
    v2013 = v2013.rename(columns={"FIPS": "fips", "RUCC_2013": "rucc_2013", "Population_2010": "pop_2010"})[
        ["fips", "rucc_2013", "pop_2010"]
    ]

    long23 = pd.read_csv(RAW / "rucc2023.csv", dtype=str, encoding="latin-1")
    v2023 = long23.pivot(index="FIPS", columns="Attribute", values="Value").reset_index()
    v2023 = v2023.rename(
        columns={"FIPS": "fips", "RUCC_2023": "rucc_2023", "Population_2020": "pop_2020"}
    )[["fips", "rucc_2023", "pop_2020"]]

    df = v2013.merge(v2003, on="fips", how="outer").merge(v2023, on="fips", how="outer")
    for col in VINTAGES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # The 1993 release used a 0-9 scale that split metro areas of 1M+ into
    # central (0) and fringe (1) counties; later releases merged them into 1.
    df["rucc_1993"] = df["rucc_1993"].replace(0, 1)
    for col in ["pop_2000", "pop_2010", "pop_2020"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def unit_rucc() -> pd.DataFrame:
    """RUCC per stable analysis unit.

    A merged unit takes the code of its most populous member. `rucc_dominance`
    records that member's share of unit population, so units that mix
    settlement types can be identified and excluded.
    """
    from birthrate.geography import to_unit

    df = load_rucc()
    df["unit"] = df["fips"].map(to_unit)
    df = df[df["unit"].notna()].copy()
    df["weight"] = df[["pop_2020", "pop_2010", "pop_2000"]].max(axis=1)

    df = df.sort_values("weight", ascending=False)
    out = df.groupby("unit", as_index=False).first()[["unit", *VINTAGES]]

    # Population-weighted metro share per vintage. For single-county units this
    # is 0 or 1; for merged units it measures how cleanly the unit sits on one
    # side of the metro/nonmetro line.
    totals = df.groupby("unit")["weight"].sum()
    for vintage in VINTAGES:
        metro_w = df[df[vintage].between(1, 3)].groupby("unit")["weight"].sum()
        share = (metro_w / totals).fillna(0.0)
        out[f"metro_share_{vintage[-4:]}"] = out["unit"].map(share).round(4)

    out = out.rename(columns={"unit": "fips"})
    for col in VINTAGES:
        out[col] = out[col].astype("Int64")
    return out


if __name__ == "__main__":
    import sys

    sys.path.insert(0, "src")
    u = unit_rucc()
    print(f"units with RUCC: {len(u)}")
    print(u["rucc_2013"].value_counts().sort_index().to_string())
    print("\nmerged units and their assigned code:")
    from birthrate.geography import UNIT_LABELS

    print(u[u.fips.isin(UNIT_LABELS)].to_string(index=False))
    lo, hi = MIXED_METRO_BAND
    mixed = u[u["metro_share_2013"].between(lo, hi, inclusive="neither")]
    print(f"\nunits straddling the metro line ({lo}-{hi}): {len(mixed)}")
    print(mixed.to_string(index=False))
