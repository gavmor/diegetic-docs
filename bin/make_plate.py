#!/usr/bin/env python3
"""Bake aged-paper @page plate PNGs (single background-image layer per page).

The plate carries everything the page background needs — tonal patches,
grain, stains, vignette, crease — because WeasyPrint silently drops
multiple background layers on @page. See references/print-css.md.

Supports diverse, randomized visual storytelling marks per page:
- Soft organic tonal aging varied per seed
- Randomized coffee stains: full rings, crescents/arcs with pooled wash,
  double rims, broken rings, varied aspect ratio and rotation
- Coffee droplet splatters and downward drip trails
- Handling smudges and finger/thumb grime along margins
- Natural fold creases: angled horizontal/vertical folds (bifold/trifold)
  with embossed highlight/shadow line pairs, plus optional corner dog-ears
- Multi-page plate generation with deterministic per-page seed derivation

Usage:
    make_plate.py [--format portrait|landscape] [--dpi 200] [--seed 7]
                  [--pages 1] [--page N] [--stains 6] [--no-crease]
                  [--no-drips] [--no-smudges] [--out paper-plate.png]
"""
import argparse
import math
import os as _os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE = (233, 222, 198)
PATCH = (228, 214, 186)
DARK = (150, 120, 80)
STAIN = (120, 84, 40)
CREASE = (110, 88, 55)
HIGHLIGHT = (250, 246, 236)
SMUDGE = (95, 75, 50)


def derive_page_seed(base_seed: int, page_num: int) -> int:
    """Deterministically derive a unique seed for page_num (1-indexed)."""
    if page_num == 1:
        return base_seed
    return (base_seed + (page_num - 1) * 1000) & 0x7FFFFFFF


def resolve_out_path(out_arg: str, fmt: str, page_num: int, total_pages: int) -> str:
    """Resolve destination path for a given page number."""
    if total_pages == 1 and out_arg and ("%d" not in out_arg) and ("{" not in out_arg):
        return out_arg
    if out_arg:
        if "%d" in out_arg:
            return out_arg % page_num
        if "{page}" in out_arg or "{n}" in out_arg:
            return out_arg.format(page=page_num, n=page_num)
        root, ext = _os.path.splitext(out_arg)
        if ext:
            return f"{root}-{page_num}{ext}"
        return _os.path.join(out_arg, f"paper-plate-{fmt}-{page_num}.png")
    if total_pages == 1:
        return f"paper-plate-{fmt}.png"
    return f"paper-plate-{fmt}-{page_num}.png"


