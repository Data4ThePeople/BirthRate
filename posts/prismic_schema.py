"""Build the JSON-LD that goes in a blog_post's `schema` field.

Modeled on what the existing posts carry, so search engines see the same
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

    # An analysis post and the data page it draws on target overlapping
    # queries, so say which is which rather than leaving a search engine to
    # guess. isBasedOn points the article at the dataset it is built from,
    # which is the precise relation and keeps the data page as the canonical
    # answer for "fertility rate by county".
    site_for_ref = _setting("SITE", SITE)
    if meta.get("based_on"):
        ref = meta["based_on"].strip()
        url = ref if ref.startswith("http") else f"{site_for_ref}{POST_PATH}{ref}"
        based = {"@type": "Dataset", "@id": f"{url}#dataset", "url": url}
        if meta.get("based_on_name"):
            based["name"] = meta["based_on_name"]
        schema["isBasedOn"] = based

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


def build_dataset_graph(meta: dict, uid: str, title: str, description: str,
                        image_url: str | None, faqs: list[tuple[str, str]]) -> str:
    """A @graph for a data page: Dataset, WebPage, FAQPage, Breadcrumb.

    An interactive data page is a poor Article and an excellent Dataset. The
    Dataset type is what Google Dataset Search indexes, and it is the one
    structured-data lever a page like this has that a news article does not.
    Any FAQ section in the post becomes FAQPage entries.
    """
    site = _setting("SITE", SITE)
    url = meta.get("canonical", f"{site}{POST_PATH}{uid}")
    date = meta.get("date", "")
    stamp = f"{date}T{meta.get('time', DEFAULT_TIME)}" if date else ""
    keywords = [k.strip() for k in meta.get("keywords", "").split(",") if k.strip()]

    publisher = {"@type": "Organization", "name": _setting("PUBLISHER", PUBLISHER),
                 "url": _setting("PUBLISHER_URL", PUBLISHER_URL)}
    author = {"@type": "Person",
              "name": meta.get("author", _setting("AUTHOR", AUTHOR)),
              "url": meta.get("author_url", site + AUTHOR_PATH)}

    dataset = {
        "@type": "Dataset",
        "@id": f"{url}#dataset",
        "name": meta.get("dataset_name", title),
        "description": meta.get("dataset_description", description),
        "url": url,
        "license": meta.get("license", "https://creativecommons.org/licenses/by/4.0/"),
        "isAccessibleForFree": True,
        "creator": author,
        "publisher": publisher,
        "inLanguage": LANG,
    }
    if keywords:
        dataset["keywords"] = keywords
    if stamp:
        dataset["datePublished"] = stamp
        dataset["dateModified"] = stamp
    if meta.get("temporal"):
        dataset["temporalCoverage"] = meta["temporal"]
    if meta.get("spatial"):
        dataset["spatialCoverage"] = {"@type": "Place", "name": meta["spatial"]}
    if meta.get("measured"):
        name, _, unit = meta["measured"].partition("|")
        dataset["variableMeasured"] = {
            "@type": "PropertyValue", "name": name.strip(),
            "unitText": unit.strip() or None}
        dataset["variableMeasured"] = {
            k: v for k, v in dataset["variableMeasured"].items() if v}
    if meta.get("sources"):
        dataset["isBasedOn"] = [s.strip() for s in meta["sources"].split("|") if s.strip()]

    part_of = [{"@type": "WebSite", "name": _setting("PUBLISHER", PUBLISHER),
                "url": site}]
    if meta.get("series"):
        series = {"@type": "CreativeWorkSeries", "name": meta["series"]}
        # build_schema honours position on the Article; a data page in the same
        # series has to declare its place the same way, or the front matter
        # silently does nothing here.
        if meta.get("position"):
            series["position"] = int(meta["position"])
        part_of.append(series)

    webpage = {
        "@type": "WebPage",
        "@id": url,
        "url": url,
        "name": meta.get("meta_title", title),
        "description": description,
        "isPartOf": part_of if len(part_of) > 1 else part_of[0],
        "about": {"@id": f"{url}#dataset"},
        "inLanguage": LANG,
    }
    if image_url:
        webpage["primaryImageOfPage"] = {"@type": "ImageObject", "url": image_url}
        dataset["image"] = image_url
    if stamp:
        webpage["datePublished"] = stamp
        webpage["dateModified"] = stamp

    graph = [dataset, webpage]
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs],
        })
    graph.append({
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": site},
            {"@type": "ListItem", "position": 2, "name": title, "item": url},
        ],
    })
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      indent=2, ensure_ascii=False)
