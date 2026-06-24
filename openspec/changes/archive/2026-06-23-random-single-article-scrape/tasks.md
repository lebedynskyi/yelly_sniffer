## 1. Selection logic

- [x] 1.1 Implement `_pick_one_article(sites, store, rng=None) -> tuple[SiteHandlers, ArticleMeta] | None` in `src/scraper/pipeline.py`: shuffle a copy of `sites`, for each site fetch listing + `parse_metas`, shuffle a copy of the metas, return the first `(site, meta)` not already in `store` (`store.exists(meta_title=..., original_url=...)`)
- [x] 1.2 Default `rng` to the `random` module's `shuffle` when `None`; accept a `random.Random` instance otherwise
- [x] 1.3 Return `None` when every site's shuffled metas are all already in the store

## 2. Single-article processing

- [x] 2.1 Extract the existing fetch-article/parse/sanitize/fix/save body (currently the inner loop of `_scrape_sites`) into a function that takes one `(site, meta)` pair and performs the save, reusing it unchanged from current behavior
- [x] 2.2 Wire `run_pipeline`: when `do_scrape` is true, call `_pick_one_article`; if it returns a pair, call the single-article processor once; if `None`, log at info level and continue
- [x] 2.3 Remove the old `_scrape_sites` loop-over-everything function

## 3. Tests

- [x] 3.1 Update existing `tests/test_pipeline.py` single-site tests to confirm they still pass against the new selection + single-process flow (no shuffle ambiguity with one site/one article)
- [x] 3.2 Add a test with multiple sites, all having new articles, using a seeded `random.Random` passed into `_pick_one_article` (or patched into `run_pipeline`), asserting exactly one article gets saved and the rest are untouched
- [x] 3.3 Add a test where the first shuffled site has only already-stored articles, asserting the picker moves on to the next site
- [x] 3.4 Add a test where every site/article is already stored, asserting `_pick_one_article` returns `None` and `run_pipeline` does not error and does not call fetch/parse/sanitize/fix on any article
- [x] 3.5 Add a test asserting the original `sites` list and a site's parsed `metas` list are not mutated (order preserved) after selection runs

## 4. Verification

- [x] 4.1 Run `pytest tests/test_pipeline.py -v` and confirm all pass
- [x] 4.2 Run full `pytest` suite to confirm no regressions in other modules
