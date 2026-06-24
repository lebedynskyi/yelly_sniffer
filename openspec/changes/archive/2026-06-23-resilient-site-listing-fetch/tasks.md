## 1. Error isolation in selection

- [x] 1.1 In `_pick_one_article` (`src/scraper/pipeline.py`), wrap the `site.fetcher.fetch(site.url)` + `site.parser.parse_metas(listing_html)` pair in a try/except `Exception`
- [x] 1.2 On exception: `logger.warning("Skipping site %s: %s", site.name, e)` — no traceback — then `time.sleep(1)`, then `continue` to the next shuffled site
- [x] 1.3 Import `time` in `pipeline.py`
- [x] 1.4 Confirm the existing "all sites exhausted -> return None" path still works when failures (not just empty listings) account for some/all sites

## 2. Tests

- [x] 2.1 Add a test where one site's `fetcher.fetch` raises and a second (healthy) site has a new article — assert the healthy site's article is picked, the failing site's `parse_article`/processing is never invoked, and no exception propagates out of `run_pipeline`/`_pick_one_article`
- [x] 2.2 Add a test where one site's `parser.parse_metas` raises (fetch succeeds) — same assertions as 2.1
- [x] 2.3 Add a test where every site raises — assert `_pick_one_article` returns `None` without raising
- [x] 2.4 Add a test asserting the failure log call uses `logger.warning` (not `logger.exception`) — e.g. via `caplog` or mocking `scraper.pipeline.logger` — confirming no traceback is attached
- [x] 2.5 Mock/patch `time.sleep` in the new tests (e.g. `mocker.patch("scraper.pipeline.time.sleep")`) so tests don't actually wait 1s per failure

## 3. Verification

- [x] 3.1 Run `pytest tests/test_pipeline.py -v` and confirm all pass
- [x] 3.2 Run full `pytest` suite to confirm no regressions in other modules