def make_plate(w, h, seed=7, stains=6, crease=True, drips=True, smudges=True):
    rng = random.Random(seed)
    base = Image.new("RGB", (w, h), BASE)

    # 1. Large soft organic tonal patches
    pw, ph = max(16, w // 4), max(16, h // 4)
    patch = Image.new("L", (pw, ph))
    dpx = patch.load()
    f1 = rng.uniform(0.02, 0.045)
    f2 = rng.uniform(0.015, 0.035)
    f3 = rng.uniform(0.02, 0.045)
    f4 = rng.uniform(0.015, 0.035)
    p1 = rng.uniform(0, math.tau)
    p2 = rng.uniform(0, math.tau)
    for y in range(ph):
        for x in range(pw):
            v = (math.sin(x * f1 + y * f2 + p1) + math.cos(y * f3 - x * f4 + p2)) * 0.5
            dpx[x, y] = int(128 + 34 * v)
    patch = patch.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(16))
    base = Image.composite(Image.new("RGB", (w, h), PATCH),
                           base, patch.point(lambda v: (v - 100) * 4))

    # 2. Fine grain (deterministic per seed)
    noise = Image.frombytes("L", (w, h), rng.randbytes(w * h))
    base = Image.blend(base, Image.merge("RGB", (noise, noise, noise)), 0.05)

    # 3. Coffee stains layer (rings, crescents, double rims, drips)
    if stains > 0:
        stain_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for _ in range(stains):
            if rng.random() < 0.65:
                margin_side = rng.choice(["left", "right", "top", "bottom", "corner"])
                if margin_side == "left":
                    cx = rng.randint(int(w * 0.04), int(w * 0.28))
                    cy = rng.randint(int(h * 0.05), int(h * 0.95))
                elif margin_side == "right":
                    cx = rng.randint(int(w * 0.72), int(w * 0.96))
                    cy = rng.randint(int(h * 0.05), int(h * 0.95))
                elif margin_side == "top":
                    cx = rng.randint(int(w * 0.05), int(w * 0.95))
                    cy = rng.randint(int(h * 0.04), int(h * 0.28))
                elif margin_side == "bottom":
                    cx = rng.randint(int(w * 0.05), int(w * 0.95))
                    cy = rng.randint(int(h * 0.72), int(h * 0.96))
                else:  # corner
                    cx = rng.choice([rng.randint(int(w * 0.04), int(w * 0.25)),
                                     rng.randint(int(w * 0.75), int(w * 0.96))])
                    cy = rng.choice([rng.randint(int(h * 0.04), int(h * 0.25)),
                                     rng.randint(int(h * 0.75), int(h * 0.96))])
            else:
                cx = rng.randint(int(w * 0.08), int(w * 0.92))
                cy = rng.randint(int(h * 0.08), int(h * 0.92))

            rx = rng.randint(80, 240)
            ry = int(rx * rng.uniform(0.85, 1.15))
            rot = rng.uniform(0, 360)
            stype = rng.choice(["full", "crescent", "crescent", "double", "broken"])

            pw = int(max(rx, ry) * 2.5 + 50)
            p_img = Image.new("RGBA", (pw, pw), (0, 0, 0, 0))
            pd = ImageDraw.Draw(p_img)
            pc = pw // 2

            if stype == "full":
                for dr, a, lw in ((0, rng.randint(10, 16), rng.randint(4, 8)),
                                  (-5, rng.randint(12, 19), rng.randint(5, 9)),
                                  (-11, rng.randint(7, 12), rng.randint(3, 6))):
                    pd.ellipse([pc - rx + dr, pc - ry + dr, pc + rx - dr, pc + ry - dr],
                               outline=STAIN + (a,), width=lw)
            elif stype == "crescent":
                span = rng.randint(90, 260)
                start_ang = rng.randint(0, 360)
                for dr, a, lw in ((0, rng.randint(12, 19), rng.randint(4, 9)),
                                  (-5, rng.randint(15, 23), rng.randint(5, 10)),
                                  (-11, rng.randint(8, 14), rng.randint(3, 7))):
                    pd.arc([pc - rx + dr, pc - ry + dr, pc + rx - dr, pc + ry - dr],
                           start=start_ang, end=start_ang + span,
                           fill=STAIN + (a,), width=lw)
                if rng.random() < 0.6:
                    pd.chord([pc - rx + 14, pc - ry + 14, pc + rx - 14, pc + ry - 14],
                             start=start_ang + 25, end=start_ang + span - 25,
                             fill=STAIN + (rng.randint(3, 7),))
            elif stype == "broken":
                ang1 = rng.randint(0, 180)
                span1 = rng.randint(60, 130)
                ang2 = (ang1 + 180 + rng.randint(-30, 30)) % 360
                span2 = rng.randint(50, 120)
                for dr, a, lw in ((0, rng.randint(11, 17), rng.randint(4, 8)),
                                  (-5, rng.randint(14, 20), rng.randint(5, 9))):
                    pd.arc([pc - rx + dr, pc - ry + dr, pc + rx - dr, pc + ry - dr],
                           start=ang1, end=ang1 + span1, fill=STAIN + (a,), width=lw)
                    pd.arc([pc - rx + dr, pc - ry + dr, pc + rx - dr, pc + ry - dr],
                           start=ang2, end=ang2 + span2, fill=STAIN + (a,), width=lw)
            elif stype == "double":
                for dr, a, lw in ((0, 14, rng.randint(4, 7)),
                                  (-4, 18, rng.randint(4, 8)),
                                  (-18, 13, rng.randint(3, 6)),
                                  (-22, 10, rng.randint(3, 5))):
                    pd.ellipse([pc - rx + dr, pc - ry + dr, pc + rx - dr, pc + ry - dr],
                               outline=STAIN + (a,), width=lw)

            rot_p = p_img.rotate(rot, resample=Image.BILINEAR)
            px_pos = cx - rot_p.width // 2
            py_pos = cy - rot_p.height // 2
            stain_layer.alpha_composite(rot_p, (px_pos, py_pos))

            # Drips & splatter around the stain
            if drips and rng.random() < 0.7:
                sd = ImageDraw.Draw(stain_layer)
                for _ in range(rng.randint(1, 4)):
                    dist = rng.uniform(rx * 0.85, rx * 1.55)
                    ang = rng.uniform(0, math.tau)
                    dx = int(cx + dist * math.cos(ang))
                    dy = int(cy + dist * math.sin(ang))
                    dr = rng.randint(2, 6)
                    sd.ellipse([dx - dr, dy - dr, dx + dr, dy + dr],
                               fill=STAIN + (rng.randint(16, 36),))
                    if rng.random() < 0.45:
                        trail_len = rng.randint(10, 30)
                        sd.line([dx, dy, dx + rng.randint(-3, 3), dy + trail_len],
                                fill=STAIN + (rng.randint(14, 28),), width=rng.randint(1, 3))

        stain_layer = stain_layer.filter(ImageFilter.GaussianBlur(5))
        base = Image.alpha_composite(base.convert("RGBA"), stain_layer).convert("RGB")

    # 4. Handling smudges & finger grime
    if smudges:
        smudge_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        smd = ImageDraw.Draw(smudge_layer)
        for _ in range(rng.randint(2, 4)):
            side = rng.choice(["left", "right", "bottom"])
            if side == "left":
                sx = rng.randint(8, int(w * 0.08))
                sy = rng.randint(int(h * 0.12), int(h * 0.88))
            elif side == "right":
                sx = rng.randint(int(w * 0.92), w - 8)
                sy = rng.randint(int(h * 0.12), int(h * 0.88))
            else:
                sx = rng.randint(int(w * 0.12), int(w * 0.88))
                sy = rng.randint(int(h * 0.92), h - 8)
            sw = rng.randint(20, 55)
            sh = rng.randint(35, 90)
            smd.ellipse([sx - sw, sy - sh, sx + sw, sy + sh],
                        fill=SMUDGE + (rng.randint(6, 13),))
        smudge_layer = smudge_layer.filter(ImageFilter.GaussianBlur(16))
        base = Image.alpha_composite(base.convert("RGBA"), smudge_layer).convert("RGB")

    # 5. Edge vignette
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    for inset, alpha in ((0, 60), (18, 34), (40, 18)):
        vd.rectangle([inset, inset, w - inset, h - inset],
                     outline=alpha, width=22)
    vig = vig.filter(ImageFilter.GaussianBlur(30))
    base = Image.composite(Image.new("RGB", (w, h), DARK),
                           base, vig.point(lambda v: v * 2))

    # 6. Handling creases (folds, angles, dog-ears)
    if crease:
        d = ImageDraw.Draw(base, "RGBA")

        def draw_crease_line(p0, p1):
            x0, y0 = p0
            x1, y1 = p1
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length == 0:
                return
            nx, ny = -dy / length, dx / length
            for off, a, lw in ((-1.5, 20, 2), (0, 36, 2), (1.5, 18, 2)):
                d.line([x0 + nx * off, y0 + ny * off, x1 + nx * off, y1 + ny * off],
                       fill=CREASE + (a,), width=lw)
            hoff = 3.5
            d.line([x0 + nx * hoff, y0 + ny * hoff, x1 + nx * hoff, y1 + ny * hoff],
                   fill=HIGHLIGHT + (24,), width=2)

        if w >= h:  # landscape: vertical folds
            fx = int(w * rng.uniform(0.46, 0.64))
            tilt = rng.randint(-25, 25)
            draw_crease_line((fx - tilt, 0), (fx + tilt, h))
            if rng.random() < 0.45:
                fx2 = int(w * (0.33 if fx > w * 0.55 else 0.67))
                tilt2 = rng.randint(-25, 25)
                draw_crease_line((fx2 - tilt2, 0), (fx2 + tilt2, h))
        else:  # portrait: horizontal folds
            fy = int(h * rng.uniform(0.32, 0.40))
            tilt = rng.randint(-25, 25)
            draw_crease_line((0, fy - tilt), (w, fy + tilt))
            if rng.random() < 0.55:
                fy2 = int(h * rng.uniform(0.64, 0.72))
                tilt2 = rng.randint(-25, 25)
                draw_crease_line((0, fy2 - tilt2), (w, fy2 + tilt2))

        # Dog-ear corner fold
        if rng.random() < 0.4:
            corner = rng.choice(["top-right", "top-left", "bottom-right", "bottom-left"])
            fl = rng.randint(90, 180)
            if corner == "top-right":
                draw_crease_line((w - fl, 0), (w, fl))
            elif corner == "top-left":
                draw_crease_line((0, fl), (fl, 0))
            elif corner == "bottom-right":
                draw_crease_line((w - fl, h), (w, h - fl))
            else:
                draw_crease_line((0, h - fl), (fl, h))

    return base


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--format", choices=["portrait", "landscape"],
                   default="portrait")
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--seed", type=int, default=7,
                   help="base random seed (default: 7)")
    p.add_argument("--pages", "--count", dest="pages", type=int, default=1,
                   help="number of distinct pages to generate (default: 1)")
    p.add_argument("--page", type=int, default=None,
                   help="generate only this specific 1-indexed page from the seed sequence")
    p.add_argument("--stains", type=int, default=6,
                   help="number of coffee stains per page (default: 6)")
    p.add_argument("--no-crease", action="store_true",
                   help="disable fold creases")
    p.add_argument("--no-drips", action="store_true",
                   help="disable coffee droplet splatters and drip trails")
    p.add_argument("--no-smudges", action="store_true",
                   help="disable edge/handling smudges")
    p.add_argument("--out", default=None,
                   help="output path, directory, or pattern (e.g. assets/paper-plate.png or plate-%%d.png)")
    a = p.parse_args()

    if a.format == "portrait":
        w, h = int(8.5 * a.dpi), int(11 * a.dpi)
    else:
        w, h = int(11 * a.dpi), int(8.5 * a.dpi)

    if a.page is not None:
        pages_to_generate = [a.page]
    else:
        pages_to_generate = list(range(1, a.pages + 1))

    for pnum in pages_to_generate:
        p_seed = derive_page_seed(a.seed, pnum)
        plate = make_plate(w, h, p_seed, a.stains, not a.no_crease,
                           not a.no_drips, not a.no_smudges)
        out = resolve_out_path(a.out, a.format, pnum, a.pages)
        _os.makedirs(_os.path.dirname(_os.path.abspath(out)), exist_ok=True)
        plate.save(out)
        print(f"wrote {out} (page {pnum}, seed {p_seed}, {w}x{h})")

        # Compatibility: if plain filename like --out assets/paper-plate.png was given:
        # ensure both unnumbered (assets/paper-plate.png) and numbered (assets/paper-plate-1.png)
        # exist so single-page and multi-page stylesheets resolve seamlessly.
        if pnum == 1 and a.out and "%d" not in a.out and "{" not in a.out:
            root, ext = _os.path.splitext(a.out)
            if ext:
                alt = a.out if a.pages > 1 else f"{root}-1{ext}"
                if alt != out:
                    plate.save(alt)
                    print(f"wrote {alt} (compatibility plate)")


if __name__ == "__main__":
    main()
