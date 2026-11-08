# Sitemaps

Hugo's generated `public/sitemap.xml` is the source of truth. After every
production build, `tools/export_sitemaps.py` exports two equivalent alternatives:

- `/sitemap-pages.xml`: an exact byte copy, to test a different XML URL.
- `/sitemap.txt`: the same URLs in UTF-8, one per line, to test Google's text format.

Both formats are supported by [Google's sitemap documentation](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
The alternatives are generated on every deployment so content updates cannot
leave manually copied URL lists behind.

Run the export tests with:

```sh
python3 -m unittest discover -s tools -p 'test_*.py'
```

After a local Hugo build, run `python3 tools/export_sitemaps.py public` to
reproduce the deployment output.

`layouts/robots.txt` advertises the original XML and text sitemap so crawlers
can discover both without relying on a manual Search Console submission.

The alternate URLs were introduced to diagnose Search Console's persistent
fetch failure. A successful live URL test is not proof that the scheduled
sitemap processor has accepted a file; check the Sitemaps report separately.
