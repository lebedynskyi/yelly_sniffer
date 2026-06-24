from scraper.sanitizer import Bs4HtmlSanitizer


def test_disallowed_tags_and_attributes_stripped():
    sanitizer = Bs4HtmlSanitizer()
    html = '<div onclick="evil()"><p style="color:red">Hello <iframe src="x"></iframe></p></div>'

    result = sanitizer.sanitize_html(html)

    assert "onclick" not in result
    assert "style=" not in result
    assert "<iframe" not in result


def test_allowed_structural_content_preserved():
    sanitizer = Bs4HtmlSanitizer()
    html = "<p>Para</p><h2>Heading</h2><ul><li>item</li></ul><a href='https://x.com'>link</a>"

    result = sanitizer.sanitize_html(html)

    assert "Para" in result
    assert "Heading" in result
    assert "item" in result
    assert 'href="https://x.com"' in result


def test_known_cta_phrase_removed():
    sanitizer = Bs4HtmlSanitizer()
    html = "<p>Real content here.</p><p>Подписывайтесь на канал!</p>"

    result = sanitizer.sanitize_html(html)

    assert "Real content here." in result
    assert "Подписывайтесь" not in result


def test_aggressive_uppercase_spam_removed():
    sanitizer = Bs4HtmlSanitizer()
    html = "<p>Normal text.</p><p>THIS IS A VERY LOUD SPAM LINE HERE</p>"

    result = sanitizer.sanitize_html(html)

    assert "Normal text." in result
    assert "VERY LOUD SPAM" not in result


def test_empty_block_removed_after_cta_stripped():
    sanitizer = Bs4HtmlSanitizer()
    html = "<p>Keep this.</p><p>Подписывайтесь на канал!</p>"

    result = sanitizer.sanitize_html(html)

    # only one <p> should remain once the CTA-only paragraph is stripped empty
    assert result.count("<p>") == 1


def test_empty_block_with_media_preserved():
    sanitizer = Bs4HtmlSanitizer()
    html = '<p><img src="https://x.com/a.jpg"></p>'

    result = sanitizer.sanitize_html(html)

    assert "<img" in result
