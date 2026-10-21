# Magazine design system

A report is a printed object. Think *Monocle*, *The Economist* special reports, *Bloomberg
Businessweek*, *Kinfolk*, McKinsey Quarterly, an annual report from a good studio — not a
SaaS landing page.

**Priority order:** user's `design-references/` > this file > template defaults.

## 1. Page engine (keep from the template)

- A4 portrait sheets: `.page` = 210 × 297 mm, `@page { size: A4; margin: 0 }`, each page
  `break-after: page`. US Letter only if the user asks (change `--page-w/--page-h`).
- Margins via padding on `.page`: inside 18 mm, outside 16 mm, top 16 mm, bottom 20 mm.
  Full-bleed elements use `.bleed` (negative margins back to the sheet edge).
- 12-column grid inside the margins, 5 mm gutter. Body text spans 2 or 3 columns of ~60–70
  characters. Never one full-width text column on A4 — that is the #1 "this is a web page" tell.
- Content must fit its page. There is no auto-flow between pages: when text overflows,
  cut copy, shrink an image, or split into another page. The render self-check catches it.

## 2. Page types — compose an issue from these

| Type | Purpose | Anatomy |
|---|---|---|
| `cover` | One idea, one image | Masthead, issue line (No. / date), 1 cover line large + 2–3 small, full-bleed slot |
| `contents` | Navigation + taste | Numbered list with page numbers, a small image per major story, editor's note |
| `opener` | Start a section | Huge section numeral or kicker, headline 60–96 pt, standfirst, half/full-bleed slot |
| `feature` | Long read | Kicker, headline, standfirst, byline, drop cap, 2–3 column body, pull quote, captioned slot |
| `numbers` | The data page | 3–6 giant stats with one-line labels and sources; or one hero chart |
| `chart` | One argument, one chart | Headline that states the finding, chart, 2-line takeaway, source line |
| `voices` | Quotes / tweets | Grid of 3–6 quotes with name, role/@handle, date; one oversized |
| `essay` | Photo story | 1–3 large slots, minimal text, captions |
| `timeline` | Chronology | Vertical or horizontal rule, dated entries |
| `profile` | Person/company | Portrait slot, Q&A or fact box sidebar |
| `back` | Close | Methodology, sources list, colophon, credits |

Rhythm: alternate dense and open pages. Never two `numbers` pages in a row. Every 3–4 text
pages, a page that is mostly image or one big number.

## 3. Typography

- Pair **one serif display** with **one sans for text/UI** — or one serif for both with a
  mono for data. Load from Google Fonts with `display=swap`; embed nothing proprietary.
  Proven pairings:
  - Fraunces / Newsreader + Inter Tight — warm editorial
  - Playfair Display + Source Sans 3 — classic magazine (watch Playfair's contrast at small sizes)
  - Instrument Serif + Inter — fashion/culture
  - DM Serif Display + DM Sans — modern business
  - Libre Caslon Text + Archivo — serious report
  - Space Grotesk + JetBrains Mono — tech/data issue
- Scale (pt, print): body 9.5–10.5 / leading 1.4–1.5 · standfirst 14–17 · H2 22–30 ·
  headline 40–72 · opener headline 72–110 · stat numerals 60–140 · captions 7.5–8.5 ·
  folios and running heads 7–8, letter-spaced caps.
- Body text: `hyphens: auto; text-align: left` (justified only with hyphenation and
  ≥ 55 characters per line). `orphans: 3; widows: 3`.
- Drop cap on the first paragraph of a feature (`.dropcap`), 3 lines deep.
- Kickers: small caps or 7–8 pt letter-spaced caps in the accent colour.
- Numbers in tables/stats: `font-variant-numeric: tabular-nums lining-nums`.

## 4. Colour

- Paper + ink + one accent (+ optional second accent for charts). Paper is rarely pure
  white: try `#F6F2EA`, `#F4F1EC`, `#EEF0EA`. Ink is rarely pure black: `#141414`, `#1C1B19`.
- Accent from the brand or the cover photo. Use it on kickers, rules, one chart series, the
  drop cap, section numerals — not on body text and not on big background blocks every page.
- Section colour coding is fine (each section gets a tint), but keep it to 3–5 tints.
- Charts: grey for context series, accent for the series the headline is about.

## 5. Images and slots

- Every image is a `figure.slot` with a stable `data-slot` id (kebab-case, page-prefixed:
  `p03-opener`, `p07-portrait`), a `data-ratio` and a `data-hint` describing the ideal
  picture. The id is the filename the user drops into `images/`.
- Crop with `object-fit: cover` and set `object-position` on the `img` for focal point.
- Captions: 7.5–8.5 pt, under or beside the image, credit in a lighter weight.
- Full-bleed images extend to the sheet edge on at least one side — partial bleed
  (one edge) looks more designed than a boxed picture with a border.
- No stock-photo clichés (handshakes, people pointing at screens, glowing brains).
  If no image is available, leave the slot — or design the page so it does not need one
  (big type, a number, a pattern drawn in SVG).

## 6. Data

- Charts are inline SVG drawn by hand (or via a small script) — crisp in PDF, styleable.
  Headline states the finding ("Fintech funding halved in two years"), not the
  topic ("Fintech funding").
- Always a source line: `Source: <org>, <report>, <year>`.
- Big-number modules: number, unit, one-line label, source. Max 6 per page.
- Tables: no vertical rules, hairline horizontal rules, right-aligned numbers.

## 7. Page furniture

- Folio (page number) + running head (issue / section name) on every page except cover and
  full-bleed image pages. Bottom outer corner.
- Thin rules (0.5 pt) to separate kicker/headline zones and columns.
- Pull quotes: 18–26 pt serif italic, accent-coloured opening mark, span 2 columns, attribution
  in caps below.

## 8. Anti-slop checklist (fail any → fix before shipping)

- [ ] No card grids with rounded corners and drop shadows. Print uses rules and white space.
- [ ] No gradients-as-decoration, no glassmorphism, no emoji as icons.
- [ ] No centred body text. No single full-width text column.
- [ ] Headlines are claims written by an editor, not labels ("Overview", "Key Insights").
- [ ] Every number has a source. Every quote has a name and date.
- [ ] Type scale has real contrast (largest ≥ 6× body on at least the cover and openers).
- [ ] Pages differ in structure — not the same header + 3 boxes layout repeated.
- [ ] No overflowing text, no half-empty pages, no heading stranded at a page bottom.
- [ ] Cover would work as a magazine on a newsstand: one image, one big line.

## 9. Working from the user's references

When `design-references/` has files, before designing:

1. Read each image/PDF. For each, note: page type, grid (columns, margins), type
   (serif/sans, size relationships, weights, case, tracking), colour, image treatment
   (bleed, crop, duotone, cut-outs), furniture (folios, rules, kickers), and the one thing
   that makes it distinctive.
2. Write those notes into `brief.md` under "Design system (from references)".
3. Map each reference to the page types in §2 that it should drive — e.g. "ref-03 → opener
   pages", "ref-05 → numbers page".
4. Build the CSS variables (fonts, colours, sizes) from the notes first, then the pages.
5. After rendering, put a preview next to the reference and compare. Iterate on the biggest
   difference first.

If a reference is annotated (arrows, boxes, "image here"), treat each marked area as a slot
and name it after the page and position.
