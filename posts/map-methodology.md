---
title: US Fertility Rate by County, 1982-2024
subtitle: An interactive map of birth rate trends in every American county, and the sources behind it.
slug: us-fertility-rate-by-county
date: 2026-09-01
description: Interactive map of the US fertility rate by county, 1982-2024. Birth rate trends for all 3,098 county units, with the data sources and method behind them.
keywords: fertility rate, birth rate, birth rate trends, US fertility rate by county, fertility rate map, county birth rates, general fertility rate, declining birth rate, NCHS natality, demography
meta_title: US Fertility Rate by County, 1982-2024 | Interactive Map
schema_type: dataset
temporal: 1982/2024
spatial: United States
measured: General fertility rate|births per 1,000 women aged 15-44
dataset_name: US county fertility rates, 1982-2024
dataset_description: Annual general fertility rate for 3,098 stable US county units from 1982 to 2024, built from NCHS natality microdata, Census Population Estimates births and SEER county population by age and sex.
sources: https://www.census.gov/programs-surveys/popest.html | https://www.nber.org/research/data/vital-statistics-natality-birth-data | https://seer.cancer.gov/popdata/
section: Data
---

# US fertility rate by county, 1982-2024

The American **fertility rate** has fallen from 67.3 births per 1,000 women aged 15 to 44 in 1982 to **53.5 in 2024**, its lowest level on record. But that national figure hides the thing worth seeing: the decline is not evenly spread, and for most of those years it was barely happening at all.

This map shows the **birth rate** in every US county, every year from 1982 to 2024. Press play to run the series, switch between the level and the change since 1982, or zoom to a single state.

::: embed 780px

## What the map shows

The measure is the **general fertility rate**: live births per 1,000 women aged 15 to 44 living in the county. It already accounts for how many women of childbearing age live in a place, which is what makes a county of 3,000 people comparable with Los Angeles.

Two views are available. **Change since 1982** compares each county with its own 1982-84 baseline, so colour means how far that place has moved rather than where it stands - red is decline, blue is increase. **Fertility rate** shows the level instead, on one scale, so counties can be compared with each other.

Rates are three-year pooled averages. Without that, a county with forty births a year swings wildly on chance alone and the map flickers rather than showing a trend.

## Three birth rate trends worth knowing

**The decline is recent.** The national rate went essentially nowhere for twenty-five years - 67.3 in 1982, a peak of 70.8 in 1990, a trough of 63.7 in 1998, back to 69.1 by 2007. Roughly **96% of the net fall has come since 2007**.

**Rural and urban America traded places twice.** In 1982 rural counties had a fertility rate 8.2 points *higher* than metropolitan ones. That gap closed, inverted by 1987, bottomed in 1994, and has since reopened the other way to 6.6 points. Anyone treating "rural" and "urban" as fixed positions is describing a snapshot, not a trend.

**The typical county barely moved.** The median county's fertility rate fell about 9%, while the population-weighted national rate fell over 20%, and **27% of counties are higher now than in the early 1980s**. The decline is concentrated in populous places - which is exactly what a national average cannot show you and a map can.

## Frequently asked questions

### What is the current US fertility rate?

In 2024 the general fertility rate was 53.5 births per 1,000 women aged 15 to 44, the lowest in the recorded series. The total fertility rate - the number of children a woman would bear across her lifetime at current rates - was about 1.60, well below the 2.1 needed for a generation to replace itself.

### Is the US birth rate declining?

Yes, but recently rather than steadily. The rate was flat on net from 1982 to 2007 and has fallen roughly 23% since. Framing it as a long slow decline misses that it is a sharp, recent break.

### What is the difference between the birth rate and the fertility rate?

The crude birth rate counts births per 1,000 people, so it moves when a population's age structure changes. The general fertility rate counts births per 1,000 women aged 15 to 44, which removes that distortion and is the measure used here.

### Which counties have the highest and lowest fertility rates?

