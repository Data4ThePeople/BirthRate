"""Download raw source files. Idempotent: skips files already present."""
from __future__ import annotations

import sys
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

PEP = "https://www2.census.gov/programs-surveys/popest"

# State FIPS codes present in the 1990s per-state component files.
STATE_FIPS = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
    "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "44", "45", "46", "47", "48", "49", "50", "51", "53",
    "54", "55", "56",
]

FILES: dict[str, str] = {
    # PEP components of change, 2000s / 2010s / 2020s
    "pep/co-est2009-alldata.csv": f"{PEP}/datasets/2000-2009/counties/totals/co-est2009-alldata.csv",
    "pep/co-est2019-alldata.csv": f"{PEP}/datasets/2010-2019/counties/totals/co-est2019-alldata.csv",
    # Vintage 2020 supersedes vintage 2019 for 2011-2019 and uniquely supplies
    # a full estimate-year 2020 (Jul 2019-Jun 2020), closing the decade-boundary gap.
    "pep/co-est2020-alldata.csv": f"{PEP}/datasets/2010-2020/counties/totals/co-est2020-alldata.csv",
    "pep/co-est2024-alldata.csv": f"{PEP}/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
    # SEER county population by age/sex/race, 1969-2024
    "seer/us.1969_2024.20ages.adjusted.txt.gz":
        "https://seer.cancer.gov/popdata/yr1969_2024.20ages/us.1969_2024.20ages.adjusted.txt.gz",
    # USDA ERS county typology. The 1979 edition classifies county economies on
    # 1975-79 income shares, before the farm and energy busts, so it is not
    # itself a product of the downturn it is used to study.
    "typology/typ1979_1986.xls":
        "https://www.ers.usda.gov/media/6179/1979-and-1986-county-typology-codes-uses-the-1983-nonmetro-definition.xls?v=89217",
    "typology/typ1989.xls":
        "https://www.ers.usda.gov/media/6178/1989-county-typology-codes.xls?v=87292",
    # USDA ERS Rural-Urban Continuum Codes
    "rucc/ruralurbancodes2013.xls":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/ruralurbancodes2013.xls",
    "rucc/ruralurbancodes2003.xls":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/ruralurbancodes2003.xls",
    "rucc/rucc2023.csv":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv",
}

# NCHS natality microdata via NBER. Public files identify every county of
# residence before 1989; from 1989 only counties of 100,000+. Raw fixed-width
# zips are ~15x smaller than the parsed CSVs, so they are what we pull.
NBER_YEARS = range(1982, 1991)
for _y in NBER_YEARS:
    FILES[f"nber/Nat{_y}.zip"] = (
        f"https://data.nber.org/nvss/natality/inputs/raw/{_y}/Nat{_y}.zip"
    )
    FILES[f"nber/natality{_y}.dct"] = (
        f"https://data.nber.org/nvss/natality/programs/dct/natality{_y}.dct"
    )

# 1990s annual county components of change, one file per state (CO-99-8).
for _st in STATE_FIPS:
    FILES[f"pep/99c8_{_st}.txt"] = (
        f"{PEP}/tables/1990-2000/counties/totals/99c8_{_st}.txt"
    )


def fetch(dest: str, url: str, force: bool = False) -> Path:
    path = RAW / dest
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0 and not force:
        return path
    resp = requests.get(url, timeout=180, headers={"User-Agent": "birthrate-research/0.1"})
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return path


def main() -> int:
    failures = []
    for dest, url in FILES.items():
        try:
            path = fetch(dest, url)
            print(f"ok   {dest:52s} {path.stat().st_size:>12,d} bytes")
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append((dest, url, exc))
            print(f"FAIL {dest:52s} {exc}")
    if failures:
        print(f"\n{len(failures)} download(s) failed:")
        for dest, url, exc in failures:
            print(f"  {dest}\n    {url}\n    {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
