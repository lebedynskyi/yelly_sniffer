import os
import re
from pathlib import Path

from huggingface_hub import snapshot_download
from huggingface_hub import list_repo_files

SHARD_RE = re.compile(r"(.*)-00001-of-(\d+)\.gguf$")


def download_model(model_repo: str, model_pattern: str, directory: Path) -> str:
    """
    Downloads a (possibly sharded) GGUF model using a filename pattern
    and returns the path to the first shard (00001-of-XXXXX),
    which is the correct entrypoint for llama.cpp.
    """

    os.makedirs(directory, exist_ok=True)

    # 1. Download all matching files
    snapshot_download(
        repo_id=model_repo,
        local_dir=directory,
        allow_patterns=[model_pattern],
    )

    # 2. Collect downloaded GGUF files
    files = sorted(
        f for f in os.listdir(directory)
        if f.endswith(".gguf")
    )

    if not files:
        raise RuntimeError("No GGUF files downloaded")

    # 3. Find first shard
    for f in files:
        match = SHARD_RE.match(f)
        if match:
            base, total = match.groups()
            total = int(total)

            # 4. Verify all shards exist
            expected = [
                f"{base}-{i:05d}-of-{total:05d}.gguf"
                for i in range(1, total + 1)
            ]

            missing = [s for s in expected if s not in files]
            if missing:
                raise RuntimeError(
                    f"Missing model shards: {missing}"
                )

            return os.path.join(directory, f)

    # 5. Non-sharded GGUF fallback
    if len(files) == 1:
        return os.path.join(directory, files[0])

    raise RuntimeError(
        "Could not determine model entrypoint (no shard 00001 found)"
    )

if __name__ == "__main__":
    print(list_repo_files("bartowski/Mistral-7B-Instruct-v0.3-GGUF"))