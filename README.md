# scraper

Multi-site article scraper that fetches, cleans, AI-fixes, and republishes content to WordPress (XML-RPC) and Facebook (Graph API).

## Setup

```bash
cd new
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
python -m playwright install --with-deps chromium
cp .env.example .env  # then fill in real secrets
```

## Running tests

```bash
source .venv/bin/activate
pytest
```

## Running the CLI

```bash
source .venv/bin/activate
python -m scraper.cli --help
```

## Updating dependencies

Direct dependencies live in `requirements.in` / `requirements-dev.in`. Never hand-edit `requirements.txt` / `requirements-dev.txt` — they are generated lockfiles.

```bash
source .venv/bin/activate
# after editing requirements.in or requirements-dev.in:
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt
pip install -r requirements.txt -r requirements-dev.txt
git add requirements.in requirements.txt requirements-dev.in requirements-dev.txt
```

## Cron

Cron has a minimal environment, so always invoke the venv's interpreter by absolute path. Secrets are loaded from `.env` inside the app (via `python-dotenv`), not by the shell, so this works without sourcing anything:

```cron
*/30 * * * * cd /abs/path/to/new && /abs/path/to/new/.venv/bin/python -m scraper.cli run --scrape --xmlrpc --facebook >> /abs/path/to/new/data/cron.log 2>&1
```
