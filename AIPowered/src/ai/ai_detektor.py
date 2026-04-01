import logging

import json
from pathlib import Path

from src.ai.model import AiModel

logger = logging.getLogger(__name__)

AUDIT_PROMPT = """
You are an senior editorial auditor.

Analyze the provided HTML article.

Tasks:
1. Assess whether the text shows characteristics of AI-generated writing.
2. Identify any Call-To-Action (CTA), explicit or implicit.
3. Identify promotional or persuasive language.
4. Point out suspicious or borderline cases.

Rules:
- Do not rewrite the text.
- Do not guess intent beyond the content.
- Quote exact sentences when flagging issues.
- If nothing is found, state "none".
- Base conclusions only on textual evidence.

Output is exactly JSON string with this exact schema:
{
  "ai_likelihood": "low | medium | high",
  "ai_signals": [string],
  "cta_found": boolean,
  "cta_items": [
    {
      "type": "direct | soft | promotional",
      "text": "exact quote"
    }
  ],
  "marketing_tone": "none | weak | strong",
  "notes": string
}

This is PART {part} of {amount} of a longer article.
Do NOT assume this is the full text:
<<<HTML>>>
"""


class AiDetektor:
    def __init__(self, workdir: Path):
        self.workdir = workdir

    def audit_article(self, html: str) -> list:
        logger.info("Ai detection")
        ai_model = AiModel(self.workdir)

        chunks = ai_model.chunk_html_semantic(html)
        logger.info(f"Determined {len(chunks)} chunks")
        result = []
        for index, chunk in enumerate(chunks):
            prompt = AUDIT_PROMPT.replace(
                "{part}", str(index + 1)
            ).replace(
                "{amount}", str(len(chunks))
            ).replace("<<<HTML>>>", chunk)

            logger.info(f"Process {index + 1} chunk of {len(chunks)}")
            ai_answer = ai_model.process(prompt, stop_world="</json>")
            output = ai_answer["choices"][0]["text"].strip()
            try:
                result.append(json.loads(output))
            except json.JSONDecodeError as e:
                logger.warning(f"Unable to parse ai answer to json. Json={output}")
                result.append(output)
        return result
