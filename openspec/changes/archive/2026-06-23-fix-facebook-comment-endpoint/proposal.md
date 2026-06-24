## Why

The `facebook-rich-post` capability's link-comment step is broken in production: `GraphApiPublisher.publish` constructs `Comment(parent_id=post_id).remote_create(...)`, which raises `NotImplementedError: Comment must have implemented get_endpoint` every time, because the `Comment` adobject class in the `facebook_business` SDK never implements `get_endpoint()` — it's not meant to be instantiated standalone for creation. The photo post itself succeeds; only the follow-up comment fails (confirmed in production logs), so this is purely a comment-call fix, not a redesign.

## What Changes

- Replace `Comment(parent_id=post_id).remote_create(params={"message": ...})` with `Post(post_id).create_comment(params={"message": ...})` in `GraphApiPublisher.publish` (`publishing/facebook.py`).
- `Post` (and `PagePost`/`Photo`/etc.) implement `get_endpoint()` and own the `create_comment` edge method; `Comment` does not — confirmed by inspecting the installed `facebook_business` package source.
- No behavior change to the excerpt, image, or CTA logic — those already work correctly per production logs ("Post works well").

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `facebook-rich-post`: requirement text and outcome unchanged ("a comment containing the article's wordpress_url SHALL be added"); the scenario is clarified to specify the comment is created via the post's `create_comment` edge, not a standalone `Comment` object — this is the implementation detail that was wrong, not the requirement

## Impact

- `src/scraper/publishing/facebook.py`: swap `Comment(parent_id=...).remote_create(...)` for `Post(post_id).create_comment(...)`; update the `Comment` import to `Post`.
- `tests/test_facebook_publishing.py`: update mocks from `Comment` to `Post` for the comment-creation assertions.
