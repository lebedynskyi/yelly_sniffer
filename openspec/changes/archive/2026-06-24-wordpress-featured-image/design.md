## Context

`Article.feature_image_url` is already populated end-to-end (parser → pipeline → DB) and already consumed by the Facebook publisher (`facebook.py:110`, passed straight through as a remote `url` param to Graph API's photo-post call). WordPress XML-RPC has no equivalent "post a remote URL as the image" call — `wp.uploadFile` requires base64-encoded bytes, and the resulting attachment id is what `WordPressPost.thumbnail` (→ `post_thumbnail`) expects.

## Decision: inline, best-effort, in `publish()`

The upload step is added directly inside `WordpressRpcPublisher.publish`, not factored into a separate method/module. Rationale: it's a single conditional block (download → upload → set field), there's exactly one caller, and the existing codebase pattern for fixers/publishers favors small concrete classes over speculative abstraction. If a second target ever needs the same upload-to-media-library logic, extract then.

Failure handling: catch broadly around the whole image step (download + upload), log via `logger.exception`, and fall through to the normal `NewPost` call without a thumbnail. This mirrors the existing pattern at the `publish_pending` level (one bad article doesn't block the cron loop) — here it's one bad image doesn't block the post.

## Decision: Content-Type sniffing for mime type

`requests.get(feature_image_url)` returns a `Content-Type` response header in the overwhelming majority of cases (real image CDNs/servers). Use that directly for the `type` field in `wp.uploadFile`'s data dict. Only fall back to guessing from the URL's extension (`mimetypes.guess_type`) when the header is absent or a non-specific value like `application/octet-stream` — this is more robust than URL-extension-first, since these scraped image URLs often carry CDN query strings or no extension at all.

## Risks

- Extra HTTP round-trip (image download) + XML-RPC round-trip (upload) per WordPress publish call, on top of the existing `NewPost` + `getPost` calls. Acceptable: `publish_pending` already processes one article per run; this isn't a hot loop.
- If `feature_image_url` points to a since-deleted/expired image (scrape-to-publish lag), download fails — handled by the swallow-and-continue behavior above.
