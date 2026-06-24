## Why

Facebook posts today are bare link-shares (`message` + `link`, no image) and WordPress posts are created as unpublished drafts, so the article URL a Facebook comment would point to doesn't exist yet. To post real Facebook content (image + excerpt) with a working "read more" link in the first comment, WordPress posts must go live and their URL must be captured, and the Facebook publisher must be rebuilt around an image+excerpt+comment flow instead of a link share.

## What Changes

- **BREAKING**: WordPress posts are now published live (`post_status = "publish"`) instead of created as drafts.
- WordPress publish now fetches and persists the live post URL (extra `wp.getPost` call after `NewPost`), stored in a new `wordpress_url` column.
- Article's `feature_image` (already parsed, currently discarded) is persisted to a new `feature_image_url` column.
- Facebook publish eligibility changes: only articles with a non-null `wordpress_url` are eligible (Facebook publish now implicitly waits on WordPress publish, enforced via the DB query, not in-process ordering).
- Facebook publisher switches from `Page.create_feed` (link-only) to `Page.create_photo` (image + text), where the text is:
  - A plain-text (HTML-stripped) excerpt of `article_body`, length-tiered by raw HTML character count: small (<5000 chars) → 70%, medium (5000-9000) → 50%, big (>9000) → 30%. Excerpt cut lands on the nearest sentence boundary to the target percentage.
  - Followed by a blank line and one randomly chosen CTA from 5 fixed Russian variants pointing to "first comment".
- After the Facebook post is created, a follow-up comment is added on that post containing the article's `wordpress_url`.

## Capabilities

### New Capabilities
- `facebook-rich-post`: Facebook Page publishing as image + tiered text excerpt + CTA, followed by a link-to-article comment, gated on WordPress having already published and exposed a live URL.

### Modified Capabilities
(none — no existing specs in this repo to modify; WordPress live-publish and URL capture are folded into `facebook-rich-post` as a precondition rather than spec'd separately, since they exist solely to support this capability)

## Impact

- `src/scraper/publishing/wordpress.py`: `post_status` change, add `wp.getPost` URL fetch, persist URL.
- `src/scraper/publishing/facebook.py`: replace `create_feed` call with `create_photo` + comment follow-up call; new excerpt/CTA logic.
- `src/scraper/post_tracking.py`: schema migration — add `wordpress_url`, `feature_image_url` columns; `find_unpublished("facebook")` query gains `wordpress_url IS NOT NULL` filter.
- `src/scraper/pipeline.py:97-105`: stop discarding `feature_image`, pass it into the stored `Article`.
- `src/scraper/parsing/__init__.py` / storage `Article` dataclass: add `feature_image_url` field end-to-end.
