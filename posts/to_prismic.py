"""Push a Markdown post into Prismic, images and all.

Three steps, so nothing has to be laid out by hand:

  1. Convert Markdown to Prismic Rich Text. Blocks are flat, and bold, italic
     and links are character offsets into the plain text, so the markers are
     stripped while their positions are recorded.
  2. Upload each referenced image to the media library through the Asset API,
     caching the returned ids so re-runs do not create duplicates.
  3. Create the page through the Migration API, which lands it as a draft in
     the Migration Release for review.

Rich Text has no table block. Markdown tables become aligned preformatted
text; for a real table use Prismic's Table field in a slice, or an image.

Usage
    python to_prismic.py posts/*.md                 # convert only, writes .prismic.json
    python to_prismic.py --list-types               # discover type and field ids
    python to_prismic.py posts/*.md --publish       # upload assets, then create pages
    python to_prismic.py posts/*.md --publish -n    # dry run: show every call first

Environment
    PRISMIC_TOKEN   permanent token, from Settings > API & Security
    PRISMIC_REPO    repository id, e.g. "data4thepeople"
    PRISMIC_TYPE    custom type to create, e.g. "blog_post"   (--list-types finds it)
    PRISMIC_FIELD   the Rich Text field in that type, e.g. "content"
    PRISMIC_LANG    optional, defaults to en-us

Both APIs allow one request per second, which the script paces itself to.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

def load_dotenv() -> None:
    """Read .env from the project root or beside this script.

    Anything already set in the real environment wins, so an inline
    PRISMIC_TOKEN=... or an export still overrides the file.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        Path(os.environ["PRISMIC_ENV"]) if os.environ.get("PRISMIC_ENV") else None,
        Path.cwd() / ".env",              # the project being published from
        here / ".env",                    # the shared install, one config for all
        Path.home() / ".prismic.env",
    ]
    for candidate in [c for c in candidates if c]:
        if not candidate.exists():
            continue
        for raw in candidate.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key, value)


ASSET_API = "https://asset-api.prismic.io/assets"
MIGRATION_API = "https://migration.prismic.io/documents"
CUSTOM_TYPES_API = "https://customtypes.prismic.io/customtypes"
RATE_LIMIT_SECONDS = 1.1  # both APIs allow one request per second

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


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Pull a leading --- block of key: value pairs off the Markdown."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip().strip('"\'')
    return meta, text[end + 4:].lstrip("\n")


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

        # ::: blurb  Optional heading      -> highlited_page_blurb
        # ::: blurb-full Optional heading    -> its full-width variation
        fence = re.match(r"^:::\s*(?P<kind>blurb(?:-full)?)\s*(?P<title>.*)$", line)
        if fence:
            inner: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(":::"):
                inner.append(lines[i])
                i += 1
            i += 1  # closing fence
            blocks.append({"type": "blurb",
                           "title": fence["title"].strip(),
                           "full": fence["kind"].endswith("-full"),
                           "blocks": convert("\n".join(inner), tables)})
            continue

        # ::: embed 760px   -> an html_embed slice left empty, for the author
        # to paste the iframe into from the Prismic editor
        blank = re.match(r"^:::\s*embed\s*(?P<height>\S+)?\s*$", line)
        if blank:
            blocks.append({"type": "embed", "html": "",
                           "height": blank["height"] or "760px"})
            i += 1
            continue

        if line.lstrip().startswith("<iframe"):
            html = [line]
            while i + 1 < len(lines) and "</iframe>" not in html[-1]:
                i += 1
                html.append(lines[i])
            blocks.append({"type": "embed", "html": " ".join(x.strip() for x in html),
                           "height": "760px"})
            i += 1
            continue

        image = re.match(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)\s*$", line)
        if image:
            # Rich Text images must point at a Prismic-hosted asset, so the file
            # cannot be inlined from here. Leave an obvious marker at the right
            # position for the image to be dropped in.
            blocks.append({"type": "image", "_src": image["src"],
                           "alt": image["alt"]})
            images.append(image["src"])
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
        print(f"  {len(images)} image(s) referenced", file=sys.stderr)
    return blocks


