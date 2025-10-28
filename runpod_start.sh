#!/bin/bash
set -e

echo "Installing compatible transformers version..."
pip install --no-cache-dir transformers==4.36.2

echo "Starting RunPod handler..."
python -u /app/runpod_handler.py
