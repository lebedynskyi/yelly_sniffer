## ADDED Requirements

### Requirement: WordPress publish exposes a live, persisted post URL
WordPress publishing SHALL create posts with `post_status = "publish"` (not draft), and SHALL persist the resulting live post URL on the article record for downstream use.

#### Scenario: Successful WordPress publish persists URL
- **WHEN** `publish_pending` publishes a pending article to WordPress
- **THEN** the post is created with `post_status = "publish"`, a follow-up call retrieves the post's `link`, and that URL is stored in the article's `wordpress_url` column

#### Scenario: WordPress publish succeeds but URL retrieval fails
- **WHEN** `NewPost` succeeds but the follow-up `wp.getPost` call fails or returns no `link`
- **THEN** `wordpress_published` is still marked true, but `wordpress_url` remains NULL, and the article is therefore not yet eligible for Facebook publish

### Requirement: Article feature image is persisted through the pipeline
The scrape pipeline SHALL persist the parsed `feature_image` URL into the stored article record instead of discarding it.

#### Scenario: Article with a feature image is scraped
- **WHEN** a site parser returns an `Article` with a non-null `feature_image`
- **THEN** the stored article record's `feature_image_url` column is populated with that value

#### Scenario: Article with no feature image is scraped
- **WHEN** a site parser returns an `Article` with `feature_image = None`
- **THEN** the stored article record's `feature_image_url` column is NULL

### Requirement: Facebook publish eligibility requires a live WordPress URL and an image
An article SHALL only be eligible for Facebook publishing once it has a non-null `wordpress_url` and a non-null `feature_image_url`.

#### Scenario: Article not yet published to WordPress
- **WHEN** Facebook `publish_pending` looks for pending articles and an article has `wordpress_url IS NULL`
- **THEN** that article is excluded from the eligible set, regardless of its `facebook_published` flag

#### Scenario: Article has no feature image
- **WHEN** an article has `wordpress_url` set but `feature_image_url IS NULL`
- **THEN** that article is excluded from the eligible Facebook publish set

#### Scenario: Article eligible for Facebook publish
- **WHEN** an article has `facebook_published = 0`, `wordpress_url` set, and `feature_image_url` set
- **THEN** that article is included in the eligible set for Facebook publishing

### Requirement: Facebook post contains a length-tiered, sentence-bounded plain-text excerpt
The Facebook post text SHALL be a plain-text excerpt of the article body with HTML stripped, sized by a percentage of the article's raw HTML character length, cut at the nearest sentence boundary to the target offset.

#### Scenario: Small article excerpt
- **WHEN** an article's raw HTML `article_body` is under 5000 characters
- **THEN** the excerpt covers approximately 70% of the stripped-text length, cut at the nearest sentence boundary to that target

#### Scenario: Medium article excerpt
- **WHEN** an article's raw HTML `article_body` is between 5000 and 9000 characters
- **THEN** the excerpt covers approximately 50% of the stripped-text length, cut at the nearest sentence boundary to that target

#### Scenario: Big article excerpt
- **WHEN** an article's raw HTML `article_body` is over 9000 characters
- **THEN** the excerpt covers approximately 30% of the stripped-text length, cut at the nearest sentence boundary to that target

#### Scenario: No sentence boundary before target offset
- **WHEN** the stripped text contains no sentence-ending punctuation before the computed target offset
- **THEN** the excerpt is hard-cut at the target offset instead

### Requirement: Facebook post appends a randomized CTA pointing to the first comment
After the excerpt, the Facebook post text SHALL include a blank line followed by one randomly selected call-to-action string from a fixed set of 5 variants, each directing the reader to the first comment for more.

#### Scenario: CTA appended after excerpt
- **WHEN** a Facebook post is composed for an eligible article
- **THEN** the post text is `<excerpt>\n\n<one of 5 fixed CTA strings, chosen at random>`

### Requirement: Facebook post includes the article's feature image
The Facebook post SHALL be created as an image post using the article's `feature_image_url`, not a plain text/link post.

#### Scenario: Facebook post created with image
- **WHEN** Facebook `publish_pending` publishes an eligible article
- **THEN** the post is created via the photo-post API using `feature_image_url` as the image source and the excerpt+CTA text as the caption

### Requirement: A follow-up comment with the WordPress link is added after posting
After a Facebook post is successfully created, a comment containing the article's `wordpress_url` SHALL be added to that post.

#### Scenario: Comment added after successful post
- **WHEN** the Facebook photo-post call returns a post id
- **THEN** a comment with message equal to the article's `wordpress_url` is created on that post id

#### Scenario: Post succeeds but comment creation fails
- **WHEN** the photo-post is created but the subsequent comment API call raises an exception
- **THEN** the failure is logged and swallowed consistent with existing publish error handling, and the article is still marked `facebook_published` since the primary post succeeded