def env(*names: str) -> list[str]:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        sys.exit("set " + ", ".join(missing))
    return [os.environ[n] for n in names]


def headers() -> dict:
    token, repo = env("PRISMIC_TOKEN", "PRISMIC_REPO")
    return {"Authorization": f"Bearer {token}", "repository": repo}


def check_token() -> None:
    """Report which Prismic APIs the configured token is allowed to use.

    A Content API access token and a write token are created in different
    places in the dashboard and look alike, so this distinguishes them before
    a publish run fails halfway.
    """
    import requests

    token, repo = env("PRISMIC_TOKEN", "PRISMIC_REPO")
    h = headers()
    checks = [
        ("Content API   (read)", "GET",
         f"https://{repo}.cdn.prismic.io/api/v2", {}, {"access_token": token}),
        ("Asset API     (write)", "GET", f"{ASSET_API}?limit=1", h, None),
        ("Types API     (write)", "GET", CUSTOM_TYPES_API, h, None),
    ]
    ok_write = True
    for name, method, url, hdrs, params in checks:
        try:
            r = requests.request(method, url, headers=hdrs, params=params, timeout=45)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  {name}  ERROR {exc}")
            continue
        verdict = "ok" if r.ok else f"denied ({r.status_code})"
        if not r.ok and "write" in name:
            ok_write = False
        print(f"  {name}  {verdict}")
    if not ok_write:
        print("\n  This looks like a Content API access token, which cannot write.")
        print("  Create a write token: Prismic > Settings > API & Security >")
        print("  'Write APIs' section - a different section from the access token")
        print("  at the top of that page. Or run:  npx prismic token create --write")
    else:
        print("\n  Write access confirmed; --publish will work.")


def fetch_type(type_id: str) -> dict | None:
    import requests

    resp = requests.get(CUSTOM_TYPES_API, headers=headers(), timeout=60)
    if resp.status_code >= 300:
        return None
    return next((ct for ct in resp.json() if ct["id"] == type_id), None)


def describe(ct: dict) -> tuple[list[str], list[str]]:
    """Rich-text-ish field ids, and slice zone ids, in a custom type."""
    fields, zones = [], []
    for tab in (ct.get("json") or {}).values():
        for field_id, field in tab.items():
            kind = field.get("type")
            if kind in ("StructuredText", "Text"):
                fields.append(field_id)
            elif kind in ("Slices", "Slices2", "SliceZone"):
                zones.append(field_id)
    return fields, zones


def verify(uid: str) -> None:
    """Find a created page in any release and print what actually landed.

    The Migration API is write-only, and a write token cannot read the Content
    API, so this needs PRISMIC_READ_TOKEN - a Content API access token - set
    alongside it. Without one there is no way to confirm from outside the
    dashboard what a publish produced.
    """
    import requests

    read = os.environ.get("PRISMIC_READ_TOKEN")
    if not read:
        sys.exit("set PRISMIC_READ_TOKEN (a Content API access token) to verify")
    (repo,) = env("PRISMIC_REPO")
    base = f"https://{repo}.cdn.prismic.io/api/v2"
    api = requests.get(base, params={"access_token": read}, timeout=45)
    if not api.ok:
        sys.exit(f"could not read the repository ({api.status_code})")

    refs = api.json()["refs"]
    print(f"  releases visible: " +
          ", ".join(f"{r.get('label')!r}" for r in refs))
    for ref in refs:
        r = requests.get(base + "/documents/search", timeout=60, params={
            "access_token": read, "ref": ref["ref"],
            "q": f'[[at(my.blog_post.uid,"{uid}")]]'})
        hits = r.json().get("results", []) if r.ok else []
        if not hits:
            continue
        doc = hits[0]
        data = doc["data"]
        print(f"\n  found in release {ref.get('label')!r}")
        print(f"    id={doc['id']}  uid={doc['uid']}  type={doc['type']}")
        print(f"    page_title:  {str(data.get('page_title'))[:72]}")
        print(f"    subtitle:    {str(data.get('page_subtitle'))[:72]}")
        print(f"    published:   {data.get('published_date')}")
        for sl in data.get("slices", []):
            kind = sl["slice_type"]
            if kind == "paragarph_text":
                blocks = sl["primary"]["paragraph_text"]
                kinds = ", ".join(sorted({b["type"] for b in blocks}))
                print(f"    {kind:<26s} {len(blocks):>3d} blocks ({kinds})")
            elif kind == "blog_body_content_image":
                im = sl["primary"]["image"]
                cap = sl["primary"].get("source_text") or []
                print(f"    {kind:<26s} {im.get('dimensions')} "
                      f"caption={'yes' if cap else 'NO'} url={'ok' if im.get('url') else 'MISSING'}")
            else:
                print(f"    {kind:<26s} {sl.get('variation')}")
        return
    print(f"\n  no page with uid {uid!r} found in any release")


