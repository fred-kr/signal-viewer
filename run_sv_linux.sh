#!/bin/bash
curl -LsSf https://astral.sh/uv/install.sh | sh
nohup "$HOME/.local/bin/uv" run sv >/dev/null 2>&1 &