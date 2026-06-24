import logging

from openai import OpenAI

from scraper.fixing import FIX_PROMPT_TEMPLATE, ContentFixer

logger = logging.getLogger(__name__)


class OpenAIFixer(ContentFixer):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def fix_html(self, html: str) -> str:
        logger.info("Fixing article HTML via OpenAI")
        logger.info("AI fixer input size: %d chars", len(html))
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": FIX_PROMPT_TEMPLATE.format(html=html)}],
        )
        result = response.choices[0].message.content
        logger.info(
            "AI fixer output size: %d chars (delta: %+d)", len(result), len(result) - len(html)
        )
        return result
