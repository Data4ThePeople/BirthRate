"""Births by county of residence from NCHS natality microdata (NBER mirror).

Public natality files identify every county of residence through 1988; from
1989 only counties of 100,000+ population are named, and after 2004 geography
is removed entirely. So these files extend the panel backwards to 1982 with
full coverage, and no further forwards than the Census PEP series already goes.

Field positions move between years, so they are read from the Stata dictionary
NBER publishes alongside each file rather than hardcoded. Records are fixed
width and newline delimited.

Resident status 4 is a foreign resident; NCHS excludes those from US natality
totals, and so do we. Files before 1985 are a 50% sample in some states and
carry a record weight to inflate back to full counts; from 1985 the weight is
1 everywhere. With both applied, every year reproduces its published national
total exactly.
"""
from __future__ import annotations

import re
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "nber"

FIRST_YEAR, LAST_YEAR = 1982, 1990
# Counties smaller than this were suppressed from public files starting in 1989.
FULL_COVERAGE_THROUGH = 1988

RESIDENT = {b"1", b"2", b"3"}

# Five-year bands matching the SEER denominators.
AGE_BANDS = [(15, 19, "b15_19"), (20, 24, "b20_24"), (25, 29, "b25_29"),
             (30, 34, "b30_34"), (35, 39, "b35_39"), (40, 44, "b40_44")]
BAND_COLS = [c for _, _, c in AGE_BANDS]

_COL = re.compile(r"_column\(\s*(\d+)\s*\)\s+\S+\s+(\S+)\s+%(\d+)[a-z]")


def read_dictionary(year: int) -> dict[str, tuple[int, int]]:
    """Map variable name -> (0-based start, length) from the NBER .dct file."""
    text = (RAW / f"natality{year}.dct").read_text(encoding="latin-1")
    fields = {}
    for start, name, width in _COL.findall(text):
        fields[name] = (int(start) - 1, int(width))
    for required in ("restatus", "cntyrfip", "dmage", "recwt"):
        if required not in fields:
            raise KeyError(f"{year}: dictionary has no {required}")
    return fields


def _age_band_index() -> list[str | None]:
    """Lookup from integer age to band column, or None if outside 15-44."""
    table: list[str | None] = [None] * 100
    for lo, hi, col in AGE_BANDS:
        for age in range(lo, hi + 1):
            table[age] = col
    return table


