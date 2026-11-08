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

The existing `/index.xml` RSS feed is also a supported submission format. Its
template excludes pages marked `robotsNoIndex`, and the export step checks
that every feed URL is present in the sitemap. This prevents a page deliberately
excluded from search, such as an unfinished About page, from leaking into the
RSS sitemap.

The alternate URLs were introduced to diagnose Search Console's persistent
fetch failure. A successful live URL test is not proof that the scheduled
sitemap processor has accepted a file; check the Sitemaps report separately.

## Repair checks on 2026-11-08

The original XML, identical XML alias, and text sitemap returned HTTP 200 and
contained the same 41 URLs. Google's live URL test fetched the text sitemap
successfully. Search Console also reported fetching the updated 114-byte
robots.txt. Recrawl/indexing requests for the homepage and latest Go article
were accepted into the priority queue.

The initial Sitemaps report still showed fetch failure for the original XML,
alternate XML, text file, and existing RSS feed. Submission acceptance and
these local fixes do not yet establish that Google's scheduled sitemap
processing has recovered. Keep the URLs stable and check their processing
status before attributing the failure to a filename, XML format, or theme.