def list_types() -> None:
    """Print each custom type, its text fields and its slice zones."""
    import requests

    resp = requests.get(CUSTOM_TYPES_API, headers=headers(), timeout=60)
    if resp.status_code >= 300:
        sys.exit(f"could not list custom types ({resp.status_code}): {resp.text[:300]}")
    for ct in resp.json():
        print(f"\nPRISMIC_TYPE={ct['id']}    ({ct.get('label', '')})")
        for tab in (ct.get("json") or {}).values():
            for field_id, field in tab.items():
                kind = field.get("type")
                if kind in ("StructuredText", "Text"):
                    label = field.get("config", {}).get("label", kind)
                    print(f"  PRISMIC_FIELD={field_id:<24s} {label}")
                elif kind in ("Slices", "Slices2", "SliceZone"):
                    names = sorted((field.get("config", {}).get("choices") or {}))
                    print(f"  slice zone '{field_id}' -> leave PRISMIC_FIELD blank")
                    for n in names:
                        print(f"      {n}")


def upload_assets(blocks: list[dict], base: Path, cache_path: Path,
                  dry_run: bool) -> None:
    """Upload each image once and swap the local path for its Prismic asset id."""
    import requests

    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for block in blocks:
        if block.get("type") != "image":
            continue
        src = block.pop("_src")
        path = (base / src).resolve()
        if not path.exists():
            sys.exit(f"image not found: {path}")

        if src not in cache:
            if dry_run:
                # never persisted: a placeholder id written to the cache would be
                # trusted by the next real run, which then references an asset
                # that does not exist
                print(f"    would upload {path.name}")
                cache[src] = {"id": "DRYRUN", "width": 0, "height": 0}
                block["id"] = "DRYRUN"
                block["copyright"] = None
                block["dimensions"] = {"width": 0, "height": 0}
                continue
            else:
                with path.open("rb") as fh:
                    resp = requests.post(
                        ASSET_API, headers=headers(),
                        files={"file": (path.name, fh, "image/png")},
                        data={"alt": block.get("alt", "")}, timeout=180)
                time.sleep(RATE_LIMIT_SECONDS)
                if resp.status_code >= 300:
                    sys.exit(f"asset upload failed for {path.name} "
                             f"({resp.status_code}): {resp.text[:300]}")
                body = resp.json()
                from PIL import Image

                with Image.open(path) as im:
                    w, h = im.size
                cache[src] = {"id": body.get("id") or body.get("asset_id"),
                              "width": w, "height": h,
                              "url": body.get("url") or body.get("secure_url")}
                print(f"    uploaded {path.name} -> {cache[src]['id']}")
                cache_path.write_text(json.dumps(cache, indent=2))

        asset = cache[src]
        if not asset.get("url") and not dry_run:
            # the Asset API has no single-asset GET (405), so page the list and
            # match on id - only needed for entries cached before urls were kept
            r = requests.get(ASSET_API, headers=headers(),
                             params={"limit": 100}, timeout=60)
            time.sleep(RATE_LIMIT_SECONDS)
            if r.ok:
                found = {a["id"]: a.get("url") for a in r.json().get("items", [])}
                for key, entry in cache.items():
                    if not entry.get("url") and entry["id"] in found:
                        entry["url"] = found[entry["id"]]
                cache_path.write_text(json.dumps(cache, indent=2))
        block["_url"] = asset.get("url")
        block["id"] = asset["id"]
        block["copyright"] = None
        block["dimensions"] = {"width": asset["width"], "height": asset["height"]}


