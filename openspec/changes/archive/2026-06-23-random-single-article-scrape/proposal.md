## Why

Current `_scrape_sites` drains every site's listing and processes every new article on every run, every site, every time. This makes runs unbounded in cost/time as content grows and gives no control over throughput. We want one article processed per run, picked fairly at random across sites, so load is predictable and content is spread evenly rather than front-loaded by site order in `config.yaml`.

## What Changes

- `_scrape_sites` (`src/scraper/pipeline.py`) replaced by a selection step + a single-article process step:
  - **BREAKING**: scraping no longer processes all new articles across all sites in one run — only one article is saved per invocation with `--scrape`.
  - New `_pick_one_article(sites, store, rng=None)`: shuffles sites, for each site fetches its listing, shuffles parsed article metas, returns the first `(site, meta)` pair not already in `store`. Moves to the next shuffled site if the current one has nothing new. Returns `None` if every site is exhausted.
  - Process step keeps the existing fetch-article -> parse -> sanitize -> fix -> save logic, now called once with the picked `(site, meta)` instead of looping.
  - `run_pipeline` calls pick-then-process once when `do_scrape` is true; logs and returns cleanly (no error) when nothing new is found anywhere.
  - Randomness is injectable (`random.Random` instance, defaults to the `random` module) so site/article selection can be seeded in tests.

## Capabilities

### New Capabilities
(none — this modifies existing scraping orchestration, no new capability domain)

### Modified Capabilities
- `scraping-pipeline`: requirement changes from "process all new articles across all configured sites per run" to "process exactly one new article per run, chosen via random site-then-article selection, skipping sites/articles already in the store."

## Impact

- `src/scraper/pipeline.py`: `_scrape_sites` replaced by `_pick_one_article` + single-process call inside `run_pipeline`.
- `tests/test_pipeline.py`: existing single-site/single-article tests still pass unchanged in shape; new tests needed for multi-site shuffle behavior using a seeded `random.Random`.
- No change to `fetching`, `parsing`, `sanitizer`, `fixing`, `publishing`, or `post_tracking` modules — only orchestration in `pipeline.py` changes.
- Cron/CLI invocation unaffected (`--scrape` flag semantics unchanged, just does less work per call).
