import json
import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "sections.json"
USER_AGENT = "PrasiddhBharatAutomation/1.0 (+https://www.prasiddhbharat.com/)"
TIMEOUT = 25

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def read_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def stable_id(url, title):
    raw = (url or title).strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def fetch_feed(source):
    url = source.get("feed_url")
    if not url:
        return []
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        logging.warning("Skipping non-HTTPS or invalid feed URL: %s", url)
        return []

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    items = []

    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link or not link.startswith("https://"):
            continue

        published = entry.get("published") or entry.get("updated") or ""
        items.append({
            "id": stable_id(link, title),
            "title": title,
            "source_name": source.get("name", parsed.netloc),
            "source_url": url,
            "url": link,
            "published": published,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "language": "hi",
        })
    return items


def run_section(section):
    source_path = ROOT / section["sources_file"]
    output_path = ROOT / section["data_file"]
    source_config = read_json(source_path, {"sources": []})
    existing = read_json(output_path, {"items": []})
    known = {item.get("id") for item in existing.get("items", [])}
    collected = []

    for source in source_config.get("sources", []):
        if not source.get("enabled", True):
            continue
        try:
            found = fetch_feed(source)
            collected.extend(found)
            logging.info("%s: fetched %d items from %s",
                         section["id"], len(found), source.get("name", source.get("feed_url")))
        except Exception as exc:
            logging.exception("Source failed in %s: %s", section["id"], exc)

    merged = {}
    for item in collected + existing.get("items", []):
        merged[item["id"]] = item

    ordered = sorted(
        merged.values(),
        key=lambda x: (x.get("published") or x.get("collected_at") or ""),
        reverse=True,
    )
    write_json(output_path, {
        "section": section["id"],
        "name": section["name"],
        "language": "hi",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": ordered,
    })
    new_count = sum(1 for item in collected if item["id"] not in known)
    logging.info("%s: %d new items; %d total stored",
                 section["id"], new_count, len(ordered))


def main():
    config = read_json(CONFIG_FILE, {"sections": []})
    only_section = os.getenv("SECTION_ID")
    for section in config.get("sections", []):
        if not section.get("enabled", False):
            continue
        if only_section and section["id"] != only_section:
            continue
        run_section(section)


if __name__ == "__main__":
    main()
