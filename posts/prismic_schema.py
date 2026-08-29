"""Build the JSON-LD that goes in a blog_post's `schema` field.

Modelled on what the existing posts carry, so search engines see the same
shape across the site: an Article with headline, description, hero image,
dates, keywords, author, publisher and a canonical URL.

Everything site-specific has a default here and can be overridden per post
from the Markdown front matter, or globally from the environment.
"""
from __future__ import annotations

import json
import os

SITE = "https://www.data4thepeople.com"
POST_PATH = "/p/"                      # canonical URL is SITE + POST_PATH + uid
PUBLISHER = "Data 4 The People"
PUBLISHER_URL = "https://data4thepeople.com"
AUTHOR = "Eric Pachman"
AUTHOR_PATH = "/authors/eric-pachman"
DEFAULT_TIME = "07:00:00-04:00"
DEFAULT_SECTION = "Analysis"
LANG = "en-US"


def _setting(name: str, fallback: str) -> str:
    return os.environ.get(f"PRISMIC_{name}", fallback)


def build_schema(meta: dict, uid: str, title: str, description: str,
                 image_url: str | None) -> str:
    """JSON-LD for one post, as a string - the field stores text."""
    date = meta.get("date", "")
    stamp = f"{date}T{meta.get('time', DEFAULT_TIME)}" if date else ""

    schema: dict = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
    }
    if image_url:
        schema["image"] = image_url
    if stamp:
        schema["datePublished"] = stamp
        schema["dateModified"] = (
            f"{meta['updated']}T{meta.get('time', DEFAULT_TIME)}"
            if meta.get("updated") else stamp)

    schema["articleSection"] = meta.get("section", DEFAULT_SECTION)
    if meta.get("series"):
        schema["isPartOf"] = {"@type": "CreativeWorkSeries",
                              "name": meta["series"]}
        if meta.get("position"):
            schema["position"] = int(meta["position"])

    schema["inLanguage"] = LANG
    schema["isAccessibleForFree"] = True

    keywords = [k.strip() for k in meta.get("keywords", "").split(",") if k.strip()]
    if keywords:
        schema["keywords"] = keywords

    site = _setting("SITE", SITE)
    schema["author"] = {
        "@type": "Person",
        "name": meta.get("author", _setting("AUTHOR", AUTHOR)),
        "url": meta.get("author_url", site + AUTHOR_PATH),
    }
    schema["publisher"] = {
        "@type": "Organization",
        "name": _setting("PUBLISHER", PUBLISHER),
        "url": _setting("PUBLISHER_URL", PUBLISHER_URL),
    }
    schema["mainEntityOfPage"] = {
        "@type": "WebPage",
        "@id": meta.get("canonical", f"{site}{POST_PATH}{uid}"),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False)
