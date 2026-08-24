import html
import re
import xml.etree.ElementTree as ElementTree
from datetime import timezone
from email.utils import parsedate_to_datetime

from .models import NewsItem

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
SUMMARY_MAX_CHARS = 400


def _text_of(item: ElementTree.Element, tag: str) -> str | None:
    for child in item:
        if child.tag.split("}")[-1] == tag and child.text:
            return child.text
    return None


def strip_html(raw: str) -> str:
    without_tags = _TAG_RE.sub(" ", raw)
    return _WHITESPACE_RE.sub(" ", html.unescape(without_tags)).strip()


def _parse_published(raw: str | None):
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_feed(xml_text: str, source: str) -> list[NewsItem]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []

    items: list[NewsItem] = []
    for element in root.iter():
        if element.tag.split("}")[-1] != "item":
            continue

        title = _text_of(element, "title")
        link = _text_of(element, "link")
        if not title or not link:
            continue

        title = strip_html(title)
        link = link.strip()
        if not title or not link.startswith(("http://", "https://")):
            continue

        raw_summary = _text_of(element, "description")
        summary = strip_html(raw_summary) if raw_summary else None
        if summary:
            summary = summary[:SUMMARY_MAX_CHARS].strip() or None

        items.append(
            NewsItem(
                url=link,
                title=title,
                source=source,
                summary=summary,
                published_at=_parse_published(_text_of(element, "pubDate")),
            )
        )
    return items


def deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    seen_urls: set[str] = set()
    unique: list[NewsItem] = []
    for item in items:
        if item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        unique.append(item)
    return unique
