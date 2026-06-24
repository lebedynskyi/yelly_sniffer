import pytest

from scraper.fetching import (
    FetchError,
    PlaywrightFetcher,
    RequestsFetcher,
    get_fetcher,
)


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} error")


def test_requests_fetcher_returns_html(mocker):
    mock_get = mocker.patch("scraper.fetching.requests.get")
    mock_get.return_value = FakeResponse("<html>ok</html>")

    fetcher = RequestsFetcher(user_agent="test-agent")
    html = fetcher.fetch("https://example.com/page")

    assert html == "<html>ok</html>"
    args, kwargs = mock_get.call_args
    assert args[0] == "https://example.com/page"
    assert kwargs["headers"]["User-Agent"] == "test-agent"


def test_requests_fetcher_raises_explicit_error_on_http_failure(mocker):
    mock_get = mocker.patch("scraper.fetching.requests.get")
    mock_get.return_value = FakeResponse("", status_code=500)

    fetcher = RequestsFetcher(user_agent="test-agent")

    with pytest.raises(FetchError, match="https://example.com/broken"):
        fetcher.fetch("https://example.com/broken")


def test_requests_fetcher_sends_cookies(mocker):
    mock_get = mocker.patch("scraper.fetching.requests.get")
    mock_get.return_value = FakeResponse("<html></html>")

    fetcher = RequestsFetcher(user_agent="test-agent", cookies={"session": "abc"})
    fetcher.fetch("https://example.com")

    _, kwargs = mock_get.call_args
    assert kwargs["cookies"] == {"session": "abc"}


def test_playwright_fetcher_returns_rendered_html(mocker):
    fake_page = mocker.MagicMock()
    fake_page.content.return_value = "<html>rendered</html>"

    fake_browser = mocker.MagicMock()
    fake_browser.new_page.return_value = fake_page

    fake_chromium = mocker.MagicMock()
    fake_chromium.launch.return_value = fake_browser

    fake_playwright_ctx = mocker.MagicMock()
    fake_playwright_ctx.chromium = fake_chromium

    fake_sync_playwright = mocker.patch("scraper.fetching.sync_playwright")
    fake_sync_playwright.return_value.__enter__.return_value = fake_playwright_ctx

    fetcher = PlaywrightFetcher()
    html = fetcher.fetch("https://example.com/js-page")

    assert html == "<html>rendered</html>"
    fake_chromium.launch.assert_called_once_with(headless=True)
    fake_page.goto.assert_called_once_with("https://example.com/js-page")


def test_get_fetcher_selects_requests_by_config():
    fetcher = get_fetcher({"fetcher": "requests"})
    assert isinstance(fetcher, RequestsFetcher)


def test_get_fetcher_selects_playwright_by_config():
    fetcher = get_fetcher({"fetcher": "playwright"})
    assert isinstance(fetcher, PlaywrightFetcher)


def test_get_fetcher_rejects_unknown_choice():
    with pytest.raises(ValueError):
        get_fetcher({"fetcher": "carrier-pigeon"})
