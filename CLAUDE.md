# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
source .venv/bin/activate

pytest                              # run all tests
pytest tests/test_pipeline.py       # single file
pytest tests/test_pipeline.py::test_some_case -v   # single test

python -m scraper.cli --help
python -m scraper.cli run --scrape --xmlrpc --facebook   # actual run, flags are independently togglable

python -m playwright install --with-deps chromium   # needed once for dzen (playwright fetcher)
```

Dependency updates: edit `requirements.in` / `requirements-dev.in` only, never hand-edit the generated `requirements.txt` / `requirements-dev.txt`. Then:
```bash
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt
pip install -r requirements.txt -r requirements-dev.txt
```

Cron invokes `.venv/bin/python` by absolute path (cron env has no shell sourcing); secrets load from `.env` via `python-dotenv` inside the app, not the shell.

## Architecture

Pipeline: fetch listing -> parse article metas -> skip if already in store -> fetch article -> parse -> sanitize -> AI-fix -> save to sqlite -> (separately) publish pending to WordPress/Facebook.

`pipeline.run_pipeline` (`src/scraper/pipeline.py`) is the orchestrator, driven by three independent boolean flags (`--scrape`, `--xmlrpc`, `--facebook`) — any combination can run in a single invocation, and they don't depend on each other within one process (publishing reads whatever's already in the DB, not what scrape just produced).

Each stage is an ABC with a factory that picks the concrete implementation from config/env, so adding a new site/fetcher/AI-provider means adding a class + one registry entry, not touching the pipeline:

- **Fetching** (`fetching/__init__.py`): `Fetcher` ABC, `RequestsFetcher` vs `PlaywrightFetcher`. Picked per-site via `config.yaml`'s `sites[].fetcher`. Playwright is for JS-rendered sites (currently only `dzen`).
- **Parsing** (`parsing/__init__.py`, `parsing/sites/*.py`): `Parser` ABC with `parse_metas` (listing page -> `ArticleMeta` list) and `parse_article` (article page -> `Article`). One parser class per site, looked up by site name in `get_parser`'s registry — this is where site-specific HTML scraping/quirks live. `parsing/canonical.py` has a shared helper for extracting canonical URLs from `og:url`/`<link rel=canonical>`.
- **Sanitizing** (`sanitizer.py`): `Bs4HtmlSanitizer` strips disallowed tags (bleach allowlist), drops CTA/spam lines (regex patterns for Russian-language "like/subscribe/comment" boilerplate, plus all-caps shouty lines), and removes now-empty block tags after stripping. Runs before the AI fixer.
- **Fixing** (`fixing/__init__.py`): `ContentFixer` ABC; `get_fixer` picks `OpenAIFixer`/`GeminiFixer`/`OllamaFixer` based on `AISettings.provider` (env `AI_PROVIDER`). This is an LLM pass to clean up/rewrite sanitized article HTML before storage.
- **Publishing** (`publishing/wordpress.py`, `publishing/facebook.py`): each module pairs a publisher class (raw API call) with its own `publish_pending(store, publisher)` function — pulls one unpublished article (`store.find_unpublished(target)`), publishes, marks it published. Only one article per run per target; failures are logged and swallowed so one bad article doesn't block the cron loop. WordPress posts are created as drafts, not auto-published live.

**Storage** (`post_tracking.py`): single-table sqlite (`articles`), with `wordpress_published`/`facebook_published` as independent flags on the same row — an article is scraped once but tracked separately per publish target. Dedup on scrape is by `meta_title` OR `original_url` (`ArticleStore.exists`).

**Settings** (`settings.py`): `AISettings` (pydantic) validates that the API key for the selected `AI_PROVIDER` is present at construction time — fails fast rather than at first AI call.

**Config split**: `config.yaml` holds non-secret site/db config; secrets (WP credentials, FB token, AI keys) come from `.env` / environment only, never from `config.yaml`.

Site name strings (`config.yaml` `sites[].name`, e.g. `happytimes`, `dzen`, `storyx`) are the join key between config and the parser registry in `get_parser` — adding a site means adding both.
