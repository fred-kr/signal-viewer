#!/bin/bash
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Starting Signal Viewer..."
"$HOME/.local/bin/uv" run sv &