## Purpose
Defines the WordPress XML-RPC publisher's own behavior beyond what is folded into `facebook-rich-post` as a precondition: when an article has a feature image, that image is uploaded to the WordPress media library and set as the post's featured image before the post is created, with the upload's mime type sniffed from the download response rather than assumed from the URL.

## Requirements

### Requirement: WordPress post carries the article's feature image as its featured image
When an article has a non-null `feature_image_url`, WordPress publishing SHALL upload that image to the WordPress media library and set it as the post's featured image (`post_thumbnail`) before creating the post.

#### Scenario: Article has a feature image
- **WHEN** `WordpressRpcPublisher.publish` is called for an article with a non-null `feature_image_url`
- **THEN** the image is downloaded, uploaded via `wp.uploadFile`, and the returned attachment id is set as `post.thumbnail` before `wp.newPost` is called

#### Scenario: Article has no feature image
- **WHEN** `WordpressRpcPublisher.publish` is called for an article with `feature_image_url = None`
- **THEN** no upload is attempted, and the post is created without a featured image

#### Scenario: Image download or upload fails
- **WHEN** the feature image download or the `wp.uploadFile` call raises an exception
- **THEN** the failure is logged, no thumbnail is set, and the post is still created via `wp.newPost`

### Requirement: Featured image upload mime type is sniffed, not assumed from the URL
The mime type passed to `wp.uploadFile` SHALL be taken from the image download's `Content-Type` response header, falling back to a guess based on the URL's file extension only when that header is absent or a non-specific value (e.g. `application/octet-stream`).

#### Scenario: Content-Type header present and specific
- **WHEN** the image download response has a `Content-Type` header like `image/jpeg`
- **THEN** that value is used as the upload's mime type

#### Scenario: Content-Type header missing or generic
- **WHEN** the image download response has no `Content-Type` header, or it is `application/octet-stream`
- **THEN** the mime type is instead guessed from the `feature_image_url`'s file extension
