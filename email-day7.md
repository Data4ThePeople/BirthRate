# Day 7 email — Mailchimp

The last send in the series, and the one break from how the rest went out. Days
1 through 6 were sent in full. Day 7 runs 2,275 words with a twelve-year
legislative history in it, and that does not belong in an inbox — so this one
carries the finding, one chart, and the caveat that keeps the finding honest,
and sends people to the page for the rest.

That break is worth naming inside the email. A list trained for a week to get
the whole piece will read a short one as a thinner piece rather than a longer
one, so block 2 says outright that this is the exception and why.

Companion file: `reports/day7-page-meta.md` (the page copy).

Fill one placeholder before sending: `[[POST URL]]`.

---

## Subject line

```
The SNAP rule that lands in November
```

36 characters, so it survives the mobile cut. No number in it on purpose — the
figures in this piece are a modeled ceiling, and a subject line has no room for
the conditional that makes them true. "Lands" does the work: something is
arriving, on a date, whether or not anyone is ready.

Alternates if you want to A/B:

```
Day 7: what happens if the convenience stores go
```
```
One word, twelve years, and 2,871 ZIP codes
```

The first is the plainest statement of the model and reads well to anyone who
followed the week. The second is the most interesting and the most likely to be
misread as a prediction — if you use it, the preheader has to carry "modeled,
not forecast."

## Preview text (preheader)

```
A stocking standard twelve years in the making takes effect November 4. We modeled who it lands on.
```

100 characters. It does not repeat the subject: the subject names the thing, the
preheader says what we did about it. "Modeled" is doing real work here — set it
in Mailchimp's preview-text field, **not** as the first line of body copy.

---

## Layout, block by block

Mailchimp default 600px content width.

### 1 — Kicker

```
The Stores That Stayed · Day 7
```

Same kicker pattern as the rest of the week. Add "· the last chapter" if you
want to signal the series is ending.

### 2 — Why this one is short

One line, above the headline or immediately under it. Without it, a reader who
got six full pieces this week will assume this one is slighter.

```
This last one is long — a rule change, its twelve-year history, and a model of who it lands on. Here is the finding; the rest is on the page.
```

### 3 — Headline

```
Sizing the risk to SNAP of the imminent stocking rule changes
```

### 4 — Deck

```
An epilogue. A stocking standard twelve years in the making, the guidance that still has not arrived, and a map of who would bear the risk if it goes wrong.
```

### 5 — Hero image, linked

| | |
|---|---|
| file | `reports/assets/heroes/day-7-email.jpg` |
| size | 1200×771, 61 KB |
| link | `[[POST URL]]` |

Alt text:

```
Dot map of the lower 48, one dot per ZIP code, with 2,871 marked in pink — the places that would be left with no SNAP retailer if every convenience store gave up its authorization.
```

### 6 — Key figures

Set these as **live text**, not the ledger PNG. Roughly a third of recipients
have images off, and these three lines are the email. Keep the conditional on
the first one; without it the number is a forecast, which it is not.

```
5.3 million — people whose ZIP code would have no SNAP retailer at all if convenience stores drop out
$407 — what USDA estimates it costs a small store to comply in the first year
November 4 — the 2026 date by which every SNAP retailer has to meet the new standard
```

### 7 — Body copy

Four short paragraphs. This is the whole argument; the page carries the proof.

```
On November 4, every store that accepts SNAP has to meet a stocking standard Congress first ordered in 2014. Seven varieties in each of four staple food categories, with a perishable food in three of them — 84 items in all, against the 36 that have been enforced for the last nine years.

The rule was published in May. USDA said guidance for retailers was coming soon. It has not arrived, and USDA's own retailer pages still describe the standard this one replaces. Roughly 118,000 convenience stores are now nine weeks from a compliance review against a standard whose reference material is out of date.

So we modeled the ceiling: what the country looks like if the format most exposed to the rule gives up its SNAP authorization rather than meet it.

2,871 ZIP codes would be left with no SNAP-authorized retailer of any kind — home to 5.3 million people.
```