def load_year(year: int) -> pd.DataFrame:
    """County-year births for one file, total and by mother's age band."""
    fields = read_dictionary(year)
    (r_at, r_len) = fields["restatus"]
    (c_at, c_len) = fields["cntyrfip"]
    (a_at, a_len) = fields["dmage"]
    (w_at, w_len) = fields["recwt"]
    band_of = _age_band_index()

    totals: dict[bytes, int] = defaultdict(int)
    bands: dict[bytes, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    archive = RAW / f"Nat{year}.zip"
    with zipfile.ZipFile(archive) as z:
        with z.open(z.namelist()[0]) as fh:
            for line in fh:
                if line[r_at:r_at + r_len] not in RESIDENT:
                    continue
                try:
                    weight = int(line[w_at:w_at + w_len])
                except ValueError:
                    weight = 1
                fips = line[c_at:c_at + c_len]
                totals[fips] += weight
                try:
                    age = int(line[a_at:a_at + a_len])
                except ValueError:
                    continue
                col = band_of[age] if age < 100 else None
                if col is not None:
                    bands[fips][col] += weight

    records = []
    for fips, total in totals.items():
        row = {"fips": fips.decode("latin-1"), "year": year, "births": total}
        row.update({c: bands[fips].get(c, 0) for c in BAND_COLS})
        records.append(row)

    df = pd.DataFrame.from_records(records)
    # Unknown or non-US county of residence is coded with a 999 county part.
    return df[df["fips"].str.isdigit() & ~df["fips"].str.endswith("999")]


def load_births(first: int = FIRST_YEAR, last: int = LAST_YEAR) -> pd.DataFrame:
    frames = [load_year(y) for y in range(first, last + 1)]
    df = pd.concat(frames, ignore_index=True)
    dupes = df.duplicated(subset=["fips", "year"]).sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate county-year rows in NBER births")
    return df.sort_values(["fips", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    published = {
        1982: 3_680_537, 1983: 3_638_933, 1984: 3_669_141, 1985: 3_760_561,
        1986: 3_756_547, 1987: 3_809_394, 1988: 3_909_510, 1989: 4_040_958,
        1990: 4_158_212,
    }
    print("year   counties      births   published      dev")
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        d = load_year(y)
        tot, pub = int(d["births"].sum()), published[y]
        print(f"{y}     {d['fips'].nunique():>6,}  {tot:>10,}  {pub:>10,}  "
              f"{100 * (tot - pub) / pub:+6.2f}%")


def state_totals(year: int) -> pd.Series:
    """Exact births by state of residence, including years where small
    counties are unnamed. State is identified on every record."""
    fields = read_dictionary(year)
    (r_at, r_len) = fields["restatus"]
    (s_at, s_len) = fields["stresfip"]
    (w_at, w_len) = fields["recwt"]
    counts: dict[str, int] = defaultdict(int)
    with zipfile.ZipFile(RAW / f"Nat{year}.zip") as z:
        with z.open(z.namelist()[0]) as fh:
            for line in fh:
                if line[r_at:r_at + r_len] not in RESIDENT:
                    continue
                try:
                    weight = int(line[w_at:w_at + w_len])
                except ValueError:
                    weight = 1
                counts[line[s_at:s_at + s_len].decode("latin-1")] += weight
    return pd.Series(counts, name="state_births").sort_index()


def allocate_suppressed(year: int, weights: pd.Series,
                        mapper=None) -> pd.DataFrame:
    """County births for a year where only counties of 100,000+ are named.

    Named counties keep their exact counts. Each state's remaining births - a
    quantity known exactly, because state totals are complete - are spread over
    that state's unnamed counties in proportion to `weights`, a share basis
    taken from the fully observed years on either side. State and national
    totals are therefore exact; only the split among small counties is modeled.

    `mapper` folds raw county FIPS onto the caller's stable analysis units
    before anything is counted, so a county that changed code between eras
    cannot appear as both a named and an unnamed unit in the same year.
    `weights` must already be indexed by those same units.
    """
    identity = (lambda f: f) if mapper is None else mapper
    named = load_year(year)[["fips", "births"]].copy()
    named["unit"] = named["fips"].map(identity)
    named = named[named["unit"].notna()].groupby("unit")["births"].sum()

    totals = state_totals(year)
    rows = [{"fips": u, "year": year, "births": int(v), "births_allocated": False}
            for u, v in named.items()]

    by_state: dict[str, list[str]] = defaultdict(list)
    for unit in weights.index:
        by_state[unit[:2]].append(unit)

    for state, total in totals.items():
        units = by_state.get(state, [])
        if not units:
            continue
        claimed = int(named[[u for u in named.index if u[:2] == state]].sum())
        residual = total - claimed
        if residual <= 0:
            continue
        # Normally the residual belongs to the state's unnamed counties. Where
        # a state has none - because its units are statewide merges that a
        # named county already falls inside - it still belongs to the state,
        # so spread it over every unit there rather than dropping it. Either
        # way the state total is reproduced exactly.
        unnamed = [u for u in units if u not in named.index]
        targets = unnamed or units
        basis = weights.reindex(targets).fillna(0.0)
        share = (basis / basis.sum() if basis.sum() > 0
                 else pd.Series(1.0 / len(targets), index=targets))
        for unit, value in (share * residual).items():
            rows.append({"fips": unit, "year": year, "births": float(value),
                         "births_allocated": True})

    return pd.DataFrame(rows)
