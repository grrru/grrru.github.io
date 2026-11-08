"""Validate Hugo's canonical sitemap and RSS search exclusions."""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def validate_sitemaps(publish_dir: Path) -> None:
    source = (publish_dir / "sitemap.xml").read_bytes()
    root = ET.fromstring(source)
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    if root.tag != f"{namespace}urlset":
        raise ValueError("Expected a URL sitemap, not a sitemap index")

    urls = [
        entry.findtext(f"{namespace}loc", "").strip()
        for entry in root.findall(f"{namespace}url")
    ]
    if not urls or any(not url for url in urls):
        raise ValueError("The sitemap must contain non-empty URLs")

    feed_path = publish_dir / "index.xml"
    if feed_path.is_file():
        feed_urls = {
            item.findtext("link", "").strip()
            for item in ET.parse(feed_path).findall("channel/item")
        }
        excluded = sorted(feed_urls - set(urls))
        if excluded:
            raise ValueError(f"RSS includes URLs excluded from the sitemap: {excluded}")

    print(f"Validated {len(urls)} sitemap URLs and RSS search exclusions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("publish_dir", type=Path, nargs="?", default=Path("public"))
    validate_sitemaps(parser.parse_args().publish_dir)
