#!/usr/bin/env python3
"""Fetch typewriter/display fonts and VERIFY they are real font data.

Google Fonts sometimes serves 404 HTML pages with a 200 status; a font
file that is actually HTML renders as a silent fallback and the mistake
is invisible until print. This script refuses to keep such files.

Fetches (OFL-licensed):
    Courier Prime  regular, bold, italic, bold-italic  (body)
    Special Elite  regular                              (display)

Usage:
    fetch_fonts.py [--out assets/fonts]

Exits non-zero if any file fails verification.
"""
import argparse
import os
import re
import subprocess
import sys
import urllib.request

UA = {"User-Agent": "curl/8.0"}  # non-browser UA -> css2 returns TTF urls
CSS_URL = ("https://fonts.googleapis.com/css2?"
           "family=Courier+Prime:ital,wght@0,400;0,700;1,400;1,700"
           "&family=Special+Elite&display=swap")

# (filename, family, style, weight) — matched against @font-face descriptors,
# never against document order (Google does not honor request order).
WANT = [
    ("courier-prime-regular.ttf", "Courier Prime", "normal", "400"),
    ("courier-prime-bold.ttf", "Courier Prime", "normal", "700"),
    ("courier-prime-italic.ttf", "Courier Prime", "italic", "400"),
    ("courier-prime-bold-italic.ttf", "Courier Prime", "italic", "700"),
    ("special-elite.ttf", "Special Elite", "normal", "400"),
]


def css_faces():
    """Parse @font-face blocks -> {(family, style, weight): url}."""
    req = urllib.request.Request(CSS_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        css = r.read().decode("utf-8", "replace")
    faces = {}
    for b in re.findall(r"@font-face\s*\{(.*?)\}", css, re.S):
        fam = re.search(r"font-family:\s*'([^']+)'", b)
        style = re.search(r"font-style:\s*(\w+)", b)
        weight = re.search(r"font-weight:\s*(\d+)", b)
        url = re.search(r"url\((https://[^)]+?\.ttf)\)", b)
        if not (fam and style and weight and url):
            continue
        key = (fam.group(1), style.group(1), weight.group(1))
        faces.setdefault(key, url.group(1))
    return faces


def verify(path, family, style, weight):
    want_sub = {"normal": {"400": "Regular", "700": "Bold"},
                "italic": {"400": "Italic", "700": "Bold Italic"}}[style][weight]
    out = subprocess.run(["file", "-b", path], capture_output=True,
                         text=True).stdout
    if "TrueType" not in out and "OpenType" not in out:
        return f"{path}: not font data ({out.strip()})"
    try:
        from fontTools.ttLib import TTFont
        f = TTFont(path)
        fam = f["name"].getDebugName(16) or f["name"].getDebugName(1)
        sub = f["name"].getDebugName(17) or f["name"].getDebugName(2)
    except Exception as e:  # noqa: BLE001
        return f"{path}: fontTools failed to parse ({e})"
    if fam != family or sub != want_sub:
        return (f"{path}: name mismatch, got '{fam} {sub}', "
                f"wanted '{family} {want_sub}'")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="assets/fonts")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)

    faces = css_faces()
    missing = [k for (fn, fam, st, wt) in WANT
               for k in [(fam, st, wt)] if k not in faces]
    if missing:
        print(f"css2 did not return faces for: {missing}", file=sys.stderr)
        sys.exit(1)

    failures = []
    for fname, family, style, weight in WANT:
        url = faces[(family, style, weight)]
        path = os.path.join(a.out, fname)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
            f.write(r.read())
        err = verify(path, family, style, weight)
        if err:
            failures.append(err)
            os.remove(path)
        else:
            sub = ("Bold Italic" if (style, weight) == ("italic", "700")
                   else "Bold" if weight == "700"
                   else "Italic" if style == "italic" else "Regular")
            print(f"ok  {fname}  ({family} {sub})")

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)
    print(f"\nall {len(WANT)} fonts verified in {a.out}/")


if __name__ == "__main__":
    main()
