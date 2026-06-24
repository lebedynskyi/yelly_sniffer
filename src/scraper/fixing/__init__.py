from abc import ABC, abstractmethod

from scraper.settings import AISettings

FIX_PROMPT_TEMPLATE = (
    "You are an HTML article repair/reviewer tool.\n\n"
    "Fix only broken word splits and fragmented inline tags.\n\n"
    "Do NOT rewrite, paraphrase, remove, or translate text. "
    "Do NOT change content that is already correct.\n\n"
    "Make the smallest possible changes. Remove unnecessary whitespace and "
    "line breaks, both in HTML tags and in plain text. Keep semantic block "
    "tags unchanged.\n\n"
    "Remove calls to action and third-party links, including their text and "
    "tags. Remove empty tags. Remove links and text not related to the "
    "article content.\n\n"
    "Output valid HTML only, without markdown. No explanations, no extra "
    "text.\n\n{html}"
)


class ContentFixer(ABC):
    @abstractmethod
    def fix_html(self, html: str) -> str:
        raise NotImplementedError


def get_fixer(settings: AISettings) -> ContentFixer:
    if settings.provider == "gemini":
        from scraper.fixing.gemini import GeminiFixer

        return GeminiFixer(api_key=settings.gemini_api_key, model=settings.gemini_model)

    if settings.provider == "ollama":
        from scraper.fixing.ollama import OllamaFixer

        return OllamaFixer(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            startup_timeout=settings.ollama_startup_timeout_seconds,
        )

    from scraper.fixing.openai_fixer import OpenAIFixer

    return OpenAIFixer(api_key=settings.openai_api_key, model=settings.openai_model)
