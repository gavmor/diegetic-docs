# Vintage typewriter emulation

Courier Prime is a clean digital monospace: every `e` is the identical
vector. A real manual typewriter never strikes the same letter twice —
fabric ribbon, finger pressure, and wearing typebars see to that. This
skill emulates the physical causes, not just the silhouette.

## The font: TT2020 Style B

**TT2020 Style B** (Fredrick R. Brennan, OFL-1.1, fetched + verified by
`bin/fetch_fonts.py`) is a scanned typewriter face carrying 3–5
alternate glyphs per character behind the OpenType `calt` (contextual
alternates) feature. Verified 2026-10-04: WeasyPrint/Pango applies `calt`
by default — a run of 24 `e`s renders measurably varied glyphs, and
`font-feature-settings: "calt" 0` collapses them back to one shape.

```css
@font-face { font-family: "TT2020";
             src: url("assets/fonts/tt2020-styleb-regular.ttf"); }
@font-face { font-family: "TT2020";
             src: url("assets/fonts/tt2020-styleb-italic.ttf");
             font-style: italic; }
body { font-family: "TT2020", "Courier Prime", monospace; }
/* force alternates on/off explicitly if ever needed: */
.alt-off { font-feature-settings: "calt" 0; }
```

`font-feature-settings` is accepted by WeasyPrint and passed to Pango —
proven, not assumed.

## Bold is overstrike

TT2020 ships **no bold weight**, and WeasyPrint neither synthesizes faux
bold nor implements `text-shadow`, so there is no CSS-only bold. That is
period-accurate: a typewriter had no bold key. Emphasis was ALL CAPS,
underlining — or **overstrike**: hitting the same key twice, the carriage
unmoved. `bin/typewriter.py --overstrike` does exactly this for
`<strong>`/`<b>`: every glyph is emitted twice, the second copy overlaid
at `margin-left: -1ch` with a micro-rotation and reduced opacity. The
result reads as bold with a tell-tale double-hit roughness.

## The injector: bin/typewriter.py

The manual Photoshop route (nudging individual letters) becomes a
seeded build step:

```bash
bin/typewriter.py --seed 7 --rate 0.18 --overstrike order.html -o order-typed.html
```

Per wrapped character, independently rolled:

- **baseline shift** — `position: relative; top: ±0.4–1.2pt`
  (bent typebar)
- **tracking jitter** — `margin-left: ±0.2–0.7pt`
  (slipping carriage gear)
- **rotation** — `transform: rotate(±0.3–0.8deg)` on `inline-block`
  (typebar striking at an angle)
- **opacity** — `0.72–0.95`
  (light finger strike / dry ribbon patch)

Rules that keep it honest:

- Only a **fraction** (`--rate`, default 0.18) of characters is wrapped.
  Wrapping everything would shred line-breaking and the `calt` context
  chain; sprinkling reads as wear, not noise.
- Whitespace is never wrapped. `script`/`style`/`pre`/`textarea` are
  skipped. Spans are marked `data-tw`, so re-runs don't double-wrap.
- Same `--seed` → byte-identical output. Deterministic like the plates.

## Out of scope (deliberately)

- **Ribbon weave via displacement map.** The Photoshop technique (blur →
  fabric displacement → threshold) is a raster operation; this pipeline
  emits vector-text PDFs. The plate grain (`make_plate.py`) carries the
  paper tooth, and TT2020's glyphs are scans with their own ink texture.
  Rasterizing the page to fake ribbon weave would destroy selectable
  text for negligible gain.
- **Full-width jitter.** Real carriages advance a fixed step; don't
  "kern" the text with proportional spacing. The injector only nudges.

## QA

- **Rasterize and look** (`pdftoppm -png -r 90`) — the defects are
  sub-point; `pdftotext` won't show them.
- `pdftotext` **will** fragment badly on typed documents (every wrapped
  character is a span boundary). Expected; search PDFs tolerantly.
- Watch wrapped characters at line ends in QA anyway: the `nowrap` word
  guard keeps breaks between words, but verify visually (`pdftoppm -png
  -r 90`) — the defects are sub-point and `pdftotext` won't show them.
