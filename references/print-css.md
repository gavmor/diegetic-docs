# Print CSS for diegetic form documents

Render with WeasyPrint (`python3 -m weasyprint doc.html doc.pdf`). Do **not**
use takumi-pdf for styled prose: it has unfixable paragraph-level state
corruption where a styled inline earlier in a paragraph mispositions later
italic runs (overlaps, eaten spaces, phantom gaps).

## @page background — the hard rules

- **One background-image layer only** on `@page` (also `:left`/`:right`/`:nth()`).
  Multiple comma-separated layers are silently dropped; only
  `background-color` paints. Bake the whole plate — paper, stains, vignette,
  crease — into **one PNG per page** with `bin/make_plate.py`.
- **@page backgrounds position from the page *area* origin, not the page
  box.** With non-zero margins a full-page image shifts right/down by the
  margin. Compensate with negative `background-position`:

```css
@page {
  size: 8.5in 11in;
  margin: 0.72in 0.8in 0.75in 0.8in;
  background-image: url("assets/paper-plate-1.png");
  background-size: 8.5in 11in;
  background-position: -0.8in -0.72in;  /* = -left-margin -top-margin */
  background-repeat: no-repeat;
  @bottom-left   { content: "FORM LQ-7"; font-size: 7.5pt;
                   letter-spacing: 2pt; color: #5a5245; }
  @bottom-center { content: "— " counter(page) " of " counter(pages) " —"; font-size: 8pt;
                   color: #5a5245; }
  @bottom-right  { content: "SPEAKING WOODS COMMAND"; font-size: 7.5pt;
                   letter-spacing: 2pt; color: #5a5245; }
}

/* Multi-page documents: randomize background plates per page */
@page:nth(1) { background-image: url("assets/paper-plate-1.png"); }
@page:nth(2) { background-image: url("assets/paper-plate-2.png"); }
@page:nth(3) { background-image: url("assets/paper-plate-3.png"); }
```

Generate diverse plates with:
```bash
bin/make_plate.py --pages 3 --out assets/paper-plate.png
```
This derives deterministic per-page seeds, varying coffee ring locations,
rotations, crescents, drips, smudges, and fold crease angles so consecutive
sheets don't duplicate marks.

Margin-box footers (`@bottom-left/center/right`) need an explicit
`font-family` — they do not inherit the body's.

## Type

- Body: Courier Prime 10–10.5pt, `line-height: 1.42`, ink `#26221a`.
- Display (masthead title): Special Elite.
- Always `@font-face` every weight/style you use (regular, bold, italic,
  bold-italic); WeasyPrint will not synthesize them, and unregistered
  italics silently fall back. Run `bin/check.py` to verify.

## Form patterns

**Masthead** — double-rule box, seal absolutely positioned left, stamp
absolutely positioned right:

```css
.masthead { position: relative; border-top: 5px double #26221a;
            border-bottom: 5px double #26221a; padding: 14px 10px 12px 118px; }
```

**Routing block** — label, dotted leader, value, on flex rows:

```css
.rrow { display: flex; align-items: center; }
.rrow .dots { flex: 1; border-bottom: 2px dotted #6b6252; margin: 0 6px; height: 1px; }
```

**Rubber stamp** — rotated, double border, translucent red; absolute inside
a relatively-positioned masthead so it overlaps the border like a real stamp:

```css
.stamp { position: absolute; right: -2px; top: -38px;
         transform: rotate(-9deg); border: 4px double #9c1f1f;
         color: #9c1f1f; font-weight: 700; font-size: 21pt;
         letter-spacing: 7px; padding: 4px 14px 2px 20px; opacity: 0.78; }
```

WeasyPrint supports `transform: rotate()` on block elements.

**Spec tables** — full width, double rule under the header row, single rules
between rows, double rule closing the body:

```css
table.spec { width: 100%; border-collapse: collapse; font-size: 9.6pt;
             page-break-inside: avoid; }
table.spec thead th { border-bottom: 3px double #26221a; }
table.spec tbody td { border-bottom: 1px solid #8a8069; }
table.spec tbody tr:last-child td { border-bottom: 2px solid #26221a; }
```

**Section heads** — letterspaced, ruled:

```css
h2.sec { font-size: 11.5pt; font-weight: 700; letter-spacing: 3px;
         border-bottom: 2px solid #26221a; padding-bottom: 3px; }
```

**Note boxes** — thin rule, slight paper-light fill:

```css
.notebox { border: 1.5px solid #26221a; padding: 8px 12px;
           background: rgba(255, 252, 244, 0.35);
           page-break-inside: avoid; }
```

**Correction patch** — for notes that should read as stuck on after
typing: a dirty-white tape / correction-fluid patch, slightly rotated,
whisper of shadow. No border; the lift sells it:

```css
.notebox-tape {
  position: relative;
  margin: 14px 10px;
  padding: 10px 16px 9px;
  background: linear-gradient(175deg, #f7f3e7 0%, #f0ead7 55%, #e8e1cb 100%);
  transform: rotate(-0.7deg);
  box-shadow: 1px 1px 2px rgba(74, 62, 38, 0.18);
  page-break-inside: avoid;
  font-size: 9.6pt;
}
```

Keep the shadow faint — it should read as paper on paper, not a UI
card. Proven on the Tümmler annex (141/TINE/0004).

## QA

- `pdftotext` fragments text at italic/style boundaries — never trust it
  alone for spacing QA. **Rasterize and look** (`pdftoppm -png -r 60`).
- Keep tables that must not split with `page-break-inside: avoid`; let long
  data tables break (`allowbreak`) rather than overflowing.
