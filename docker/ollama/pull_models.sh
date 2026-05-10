#!/bin/sh
set -e
echo "Pulling chat model..."
ollama pull qwen2.5:14b || echo "Failed to pull chat model, continuing..."
echo "Pulling embedding model..."
ollama pull nomic-embed-text || echo "Failed to pull embedding model, continuing..."
echo "Models ready."
