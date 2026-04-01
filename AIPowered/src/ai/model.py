import logging

from llama_cpp import Llama
from bs4 import BeautifulSoup, NavigableString, Tag

from src.ai.hug_downloder import download_model

logger = logging.getLogger(__name__)
import time


class AiModel:
    def __init__(self, folder, repo, file, context_size=2048):
        self.folder = folder
        self.repo = repo
        self.file = file

        logger.info(f"Check / Download {self.repo}/{self.file} model exist")
        model_path = download_model(repo, file, folder)

        logger.info("Initializing Llama")
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=context_size,
            n_gpu_layers=-1,  # all layers on GPU (Metal)
            n_batch=256,  # IMPORTANT
            f16_kv=True,
            verbose=False
        )
        pass

    def process(self, prompt, temperature=0.0, max_tokens=1024, stop_world=None):
        return self.llm(
            prompt,
            temperature=temperature,
            top_p=1.0,
            max_tokens=max_tokens,
            stop=stop_world
        )

    def chat(self, messages: list, temperature=0.0, top_p=0.9, repeat_penalty=1.05, max_tokens=1024):
        start = time.perf_counter()

        answer = self.llm.create_chat_completion(
            messages,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            max_tokens=max_tokens
        )

        elapsed = time.perf_counter() - start
        choice = answer["choices"][0]
        finish_reason = choice.get("finish_reason")
        usage = answer.get("usage", {})
        logger.info(
            "LLM result | finish=%s | time=%.2fs | prompt=%s | completion=%s | total=%s",
            finish_reason, elapsed, usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens"),
        )

        return answer

    def count_tokens(self, text: str) -> int:
        return len(self.llm.tokenize(text.encode("utf-8")))

    def chunk_html_preserve_all(
            self,
            html: str,
            max_tokens: int = 2000,
            safety_ratio: float = 0.65,
    ):
        soup = BeautifulSoup(html, "html.parser")

        # Decide where to chunk (usually body, fallback to soup)
        root = soup.body if soup.body else soup

        target_tokens = int(max_tokens * safety_ratio)

        chunks = []
        current = []
        current_tokens = 0

        for node in root.children:
            # Skip empty whitespace-only strings
            if isinstance(node, NavigableString):
                if not node.strip():
                    continue
                text = str(node)
            elif isinstance(node, Tag):
                text = str(node)
            else:
                continue

            tokens = self.count_tokens(text)

            # If single node is too large, force it into its own chunk
            if tokens > target_tokens:
                if current:
                    chunks.append("".join(current))
                    current = []
                    current_tokens = 0
                chunks.append(text)
                continue

            if current_tokens + tokens > target_tokens and current:
                chunks.append("".join(current))
                current = []
                current_tokens = 0

            current.append(text)
            current_tokens += tokens

        if current:
            chunks.append("".join(current))

        return chunks
