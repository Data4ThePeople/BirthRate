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
The last time farm country broke
```

32 characters. "Last time" is the whole promise — it says there is a this
time, without claiming what it looks like.

Alternates if you want to A/B:

```
Some of the 1980s setup is back
```
```
What a commodity bust did to births
```

The first is the most direct about the hook and the most likely to be read as a
forecast, which the post is careful not to be. The second matches the hero
headline and is the safest.

## Preview text (preheader)

```
Mining counties lost a fifth of their births in five years. Parts of that setup are back.
```

88 characters. Set it in Mailchimp's preview-text field, **not** as the first
line of body copy. "A fifth" is mining's 21.9%; farming fell 14.8%, so do not
widen it to "mining and farming."

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
Line chart of the fertility rate from 1982 to 2024 for rural counties grouped by what their economy ran on in 1975 to 79, with metro counties for comparison. Mining and farming counties start far above the rest at 83 and 84, fall together through the 1980s, and then separate: mining converges onto other rural counties while farming holds a premium.
```

### 6 — Body copy, part two

Under the image, where the reader has just looked at it.

```
Rural counties that ran on manufacturing, government or retirement fell about as much as the country as a whole. Rural counties that ran on things dug out of the ground or grown on it fell off a cliff. Mining counties fell 22% in five years. Farming, 15%. Metro America, 0.2%.

The farm crisis and the oil bust landed on the same kind of place — counties that lived on one commodity and had borrowed against the boom.
```

### 7 — Key figures

Live text, not an image. For the third of recipients with images off, this
block is the chart.

```
21.9% — the fall in mining counties' fertility rate, 1982 to 1987; farming counties fell 14.8%, metro 0.2%
$12.6 billion to $3.1 billion — US soybean sales to China, 2024 to 2025, after tariffs sent the buyer to Brazil
5% to 20% — inflation in December 1976, and where interest rates stood four years later
```

### 8 — The hook

The reason to click. The frame is that we went looking for one thing and found
a bigger one. Name what rhymes; do not say what is different.

```
Here is the part we did not expect.

We started this analysis looking for clues about what could happen to the birth rate. The history took us somewhere broader. The 1980s setup had four parts: a boom borrowed against, an export market lost to a rival, a rate shock, and a commodity bust. Look around. Farmland is up 150% since 2010. China took its soybean business to Brazil. Fuel and fertilizer are up 20 to 40% since the Strait of Hormuz closed. And inflation is sitting roughly where it sat in 1976 — three years before Volcker, with an Iranian oil shock underway then, too.

Those parallels have implications well beyond the birth rate. Read into that what you will. We are not forecasting anything — just calling attention to the similarities, and to the differences. Both are in today's Data 4 Thought. 📊💭
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
Tomorrow: is the decline real, or are women just having children later? The one question that changes what all of this means.
```

That is post 3, "Later, or fewer?" Adjust if the order changes.

---

## Checks before sending

- `[[POST URL]]` replaced in the hero link and the button
- Preheader in Mailchimp's field, not the body
- Hero on a phone: four lines and a legend at 600px wide; the legend is the
  first thing to go, so confirm it reads
- The figures in blocks 6, 7 and 8 match the post. All are sourced there — ERS,
  Farm Bureau, PBS, Federal Reserve History, and our own panel
