import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.core import utils


@dataclass(frozen=True)
class ParsedArgs:
    workdir: Path
    sites: List[str]
    xmlrpc: bool
    telegram: bool
    facebook: bool
    count: int

    @staticmethod
    def from_args(ns) -> "ParsedArgs":
        if ns.sites:
            sites = [utils.normalize_url(l) for l in _parse_csv(ns.sites)]
        else:
            sites = None

        return ParsedArgs(
            workdir=Path(ns.directory).resolve(),
            sites=sites,
            xmlrpc=ns.xmlrpc,
            telegram=ns.telegram,
            facebook=ns.facebook,
            count=ns.count
        )


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--directory",
        help="Working directory where config.py.ini",
        default="temp",
    )

    parser.add_argument(
        "-s", "--sites",
        help="list of sites comma separated",
        required=False,
    )

    parser.add_argument(
        '-x', "--xmlrpc",
        help="Enable xmlrpc posting",
        action='store_true',
        required=False,
        default=False
    )

    parser.add_argument(
        '-f', "--facebook",
        help="Enable facebook posting",
        action='store_true',
        required=False,
        default=False
    )

    parser.add_argument(
        '-t', "--telegram",
        help="Enable telegram posting",
        action='store_true',
        required=False,
        default=False
    )

    parser.add_argument(
        '-c', "--count",
        help="Count of posted sites",
        type=int,
        required=False,
        default=1
    )

    ns = parser.parse_args()
    return ParsedArgs.from_args(ns)
