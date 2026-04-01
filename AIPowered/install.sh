#!/bin/bash

source .venv/bin/activate
playwright install chromium

pip install requirements.txt
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
