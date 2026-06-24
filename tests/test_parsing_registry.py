import pytest

from scraper.parsing import get_parser
from scraper.parsing.sites.crykami import CrykamiParser
from scraper.parsing.sites.dzen import DzenParser
from scraper.parsing.sites.happytimes import HappyTimesParser
from scraper.parsing.sites.storyx import StoryxParser
from scraper.parsing.sites.yelly import YellyParser


@pytest.mark.parametrize(
    "site_name,expected_cls",
    [
        ("yelly", YellyParser),
        ("crykami", CrykamiParser),
        ("happytimes", HappyTimesParser),
        ("dzen", DzenParser),
        ("storyx", StoryxParser),
    ],
)
def test_get_parser_returns_correct_implementation(site_name, expected_cls):
    assert isinstance(get_parser(site_name), expected_cls)


def test_get_parser_rejects_unknown_site():
    with pytest.raises(ValueError):
        get_parser("not-a-real-site")
