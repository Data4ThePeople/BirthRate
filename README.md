# County fertility in the United States, 1991–2024

A complete county-level panel of the US fertility decline, built to test whether the
metro/nonmetro divergence visible in other domains also shows up in birth rates.

## Headline findings

| | |
|---|---|
| National fertility rate (births per 1,000 women 15–44) | **69.7 → 53.5** (−23%) |
| Large metro counties (1M+) | **−26.9%** |
| Remote rural counties | **−2.8%** |
| Counties where fertility *rose* | **27%** |
| Share of the national decline explained by migration between metro and nonmetro | **≈0%** |

Three things came out of it:

1. **The ranking reversed.** In 1991 metro counties had *higher* fertility than nonmetro
   ones (70.1 vs 67.3). The lines cross around 2005; by 2024 nonmetro leads by 6.6 points.
2. **It is a gradient, not a divide.** Ranked along the USDA rural–urban continuum, the
   decline tracks settlement density almost monotonically, from −26.9% in the largest
   metros to −2.8% in the most remote rural counties.
3. **It is not people moving.** Women aged 15–44 did shift toward metro areas (nonmetro
   held 15.1% of them in 1991, 12.1% in 2024), but a shift-share decomposition puts
   98.6% of the national decline in *within-group* rate change and essentially none in
   composition — because in 1991 the places women moved *to* had the higher birth rates.

The divergence also survives age standardisation, so it is not an artefact of the female
age structure of different places.

## The data problem, and the way around it

NCHS strips all geography from public natality microdata after 2004, and CDC WONDER
identifies only counties of 100,000+ population, pooling the rest into an unnamed
per-state remainder. That leaves most of rural America blank.

The workaround is the **Census Population Estimates Program**, which publishes an annual
birth count for every county as an input to its population estimates. Same vital records,
no suppression.

| Years | Source |
|---|---|
| 1991–1999 | `99c8_XX.txt` — CO-99-8 annual county components of change (blocked fixed-width, per state) |
| 2001–2009 | `co-est2009-alldata.csv` |
| 2011–2020 | `co-est2020-alldata.csv` (supersedes vintage 2019; uniquely supplies estimate-year 2020) |
| 2021–2024 | `co-est2024-alldata.csv` |
| Denominators | SEER `us.1969_2024.20ages.adjusted.txt.gz` — county × year × age × sex × race |
| Rate schedule | NCHS `yt7u-eiyg` (1940–2018) + DQS `daba-4vfq` (2016–2024) |
| Classification | USDA ERS Rural–Urban Continuum Codes, 1993 / 2003 / 2013 / 2023 |

## Known properties of the panel

- **Estimate years, not calendar years.** PEP birth years run July–June. Aligning to a
  July–June blend of NCHS calendar-year totals cuts the median discrepancy from 0.63% to
  0.28%, confirming the offset is the window rather than an error.
- **2000 and 2010 are interpolated.** Every PEP vintage reports a partial Apr–Jun quarter
  in its launch year, so no published county file covers those two estimate years. Both
  are flagged in `births_interpolated`.
- **3,098 analysis units, not 3,143 counties.** Alaska, Connecticut and Hawaii are held as
  single statewide units and Broomfield County is merged with the four Colorado counties it
  was carved from in 2001, because PEP and SEER cannot be reconciled below that level.
  Alaska is excluded from the metro/nonmetro series (`rucc_reliable`).
- **27 flagged source anomalies** (0.03% of rows) — Katrina in Orleans and St Bernard
  Parish, plus a handful of 1990s reporting glitches in small counties. Flagged in
  `births_outlier`, never silently smoothed.

## Layout

```
src/birthrate/
  fetch.py          download every raw source (idempotent)
  sources/pep.py    births; parses the blocked 1990s format and drops stub years
  sources/seer.py   denominators; single streaming pass over the fixed-width file
  sources/asfr.py   national age-specific rates
  sources/rucc.py   rural-urban codes, all vintages, with metro-share for merged units
  geography.py      FIPS -> stable analysis unit
  metrics.py        GFR, expected births, comparative fertility ratio
  panel.py          assembles data/processed/county_year_fertility.parquet
  analysis.py       metro/nonmetro series and the shift-share decomposition
viz/
  project.py        TopoJSON -> Albers USA SVG paths (no JS dependencies)
  build_data.py     compiles the panel + geometry into one JSON payload
  build_page.py     inlines the payload into template.html -> fertility.html
tests/validate.py   14 end-to-end checks
```

## Running it

```bash
.venv/bin/pip install pandas pyarrow requests numpy xlrd openpyxl
.venv/bin/python src/birthrate/fetch.py          # ~90 MB of source files
PYTHONPATH=src .venv/bin/python src/birthrate/panel.py
PYTHONPATH=src .venv/bin/python tests/validate.py
PYTHONPATH=src .venv/bin/python viz/build_data.py && .venv/bin/python viz/build_page.py
```

## What this does not answer

The age-standardised measure removes the effect of local female age structure. It does
not remove differences in *who* lives where — education, income, nativity, marital status.
Those are the next question, not this one.
