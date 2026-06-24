## 1. Fix comment creation call

- [x] 1.1 In `src/scraper/publishing/facebook.py`, replace the `Comment` import with `Post` (from `facebook_business.adobjects.post`)
- [x] 1.2 Replace `Comment(parent_id=post_id).remote_create(params={"message": article.wordpress_url})` with `Post(post_id).create_comment(params={"message": article.wordpress_url})`

## 2. Update tests

- [x] 2.1 In `tests/test_facebook_publishing.py`, change the mocked `Comment` patch target to `Post`, and update assertions to check `Post(...).create_comment` was called with the right post id and message
- [x] 2.2 Update `test_publish_swallows_comment_failure` to raise from the mocked `Post.create_comment` instead of `Comment.remote_create`

## 3. Verify

- [x] 3.1 Run `pytest tests/test_facebook_publishing.py` and full suite, confirm green
