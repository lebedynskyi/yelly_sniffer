## 1. Schema migration

- [x] 1.1 Add `wordpress_url TEXT` and `feature_image_url TEXT` nullable columns to the `articles` table in `post_tracking.py`
- [x] 1.2 Add `wordpress_url` and `feature_image_url` fields to the storage `Article` dataclass and `ArticleStore` save/load mapping

## 2. Persist feature image through pipeline

- [x] 2.1 In `pipeline.py:97-105`, pass `parsed.feature_image` into the storage `Article` as `feature_image_url`
- [x] 2.2 Verify each site parser already populates `feature_image` on the parsing-layer `Article` (no parser changes expected, just confirm)

## 3. WordPress: publish live and capture URL

- [x] 3.1 Change `post.post_status` from `"draft"` to `"publish"` in `WordpressRpcPublisher.publish` (`wordpress.py:21`)
- [x] 3.2 After `NewPost`, call `wp.getPost` (or equivalent) to fetch the new post's `link`
- [x] 3.3 Change `WordpressRpcPublisher.publish` return type to include both post id and URL
- [x] 3.4 In `publish_pending`, persist the returned URL into `article.wordpress_url` via the store
- [x] 3.5 Handle missing/empty `link` in the `wp.getPost` response: log, leave `wordpress_url` NULL, still mark `wordpress_published`

## 4. Facebook eligibility query

- [x] 4.1 Update `find_unpublished("facebook")` (or its query) to require `wordpress_url IS NOT NULL AND feature_image_url IS NOT NULL` in addition to `facebook_published = 0`

## 5. Excerpt generation

- [x] 5.1 Add an HTML-to-plain-text stripper for `article_body` (reuse existing sanitizer/bleach utilities if suitable, otherwise a small helper)
- [x] 5.2 Implement tier selection by raw HTML length: <5000 → 70%, 5000-9000 → 50%, >9000 → 30%
- [x] 5.3 Implement sentence-boundary cut: find nearest `.`/`!`/`?`/`…` to the computed target offset in the stripped text; fall back to hard cut if none found before target
- [x] 5.4 Unit tests: small/medium/big tier boundaries, sentence-boundary cut, hard-cut fallback when no punctuation present

## 6. CTA variants

- [x] 6.1 Add the fixed list of 5 Russian CTA strings as a module-level constant
- [x] 6.2 Implement random selection (`random.choice`) and append `"\n\n" + cta` to the excerpt

## 7. Facebook publisher: image post + comment

- [x] 7.1 Replace `Page.create_feed(...)` with `Page.create_photo(params={"url": feature_image_url, "caption": excerpt_and_cta})` in `GraphApiPublisher.publish`
- [x] 7.2 After the photo post succeeds, create a comment on the returned post id with `message=article.wordpress_url`
- [x] 7.3 Ensure comment-creation failure is logged but does not prevent `facebook_published` from being marked true (post already succeeded)

## 8. Verification

- [ ] 8.1 Manual end-to-end test: scrape one article, publish to WordPress (confirm live, not draft, and `wordpress_url` populated), publish to Facebook (confirm image post + excerpt + CTA + comment with link) — not run, needs real WP/FB credentials
- [x] 8.2 Confirm articles missing `feature_image_url` are correctly skipped by Facebook publish (stay pending)
- [x] 8.3 Run full test suite (`pytest`) and fix any breakage from the WordPress draft→publish status change in existing tests
