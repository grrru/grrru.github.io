from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from validate_sitemaps import validate_sitemaps


class ValidateSitemapsTest(unittest.TestCase):
    def test_validates_without_creating_alternative_files(self):
        source = b'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/search/?a=1&amp;b=2</loc></url>
</urlset>
'''
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "sitemap.xml").write_bytes(source)
            (output / "index.xml").write_text(
                '<rss version="2.0"><channel><item>'
                '<link>https://example.com/</link>'
                '</item></channel></rss>',
                encoding="utf-8",
            )

            validate_sitemaps(output)

            self.assertFalse((output / "sitemap-pages.xml").exists())
            self.assertFalse((output / "sitemap.txt").exists())
            self.assertEqual((output / "sitemap.xml").read_bytes(), source)

    def test_rejects_unusable_sitemaps(self):
        sources = [
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url/></urlset>',
        ]
        for source in sources:
            with self.subTest(source=source), TemporaryDirectory() as directory:
                output = Path(directory)
                (output / "sitemap.xml").write_text(source, encoding="utf-8")

                with self.assertRaises(ValueError):
                    validate_sitemaps(output)

                self.assertFalse((output / "sitemap-pages.xml").exists())
                self.assertFalse((output / "sitemap.txt").exists())

    def test_rejects_rss_urls_excluded_from_the_sitemap(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "sitemap.xml").write_text(
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://example.com/</loc></url></urlset>',
                encoding="utf-8",
            )
            (output / "index.xml").write_text(
                '<rss version="2.0"><channel><item>'
                '<link>https://example.com/about/</link>'
                '</item></channel></rss>',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "RSS"):
                validate_sitemaps(output)


if __name__ == "__main__":
    unittest.main()