### 8 — The map

| | |
|---|---|
| file | `reports/post7/images/01-worst-case-map.png` |
| size | 1615×1060 |

Alt text:

```
Dot map of the lower 48. Faint grey marks the 19,074 ZIP codes that would still have a SNAP retailer; pink marks the 2,782 that would have none, scattered across the interior, the Plains and the rural East while cities stay grey.
```

Then this **as live text underneath**, because the chart's own key will not be
legible at phone width:

```
Grey: ZIP codes that keep a SNAP retailer. Pink: ZIP codes that would have none. The cities barely register.
```

### 9 — Who it lands on

**Live text, not the bar chart.** See the notes — that chart does not survive a
600px column. This is the finding it carries:

```
In ZIP codes with fewer than a thousand people, 50% would be left with no SNAP retailer at all. In ZIP codes above twenty-five thousand, 0.1% would.

The median ZIP code left with no SNAP retailer holds 1,051 people. The median one that keeps at least one holds 8,343.
```

### 10 — Button

```
Read the full analysis
```

Point it at `[[POST URL]]`.

### 11 — What is on the page and not in this email

A short list is worth more than a paragraph asking people to click.

```
On the page: the twelve-year history of how a 2014 law became a 2026 rule, why one word held it up for nine years, what USDA does and does not define as a "variety," the guidance that never came, and every figure sourced to the Federal Register, the US Code and USDA's own impact analysis.
```

### 12 — The caveat

**Do not cut this.** It is the difference between analysis and alarmism, and an
email is exactly where a ceiling gets quoted as a prediction.

```
This is not a forecast

USDA's own projection is a net loss of about 500 stores. Our number is a ceiling — what the map looks like if every convenience store gives up its authorization rather than meet the standard. Nobody expects that, including us.

The point of a ceiling is to show how much room sits between the agency's estimate and the edge of the board, and to show who is standing in that room. Even well short of the worst case, the losses land in the same places.
```

### 13 — Footer

```
Source: SNAP Retailer Locator Historical Data, 2005–2025, from USDA's Food and Nutrition Administration (the Food and Nutrition Service until June 2026), and the final rule at 91 FR 25082.

Every figure, the pipeline that builds it, and the verification:
github.com/Data4ThePeople/SNAP_Locations
```

---

## Notes

- **The bar chart will not work in email.** `02-worst-case-bands.png` is 1547px
  wide with ~20px label text. In a 600px column on a 375px phone that text
  renders around 5px. The finding is four numbers; live text carries it better
  than an unreadable image. Same reasoning as the Day 0 cards.
- **The map is a shape, so it survives the downscale** — the pattern reads even
  when the dots go sub-pixel. Its printed key does not, which is why block 8
  restates it as live text. If you want the chart to stand alone, I can generate
  an email-sized version with larger dots and type.
- **Images off** is the failure mode to design against. With images suppressed
  this email should still say: what changes, when, what we modeled, who it lands
  on, and that it is not a forecast. That is why blocks 2, 6, 7, 9 and 12 are
  all live text.
- **The nine weeks in block 7 is tied to an August 29 send.** The post computes it
  from `POLICY["post_date"]` in `src/analysis/post7_policy.py`. If the send slips
  past early September, change it to eight weeks — or just say "this autumn."
- **One claim in this email can go stale overnight.** "Guidance has not arrived"
  was true as of August 27, checked against USDA's own page, which still stamps
  *Page updated: May 08, 2026* at its foot. Worth ten seconds on send morning.
- **Dark hero on a light ground.** `day-7-email.jpg` is drawn on `#181A1B`. Either
  set the content background to match, as with the Day 0 cards, or give it
  padding and accept the contrast.
- **Total image payload is about 400 KB** — the hero at 61 KB plus the map at
  ~345 KB. If that is more than you want, the map is the one to compress; it is
  a dot field and tolerates JPEG at quality 80 without visible loss.
