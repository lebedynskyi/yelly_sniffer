import os

import yaml

from scraper.cli import build_arg_parser, load_config


def test_arg_parser_defaults_all_stages_off():
    parser = build_arg_parser()
    args = parser.parse_args([])

    assert args.scrape is False
    assert args.xmlrpc is False
    assert args.facebook is False


def test_arg_parser_flags_enable_stages():
    parser = build_arg_parser()
    args = parser.parse_args(["--scrape", "--xmlrpc", "--facebook"])

    assert args.scrape is True
    assert args.xmlrpc is True
    assert args.facebook is True


def test_load_config_reads_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"database": {"path": "data/x.sqlite"}, "sites": []}))

    config = load_config(config_file)

    assert config["database"]["path"] == "data/x.sqlite"


def test_config_yaml_has_no_secret_shaped_values():
    repo_config = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(repo_config) as f:
        config = yaml.safe_load(f)

    serialized = yaml.dump(config).lower()
    for forbidden in ("password", "secret", "token", "api_key", "access_key"):
        assert forbidden not in serialized
