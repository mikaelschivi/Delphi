from datetime import datetime, timezone

from delphi_backend.models import NewsItem
from delphi_backend.news_parser import deduplicate, parse_feed, strip_html

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Bitcoin tops $100k</title>
    <link>https://example.com/a</link>
    <pubDate>Mon, 24 Aug 2026 13:30:00 +0000</pubDate>
    <description>&lt;p&gt;BTC rallied &amp;amp; held.&lt;/p&gt;</description>
  </item>
  <item>
    <title>Wallet flaw patched</title>
    <link>https://example.com/b</link>
    <pubDate>Mon, 24 Aug 2026 12:00:00 +0000</pubDate>
    <description>No coin named in the headline.</description>
  </item>
</channel></rss>"""


def test_parse_feed_extracts_and_cleans_items():
    items = parse_feed(FEED, "Example")

    assert len(items) == 2
    item = items[0]
    assert item.title == "Bitcoin tops $100k"
    assert item.url == "https://example.com/a"
    assert item.source == "Example"
    assert item.summary == "BTC rallied & held."
    assert item.published_at == datetime(2026, 8, 24, 13, 30, tzinfo=timezone.utc)


def test_parse_feed_keeps_items_the_source_tagged_bitcoin():
    assert [item.title for item in parse_feed(FEED, "Example")][1] == "Wallet flaw patched"


def test_parse_feed_skips_items_missing_title_or_link():
    feed = """<rss><channel>
      <item><title>Only a title</title></item>
      <item><link>https://example.com/c</link></item>
      <item><title>Complete</title><link>https://example.com/d</link></item>
    </channel></rss>"""

    assert [item.url for item in parse_feed(feed, "Example")] == ["https://example.com/d"]


def test_parse_feed_rejects_non_http_links():
    feed = """<rss><channel><item>
      <title>Suspicious</title><link>javascript:alert(1)</link>
    </item></channel></rss>"""

    assert parse_feed(feed, "Example") == []


def test_parse_feed_survives_malformed_xml():
    assert parse_feed("<rss><channel><item>truncated", "Example") == []


def test_parse_feed_handles_namespaced_feeds():
    feed = """<rss xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel><item>
        <title>Bitcoin moves</title>
        <link>https://example.com/e</link>
        <content:encoded>ignored</content:encoded>
      </item></channel></rss>"""

    assert [item.title for item in parse_feed(feed, "Example")] == ["Bitcoin moves"]


def test_parse_feed_tolerates_missing_or_bad_pubdate():
    feed = """<rss><channel>
      <item><title>A</title><link>https://example.com/f</link></item>
      <item><title>B</title><link>https://example.com/g</link>
        <pubDate>not a date</pubDate></item>
    </channel></rss>"""

    assert [item.published_at for item in parse_feed(feed, "Example")] == [None, None]


def test_strip_html_removes_tags_and_decodes_entities():
    assert strip_html("<p>a &amp; <b>b</b></p>") == "a & b"


def test_deduplicate_drops_repeat_urls():
    def item(url, title):
        return NewsItem(url=url, title=title, source="s", summary=None, published_at=None)

    unique = deduplicate([
        item("https://a", "Story"),
        item("https://a", "Story republished"),
        item("https://b", "Other"),
    ])

    assert [i.url for i in unique] == ["https://a", "https://b"]
