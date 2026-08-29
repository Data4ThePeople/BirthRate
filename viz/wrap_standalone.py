"""Wrap a built page as a complete HTML document for self-hosting.

The artifact platform supplies <!doctype html>, <head> and <body> at publish
time, so the built pages are fragments. Served directly from a web server a
fragment lacks a doctype, which puts the browser in quirks mode - box-sizing,
line heights and inline-block metrics all shift - so anything hosted outside
the artifact platform needs the document built properly around it.

Writes to viz/dist/, leaving the originals untouched for publishing.
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"

HEAD_TAGS = re.compile(
    r"(<title>.*?</title>|<link\b[^>]*>|<style>.*?</style>)", re.S | re.I)

DOC = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{description}">
{head}
</head>
<body>
{body}
</body>
</html>
"""


def wrap(fragment: str, description: str) -> str:
    """Lift title, stylesheet links and style blocks into a real <head>."""
    head_parts: list[str] = []

    def take(match: re.Match) -> str:
        head_parts.append(match.group(0).strip())
        return ""

    # only hoist from the leading block, before any page content begins
    split = fragment.find("<div class=\"wrap\">")
    if split < 0:
        split = len(fragment)
    head_src, body = fragment[:split], fragment[split:]
    head_src = HEAD_TAGS.sub(take, head_src)

    body = (head_src.strip() + "\n" + body).strip()
    return DOC.format(description=description,
                      head="\n".join(head_parts), body=body)


TARGETS = [
    ("map.html", "Interactive county map of US fertility, 1982-2024."),
    ("fertility.html", "County-level US fertility, 1982-2024: the rural birth-rate "
                       "premium collapsed, inverted, and came back."),
]


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for name, description in TARGETS:
        src = HERE / name
        if not src.exists():
            print(f"  skip {name} (not built)")
            continue
        out = DIST / name
        doc = wrap(src.read_text(), description)
        for required in ("<!doctype html>", "<meta charset", "viewport",
                         "<title>", "</body>", "</html>"):
            if required not in doc:
                raise SystemExit(f"{name}: wrapper missing {required}")
        out.write_text(doc)
        print(f"  {name:16s} -> dist/{name}  {out.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
