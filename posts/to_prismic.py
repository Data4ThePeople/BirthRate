"""Convert a Markdown post into Prismic Rich Text JSON, and optionally upload it.

Prismic Rich Text is a flat list of blocks. Each block carries plain text plus
`spans` - character offsets marking bold, italic and links - so the Markdown
markers have to be stripped while their positions are recorded.

Supported blocks: heading1-6, paragraph, list-item, o-list-item, preformatted.
Rich Text has no table type, so Markdown tables are emitted as preformatted
monospace blocks by default. That renders correctly but is not a real table;
for a proper one, use Prismic's dedicated Table field in a slice, or drop in an
image. Pass --tables=skip to leave them out and place them by hand.

Usage
    python to_prismic.py post.md                 # write post.prismic.json
    python to_prismic.py post.md --upload        # also POST to the Migration API

Uploading needs a write token and repository, from the environment:
    PRISMIC_TOKEN     permanent token (Settings > API & Security)
    PRISMIC_REPO      repository id, e.g. "birthrate"
    PRISMIC_TYPE      custom type id to create, e.g. "blog_post"
    PRISMIC_FIELD     Rich Text field id in that type, e.g. "content"
Documents arrive as drafts in the Migration Release for review.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

INLINE = re.compile(
    r"\*\*(?P<strong>[^*]+)\*\*"
    r"|(?<!\*)\*(?P<em>[^*]+)\*(?!\*)"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<lurl>[^)]+)\)"
    r"|`(?P<code>[^`]+)`"
)


def parse_inline(text: str) -> tuple[str, list[dict]]:
    """Strip inline markers, returning plain text and Prismic spans."""
    out, spans, pos = [], [], 0
    cursor = 0
    for m in INLINE.finditer(text):
        out.append(text[cursor:m.start()])
        pos += m.start() - cursor
        if m["strong"] is not None:
            body, kind = m["strong"], "strong"
        elif m["em"] is not None:
            body, kind = m["em"], "em"
        elif m["ltext"] is not None:
            body, kind = m["ltext"], "hyperlink"
        else:
            body, kind = m["code"], None
        if kind == "hyperlink":
            spans.append({"start": pos, "end": pos + len(body), "type": "hyperlink",
                          "data": {"link_type": "Web", "url": m["lurl"]}})
        elif kind:
            spans.append({"start": pos, "end": pos + len(body), "type": kind})
        out.append(body)
        pos += len(body)
        cursor = m.end()
    out.append(text[cursor:])
    return "".join(out), spans


def block(kind: str, text: str) -> dict:
    plain, spans = parse_inline(text)
    return {"type": kind, "text": plain, "spans": spans}


def convert(markdown: str, tables: str = "preformatted") -> list[dict]:
    blocks: list[dict] = []
    lines = markdown.replace("\r\n", "\n").split("\n")
    i, warnings, images = 0, [], []

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip() or set(line.strip()) <= {"-", "*", "_"} and len(line.strip()) >= 3:
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            blocks.append(block(f"heading{len(heading[1])}", heading[2].strip()))
            i += 1
            continue

        if line.lstrip().startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                if not re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            warnings.append(f"table with {len(rows)} rows")
            if tables == "skip":
                continue
            widths = [max(len(r[c]) for r in rows if c < len(r))
                      for c in range(max(len(r) for r in rows))]
            for n, row in enumerate(rows):
                text = "  ".join(
                    re.sub(r"\*\*|\*", "", cell).ljust(widths[c])
                    for c, cell in enumerate(row)).rstrip()
                blocks.append({"type": "preformatted", "text": text, "spans": []})
                if n == 0:
                    blocks.append({"type": "preformatted",
                                   "text": "  ".join("-" * w for w in widths), "spans": []})
            continue

        image = re.match(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)\s*$", line)
        if image:
            # Rich Text images must point at a Prismic-hosted asset, so the file
            # cannot be inlined from here. Leave an obvious marker at the right
            # position for the image to be dropped in.
            name = image["src"].rsplit("/", 1)[-1]
            blocks.append({"type": "preformatted",
                           "text": f"[IMAGE: {name}]", "spans": []})
            images.append(name)
            i += 1
            continue

        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            blocks.append(block("list-item", bullet[1].strip()))
            i += 1
            continue

        numbered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if numbered:
            blocks.append(block("o-list-item", numbered[1].strip()))
            i += 1
            continue

        quote = re.match(r"^>\s?(.*)$", line)
        if quote:
            blocks.append(block("paragraph", quote[1].strip()))
            i += 1
            continue

        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and \
                not re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\||>)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(block("paragraph", " ".join(para)))

    if warnings:
        print(f"  note: {len(warnings)} table(s) rendered as preformatted text "
              f"({tables}); Prismic Rich Text has no table block", file=sys.stderr)
    if images:
        print(f"  note: {len(images)} image placeholder(s): {', '.join(images)}",
              file=sys.stderr)
    return blocks


def upload(blocks: list[dict], title: str, uid: str) -> None:
    import requests

    missing = [v for v in ("PRISMIC_TOKEN", "PRISMIC_REPO", "PRISMIC_TYPE", "PRISMIC_FIELD")
               if not os.environ.get(v)]
    if missing:
        sys.exit(f"set {', '.join(missing)} to upload")
    body = {
        "title": title,
        "type": os.environ["PRISMIC_TYPE"],
        "uid": uid,
        "lang": os.environ.get("PRISMIC_LANG", "en-us"),
        "data": {os.environ["PRISMIC_FIELD"]: blocks},
    }
    resp = requests.post(
        "https://migration.prismic.io/documents",
        headers={"Authorization": f"Bearer {os.environ['PRISMIC_TOKEN']}",
                 "repository": os.environ["PRISMIC_REPO"],
                 "Content-Type": "application/json"},
        json=body, timeout=60)
    if resp.status_code >= 300:
        sys.exit(f"upload failed {resp.status_code}: {resp.text[:400]}")
    print(f"  uploaded as a draft in the Migration Release: {resp.json().get('id', '')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--tables", choices=["preformatted", "skip"], default="preformatted")
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()

    for path in args.files:
        md = path.read_text()
        blocks = convert(md, args.tables)
        out = path.with_suffix(".prismic.json")
        out.write_text(json.dumps(blocks, indent=2))
        title = next((b["text"] for b in blocks if b["type"] == "heading1"), path.stem)
        counts: dict[str, int] = {}
        for b in blocks:
            counts[b["type"]] = counts.get(b["type"], 0) + 1
        print(f"{path.name} -> {out.name}  {len(blocks)} blocks  "
              f"{', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}")
        if args.upload:
            upload(blocks, title, path.stem)


if __name__ == "__main__":
    main()
