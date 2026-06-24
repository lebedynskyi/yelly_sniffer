## Context

`GraphApiPublisher.publish` (`publishing/facebook.py`) was changed in `facebook-image-excerpt-post` to add a follow-up comment after the photo post, using:

```python
Comment(parent_id=post_id).remote_create(params={"message": article.wordpress_url})
```

In production this raises:
```
NotImplementedError: Comment must have implemented get_endpoint.
```
from `facebook_business/adobjects/abstractcrudobject.py:262` via `abstractobject.py:103`. The photo post itself succeeds (confirmed in prod logs) — only this follow-up call fails, every time, deterministically (not a transient API error).

Root cause: in the `facebook_business` Python SDK, `Comment` is the *result* type returned by reading comments off a post — it is not designed to be instantiated standalone and have `.remote_create()` called on it. `AbstractCrudObject.remote_create()` requires `self.get_endpoint()`, which `Comment` never overrides (`abstractobject.get_endpoint()` raises `NotImplementedError` by default). Classes that *do* implement `get_endpoint()` and expose `create_comment(...)` as a proper edge method include `Post`, `PagePost`, `Photo`, `Album`, `AdVideo`, `IGMedia` (confirmed via `grep -rl create_comment` over the installed package).

## Goals / Non-Goals

**Goals:**
- Make the link-comment step actually succeed against the real Graph API.
- Keep the call shape consistent with how `create_photo`'s returned post id is already used.

**Non-Goals:**
- No change to excerpt/image/CTA logic — unaffected, already verified working in production.
- No change to comment-failure handling (still logged + swallowed, per existing `facebook-rich-post` spec scenario "Post succeeds but comment creation fails").

## Decisions

**Use `Post(post_id).create_comment(params={"message": ...})` instead of `Comment(parent_id=post_id).remote_create(...)`.**
`Post.create_comment` has the same call signature shape (`fields, params, batch, success, failure, pending`) as other edge-creation methods already used in this codebase (e.g. `Page.create_photo`), and `Post` correctly implements `get_endpoint()` so the SDK can build the `/{post_id}/comments` request. `PagePost` was also considered (same `create_comment` capability) — `Post` is the more generic/lower-overhead class and is sufficient since no Page-post-specific fields are needed for this call.

## Risks / Trade-offs

- **None significant** — this is a one-line API-object swap; the Graph API endpoint hit (`POST /{post_id}/comments`) is unchanged, only the SDK wrapper class used to construct that request changes.
