#!/usr/bin/env python3
"""Executable gate for diegetic document builds. Fails loudly on:

  1. font files that are not real font data (e.g. 404 HTML saved as .ttf)
  2. multi-layer background-image inside @page (WeasyPrint silently drops
     every layer but the color — bake the plate into ONE png instead)
  3. url(...) references in the HTML that point at missing files

Usage:
    check.py --html order.html [--fonts assets/fonts] [--strict]
"""
import argparse
import os
import re
import sys


def check_fonts(dirs):
    bad = []
    n = 0
    for d in dirs:
        if not os.path.isdir(d):
            bad.append(f"font dir missing: {d}")
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith((".ttf", ".otf")):
                continue
            n += 1
            p = os.path.join(d, f)
            with open(p, "rb") as fh:
                magic = fh.read(4)
            if magic not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
                bad.append(f"{p}: bad magic {magic!r} — not font data")
                continue
            try:
                from fontTools.ttLib import TTFont
                TTFont(p)
            except Exception as e:  # noqa: BLE001
                bad.append(f"{p}: fontTools cannot parse ({e})")
    if n == 0:
        bad.append("no .ttf/.otf files found in " + ", ".join(dirs))
    return bad, n


def check_page_backgrounds(html):
    """Find @page blocks whose background-image has >1 layer."""
    bad = []
    for m in re.finditer(r"@page[^{]*\{(.*?)\}", html, re.S):
        block = m.group(1)
        for prop in re.finditer(
                r"background(?:-image)?\s*:\s*([^;]+);", block):
            val = prop.group(1)
            # a comma outside url(...) and gradients = multiple layers
            tmp = re.sub(r"url\([^)]*\)", "URL", val)
            tmp = re.sub(r"(?:linear|radial|repeating-[a-z]+)-gradient\([^)]*\)",
                         "GRAD", tmp)
            if "," in tmp:
                bad.append(
                    "@page has a multi-layer background "
                    f"({val.strip()[:60]}…) — WeasyPrint drops all but one; "
                    "bake the plate into a single PNG")
                break
    return bad


def check_urls(html, root):
    bad = []
    for m in re.finditer(r'url\(["\']?([^)"\']+)["\']?\)', html):
        u = m.group(1)
        if u.startswith(("data:", "http://", "https://", "#")):
            continue
        p = os.path.normpath(os.path.join(root, u))
        if not os.path.isfile(p):
            bad.append(f"missing asset: {u} (resolved to {p})")
    # also <img src>
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html):
        u = m.group(1)
        if u.startswith(("data:", "http://", "https://")):
            continue
        p = os.path.normpath(os.path.join(root, u))
        if not os.path.isfile(p):
            bad.append(f"missing <img>: {u} (resolved to {p})")
    return bad


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--html", required=True)
    p.add_argument("--fonts", action="append", default=[])
    a = p.parse_args()

    if not os.path.isfile(a.html):
        print(f"no such html: {a.html}")
        sys.exit(1)
    with open(a.html, encoding="utf-8") as f:
        html = f.read()
    root = os.path.dirname(os.path.abspath(a.html)) or "."

    problems = []
    font_problems, nfonts = check_fonts(a.fonts or
                                       [os.path.join(root, "assets", "fonts")])
    problems += font_problems
    problems += check_page_backgrounds(html)
    problems += check_urls(html, root)

    if problems:
        print("CHECK FAILED:")
        for x in problems:
            print(f"  - {x}")
        sys.exit(1)
    print(f"check ok: {nfonts} fonts verified, "
          f"@page backgrounds single-layer, all urls resolve")


if __name__ == "__main__":
    main()
