import logging
import time

from pathlib import Path
from google import genai
from google.genai import Client, types

from src.ai.model import AiModel

logger = logging.getLogger(__name__)

SYSTEM_CHAT_PROMPT_OPTIMIZED = """
You are an HTML article repair/reviewer tool.

Fix only broken words splits and fragmented inline tags.

Do NOT rewrite, DO NOT paraphrase, DO NOT remove, DO NOT translate text, Do NOT change content that is already correct.

DO the smallest possible changes. Do Removing unnecessary whitespaces and line breaks as HTML tags and as pure text.
Keep semantic block tags unchanged.
Remove call to action and 3rd party links with text and tags. Remove empty tags. Remove links and text not related to article content

Output valid HTML only without markdown. No explanations. No extra text
"""

SYSTEM_CHAT_PROMPT_OPTIMIZED_1 = """
You are an HTML article repair/reviewer tool.
Your job is to return the cleaned article as valid HTML.

Allowed changes (ONLY):
Fix broken word splits caused by line breaks/spaces (e.g., "exam ple" → "example").
Fix fragmented/broken inline HTML tags (e.g., <sp + an> → <span>).

Remove unnecessary whitespace, extra spaces, and meaningless line breaks:
inside text
between inline tags
around inline tags
Remove empty tags (tags containing only whitespace or nothing).
Remove call-to-action blocks, promotional fragments, sponsor text.
Remove 3rd-party links, including their surrounding text and tags (ads, “read more”, “subscribe”, “source”, “follow us”, etc.).
Remove links and text that are not part of the article content.

Forbidden changes (MUST NOT):
Do NOT rewrite.
Do NOT paraphrase.
Do NOT translate.
Do NOT summarize.
Do NOT reorder content.
Do NOT change correct text.
Do NOT change semantic block structure (keep headings/paragraphs/lists/sections as they are unless removing unwanted CTA/link blocks).

Output rules:
Output ONLY final valid HTML.
No markdown.
No explanations.
No extra text.
"""

USER_CHAT_PROMPT_OPTIMIZED = """
Fix this HTML:
<<<HTML>>>
"""

# MODEL_REPO = "Qwen/Qwen2.5-32B-Instruct-GGUF"
# MODEL_FILE = "qwen2.5-32b-instruct-q4_k_m-*.gguf"

# MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct-GGUF"
# MODEL_FILE = "qwen2.5-7b-instruct-q4_k_m-*.gguf"

MODEL_REPO = "bartowski/Mistral-7B-Instruct-v0.3-GGUF"
MODEL_FILE = "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"

CHUNK_TOKEN_SIZE = 800
CONTEXT_SIZE = 2048

GEMINI_MODEL = "gemini-2.5-flash"


class LLMFixer:
    def __init__(self, workdir: Path):
        self.workdir = workdir

    def fix_broken_html(self, html: str) -> str:
        logger.info("Fixing ")

        ai_model = AiModel(self.workdir, MODEL_REPO, MODEL_FILE, context_size=CONTEXT_SIZE)
        chunks = ai_model.chunk_html_preserve_all(html, max_tokens=CHUNK_TOKEN_SIZE)
        logger.info(f"Determined {len(chunks)} chunks")

        result = []
        for i, chunk in enumerate(chunks):
            user_prompt = USER_CHAT_PROMPT_OPTIMIZED.replace(
                "{part}", str(i + 1)
            ).replace(
                "{amount}", str(len(chunks))
            ).replace("<<<HTML>>>", chunk)

            message = [
                {
                    "role": "system",
                    "content": SYSTEM_CHAT_PROMPT_OPTIMIZED_1
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]

            prompt_tokens = ai_model.count_tokens(user_prompt)
            chunk_tokens = ai_model.count_tokens(chunk)
            logger.info(f"Process {i + 1} chunk of {len(chunks)}, Prompt {prompt_tokens}, chunk {chunk_tokens} tokens")

            ai_answer = ai_model.chat(message, max_tokens=CHUNK_TOKEN_SIZE)
            output = ai_answer["choices"][0]["message"]["content"]
            result.append(output)
        return "".join(result)


class GeminiFixer:
    client: Client

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def fix_broken_html(self, html: str) -> str:
        user_prompt = USER_CHAT_PROMPT_OPTIMIZED.replace("<<<HTML>>>", html)
        for i in range(0, 3):
            logger.info(f"🛁Clearing html with Google Gen ai model  {GEMINI_MODEL}. Attempt {i + 1}")
            try:
                answer = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_CHAT_PROMPT_OPTIMIZED
                    ),
                    contents=user_prompt
                )
                usage = getattr(answer, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", None)
                answer_tokens = getattr(usage, "candidates_token_count", None)
                total_tokens = getattr(usage, "total_token_count", None)
                logger.info(
                    "🛁Gemini API call completed | prompt_tokens=%s answer_tokens=%s total_tokens=%s",
                    prompt_tokens, answer_tokens, total_tokens
                )
                if not answer.text:
                    logger.info(f"AI returned null or empty text - {answer}")

                return _sanitize_markdown(answer.text)
            except BaseException as e:
                logger.info(f"Exception during communication with google AI {e}")
                time.sleep(5)

        raise IOError("Unable to fix html using google ai")


def _sanitize_markdown(text) -> str:
    start = text.find("<")
    end = text.rfind(">")
    if start == -1 or end == -1 or start > end:
        return text  # or return s, depending on your needs
    return text[start:end + 1]
