from bs4 import BeautifulSoup

from scraper.parsing.cleanup import strip_by_selectors


def test_strip_by_selectors_removes_matching_elements():
    soup = BeautifulSoup(
        """
        <div class="entry-content">
            <p>Keep me</p>
            <ins class="adsbygoogle">ad</ins>
            <div class="ads">ad block</div>
            <script>tracker()</script>
        </div>
        """,
        "html.parser",
    )

    strip_by_selectors(soup, ["ins.adsbygoogle", "div.ads", "script"])

    assert soup.find("ins") is None
    assert soup.find("div", class_="ads") is None
    assert soup.find("script") is None
    assert soup.find("p").get_text(strip=True) == "Keep me"


def test_strip_by_selectors_supports_attribute_prefix_selectors():
    soup = BeautifulSoup(
        '<div id="yandex-rtb-1">tracker</div><p>content</p>', "html.parser"
    )

    strip_by_selectors(soup, ['div[id^="yandex"]'])

    assert soup.find("div") is None
    assert soup.find("p").get_text(strip=True) == "content"


def test_strip_by_selectors_no_match_is_noop():
    soup = BeautifulSoup("<p>content</p>", "html.parser")

    strip_by_selectors(soup, ["div.does-not-exist"])

    assert soup.find("p").get_text(strip=True) == "content"
