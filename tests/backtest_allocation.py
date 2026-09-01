"""How accurate is the 1989-90 small-county allocation?

Those two years name only counties of 100,000+, so the rest are recovered from
exact state totals on a share basis from 1988 and 1991. 1986 is the year that
can answer whether that works: every county is named, so the method can be run
against a truth it never sees.

The test reproduces the real procedure exactly - same suppression set (whichever
units 1989 leaves unnamed), same state constraint, same neighboring-year share
basis - and compares the result with the counts actually recorded.

Run: PYTHONPATH=src .venv/bin/python tests/backtest_allocation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from birthrate.geography import harmonize, to_unit  # noqa: E402
from birthrate.sources import nber  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
TARGET = 1986                      # the year to reconstruct
BASIS = (1985, 1987)               # its neighbors, as 1989-90 use 1988 and 1991
SUPPRESSION_YEAR = 1989            # whose unnamed set defines "small"
MIN_BIRTHS = 10                    # below this a percentage error is meaningless

SIZE_BANDS = [(10, 50, "10-50"), (50, 100, "50-100"), (100, 250, "100-250"),
              (250, 500, "250-500"), (500, 1000, "500-1,000"),
              (1000, 10**9, "1,000+")]


def _units(year: int) -> pd.Series:
    df = nber.load_year(year)[["fips", "year", "births"]]
    return harmonize(df, ["births"]).set_index("fips")["births"]


def backtest() -> dict:
    truth = _units(TARGET)
    basis = pd.concat([_units(BASIS[0]), _units(BASIS[1])], axis=1).mean(axis=1).dropna()
    named = set(nber.load_year(SUPPRESSION_YEAR)["fips"].map(to_unit).dropna())

    estimate: dict[str, float] = {}
    for state, total in nber.state_totals(TARGET).items():
        here = [u for u in truth.index if u[:2] == state]
        unnamed = [u for u in here if u not in named]
        if not unnamed:
            continue
        residual = total - truth.reindex([u for u in here if u in named]).sum()
        share = basis.reindex(unnamed).fillna(0.0)
        share = (share / share.sum() if share.sum() > 0
                 else pd.Series(1.0 / len(unnamed), index=unnamed))
        estimate.update((share * residual).items())

    cmp = pd.DataFrame({"actual": truth, "est": pd.Series(estimate)}).dropna()
    cmp = cmp[cmp["actual"] >= MIN_BIRTHS]
    cmp["pct"] = 100 * (cmp["est"] / cmp["actual"] - 1)

    bands = []
    for lo, hi, label in SIZE_BANDS:
        sub = cmp[(cmp["actual"] >= lo) & (cmp["actual"] < hi)]
        if len(sub) < 20:
            continue
        bands.append({"band": label, "n": int(len(sub)),
                      "median_abs": round(float(sub["pct"].abs().median()), 1)})

    return {
        "target_year": TARGET, "basis_years": list(BASIS), "counties": int(len(cmp)),
        "median_abs": round(float(cmp["pct"].abs().median()), 2),
        "mean_abs": round(float(cmp["pct"].abs().mean()), 2),
        "p90_abs": round(float(cmp["pct"].abs().quantile(0.90)), 2),
        "mean_signed": round(float(cmp["pct"].mean()), 2),
        "within_5": round(float((cmp["pct"].abs() <= 5).mean() * 100), 1),
        "within_10": round(float((cmp["pct"].abs() <= 10).mean() * 100), 1),
        "bands": bands,
    }


def main() -> None:
    r = backtest()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "_allocation_backtest.json"
    path.write_text(json.dumps(r, indent=1))

    print(f"Reconstructing {r['target_year']} from {r['basis_years']}, "
          f"{r['counties']:,} small counties\n")
    print(f"  median |error|   {r['median_abs']:5.1f}%")
    print(f"  mean |error|     {r['mean_abs']:5.1f}%")
    print(f"  p90  |error|     {r['p90_abs']:5.1f}%")
    print(f"  mean signed      {r['mean_signed']:+5.2f}%   (directional tilt)")
    print(f"  within +/-5%     {r['within_5']:5.1f}% of counties")
    print(f"  within +/-10%    {r['within_10']:5.1f}%\n")
    print(f"  {'births in county':<20}{'counties':>10}{'median |error|':>16}")
    for b in r["bands"]:
        print(f"  {b['band']:<20}{b['n']:>10,}{b['median_abs']:>15.1f}%")
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
