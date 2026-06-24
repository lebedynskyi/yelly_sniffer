## Why

Every site parser already extracts a `feature_image` URL (first `<img>` in the article body), and it already flows through the pipeline into `Article.feature_image_url` — Facebook's publisher uses it directly as a remote URL for its photo post. WordPress's XML-RPC publisher ignores it entirely: `NewPost` is called with no `post_thumbnail`, so published posts never get a featured image. Unlike Facebook's Graph API, WordPress XML-RPC can't take a remote URL for a thumbnail — it needs an uploaded media attachment ID — so this requires an upload step, not just a field assignment.

## What Changes

- `WordpressRpcPublisher.publish` gains an inline step, before `NewPost`: if `article.feature_image_url` is set, download the image, upload it via `wp.uploadFile`, and set `post.thumbnail` to the returned attachment id.
- Mime type for the upload is taken from the download response's `Content-Type` header; falls back to a guess from the URL's file extension only if the header is missing or generic (e.g. `application/octet-stream`).
- Any failure in this step (download error, upload error, no `feature_image_url`) is logged and swallowed — the post still publishes via `NewPost`, just without a featured image. No new partial-failure plumbing; this is a plain extra call inside the existing `publish` method, consistent with how `publish_pending` already swallows per-article failures.

## Capabilities

### New Capabilities
- `wordpress-publish`: defines featured-image upload behavior for the WordPress XML-RPC publisher (no spec previously existed for the WordPress publisher's own behavior — its live-publish/URL-capture behavior is currently folded into `facebook-rich-post` as a precondition).

### Modified Capabilities
(none)

## Impact

- `src/scraper/publishing/wordpress.py`: `WordpressRpcPublisher.publish` — add image download + `wp.uploadFile` call + `post.thumbnail` assignment before `NewPost`.
- No schema changes — `feature_image_url` already exists on the stored `Article` and is already populated by the pipeline.
- No changes to `facebook.py` or `pipeline.py`.
