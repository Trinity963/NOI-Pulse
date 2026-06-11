#!/bin/bash
# ============================================================
# MiniTrini NOI-Pulse — setup.sh
# Platform-aware installer: Linux AVX1 | Linux AVX2/CUDA | Mac
# Architect: Victory Brilliant  |  Co-created with River
# ⟁Σ∿∞
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/minitrini_env"
TRINITY_DIR="$HOME/.trinity"
MODEL_DIR="$HOME/.minitrini/models"

echo "⟁ MiniTrini Setup — NOI-Pulse v10.1"
echo "Repo: $REPO_DIR"

# ── Detect platform ──────────────────────────────────────────
OS="$(uname -s)"
ARCH="$(uname -m)"
AVX2=$(grep -m1 avx2 /proc/cpuinfo 2>/dev/null && echo yes || echo no)
CUDA=$(command -v nvcc &>/dev/null && echo yes || echo no)

echo "Platform: $OS $ARCH | AVX2=$AVX2 | CUDA=$CUDA"

# ── Create dirs ──────────────────────────────────────────────
mkdir -p "$TRINITY_DIR"
mkdir -p "$MODEL_DIR"
mkdir -p "$HOME/.minitrini/logs"
mkdir -p "$HOME/.minitrini/exports"

# ── Virtualenv ───────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
    echo "Creating venv: $VENV"
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

pip install --upgrade pip --quiet

# ── Base requirements ─────────────────────────────────────────
echo "Installing base requirements..."
pip install -r "$REPO_DIR/requirements.txt" --quiet

# ── Torch ─────────────────────────────────────────────────────
if python3 -c "import torch" &>/dev/null; then
    echo "torch already installed — skipping"
elif [ "$CUDA" = "yes" ]; then
    echo "Installing torch + CUDA..."
    pip install torch --index-url https://download.pytorch.org/whl/cu128 --quiet
elif [ "$AVX2" = "yes" ]; then
    echo "Installing torch CPU AVX2..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet
else
    echo "Installing torch CPU AVX1 (pinned 2.3.1)..."
    pip install "torch==2.3.1" --index-url https://download.pytorch.org/whl/cpu --quiet
fi

# ── llama-cpp-python ──────────────────────────────────────────
if python3 -c "import llama_cpp" &>/dev/null; then
    echo "llama-cpp-python already installed — skipping"
elif [ "$CUDA" = "yes" ]; then
    echo "Building llama-cpp-python with CUDA..."
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir --quiet
else
    echo "Building llama-cpp-python CPU..."
    pip install llama-cpp-python --no-cache-dir --quiet
fi

# ── SentenceTransformers model ────────────────────────────────
MODEL_NAME="all-MiniLM-L6-v2"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
if [ ! -d "$MODEL_PATH" ]; then
    echo "Downloading $MODEL_NAME..."
    python3 -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('$MODEL_NAME')
m.save('$MODEL_PATH')
print('Model saved to $MODEL_PATH')
" 2>/dev/null || echo "SentenceTransformer download skipped — install manually if needed"
else
    echo "Model $MODEL_NAME already present"
fi

# ── Deploy VIVARIUM dashboard ─────────────────────────────────
DASH_SRC="$REPO_DIR/tools/vivarium_dashboard.py"
DASH_DST="$TRINITY_DIR/vivarium_dashboard.py"
if [ -f "$DASH_SRC" ]; then
    cp "$DASH_SRC" "$DASH_DST"
    echo "VIVARIUM dashboard deployed → $DASH_DST"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "⟁ Setup complete."
echo "Boot MiniTrini:"
echo "  source $VENV/bin/activate && python3 $REPO_DIR/minitrini_noi_pulse.py"
echo ""
echo "⟁Σ∿∞"
