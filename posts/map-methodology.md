# How this map was built

## What it shows

Every county in the United States, every year from 1982 to 2024, coloured by its fertility rate — births per 1,000 women aged 15 to 44.

Two views are available. **Change since 1982** compares each county to its own 1982–84 baseline, so colour means how far that place has moved rather than where it stands; red is decline, blue is increase. **Fertility rate** shows the level instead, on a single scale, so counties can be compared with each other.

Rates are three-year pooled averages — births and women summed across a three-year window centred on the displayed year. Without that, counties with a few dozen births a year swing wildly from random variation alone, and the map flickers rather than showing a trend.

## The problem this had to solve

Public US birth data has a hard geographic floor. NCHS removes all geography from natality microdata after 2004, and CDC WONDER — the standard public interface to vital statistics — identifies only counties with 100,000 people or more, pooling everything smaller into an unnamed remainder for each state.

Built the obvious way, a county fertility map leaves roughly 2,500 of 3,100 counties blank. That is most of rural America, and it makes the map useless for exactly the questions people want to ask of it.

## Two sources, spliced

**1982–1990 — NCHS natality microdata.** Before 1989, the public natality files named the county of residence on every birth record. These are the raw records, one row per birth, read directly. With the pre-1985 record weight applied (some states were a 50% sample before then) and foreign residents excluded as NCHS does, every year reproduces its published national birth total exactly.

**1991–2024 — Census Population Estimates.** The Census Bureau publishes an annual birth count for every county as an input to its population estimates. These come from the same vital records but are not suppressed, because they are being used as an ingredient rather than released as a statistic.

**Denominators — SEER county population.** County population by age and sex, 1969 to 2024, gives the number of women aged 15 to 44 in each county each year.

Where both birth sources overlap — 1995, 1998 and 2001, the years where each names the same 457 large counties — the median county-level difference is about 1%, and its sign tracks the direction of the national trend in each year. That is the signature of the Census series counting July-to-June years rather than calendar years, not a disagreement about what is being counted.

## Geography held constant

Counties change. Broomfield County, Colorado was created in 2001 out of four others; Dade County became Miami-Dade in 1997; Connecticut replaced its counties with planning regions; Alaska reorganises boroughs continually.

A map that ignores this shows boundary changes as fertility changes. So every county is mapped to a **stable analysis unit**, identical in all 43 years — 3,098 of them. Alaska, Connecticut and Hawaii are held as single statewide units, and Broomfield is merged with the four counties it came from, because the sources cannot be reconciled below that level. Renames and city-to-county reversions are folded together. The result is verified: the same set of units appears in every year of the series.

## Where numbers are estimated

Two places, both flagged in the underlying data.

**1989 and 1990.** The public microdata for these two years names only counties of 100,000 or more. State totals are complete, though, so each state's remaining births are distributed across its smaller counties in proportion to what those counties recorded in 1988 and 1991. State and national totals come out exact; only the split among small counties is modelled.

**2000 and 2010.** Every vintage of the Census estimates reports a partial quarter in its launch year, so no published county file covers these two years. Both are linearly interpolated.

A further 36 county-years — 0.03% of the panel — are flagged as isolated anomalies in the source data, Hurricane Katrina in Orleans and St Bernard Parish among them. These are flagged rather than smoothed away, because they are real events.

## What the measure does and does not capture

The general fertility rate divides births by women of childbearing age, so it already accounts for how many women live in a county. It does not account for their **age distribution within** 15 to 44 — a county whose women skew older will post a lower rate even with identical behaviour. For the analysis built on this panel, an age-standardised measure is used alongside it; on the map itself, the unadjusted rate is shown.

It is also a **period** measure. It counts births in a calendar year, which means it cannot distinguish between people having fewer children and people having them later.

## Sources

- US Census Bureau, Population Estimates Program — county components of change, vintages 1999, 2009, 2020 and 2024
- NCHS natality detail files, 1982–1990, via the National Bureau of Economic Research
- National Cancer Institute SEER — US county population data by age, sex and race, 1969–2024
- NCHS via data.cdc.gov — birth rates for females by age group, and DQS birth and fertility rates
- USDA Economic Research Service — Rural–Urban Continuum Codes and county typology codes
- County and state boundaries from TIGER, projected to Albers USA

*Every figure on the map has been tied back to its source: all 51 state series and all 133,214 county-year cells reconcile with the underlying panel, and national totals reconcile with published NCHS figures.*
