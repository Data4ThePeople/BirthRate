# County fertility in the United States, 1982–2024

A complete county-level panel of US fertility, built to test whether the metro/nonmetro
divergence visible in other domains also shows up in birth rates.

## Headline findings

| | |
|---|---|
| National fertility rate (births per 1,000 women 15–44) | **67.3 → 53.5** |
| Rural premium over metro, 1982 | **+8.2** |
| Rural premium, 1994 (the low point) | **−3.7** |
| Rural premium, 2024 | **+6.6** |
| Share of the net decline occurring after 2007 | **~96%** |
| Share of the decline explained by migration between metro and nonmetro | **≈3%** |

1. **The rural–urban gradient ran in both directions.** In 1982 rural counties had far
   *higher* fertility than large metros (+8.2 births per 1,000 women). That premium
   collapsed through the 1980s, crossed below zero in 1987, bottomed in 1994, and has
   climbed back to +6.6 since. It is a U, not a trend — and a panel starting in 1991
   starts at the bottom of it, which makes the shape look like a simple reversal.
2. **Each era is a clean monotonic gradient, and they mirror each other.** 1982–94:
   large metro +4.4%, remote rural −22.3%, ordered all the way down. 1994–2024: large
   metro −23.2%, remote rural +4.0%, ordered exactly the other way.
3. **The level and the geography move on different clocks.** The national rate had no
   trend for twenty-five years (67 in 1982, 71 in 1990, 64 in 1998, 69 in 2007) and then
   fell off a cliff. The gap was never still. Neither turning point lines up.
4. **It is not people moving.** Women 15–44 did shift toward metro areas, but a
   shift-share decomposition puts ~97% of the national decline in *within-group* rate
   change and ~3% in composition.

The divergence survives age standardisation, so it is not an artefact of the female age
structure of different places.

## The data problem, and the way around it

NCHS strips geography from public natality microdata after 2004, and CDC WONDER identifies
only counties of 100,000+, pooling the rest into an unnamed per-state remainder. Two
sources cover the gap from either side.

| Years | Source | Coverage |
|---|---|---|
| 1982–1988 | NCHS natality microdata via NBER | every county; national totals exact |
| 1989–1990 | same, plus state-constrained allocation | 414 named counties exact; state totals exact |
| 1991–1999 | Census PEP `99c8_XX.txt` (CO-99-8) | every county |
| 2001–2009 | `co-est2009-alldata.csv` | every county |
| 2011–2020 | `co-est2020-alldata.csv` | every county |
| 2021–2024 | `co-est2024-alldata.csv` | every county |
| Denominators | SEER county population by age/sex/race, 1969–2024 | |
| Rate schedule | NCHS `yt7u-eiyg` + DQS `daba-4vfq` | |
| Classification | USDA ERS Rural–Urban Continuum Codes | 1993 / 2003 / 2013 / 2023 |

## Splicing two sources

The eras are on different time bases: microdata counts calendar years, PEP counts
July–June estimate years. Measured on 1995, 1998 and 2001 — the only years where both
sources name the same 457 large counties — the median county-level ratio is within about
1%, and its **sign tracks the direction of the national trend in each year**, which is
the signature of a half-year offset rather than a difference in what is counted. The
1990/1991 splice produces a smaller step than the largest ordinary year-to-year step
nearby; `tests/validate.py` asserts this.

## Known properties of the panel

- **1982–1990 reproduces published NCHS national totals exactly**, once the pre-1985
  record weight (a 50% sample in some states) and the foreign-resident filter are applied.
- **1989–1990 small counties are modelled.** Public files name only counties of 100,000+,
  but state totals are complete, so each state's residual is spread over its smaller
  counties on a share basis from 1988 and 1991. State and national totals are exact; only
  the split among small counties is estimated (~28% of births in those two years).
  Flagged in `births_allocated`.
- **2000 and 2010 are interpolated** — every PEP vintage stubs its launch year, so no
  published county file covers those two estimate years. Flagged in `births_interpolated`.
- **3,098 analysis units, stable across all 43 years.** Alaska, Connecticut and Hawaii are
  held as single statewide units, Broomfield is merged with the four Colorado counties it
  was carved from, and Dade/Miami-Dade, Bedford, Halifax and Yellowstone are reconciled
  across their renames. Alaska is excluded from the metro/nonmetro series.
- **36 flagged source anomalies** (0.03% of rows), Katrina among them. Flagged, never
  silently smoothed.

## Layout

```
src/birthrate/
  fetch.py          download every raw source (idempotent, ~1 GB)
  sources/nber.py   1982-1990 microdata; dictionary-driven fixed-width parse
  sources/pep.py    1991-2024 births; blocked 1990s format, stub years dropped
  sources/seer.py   denominators; single streaming pass
  sources/asfr.py   national age-specific rates
  sources/rucc.py   rural-urban codes, all vintages
  geography.py      FIPS -> stable analysis unit
  metrics.py        GFR, expected births, comparative fertility ratio
  panel.py          assembles data/processed/county_year_fertility.parquet
  analysis.py       metro/nonmetro series and the shift-share decomposition
viz/                projection, payload build, page build
tests/validate.py   18 end-to-end checks
```

## Running it

```bash
.venv/bin/pip install pandas pyarrow requests numpy xlrd openpyxl
.venv/bin/python src/birthrate/fetch.py
PYTHONPATH=src .venv/bin/python src/birthrate/panel.py
PYTHONPATH=src .venv/bin/python tests/validate.py
PYTHONPATH=src .venv/bin/python viz/build_data.py && .venv/bin/python viz/build_page.py
```

## What this does not answer

Age standardisation removes the effect of local female age structure. It does not remove
differences in *who* lives where — education, income, nativity, marital status. Mother's
age is available in the 1982–1988 microdata (`b15_19` … `b40_44` in `sources/nber.py`) but
not for the PEP era, so county age-specific rates are not comparable across the period.
