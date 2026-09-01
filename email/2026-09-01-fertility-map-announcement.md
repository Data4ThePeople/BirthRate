# Email: fertility map announcement

**Send:** Tuesday 1 September 2026
**Audience:** Data 4 The People list
**Goal:** drive traffic to the visualization page. No analysis in this one.

---

## Subject line options

1. The other side of aging America
2. A new map: county birth rates, 1982 to 2024
3. We built a map of the American birth rate. Go break it.
4. Every county, every year, since 1982

**Preview text:** *Forty-three years of county fertility data, free and interactive.*

---

## Body

My fascination with demographics started several months back when I put together this visualization showing the divergence in labor force trends in metro and non-metro counties. For those following our work, we keep stumbling upon signs of rising geographic inequality, and we keep worrying that this experiment may not end well. It seems that the path of least resistance is for rural areas to spiral through the cycle of structural decline (the same cycle we sketched back in March, below) while metro areas outgrow already stressed infrastructure and grapple with the localized inflation that follows.

> **[IMAGE: The Cycle of Structural Decline]**
> File: `cycle-of-structural-decline.png` (1400x1400)
> *Alt text: A circular diagram of six reinforcing stages of rural decline - aging population and falling birth rate, labor force declines, industrial exit, decline in city revenue and property taxes, services decline, and working age population leaves - feeding back to the start. A separate arrow shows working-age departure cutting straight to a falling labor force.*

We've written a lot about the aging of America. But so far we have not studied the other side of that coin - the fertility rate.

That changes today.

We've released a new map-based data visualization showing the county-by-county trend in the fertility rate going all the way back to 1982. Click the map below to take it for a spin.

> **[IMAGE: US fertility map, linked to the visualization page]**
> File: `hero-fertility-map-1680x1080.png`
> Link to: `https://www.data4thepeople.com/p/us-fertility-rate-by-county`
> *Alt text: Map of the United States showing the change in fertility rate by county between 1982 and 2024, deep red across the Mountain West and blue clusters in the rural Great Plains.*

The point of today's note is simply to announce that this tool is now freely available to the public at Data 4 The People. So head over there and take it out for a spin. Look up your state. Look up your county. Form your own hypotheses on what's going on.

Thursday and Friday we will dig deep into this new viz and offer you our diagnosis.

---

## Notes before sending

- **Confirm the link.** The visualization page URL above assumes the slug `us-fertility-rate-by-county`. Check it resolves before sending.
- **Make the map image clickable** - it is the only call to action in the email.
- Follow-up posts are promised for **Thursday 3rd and Friday 4th**.
- The map image is 1680x1080 and the cycle diagram 1400x1400. Mailchimp will scale both to the template width; no need to resize.
- The cycle diagram has been redrawn to match the map's typography and palette, so the two images sit together. `viz/build_cycle.py` regenerates it, and there is an SVG alongside the PNG if you ever need to edit the wording.
- The closing is a fourth imperative, keeping the rhythm of the three before it.
- Light edits from your draft: "out work" to "our work", "t experience" removed, "in the public" to "to the public", "post" to "note" since this is going out by email.
- The opening paragraph is split into two sentences, and "localized inflation" gets its own verb - with a shared verb, "outgrow" would have distributed across both objects.
- The old second paragraph is cut; the parenthetical carries the image in and keeps the March callback, so the diagram still reads as something you called earlier rather than something new.
