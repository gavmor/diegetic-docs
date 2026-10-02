# Chart toolkit — PIL-drawn planning charts

Charts are drawn directly with PIL, not matplotlib: full control over the
period look (paper plate, typewriter labels, ink bars, rubber-stamp
accents), and no fighting a plotting library's default aesthetic.

## Setup

- Canvas: landscape 11×8.5in at 300dpi = 3300×2550. Bake the plate with
  `bin/make_plate.py --format landscape --dpi 300`.
- Fonts: `ImageFont.truetype` on the vendored Courier Prime / Special Elite
  TTFs. Typical sizes at 300dpi: titles 64–66px, axis labels 30px, bar labels
  28–30px, footnotes 26–28px.
- Palette: ink `(38,34,28)`, faint `(122,108,84)`, rule `(90,80,62)`,
  stamp-red `(140,28,28)`.

## Helpers (copy into the chart script)

```python
def dashed_line(d, x0, y0, x1, y1, fill, width=3, dash=18, gap=12):
    # manual dashes — PIL has no setdash
def hatch_rect(base, x0, y0, x1, y1, fill, hatch, border):
    # fill + diagonal hatch clipped to the rect via an L mask, then border
def diamond(d, cx, cy, r, fill):
    d.polygon([cx, cy-r, cx+r, cy, cx, cy+r, cx-r, cy], fill=fill)
```

`hatch_rect` draws the hatch on a separate RGBA layer and pastes it through
a rectangular mask — the diagonal lines never escape the bar.

## Gantt recipe (proven on a 9-row, T+0–T+120 production timetable)

1. **Header block**: seal PNG pasted top-left, centered title lines
   (Special Elite title, bold subtitle, faint sub-line), double rule under,
   RESTRICTED stamp rotated −9° top-right (build the stamp on its own RGBA
   layer, `rotate(-9, expand=True)`, then paste with its alpha).
2. **Grid**: vertical lines every 10 min (light), heavier every 30;
   tick labels `T+0 … T+120` below. Row labels right-aligned in a fixed
   left column (name bold, sub-line faint).
3. **Bars**: solid ink rects with the label in paper-light type *inside*
   the bar when it fits (`> ~340px`), otherwise in ink *right of* the bar.
   Thin sub-bars sit below the main bar with an italic faint caption.
4. **Milestones**: red diamonds with red labels above (or below when the
   row above is crowded). A red dashed vertical for the terminal event
   (e.g. MUSTER), labeled above the grid.
5. **Legend**: lay out dynamically — measure each label with
   `font.getbbox` and advance; fixed offsets collide once labels grow.

## Step-chart recipe (proven on a MW-draw-against-capacity power plan)

1. Axes: MW 0–14 horizontal gridlines, dashed capacity lines (one plant /
   two plants) labeled at right.
2. The draw line: walk the step list, drawing horizontal segments and
   vertical risers at 6–7px ink; fill under with ink at low alpha via a
   polygon closed along the bottom.
3. Annotate each step's cause ("+ COAL REFINERY — 3 MW") above the line;
   red italic for warnings ("5 MW ON A 5 MW PLANT — NO MARGIN").
4. Diegetic prohibition notes ("NEVER RUN ALL FOUR WORKS AT ONCE…") in red
   bold below the axis, clear of the axis title.

## Data-grounding rule

Every bar's endpoints come from stated figures in the source order. A
duration the order does not give is **not** a bar — it is a milestone
diamond (an event) or it is omitted. Never invent end times to fill the
chart; a staff officer's chart with a guessed bar is worse than an honest
gap.
