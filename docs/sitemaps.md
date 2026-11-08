# Sitemap

Hugo generates the site's only submitted sitemap at
`https://grrru.github.io/sitemap.xml`. `layouts/robots.txt` advertises this URL.
Submit only this sitemap in the Search Console property
`https://grrru.github.io/`.

The experimental `/sitemap-pages.xml` and `/sitemap.txt` files are no longer
generated. `/index.xml` remains available as the blog's RSS feed, but is not
submitted as another sitemap.

The RSS template excludes pages marked `robotsNoIndex`.
`tools/validate_sitemaps.py` checks that the canonical sitemap contains non-empty
URLs and that every RSS article is included in it. Validation does not create
additional sitemap files. CI runs the tests before building and validates the
generated output before deployment:

```sh
python3 -m unittest discover -s tools -p 'test_*.py'
hugo --gc --minify
python3 tools/validate_sitemaps.py public
```

The alternatives were introduced on 2026-11-08 to investigate Search Console's
fetch failure. All four submitted formats failed there, while public HTTP
requests and Google's live URL test succeeded. Removing the alternatives and
resubmitting the canonical URL simplifies the configuration; it does not by
itself establish the cause or resolution of that failure. Check the Sitemaps
report for a successful read separately from submission acceptance.
