import logging
import subprocess
import time

import requests

from scraper.fixing import FIX_PROMPT_TEMPLATE, ContentFixer

logger = logging.getLogger(__name__)

LIVENESS_CHECK_TIMEOUT_SECONDS = 2
POLL_INTERVAL_SECONDS = 0.5


class OllamaFixer(ContentFixer):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        startup_timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.startup_timeout = startup_timeout

    def fix_html(self, html: str) -> str:
        logger.info("Fixing article HTML via local Ollama server")
        logger.info("AI fixer input size: %d chars", len(html))
        self._ensure_server_running()
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": FIX_PROMPT_TEMPLATE.format(html=html),
                "stream": False,
            },
        )
        response.raise_for_status()
        result = response.json()["response"]
        logger.info(
            "AI fixer output size: %d chars (delta: %+d)", len(result), len(result) - len(html)
        )
        return result

    def _is_alive(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", timeout=LIVENESS_CHECK_TIMEOUT_SECONDS
            )
            return response.ok
        except requests.RequestException:
            return False

    def _ensure_server_running(self) -> None:
        if self._is_alive():
            return

        logger.info("Local Ollama server not reachable, starting it")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self._is_alive():
                logger.info("Local Ollama server is ready")
                return
            time.sleep(POLL_INTERVAL_SECONDS)

        raise RuntimeError(
            f"Ollama server did not become ready within {self.startup_timeout}s"
        )
