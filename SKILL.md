---
name: "diegetic-docs"
description: "Generate diegetic in-world documents — military orders, requisition forms, staff paperwork — and planning charts (Gantt timetables, capacity step-charts) on aged paper with typewriter typography. Use when the user wants an immersive prop document for LARPing or a tabletop game, or asks for a document that looks typed, stamped, and filed."
metadata: { "includeInPrompt": true }
---

# diegetic-docs

Turn source text into documents that look like they were typed at a depot
desk: baked aged-paper plates, real typewriter fonts, rubber stamps, ruled
spec tables, and PIL-drawn planning charts. Proven on an 11-page Warden
requisition order (Form LQ-7, rev. 2) plus a production Gantt and power-plan
chart.

## Styles — shared dependency

The Foxhole look (fonts, plate baker, print CSS patterns, Homebrewery
theme) is canonically owned by **gavmor/foxhole-styles** and vendored
here by `bin/sync-styles.sh` (fonts → `fonts/`, plate baker →
`bin/make_plate.py`, print patterns → `references/foxhole-print.css`).
The vendored copies are committed so the skill works standalone; re-run
the sync after any visual change upstream. Do not edit the vendored
files here — change them in foxhole-styles and re-sync.

## Workflow

1. **Plate** — `bin/make_plate.py --format portrait|landscape --dpi 200 [--pages N]`
   bakes PNGs carrying the whole page background (tone, grain, stains,
   vignette, crease). Supports randomized coffee rings, crescents, drips,
   smudges, angled fold creases, and deterministic per-page seeds for
   multi-page documents. WeasyPrint drops every `@page` background layer but
   one, so there is no other route.
2. **Fonts** — `bin/fetch_fonts.py --out assets/fonts` downloads Courier
   Prime (body) + Special Elite (display) + TT2020 Style B (vintage body:
   scanned glyphs with contextual alternates) and **verifies** each file
   is real font data. A 404 HTML page saved as `.ttf` renders as a silent
   fallback; the script deletes those and fails.
3. **Document** — write the HTML per `references/print-css.md` (masthead,
   routing block with dotted leaders, spec tables, note boxes, stamp,
   margin-box footers). Transcribe the source faithfully; form furniture
   (copy numbers, page numbers, stamps) is fine to add, content is not.
   For live-stamped orders, pull war telemetry first:
   `bin/war_telemetry.py --shard live-1` prints the WAR / WAR ID / DATE /
   WAR START routing lines — see `references/war-telemetry.md`. Dates stay
   diegetic ("Day 27 of the 141st War"); the war number, war ID, and
   in-game day are already in-world.
4. **Charts** — `bin/gantt.py` / `bin/stepchart.py` render JSON-driven
   planning charts (Gantt timetables, capacity step-charts) directly in
   PIL; see `references/charts.md` and the runnable LQ-7 specs in
   `examples/charts/`. Every bar endpoint comes from a stated figure;
   an unstated duration becomes a milestone diamond, never a guessed bar.
5. **Render + QA** — `bin/check.py --html doc.html` (fonts real,
   single-layer `@page` background, all `url()`s resolve), then
   `python3 -m weasyprint doc.html doc.pdf`. **Rasterize and look**
   (`pdftoppm -png -r 60`); never trust `pdftotext` alone at style
   boundaries. For Discord, export PNGs at 150–200dpi.
6. **Vintage type (optional)** — for the full manual-typewriter look,
   set the body in TT2020 (`references/typewriter.md`) and run
   `bin/typewriter.py --seed 7 --rate 0.18 --overstrike doc.html -o
   doc-typed.html` before rendering: seeded per-letter baseline shifts,
   tracking jitter, rotation, opacity, plus double-strike overstrike for
   `<strong>` (TT2020 has no bold; a real typewriter faked it the same
   way). Deterministic; QA the raster for mid-word breaks.

A runnable minimal example is in `examples/minimal-order/`.

## Tooling

- `bin/make_plate.py` — aged-paper plates, portrait/landscape, seeded,
  multi-page (`--pages N`) with randomized coffee stains, crescents, drips,
  smudges, and fold creases.
- `bin/fetch_fonts.py` — fetch + verify Courier Prime / Special Elite /
  TT2020 Style B (OFL license vendored alongside).
- `bin/check.py` — executable gate: font validity, `@page` background
  layering, asset references.
- `bin/war_telemetry.py` — live Foxhole war telemetry for stamped orders
  (war number/ID, in-game day, diegetic war start); see
  `references/war-telemetry.md`.
- `bin/chartkit.py` — shared chart primitives (plates, fonts, dashed
  lines, hatch rects, milestone diamonds, seal/stamp header, footer).
- `bin/gantt.py --spec spec.json --out chart.png` — JSON-driven Gantt
  timetable renderer.
- `bin/stepchart.py --spec spec.json --out chart.png` — JSON-driven
  capacity step-chart renderer.
- `examples/charts/` — runnable LQ-7 specs (`production-timetable.json`,
  `power-plan.json`) proving both renderers.
- `assets/fonts/` — OFL fonts (Courier Prime, Special Elite); populate per
  project with `fetch_fonts.py` — or copy the vendored set from
  `examples/minimal-order/assets/fonts/` for offline use.

## Output Contract

- Documents: US Letter PDF via WeasyPrint (portrait for orders, landscape
  for charts), plus 150–200dpi PNGs when the user wants them for chat/Discord.
- Charts: landscape PNGs at 300dpi; a 2-up landscape PDF when print is wanted.
- All figures traceable to the source text; no invented content in bars,
  tables, or routing blocks.

## Operating Rules

1. WeasyPrint for styled prose — never takumi-pdf (unfixable italic/state
   corruption in real paragraphs).
2. One `@page` background-image layer, positioned with negative offsets
   equal to the margins (`background-position: -0.8in -0.72in`).
3. Register every font weight/style with `@font-face`; verify the TTFs are
   real before trusting a render.
4. QA is rasterize-and-look, always. Two failed visual attempts → ask one
   sharp disambiguating question instead of shipping a third guess.
5. Keep the user's source text intact; flag tensions between their spec and
   the layout in one line rather than silently "fixing" either.
