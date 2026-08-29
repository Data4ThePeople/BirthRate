"""County population denominators from SEER U.S. county population data.

File: us.1969_2024.20ages.adjusted.txt.gz, fixed width, 26 chars per record.

    0:4   year            13     race (1 White, 2 Black, 3 Other)
    4:6   state postal    14     origin (9 = not applicable in this file)
    6:8   state FIPS      15     sex (1 male, 2 female)
    8:11  county FIPS     16:18  age group (00-19)
    11:13 registry        18:26  population

The 20 age groups are <1, 1-4, then five-year bands 5-9 ... 85-89, and 90+.
Childbearing ages 15-44 are therefore codes 04 through 09.
"""
from __future__ import annotations

import gzip
from collections import defaultdict
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "seer"
SOURCE = RAW / "us.1969_2024.20ages.adjusted.txt.gz"

# age code -> label, for the childbearing bands only
FERTILE_AGES = {
    "04": "w15_19", "05": "w20_24", "06": "w25_29",
    "07": "w30_34", "08": "w35_39", "09": "w40_44",
}


def load_denominators(min_year: int = 1990, max_year: int = 2024) -> pd.DataFrame:
    """County-year female population by childbearing band, plus total population."""
    if not SOURCE.exists():
        raise FileNotFoundError(f"{SOURCE} missing; run fetch.py")

    women: dict[tuple[str, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[tuple[str, int], int] = defaultdict(int)

    with gzip.open(SOURCE, "rt", encoding="ascii") as fh:
        for line in fh:
            year = int(line[0:4])
            if year < min_year or year > max_year:
                continue
            pop = int(line[18:26])
            key = (line[6:11], year)
            totals[key] += pop
            if line[15] == "2":
                band = FERTILE_AGES.get(line[16:18])
                if band is not None:
                    women[key][band] += pop

    records = []
    for key, total in totals.items():
        fips, year = key
        row = {"fips": fips, "year": year, "pop_total": total}
        bands = women.get(key, {})
        for label in FERTILE_AGES.values():
            row[label] = bands.get(label, 0)
        records.append(row)

    df = pd.DataFrame.from_records(records)
    df["women_15_44"] = df[list(FERTILE_AGES.values())].sum(axis=1)
    return df.sort_values(["fips", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    d = load_denominators()
    d.to_parquet("data/processed/_seer_denominators.parquet", index=False)
    print(d.head().to_string())
    print("\ncounties per year (sample):")
    print(d.groupby("year")["fips"].nunique().loc[[1990, 2000, 2010, 2020, 2024]].to_string())
    nat = d.groupby("year")[["women_15_44", "pop_total"]].sum()
    print("\nnational totals:")
    print(nat.loc[[1990, 2000, 2010, 2020, 2024]].to_string())
