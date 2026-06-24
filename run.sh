#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

DELAY=$(( (RANDOM % 601) + 300 ))   # random 300-900s = 5-15 min
sleep "$DELAY"

exec .venv/bin/python src/scraper/cli.py --scrape --xmlrpc --facebook
