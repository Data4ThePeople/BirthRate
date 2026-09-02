# Fertility post 1 email — Mailchimp

A teaser send, not the piece. The post runs about 1,100 words and its argument
is cumulative — three checks that only mean something once you have seen the
chart — so the email carries the setup and the chart, then hands over the
questions the post spends its length answering.

The questions are the whole mechanism here. They are the post's own three
checks, in its order, and each has an answer on the page — so the send promises
nothing it cannot pay off.

Fill one placeholder before sending: `[[POST URL]]`.

---

## Subject line

```
What the national birth rate hides
```

34 characters, survives the mobile cut. No number on purpose — the interesting
figures here only land once you know there are two lines, and a subject line
has no room to set that up. "Hides" carries the promise instead.

Alternates if you want to A/B:

```
Fertility fell in 84% of US counties
```
```
Rural America already had its fertility crisis
```

The first is the plainest and the most likely to get opened on the number. The
second is the most interesting, but it gives away tomorrow's piece — hold it
for that send if you are running the rural post next.

## Preview text (preheader)

```
Split it metro versus nonmetro, go back to 1982, and the simple story stops working.
```

84 characters. Does not repeat the subject: the subject says something is
hidden, the preheader says what to do about it. Set it in Mailchimp's
preview-text field, **not** as the first line of body copy.

---

## Layout, block by block

Mailchimp default 600px content width.

### 1 — Kicker

```
The American Fertility Decline · Part 1
```

Matches the `series` value now carried in the post's schema, so the email, the
page and the structured data all name the series the same way.

### 2 — Headline

```
The fertility decline is real, recent, and everywhere
```

### 3 — Deck

```
Non-metro fertility fell 17% by 1996 while the national rate barely moved. The decline we are in now dates from the financial crisis.
```

### 4 — Body copy, part one

Three short paragraphs. This is the post's opening, cut to the bone.

```
It is probably no surprise that the fertility rate is in structural decline. There has been plenty of coverage of it.

But the point of consulting the data is to fill in the blanks around the simple narrative we get fed. And this one is worth the effort, because people are at the heart of this economy and society. We cannot out-smart needing them.

We keep setting record lows — four of the last five years, and 2024 the lowest since national records began in 1909.
```

### 5 — Hero image, linked

| | |
|---|---|
| file | `posts/images/01-email-hero-1200x772.png` |
| size | 1200×772, 67 KB |
| link | `[[POST URL]]` |

Alt text:

```
Line chart of the US fertility rate from 1982 to 2024, split into metropolitan and non-metropolitan counties. Rural fertility starts far above metro, crosses below it in 1987, recovers through the 2000s, then both fall steeply after 2008.
```

### 6 — Body copy, part two

The turn. One line above the image would be ignored; put it under, where the
reader has already looked at the chart and wants to be told what they saw.

```
That is the same national decline everyone reports, split in two. And split, it stops behaving. Rural America starts far above the cities and crosses below them in 1987. It climbs all the way back by 2009. Then both lines go over a cliff together.
```

### 7 — Key figures

Set as **live text**, not an image. Roughly a third of recipients read with
images off, and for them this block is the chart.

```
17% — how far non-metro fertility fell between 1982 and 1996, while the national rate declined just 5%
2007 — the year metro fertility last turned down; nonmetro followed in 2009
84% — share of American counties where fertility has fallen since 2007
```

### 8 — The open questions

The pivot, and the reason to click. The post's own three checks, in its order,
posed and left hanging.

```
Which leaves the obvious questions.

Is the gap between metro and rural just an age gap?

Is the national decline just women getting older?

Or is it just women moving out of the countryside and into the cities?
```

All three are answered on the page, so this block promises nothing the post
does not deliver. Each one names what it tests — the gap, then the decline,
then the decline again by a different route — because out of context "is it
just that women are getting older?" and "does aging explain the decline?" read
as the same question asked twice. The post's headings now match these.

Note what is deliberately **not** here. The rural collapse is a finding this
post delivers, not a mystery it opens, so it belongs in block 7 as a figure.
Its cause is tomorrow's piece, which the sign-off holds. Asking "why did rural
America collapse?" in this send would promise an answer that is one email away.

### 9 — Call to action

Button, centred, linked to `[[POST URL]]`.

```
Read the full analysis
```

Text link immediately beneath for the images-off readers, same destination:

```
data4thepeople.com — the fertility decline is real, recent, and everywhere
```

### 10 — Sign-off

```
Tomorrow: what actually happened to rural fertility in the 1980s and 1990s, and what it tells us about where this goes next.
```

---

## Checks before sending

- `[[POST URL]]` replaced in both the hero link and the button
- Preheader set in Mailchimp's field, not pasted into the body
- Hero renders at 600px wide on mobile; the axis labels are the first thing to
  go illegible, so check it on a phone rather than in the desktop preview
- The three figures in block 7 match the post. They are checked against the
  panel; if the post's numbers move, these move with them
