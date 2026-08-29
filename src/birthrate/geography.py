"""Harmonize county FIPS codes into analysis units stable over 1991-2024.

Census PEP and SEER disagree about county geography in six states, either
because real boundary events occurred or because the two programs absorbed
them on different schedules. Every discrepancy is enumerated below; each
becomes a merge group whose members collapse to a single stable unit.

Merging is the only option for groups where the split cannot be reversed
without sub-county data (Broomfield, Connecticut's planning regions), and
the conservative option elsewhere. The cost is 5 states losing internal
county detail, together about 1.9% of US births.
"""
from __future__ import annotations

import pandas as pd

# Groups of source FIPS codes that collapse to one analysis unit.
# unit id -> (label, {member codes})
MERGE_GROUPS: dict[str, tuple[str, set[str]]] = {
    # Alaska reorganizes boroughs continually (Valdez-Cordova -> Chugach +
    # Copper River in 2019, Wade Hampton -> Kusilvak in 2015, three
    # 2007-08 splits) and SEER additionally uses pre-1994 aggregates.
    "02000": ("Alaska (statewide)", set()),  # populated by prefix rule
    # Connecticut replaced 8 counties with 9 planning regions as county
    # equivalents. PEP switched in 2021; SEER still reports legacy counties.
    # The two nest only at town level, so hold the state as one unit.
    "09000": ("Connecticut (statewide)", set()),
    # SEER reports Hawaii as a single statewide unit (15900) through 1999.
    "15000": ("Hawaii (statewide)", set()),
    # La Paz County split from Yuma in 1983; SEER kept them combined to 1993.
    "04027": ("Yuma + La Paz, AZ", {"04012", "04027", "04910"}),
    # Broomfield County was created in 2001 from parts of Adams, Boulder,
    # Jefferson and Weld. SEER codes 08911-08914 are those four counties
    # pre-split (including the territory that became Broomfield), so the
    # only stable unit is all five combined.
    "08001": (
        "Adams + Boulder + Broomfield + Jefferson + Weld, CO",
        {"08001", "08013", "08014", "08059", "08123",
         "08911", "08912", "08913", "08914"},
    ),
    # Shannon County renamed Oglala Lakota County in 2015 (46113 -> 46102).
    "46102": ("Oglala Lakota County, SD", {"46113", "46102"}),
    # Bedford City reverted to town status in 2013 and merged into Bedford
    # County; SEER reports the pair as 51917 throughout.
    "51019": ("Bedford County + Bedford City, VA", {"51019", "51515", "51917"}),
    # Clifton Forge City reverted to town status in 2001, joining Alleghany.
    "51005": ("Alleghany County + Clifton Forge City, VA", {"51005", "51560"}),
}

# Whole-state merges, applied by FIPS prefix.
STATE_MERGES = {"02": "02000", "09": "09000", "15": "15000"}

# Records that are not real counties.
DROP_CODES = {"99999"}

_MEMBER_TO_UNIT = {
    code: unit for unit, (_, members) in MERGE_GROUPS.items() for code in members
}
UNIT_LABELS = {unit: label for unit, (label, _) in MERGE_GROUPS.items()}

# Units whose members span very different settlement types, so a single
# rural-urban code would be misleading. Excluded from metro/nonmetro series.
HETEROGENEOUS_UNITS = {"02000"}


def to_unit(fips: str) -> str | None:
    """Map a source county FIPS to its stable analysis unit, or None to drop."""
    if fips in DROP_CODES:
        return None
    state = fips[:2]
    if state in STATE_MERGES:
        return STATE_MERGES[state]
    return _MEMBER_TO_UNIT.get(fips, fips)


def harmonize(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Collapse a county-year frame onto stable analysis units by summing."""
    out = df.copy()
    out["unit"] = out["fips"].map(to_unit)
    out = out[out["unit"].notna()]
    grouped = out.groupby(["unit", "year"], as_index=False)[value_cols].sum()
    return grouped.rename(columns={"unit": "fips"})


if __name__ == "__main__":
    import sys

    sys.path.insert(0, "src")
    from birthrate.sources.pep import load_births

    births = harmonize(load_births(), ["births"])
    seer = pd.read_parquet("data/processed/_seer_denominators.parquet")
    pop_cols = [c for c in seer.columns if c not in ("fips", "year")]
    pop = harmonize(seer, pop_cols)

    b_units = births.groupby("year")["fips"].apply(set)
    p_units = pop.groupby("year")["fips"].apply(set)
    print(f"births units: {births.fips.nunique()}   pop units: {pop.fips.nunique()}")

    ok = True
    for year in sorted(b_units.index):
        diff = b_units[year] ^ p_units[year]
        if diff:
            ok = False
            print(f"  {year}: {len(diff)} mismatched units: {sorted(diff)[:8]}")
    print("unit sets identical across sources for every year:", ok)

    counts = births.groupby("fips")["year"].count()
    print("units missing years in births panel:", (counts != counts.max()).sum())
