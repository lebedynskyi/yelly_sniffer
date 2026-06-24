## MODIFIED Requirements

### Requirement: A follow-up comment with the WordPress link is added after posting
After a Facebook post is successfully created, a comment containing the article's `wordpress_url` SHALL be added to that post.

#### Scenario: Comment added after successful post
- **WHEN** the Facebook photo-post call returns a post id
- **THEN** a comment with message equal to the article's `wordpress_url` is created on that post id via the post's `create_comment` edge (not via a standalone `Comment` object, which does not implement the endpoint needed to create new comments)

#### Scenario: Post succeeds but comment creation fails
- **WHEN** the photo-post is created but the subsequent comment API call raises an exception
- **THEN** the failure is logged and swallowed consistent with existing publish error handling, and the article is still marked `facebook_published` since the primary post succeeded
