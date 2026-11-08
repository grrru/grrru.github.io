from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from export_sitemaps import export_sitemaps


class ExportSitemapsTest(unittest.TestCase):
    def test_exports_identical_xml_and_decoded_urls_as_utf8_text(self):
        source = b'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/search/?a=1&amp;b=2</loc></url>
</urlset>
'''
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "sitemap.xml").write_bytes(source)

            export_sitemaps(output)

            self.assertEqual((output / "sitemap-pages.xml").read_bytes(), source)
            self.assertEqual(
                (output / "sitemap.txt").read_text(encoding="utf-8"),
                "https://example.com/\nhttps://example.com/search/?a=1&b=2\n",
            )
            self.assertEqual((output / "sitemap.xml").read_bytes(), source)

    def test_rejects_unusable_sources_before_writing_alternatives(self):
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
                    export_sitemaps(output)

                self.assertFalse((output / "sitemap-pages.xml").exists())
                self.assertFalse((output / "sitemap.txt").exists())


if __name__ == "__main__":
    unittest.main()
