"""Births by county-year from Census Population Estimates components of change.

PEP "estimate years" run July 1 - June 30, not calendar years. Each vintage's
launch year is a partial Apr 1 - Jun 30 stub (roughly a quarter of a year's
births) and is dropped. Because every vintage stubs its own launch year, the
decade-boundary years 2000 and 2010 are unavailable from any published county
file and are interpolated downstream; 2020 is recovered from vintage 2020.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "pep"

# Vintage -> (filename, first full estimate year, last estimate year).
# The launch-year stub (vintage base year) is excluded by construction.
CSV_VINTAGES = [
    ("co-est2009-alldata.csv", 2001, 2009),
    ("co-est2020-alldata.csv", 2011, 2020),  # supersedes vintage 2019
    ("co-est2024-alldata.csv", 2021, 2024),
]

_ROW_1990S = re.compile(
    r"^4\s+(?P<fips>\d{5})\s+(?P<nums>[\d,\s-]+?)\s+(?P<name>[A-Za-z].*?)\s*$"
)


def _read_1990s_state(path: Path) -> pd.DataFrame:
    """Parse Block 4 (Births) of a CO-99-8 per-state annual time series file.

    Block 4 rows are: marker, 5-digit FIPS, a 1990-99 total, then ten period
    values ordered NEWEST FIRST (1999 ... 1991, then the Apr-Jun 1990 stub),
    then the county name.
    """
    lines = path.read_text(encoding="latin-1").splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith("Block 4:"))
        end = next(i for i, ln in enumerate(lines) if ln.startswith("Block 5:"))
    except StopIteration as exc:  # pragma: no cover - malformed source file
        raise ValueError(f"{path.name}: Block 4/5 markers not found") from exc

    records = []
    for line in lines[start:end]:
        m = _ROW_1990S.match(line)
        if not m:
            continue
        nums = [int(v.replace(",", "")) for v in m["nums"].split()]
        if len(nums) != 11:
            raise ValueError(f"{path.name}: expected 11 values, got {len(nums)}: {line!r}")
        total, values = nums[0], nums[1:]
        if abs(sum(values) - total) > 1:
            raise ValueError(
                f"{path.name} {m['fips']}: components {sum(values)} != stated total {total}"
            )
        # values[0] is 1999 ... values[8] is 1991; values[9] is the 1990 stub.
        for offset, births in enumerate(values[:9]):
            records.append((m["fips"], 1999 - offset, births))

    if not records:
        raise ValueError(f"{path.name}: no Block 4 county rows parsed")
    return pd.DataFrame(records, columns=["fips", "year", "births"])


def load_1990s() -> pd.DataFrame:
    paths = sorted(RAW.glob("99c8_*.txt"))
    if not paths:
        raise FileNotFoundError(f"no 99c8_*.txt in {RAW}; run fetch.py")
    frames = [_read_1990s_state(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    # Per-state files repeat the state-level row (FIPS ending 000); drop it.
    return df[~df["fips"].str.endswith("000")].reset_index(drop=True)


def _read_csv_vintage(filename: str, first: int, last: int) -> pd.DataFrame:
    df = pd.read_csv(RAW / filename, encoding="latin-1", dtype=str)
    df = df[df["SUMLEV"] == "050"].copy()
    df["fips"] = df["STATE"].str.zfill(2) + df["COUNTY"].str.zfill(3)

    out = []
    for year in range(first, last + 1):
        col = next(
            (c for c in df.columns if c.replace("_", "") == f"BIRTHS{year}"), None
        )
        if col is None:
            raise KeyError(f"{filename}: no births column for {year}")
        out.append(
            pd.DataFrame(
                {"fips": df["fips"], "year": year, "births": df[col].astype(int)}
            )
        )
    return pd.concat(out, ignore_index=True)


def load_births() -> pd.DataFrame:
    """Return county-year births, 1991-2024, with 2000 and 2010 absent."""
    frames = [load_1990s()]
    frames += [_read_csv_vintage(*v) for v in CSV_VINTAGES]
    df = pd.concat(frames, ignore_index=True)

    dupes = df.duplicated(subset=["fips", "year"]).sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate county-year rows in PEP births")
    return df.sort_values(["fips", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    b = load_births()
    print(b.groupby("year")["births"].agg(["sum", "count"]).to_string())
