## Context

`_pick_one_article` (`src/scraper/pipeline.py`) shuffles configured sites and, for each, fetches the listing page and parses article metas before deciding whether to move to the next site. Today that fetch+parse call is unguarded — any exception (network timeout, HTTP error, malformed HTML the parser can't handle) propagates straight out of `_pick_one_article`, out of `run_pipeline`, and crashes the whole CLI invocation. This is a single, narrowly-scoped fix confirmed via `/opsx:explore`: wrap that one call site in a try/except.

## Goals / Non-Goals

**Goals:**
- A site whose listing fetch or `parse_metas` call raises is skipped, not fatal to the run.
- The failure is logged as a single clean line (site name + error), not a full traceback — keeps cron logs scannable when a site is flaky.
- A fixed 1s delay after a failure, before evaluating the next shuffled site, regardless of whether more sites remain.
- Selection still returns `None` (today's existing "all exhausted" behavior) if every site fails or has nothing new.

**Non-Goals:**
- No retry of the same site within this run (single attempt per site per run, consistent with current selection semantics).
- No change to `_process_article`'s error handling — a chosen article's own fetch/parse/sanitize/fix/save failures are out of scope for this change (that's option B from the earlier exploration, not what was approved).
- No backoff/circuit-breaker state persisted across runs for chronically-failing sites — plain per-run skip is sufficient for now.

## Decisions

**1. `logger.warning` (one line, exception message only) instead of `logger.exception` (full traceback).**
Confirmed with user: "pretty clean logs" means scannable one-liners, not stack traces, even though `publish_pending` (`publishing/wordpress.py`) uses `logger.exception` for its failure path. This is an intentional deviation for this call site, not a house-style change elsewhere.

**2. `time.sleep(1)` always runs on failure, even for the last site in the shuffled order.**
Confirmed with user: simpler code (no "is this the last site" check) outweighs the minor cost of an unnecessary 1s sleep right before returning `None` on full exhaustion.

**3. Catch `Exception` broadly around the combined `fetch` + `parse_metas` call, not narrower exception types.**
Fetchers (`requests`/`playwright`) and parsers can each raise different exception types (network errors, HTML parsing errors, site-specific parser bugs); a broad catch at this boundary matches the existing precedent in `publish_pending` and keeps the fix simple. Site-specific error types aren't currently exposed through a common base class, so narrowing would require larger changes elsewhere.

## Risks / Trade-offs

- **[Risk]** Broad `except Exception` could swallow a programming bug (e.g. a typo in a parser) silently forever → mitigated by still logging the error message every time it happens, so it's visible in logs even though the run doesn't crash.
- **[Trade-off]** No retry/backoff means a permanently broken site gets re-attempted (and re-fails) every single run forever → acceptable per non-goals; revisit only if log noise from a known-broken site becomes a problem.
