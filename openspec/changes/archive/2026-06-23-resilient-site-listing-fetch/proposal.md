## Why

`_pick_one_article`'s site-selection walk (`src/scraper/pipeline.py`) has no error handling around fetching/parsing a site's listing page. A single site being down, timing out, or returning malformed HTML currently crashes the whole run with an uncaught exception and traceback — no article gets picked, no other site gets a chance, and the cron invocation fails noisily. We want a flaky/broken site to be skipped cleanly so the run still has a chance to pick an article from a healthy site.

## What Changes

- `_pick_one_article` (`src/scraper/pipeline.py`) wraps the per-site listing fetch + `parse_metas` call in a try/except: on any exception, log one clean warning line (no full traceback) naming the site and the error, sleep 1 second, then continue to the next shuffled site.
- Behavior is unchanged for sites whose listing fetch/parse succeeds.
- If every site in the shuffle fails, the function still returns `None` (same as the existing "all exhausted" case) after the per-failure delays.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `scraping-pipeline`: site selection now tolerates a single site's listing fetch/parse failure by skipping that site (with a clean one-line warning log and a 1s delay) instead of letting the exception propagate and abort the entire run.

## Impact

- `src/scraper/pipeline.py`: `_pick_one_article` gains a try/except around `site.fetcher.fetch(site.url)` + `site.parser.parse_metas(...)`, plus a `time.sleep(1)` on failure.
- `tests/test_pipeline.py`: new test(s) for a site whose listing fetch/parse raises, asserting the run still picks an article from a later healthy site, and that the failure is logged without crashing.
- No change to `_process_article`, publishing modules, or `ArticleStore` — scope is limited to the site-selection loop.