def build_data(blocks: list[dict], meta: dict, title: str,
               uid: str = "") -> dict:
    """The document body. blog_post keeps its content in a slice zone, so a
    flat Rich Text field is only used when PRISMIC_FIELD names one."""
    field = os.environ.get("PRISMIC_FIELD", "").strip()
    if field and field not in ("slices", "auto"):
        return {field: [b for b in blocks if b.get("type") != "embed"]}

    from prismic_slices import to_slices

    body = [{k: v for k, v in b.items() if k != "_url"}
            for b in blocks if b.get("type") != "heading1"]
    data = {
        "page_title": meta.get("title", title),
        "page_subtitle": meta.get("subtitle", ""),
        "published_date": meta.get("date", ""),
        "updated_date": meta.get("updated", meta.get("date", "")),
        "meta_title": meta.get("meta_title", meta.get("title", title)),
        "meta_description": meta.get("description", meta.get("subtitle", "")),
        "meta_keywords": meta.get("keywords", ""),
        "make_this_main_post": False,
        "slices": to_slices(body),
    }

    from prismic_schema import build_dataset_graph, build_schema

    faqs: list[tuple[str, str]] = []
    question = None
    for b in body:
        if b.get("type") == "heading3" and b.get("text", "").endswith("?"):
            question = b["text"]
        elif question and b.get("type") == "paragraph":
            faqs.append((question, b["text"]))
            question = None

    hero = next((b.get("_url") for b in blocks
                 if b.get("type") == "image" and b.get("_url")), None)
    if meta.get("schema_type", "article").lower() == "dataset":
        data["schema"] = build_dataset_graph(
            meta, uid or data["page_title"], data["page_title"],
            data.get("meta_description", ""), hero, faqs)
    else:
        data["schema"] = build_schema(
            meta, uid or data["page_title"], data["page_title"],
            data.get("meta_description", ""), hero)
    return {k: v for k, v in data.items() if v != ""}


