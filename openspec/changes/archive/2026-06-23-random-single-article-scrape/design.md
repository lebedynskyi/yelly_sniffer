## Context

`run_pipeline` (`src/scraper/pipeline.py`) currently calls `_scrape_sites`, which loops every configured site in `config.yaml` order, fetches its listing, and processes (fetch/parse/sanitize/fix/save) every meta not already in `store`. This means a single `--scrape` run can save many articles, and the number/cost is unbounded by config size and listing freshness, not by intent. We want exactly one article saved per run, selected fairly at random rather than always favoring sites earlier in `config.yaml`.

No new external dependency — `random` is stdlib. No data model change (`ArticleStore`/`Article` untouched). No migration needed; this is a pure orchestration change in one function.

## Goals / Non-Goals

**Goals:**
- Process at most one new article per `run_pipeline(do_scrape=True)` call.
- Give every configured site a fair (uniform) chance of being the one scraped this run, not just the first one in config with new content.
- Within a chosen site, give every not-yet-stored article a fair chance, not just the first one in listing order.
- Keep selection deterministic/testable via an injectable RNG.
- Preserve all existing per-article processing behavior (fetch, parse, sanitize, fix, save) unchanged.

**Non-Goals:**
- No cross-run fairness/backoff state (e.g. remembering which sites were empty recently). Plain per-run shuffle is accepted as good enough.
- No change to how many listing fetches happen in the worst case (still up to one listing fetch per site per run).
- No change to publishing (`wordpress`/`facebook`) logic — untouched.
- No new capping of fetch *attempts*; only capping how many articles get *saved*.

## Decisions

**1. Selection split into its own function: `_pick_one_article(sites, store, rng=None) -> tuple[SiteHandlers, ArticleMeta] | None`.**
Keeps the "find a candidate" concern testable independent of fetch/parse/sanitize/fix/save side effects. Mirrors the existing module's style of small composable functions.
Alternative considered: inline shuffle-and-pick directly in `_scrape_sites`. Rejected — harder to unit test selection logic without mocking the full processing chain too.

**2. Shuffle sites, then shuffle metas within the first site that has any new article — not a global shuffle of all (site, meta) pairs.**
Listings are fetched lazily per site in shuffled order; we stop fetching further listings the moment a site yields a usable candidate. A global pre-shuffle of all (site, meta) pairs would require fetching every site's listing every run regardless of outcome, increasing unnecessary network calls when an early site already has a candidate.
Alternative considered: fetch all listings upfront, build one big pool, shuffle, pick first valid. Rejected — defeats the purpose of bounding work per run and adds avoidable Playwright invocations for `dzen`.

**3. Randomness injected via optional `rng: random.Random | None = None`, defaulting to `random.shuffle`/module-level `random` functions when not provided.**
Lets tests pass `random.Random(0)` (or a mock) for deterministic ordering without changing production call sites (`run_pipeline` doesn't need to pass anything).
Alternative considered: require callers to always pass an `rng`. Rejected — adds boilerplate to the CLI entrypoint for no real benefit.

**4. Exhaustion (no site has any new article) is logged at `info` level and `run_pipeline` returns normally — not an exception.**
Matches current behavior where an empty result is unremarkable (e.g. listing has nothing new) rather than an error condition.

**5. `run_pipeline` orchestration becomes: if `do_scrape`, call `_pick_one_article`; if it returns a pair, run the existing single-article processing logic once; else log "nothing to do" and continue to publishing steps as before.**
Publishing flags (`do_xmlrpc`, `do_facebook`) are unaffected by whether scraping found anything — same as today.

## Risks / Trade-offs

- **[Risk]** Sites with large listings or many sites configured mean more listing fetches per run in the worst case (when the first several shuffled sites are already fully scraped) → no worse than today's behavior, since today already fetches every site's listing unconditionally every run. **No regression**, just reordering.
- **[Risk]** Throughput drops from "all new articles per run" to "one per run" → if the cron cadence isn't increased, content backlog could grow unboundedly over time → out of scope for this change; cron frequency is an operational knob the user controls separately (noted as an open question below).
- **[Risk]** `random.shuffle` mutates the list it's given in place → must shuffle a copy of `metas`/`sites`, not the caller's original list, to avoid surprising side effects on lists owned by the CLI/config layer.
- **[Trade-off]** No fairness memory across runs (explicitly a non-goal) → a site that's unlucky in the shuffle for many consecutive runs could lag behind in publish cadence purely by chance. Accepted per proposal discussion.

## Migration Plan

No data migration. Deploy is just shipping the new `pipeline.py` logic; next cron invocation picks up the new one-article-per-run behavior automatically. Rollback is a plain revert of `pipeline.py` (and its tests) — no state to unwind since `ArticleStore` schema/contents are untouched.

## Open Questions

- Should cron cadence be increased now that each run only saves one article, to keep total daily throughput comparable to before? (Operational decision, not part of this code change — flagging for the user to decide separately.)
