import logging

from google import genai

from scraper.fixing import FIX_PROMPT_TEMPLATE, ContentFixer

logger = logging.getLogger(__name__)


class GeminiFixer(ContentFixer):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def fix_html(self, html: str) -> str:
        logger.info("Fixing article HTML via Gemini")
        logger.info("AI fixer input size: %d chars", len(html))
        response = self.client.models.generate_content(
            model=self.model,
            contents=FIX_PROMPT_TEMPLATE.format(html=html),
        )
        result = response.text
        logger.info(
            "AI fixer output size: %d chars (delta: %+d)", len(result), len(result) - len(html)
        )
        return result