def create_document(blocks: list[dict], meta: dict, title: str, uid: str,
                    dry_run: bool, ledger_path: Path | None = None) -> None:
    """Create the page, or update it if this uid was created from here before.

    Without the ledger a second run would create a duplicate rather than
    revise the page, since the API has no upsert.
    """
    import requests

    ledger = (json.loads(ledger_path.read_text())
              if ledger_path and ledger_path.exists() else {})
    existing = ledger.get(uid)

    (doc_type,) = env("PRISMIC_TYPE")

    # A PRISMIC_FIELD naming something the type does not have would produce a
    # document with an empty body, so check it against the real type first.
    field = os.environ.get("PRISMIC_FIELD", "").strip()
    if field and field not in ("slices", "auto"):
        ct = fetch_type(doc_type)
        if ct is not None:
            fields, zones = describe(ct)
            if field not in fields:
                sys.exit(
                    f"PRISMIC_FIELD={field!r} is not a field on {doc_type}.\n"
                    f"  text fields: {', '.join(fields) or 'none'}\n"
                    f"  slice zones: {', '.join(zones) or 'none'}\n"
                    f"  For a slice-based type, leave PRISMIC_FIELD blank.")

    data = build_data(blocks, meta, title, uid)
    body = {
        "title": title,
        "type": doc_type,
        "uid": uid,
        "lang": os.environ.get("PRISMIC_LANG", "en-us"),
        "data": data,
    }
    if dry_run:
        shape = (f"{len(data['slices'])} slices" if "slices" in data
                 else f"field {list(data)[0]}")
        verb = f"PUT (update {existing})" if existing else "POST (create)"
        print(f"    would {verb}  type={doc_type} uid={uid}  {shape}")
        for sl in data.get("slices", []):
            label = sl["primary"].get("spacer_value", sl["variation"])
            print(f"      {sl['slice_type']} ({label})")
        return

    if existing:
        # type, lang and alternate_language_id are ignored on update
        payload = {k: v for k, v in body.items() if k in ("uid", "data", "title", "tags")}
        resp = requests.put(f"{MIGRATION_API}/{existing}",
                            headers={**headers(), "Content-Type": "application/json"},
                            json=payload, timeout=120)
    else:
        resp = requests.post(MIGRATION_API,
                             headers={**headers(), "Content-Type": "application/json"},
                             json=body, timeout=120)
    time.sleep(RATE_LIMIT_SECONDS)
    if resp.status_code >= 300:
        verb = "update" if existing else "create"
        sys.exit(f"{verb} failed ({resp.status_code}): {resp.text[:400]}")

    doc_id = existing or resp.json().get("id", "")
    if ledger_path:
        ledger[uid] = doc_id
        ledger_path.write_text(json.dumps(ledger, indent=2))
    action = "updated" if existing else "created"
    print(f"    {action} draft {doc_id} in the Migration Release")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--tables", choices=["preformatted", "skip"], default="preformatted")
    ap.add_argument("--publish", action="store_true",
                    help="upload images and create the pages in Prismic")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="with --publish, show every call without making it")
    ap.add_argument("--list-types", action="store_true",
                    help="print custom type and field ids from the repository")
    ap.add_argument("--check", action="store_true",
                    help="report which Prismic APIs the token is allowed to use")
    ap.add_argument("--verify", metavar="UID",
                    help="find a created page in any release and show what landed")
    args = ap.parse_args()
    load_dotenv()

    if args.check:
        check_token()
        return
    if args.verify:
        verify(args.verify)
        return
    if args.list_types:
        list_types()
        return
    if not args.files:
        ap.error("give at least one Markdown file, or --check / --list-types")

    for path in args.files:
        cache_path = path.parent / ".prismic-assets.json"

        meta, markdown = split_frontmatter(path.read_text())
        uid = meta.get("slug", path.stem)
        blocks = convert(markdown, args.tables)
        title = next((b["text"] for b in blocks if b["type"] == "heading1"), path.stem)
        counts: dict[str, int] = {}
        for b in blocks:
            counts[b["type"]] = counts.get(b["type"], 0) + 1
        print(f"{path.name} -> {len(blocks)} blocks  "
              f"{', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}")

        if args.publish:
            upload_assets(blocks, path.parent, cache_path, args.dry_run)
            create_document(blocks, meta, title, uid, args.dry_run,
                            path.parent / ".prismic-documents.json")
        else:
            # resolve ids and urls from the cache so the preview matches what a
            # publish would send, without touching the network
            cached = (json.loads(cache_path.read_text())
                      if cache_path.exists() else {})
            for b in blocks:
                entry = cached.get(b.get("_src", "")) if b.get("type") == "image" else None
                if entry:
                    b["id"], b["_url"] = entry["id"], entry.get("url")
                    b["copyright"] = None
                    b["dimensions"] = {"width": entry["width"], "height": entry["height"]}
                b.pop("_src", None)
            pending = sum(1 for b in blocks
                          if b.get("type") == "image" and not b.get("id"))
            out = path.with_suffix(".prismic.json")
            out.write_text(json.dumps(
                build_data(blocks, meta, title, uid), indent=2))
            note = (f"; {pending} image block(s) still need asset ids, "
                    f"which --publish fills in") if pending else ""
            print(f"    wrote {out.name}{note}")


if __name__ == "__main__":
    main()
