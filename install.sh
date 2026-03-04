#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Kokoro TTS CLI installer ==="

# System dependencies
if command -v apt-get &>/dev/null; then
    echo "Installing system dependencies..."
    sudo apt-get install -y espeak-ng libportaudio2
elif command -v brew &>/dev/null; then
    echo "Installing system dependencies..."
    brew install espeak portaudio
else
    echo "WARNING: Could not install system dependencies (espeak-ng, portaudio). Install them manually."
fi

# Install uv if not present (used to manage Python versions and venvs)
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for the rest of this script
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create venv with Python 3.12 (kokoro requires >=3.10,<3.13)
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with Python 3.12..."
    uv venv .venv --python 3.12
fi

# Install Python dependencies
echo "Installing Python dependencies..."
uv pip install --python .venv/bin/python -r requirements.txt

# Make tts.py executable
chmod +x tts.py

echo ""
echo "Done! You can run the tool with:"
echo "  .venv/bin/python tts.py \"Hello, world!\""
echo ""
echo "To install as a system command 'tts' (uses the venv):"
echo "  sudo ln -sf \$(pwd)/tts.py /usr/local/bin/tts"
echo "  sudo sed -i '1s|.*|#!$(pwd)/.venv/bin/python3|' /usr/local/bin/tts"
