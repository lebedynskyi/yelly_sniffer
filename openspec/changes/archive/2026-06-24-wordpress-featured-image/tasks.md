## 1. Featured image upload in WordPress publish

- [x] 1.1 In `WordpressRpcPublisher.publish` (`wordpress.py`), before building/calling `NewPost`, add: if `article.feature_image_url` is set, `requests.get` the image
- [x] 1.2 Determine mime type from the response's `Content-Type` header; fall back to `mimetypes.guess_type(feature_image_url)` only if the header is missing or `application/octet-stream`
- [x] 1.3 Call `wp.uploadFile` (via `UploadFile` method) with `{name, type, bits: xmlrpc_client.Binary(content)}`, set `post.thumbnail = result["id"]`
- [x] 1.4 Wrap the whole image step (download + upload) in a single try/except; on any exception, `logger.exception` and continue to `NewPost` without a thumbnail
- [x] 1.5 Skip the image step entirely (no log noise) when `feature_image_url` is `None`

## 2. Tests

- [x] 2.1 Unit test: article with `feature_image_url` set → `UploadFile` called, `post.thumbnail` set to returned id before `NewPost`
- [x] 2.2 Unit test: article with `feature_image_url = None` → no `UploadFile` call, post published without thumbnail
- [x] 2.3 Unit test: image download raises → post still published via `NewPost`, no thumbnail set, exception logged
- [x] 2.4 Unit test: `wp.uploadFile` call raises → same as above
- [x] 2.5 Unit test: mime type taken from `Content-Type` header when present; falls back to extension guess when header is `application/octet-stream`/missing

## 3. Verification

- [x] 3.1 Run `pytest` and fix any breakage in existing `wordpress.py` tests from the new constructor/call surface
- [ ] 3.2 Manual end-to-end check against a real WP instance if credentials available (not required to close this change)
