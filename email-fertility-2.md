# Fertility post 2 email — Mailchimp

A teaser send. The post is long — a history, a test of it against the births,
and a section on how the setup rhymes with today — so the email carries one
chart and one hook, and the hook is the present.

One chart, deliberately. The rural-urban gradient chart is the stronger
evidence, but it needs a sentence of instruction to read and it is not what
people will click for. The commodity chart is: two lines start at the top and
fall off a cliff, and the email's job is to say that some of what caused that
is back.

The tease names the parallels and withholds the differences. Parallels are the
draw; differences are the payoff, and they are on the page.

Fill one placeholder before sending: `[[POST URL]]`.

---

## Subject line

```
Could rural America's 1980s happen again?
```

41 characters, survives the mobile cut. A question rather than a claim: the
post is careful not to forecast, and a question is the honest form of "read
this and decide." "Again" carries the whole promise.

Alternates if you want to A/B:

```
What can 1981 tell us about 2026?
```
```
What broke rural America — and is it back?
```
```
What can the 1980s farm bust prepare us for?
```

The first is the sharpest at 33 characters, but "1981" lands cold on a reader
who does not already know the reference. The second echoes the post's old
title and pairs the history with the present in one breath. The third is
closest to the brief and three characters over the safe line.

## Preview text (preheader)

```
We went looking for what broke rural births in the 1980s. The setup we found is partly back.
```

92 characters. Set it in Mailchimp's preview-text field, **not** as the first
line of body copy. It is the same turn the hook makes in block 8 — went looking
for one thing, found a bigger one — so the reader who opens on it arrives
already primed for that beat. It does not repeat the subject.

Alternates:

```
A boom borrowed against, a lost export market, a rate shock. Three of the four are visible today.
```
```
Rural fertility fell 17% in the 1980s. We traced why, and the parallels reach well past births.
```

The first names the parallels outright and is the most concrete. The second
leads with the number and is the safest if the subject line you pick is
already about the present.

---

## Layout, block by block

Mailchimp default 600px content width.

### 1 — Kicker

```
The American Fertility Decline · Part 2
```

### 2 — Headline

```
The collapse of the fertility rate in rural America in the 1980s
```

### 3 — Deck

```
Rural fertility fell 11.6% in five years while metro America did not move. The collapse tracks commodity exposure — and the setup has echoes today.
```

### 4 — Body copy, part one

```
Yesterday we showed you that rural America already lived through a fertility crisis — a 17% fall from 1982 to 1996 that the national number hid almost completely. Today we go looking for the why.

The 1970s were the best decade American farming had seen since the First World War. Exports climbed from $8 billion to $44 billion. Farmland tripled. Farmers borrowed against it, because that was the obvious move. Then Volcker took rates to 20%, a grain embargo handed the Soviet market to Argentina, the dollar soared, and land fell 40 to 60% from its peak.

Here is what that did to births.
```

### 5 — Hero image, linked

| | |
|---|---|
| file | `posts/images/02-email-hero-1200x772.png` |
| size | 1200×772, 87 KB |
| link | `[[POST URL]]` |

Alt text:

```
Line chart of the fertility rate from 1982 to 2024 for rural counties grouped by what their economy ran on in 1975 to 79, with metro counties for comparison. Mining and farming counties start far above the rest at 83 and 84, fall together through the 1980s, and then separate: mining converges onto all other non-metro counties while farming holds a premium.
```

### 6 — Body copy, part two

Under the image, where the reader has just looked at it.

```
Rural counties that ran on manufacturing, government or retirement fell 8 to 9%. Rural counties that ran on things dug out of the ground or grown on it fell off a cliff: mining 22% in five years, farming 15%. Metro America, 0.2%.

The farm crisis and the oil bust landed on the same kind of place — counties that were heavily reliant on a commodity and had borrowed against the boom.
```

### 7 — Key figures

Live text, not an image. For the third of recipients with images off, this
block is the chart. All four are from the 1970s and 80s: two from the births,
two from the economy that broke them.

```
21.9% — the fall in mining counties' fertility rate, 1982 to 1987. Farming counties: 14.8%. Metro America: 0.2%.
17% — how far rural fertility fell overall, from 1982 to its low in 1996
$35 to $10 — a barrel of oil, 1981 to 1986. Wheat fell by a third over the same five years.
5% to 20% — inflation in December 1976, and where interest rates stood four years later
```

Order is the post's: what happened to births, then the commodity bust that
tracks it, then the rate shock that the hook says is being set up again.

### 8 — The hook

The reason to click. The frame is that we went looking for one thing and found
a bigger one. Name what rhymes; do not say what is different.

```
Here is the part we did not expect.

We started this analysis looking for clues about what could happen to the birth rate. The history took us somewhere broader. The 1980s setup had four parts: a boom borrowed against, an export market lost to a rival, a rate shock, and a commodity bust. Look around. Farmland is up 150% since 2010. China took its soybean business to Brazil. Fuel and fertilizer are up 20 to 40% since the Strait of Hormuz closed. But inflation now is still tame, a couple of points below where it was in 1976. Or is it? And even so, we can still learn a thing or two about nonlinearity from the late 1970s, when 5% inflation in 1976 required 20% interest rates to tame just a few years later.

In short, this is a post about the fertility rate that goes well beyond the fertility rate. Make of it what you will. We are not forecasting anything — just calling attention to the similarities, and to the differences. Both are in today's Data 4 Thought. 📊💭
```

Every figure in this block is in the post with a source. "The differences" is
the promise the page pays off with four of them — leverage, what floats, the
backstop, and the demographic base. Do not list them here; they are why
someone reads to the end.

### 9 — Call to action

Button, centred, linked to `[[POST URL]]`.

```
Read the full analysis
```

Text link beneath, same destination:

```
data4thepeople.com — the collapse of the fertility rate in rural America in the 1980s
```

### 10 — Sign-off

```
We'll be taking Monday off in observance of Labor Day. But brace yourself for Tuesday morning's email, where we will share a new viz that has been in the works for some time — one that will help you really see what's underneath our nation's labor data (which was just updated this morning!).
```

Post 3, "Later, or fewer?", moves to whenever the labor viz has run.

---

## Checks before sending

- `[[POST URL]]` replaced in the hero link and the button
- Preheader in Mailchimp's field, not the body
- Hero on a phone: four lines and a legend at 600px wide; the legend is the
  first thing to go, so confirm it reads
- The figures in blocks 6, 7 and 8 match the post. All are sourced there — ERS,
  Farm Bureau, PBS, Federal Reserve History, and our own panel
