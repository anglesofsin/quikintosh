#!/usr/bin/env bash
set -e
KOKORO_DIR="$HOME/.local/share/say-kokoro"
VENV_DIR="$KOKORO_DIR/venv"
mkdir -p "$KOKORO_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Kokoro venv..."
    nix-shell /home/pg/scripts/kokoro/shell.nix --run '
        python3.12 -m venv '"$VENV_DIR"'
        source '"$VENV_DIR"'/bin/activate
        pip install --upgrade pip wheel setuptools
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
        pip install kokoro onnxruntime numpy
    '
    echo "Kokoro venv created at $VENV_DIR"
else
    echo "Kokoro venv already exists"
fi
