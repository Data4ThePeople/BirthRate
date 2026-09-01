"""Turn parsed Markdown blocks into the slice structure a blog_post expects.

The blog_post type has no single Rich Text body. Its content is a slice zone,
so an import has to emit slices rather than a flat field. Learned from the
live repository:

    paragarph_text            primary.paragraph_text   Rich Text  (the body;
                              carries paragraph, heading1-3, list-item,
                              o-list-item - note Prismic's own spelling)
    spacer                    primary.spacer_value     e.g. "20px"
    highlited_page_blurb      primary.title            Text  (optional)
                              primary.content          Rich Text
    blog_body_content_image   primary.image            Image
                              primary.source_text      Rich Text  (caption)
    html_embed / fullWidth    primary.html_content     Rich Text with one
                                                       preformatted block of
                                                       raw HTML
                              primary.embed_height     e.g. "1200px"

Rich Text blocks in this repository carry a `direction` key alongside type,
text and spans, so they are written that way here too.
"""
from __future__ import annotations

TEXT_BLOCKS = {"paragraph", "heading1", "heading2", "heading3", "heading4",
               "heading5", "heading6", "list-item", "o-list-item", "preformatted"}
HEADINGS = {"heading1", "heading2", "heading3", "heading4", "heading5", "heading6"}

# Sections read better with air above their heading. A break closes the current
# text slice, drops a spacer, and opens a new one - but not against an image,
# which brings its own margin.
SECTION_GAP = "20px"


def _rt(blocks: list[dict]) -> list[dict]:
    """Rich Text as this repository stores it."""
    return [{"type": b["type"], "text": b.get("text", ""),
             "spans": b.get("spans", []), "direction": "ltr"} for b in blocks]


def _slice(slice_type: str, primary: dict, variation: str = "default") -> dict:
    return {"slice_type": slice_type, "slice_label": None,
            "variation": variation, "version": "initial",
            "items": [], "primary": primary}


def to_slices(blocks: list[dict]) -> list[dict]:
    """Group flat Markdown blocks into slices.

    Runs of text become paragarph_text slices, broken at each section heading
    with a spacer between, and wherever an image, embed or blurb interrupts.
    """
    slices: list[dict] = []
    run: list[dict] = []

    def flush() -> None:
        if run:
            slices.append(_slice("paragarph_text", {"paragraph_text": _rt(run)}))
            run.clear()

    def gap() -> None:
        """A spacer, unless one is already there or an image sits alongside."""
        if not slices:
            return
        if slices[-1]["slice_type"] in ("spacer", "blog_body_content_image",
                                        "html_embed"):
            return
        slices.append(_slice("spacer", {"spacer_value": SECTION_GAP}))

    i = 0
    while i < len(blocks):
        block = blocks[i]
        kind = block.get("type")

        if kind == "image":
            flush()
            caption: list[dict] = []
            # an italic line straight after an image is its caption, and belongs
            # in the image slice rather than floating as its own paragraph
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            if (nxt and nxt.get("type") == "paragraph"
                    and len(nxt.get("spans", [])) == 1
                    and nxt["spans"][0]["type"] == "em"
                    and nxt["spans"][0]["start"] == 0
                    and nxt["spans"][0]["end"] == len(nxt["text"])):
                caption = _rt([{**nxt, "spans": []}])
                i += 1
            image = {k: block[k] for k in ("id", "alt", "copyright", "dimensions")
                     if k in block}
            image.setdefault("copyright", None)
            slices.append(_slice("blog_body_content_image",
                                 {"image": image, "source_text": caption}))
        elif kind == "embed":
            flush()
            html = block.get("html", "")
            content = _rt([{"type": "preformatted", "text": html, "spans": []}]) if html else []
            slices.append(_slice(
                "html_embed",
                {"html_content": content,
                 "embed_height": block.get("height", "760px")},
                variation="fullWidth"))
        elif kind == "blurb":
            flush()
            gap()
            primary = {"content": _rt(block["blocks"])}
            variation = "noTitle" if not block.get("title") else "default"
            if block.get("title"):
                primary = {"title": block["title"], **primary}
            if block.get("full"):
                variation = ("noTitleFullWidth" if variation == "noTitle"
                             else "defaultFullWidth")
            slices.append(_slice("highlited_page_blurb", primary, variation))
        elif kind in HEADINGS and run:
            # a heading that opens a new section, rather than the first block
            flush()
            gap()
            run.append(block)
        elif kind in TEXT_BLOCKS:
            run.append(block)
        i += 1

    flush()
    return slices