The highest are concentrated in the rural Great Plains, parts of Utah and Idaho, and counties with large Amish or Hispanic populations. The lowest cluster in Appalachia, northern New England and dense urban cores. The map's level view shows the full distribution.

### Where does the county birth rate data come from?

Births come from NCHS natality microdata for 1982-1990 and Census Population Estimates for 1991-2024; the population denominators come from SEER. The method section below covers how they fit together.

## The problem this map had to solve

Public US birth data has a hard geographic floor. NCHS removes all geography from natality microdata after 2004, and CDC WONDER - the standard public interface to vital statistics - identifies only counties with 100,000 people or more, pooling everything smaller into an unnamed remainder for each state.

Built the obvious way, a county fertility map leaves roughly 2,500 of 3,100 counties blank. That is most of rural America, and it makes the map useless for exactly the questions people want to ask of it.

## Two sources, spliced

**1982-1990 - NCHS natality microdata.** Before 1989 the public natality files named the county of residence on every birth record. These are the raw records, one row per birth. With the pre-1985 record weight applied and foreign residents excluded as NCHS does, every year reproduces its published national birth total exactly.

**1991-2024 - Census Population Estimates.** The Census Bureau publishes an annual birth count for every county as an input to its population estimates. Same vital records, not suppressed, because they are an ingredient rather than a release.

**Denominators - SEER county population.** County population by age and sex, 1969 to 2024, gives the number of women aged 15 to 44 in each county each year.

Where both birth sources overlap - 1995, 1998 and 2001, the years where each names the same 457 large counties - the median county-level difference is about 1%, and its sign tracks the direction of the national trend in each year. That is the signature of the Census series counting July-to-June years rather than calendar years, not a disagreement about what is counted.

## Geography held constant

Counties change. Broomfield County, Colorado was created in 2001 out of four others; Dade County became Miami-Dade in 1997; Connecticut replaced its counties with planning regions; Alaska reorganises boroughs continually.

A map that ignores this shows boundary changes as fertility changes. So every county is mapped to a **stable analysis unit**, identical in all 43 years - 3,098 of them. Alaska, Connecticut and Hawaii are held as single statewide units, and Broomfield is merged with the four counties it came from, because the sources cannot be reconciled below that level. The same set of units appears in every year of the series.

## Where numbers are estimated

Two places, both flagged in the underlying data.

**1989 and 1990.** Public microdata for these years names only counties of 100,000 or more. State totals are complete, so each state's remaining births are distributed across its smaller counties in proportion to what they recorded in 1988 and 1991. State and national totals come out exact; only the split among small counties is modelled.

**2000 and 2010.** Every vintage of the Census estimates reports a partial quarter in its launch year, so no published county file covers these two years. Both are linearly interpolated.

A further 36 county-years - 0.03% of the panel - are flagged as isolated anomalies in the source data, Hurricane Katrina in Orleans and St Bernard Parish among them. These are flagged rather than smoothed away, because they are real events.

## What this measure does not capture

The general fertility rate accounts for how many women of childbearing age live in a county, but not their **age distribution within** 15 to 44 - a county whose women skew older posts a lower rate with identical behaviour.

It is also a **period** measure. It counts births in a calendar year, so it cannot by itself distinguish between people having fewer children and people having them later.

## Sources

- US Census Bureau, Population Estimates Program - county components of change, vintages 1999, 2009, 2020 and 2024
- NCHS natality detail files, 1982-1990, via the National Bureau of Economic Research
- National Cancer Institute SEER - US county population data by age, sex and race, 1969-2024
- NCHS via data.cdc.gov - birth rates for females by age group, and DQS birth and fertility rates
- USDA Economic Research Service - Rural-Urban Continuum Codes and county typology codes

*Every figure has been reconciled with its source: all 51 state series and all 133,214 county-year cells tie back to the underlying panel, and national totals match published NCHS figures.*
