## Context

Current state (pre-change):
- `WordpressRpcPublisher.publish` (`publishing/wordpress.py:15-23`) creates posts as `post_status = "draft"`; the post is never publicly reachable and the call returns only an int `post_id`, no URL.
- `feature_image` is parsed by every site parser (`parsing/__init__.py:12-17`) but discarded at `pipeline.py:97-105` when building the storage `Article`.
- `GraphApiPublisher.publish` (`publishing/facebook.py:23-32`) posts via `Page.create_feed(message=title, link=original_url)` — text+link only, no image, no comment.
- `articles` table (`post_tracking.py:11-22`) has no column for image URL or WordPress permalink — only boolean `wordpress_published`/`facebook_published` flags.
- `find_unpublished(target)` selects rows where the target's boolean flag is unset; Facebook and WordPress publish are otherwise independent per CLAUDE.md's pipeline model.

This change makes Facebook publish need data that only exists after WordPress publish succeeds (the live URL), so the existing "fully independent targets" model needs a narrow, DB-enforced exception.

## Goals / Non-Goals

**Goals:**
- WordPress posts go live and their URL is captured and persisted.
- Facebook posts carry the article's image and a length-tiered plain-text excerpt instead of a bare link.
- A follow-up comment with the WordPress URL is added to the Facebook post.
- Facebook publish naturally waits for WordPress publish via DB state, no in-process coupling between the two `publish_pending` calls.

**Non-Goals:**
- No retry/backfill mechanism for articles already published to WordPress as drafts before this change ships (pre-existing draft posts are not migrated to "live" automatically).
- No change to how `original_url` (source site URL) is used elsewhere in the pipeline.
- No support for posting without an image — if `feature_image_url` is missing, the article is left pending for Facebook (a one-line skip, not a new fallback feature).

## Decisions

**1. Capture WordPress URL via a second XML-RPC call (`wp.getPost`) rather than parsing it from `NewPost`'s response.**
`NewPost` returns only the new post's ID by design in `wordpress_xmlrpc`. Alternative considered: construct the URL by hand from a configured base URL + slug — rejected because permalink structure (and any redirects/category prefixes) is WordPress-config-dependent and would silently produce wrong links if that structure changes. Calling `wp.getPost(post_id, fields=['link'])` immediately after `NewPost` is one extra round-trip but guarantees the real URL.

**2. Persist `wordpress_url` and `feature_image_url` as new nullable columns on the existing `articles` table**, not a separate table.
Both are 1:1 per-article facts, same lifecycle as the row itself — no need for a join table. Existing rows get `NULL` via `ALTER TABLE ... ADD COLUMN` (sqlite default), which is also how `find_unpublished("facebook")` will exclude old/never-WP-published rows automatically.

**3. Facebook eligibility = `facebook_published = 0 AND wordpress_url IS NOT NULL`** (and `feature_image_url IS NOT NULL`, see Non-Goals), enforced in the `find_unpublished` query, not by having `facebook.publish_pending` call into WordPress logic.
This keeps the two `publish_pending` functions decoupled in code (per CLAUDE.md's existing architecture note) while making the real-world dependency ordering fall out of DB state rather than an explicit cross-module call. Alternative considered: have Facebook's `publish_pending` trigger a WordPress publish inline if missing — rejected, conflates two independently-scheduled cron stages and reintroduces the coupling CLAUDE.md explicitly calls out as avoided today.

**4. Excerpt tiering by raw HTML character length of `article_body`, not stripped-text length.**
Matches the thresholds the user specified (5000/9000 chars "with html"). Stripping happens only to produce the excerpt's displayed text, not to classify tier size — avoids a second length computation diverging from the one used for thresholds.

**5. Sentence-boundary excerpt cut: find sentence-ending punctuation (`.`, `!`, `?`, `…`) closest to the target character offset (tier% × stripped-text length), cut there.**
If no sentence boundary exists before the target (e.g., one giant first sentence), fall back to a hard cut at the target offset — documented edge case, not a new feature.

**6. CTA selection: fixed list of 5 hardcoded Russian strings, `random.choice` at publish time.**
No config/admin UI for editing variants — out of scope; editing the list means editing code, consistent with how site parsers are added today (code change, not data change).

**7. Facebook image+text via `Page.create_photo(params={"url": feature_image_url, "caption": excerpt_and_cta})`, followed by `Comment` creation on the returned post id.**
The Graph API photo-post return is the post id directly usable for the comment edge (`POST /{post_id}/comments`); no separate "attach media to feed item" two-step needed since `create_photo` with `published=true` (default) is a single combined call.

**8. `WordpressRpcPublisher.publish` return type changes from `int` to a small struct/tuple `(post_id, url)`** so `publish_pending` can persist the URL without a second call back into the publisher from the pipeline layer.

## Risks / Trade-offs

- **Going live immediately on WordPress is a behavior change with no feature flag.** → Mitigation: explicitly called out as **BREAKING** in proposal.md; this is the user-requested behavior, not a default worth gating.
- **`wp.getPost` immediately after `NewPost` could race WordPress's own permalink generation (rare, some plugins delay slug finalization).** → Mitigation: if `link` field is empty/missing in the response, log and leave `wordpress_url` NULL — article simply stays ineligible for Facebook until a manual fix, rather than persisting a wrong URL.
- **Sentence-boundary excerpt cut can produce very uneven lengths if punctuation is sparse (e.g., dialogue-heavy text with em-dashes instead of periods).** → Mitigation: accepted as a known content-shape limitation; not solved by this change.
- **`facebook_published` rows with `feature_image_url IS NULL` (pre-change scraped articles, or sites where the parser fails to find an image) will never become eligible.** → Mitigation: acceptable per Non-Goals; no backfill in scope.

## Migration Plan

1. Schema migration: `ALTER TABLE articles ADD COLUMN wordpress_url TEXT`, `ALTER TABLE articles ADD COLUMN feature_image_url TEXT` (both nullable, no backfill).
2. Deploy pipeline/parsing changes that populate `feature_image_url` on new scrapes.
3. Deploy WordPress publisher changes (live status + URL capture) — existing pending-draft articles in the DB are unaffected until next publish cycle picks them up; they will now publish live instead of draft going forward.
4. Deploy Facebook publisher changes last, since they depend on columns from steps 1-2 being populated.
5. Rollback: revert code changes; schema columns can stay (nullable, harmless if unused) or be dropped manually if desired — sqlite `ALTER TABLE ... DROP COLUMN` requires 3.35+, otherwise table-rebuild; not automated here.

## Open Questions

- None outstanding — thresholds, cut strategy, and CTA wording were confirmed with the user during exploration.
