#!/bin/bash
# hf-download.sh — Robust HuggingFace model downloader with auto-retry
# Handles timeouts, connection drops, and lock file cleanup automatically.
#
# Usage:
#   hf-download.sh <repo_id> [local_dir] [max_retries]
#
# Examples:
#   hf-download.sh mlx-community/Qwen3-32B-8bit
#   hf-download.sh mlx-community/Qwen3-32B-8bit ~/.omlx/models/Qwen3-32B-8bit
#   hf-download.sh stabilityai/stable-diffusion-xl-base-1.0 ~/models/sdxl 50
#
# Environment variables:
#   HF_TOKEN                    — HuggingFace access token (required for gated models)
#   HF_HUB_ENABLE_HF_TRANSFER  — Set to 1 for faster parallel downloads (default: 1)
#   HF_HUB_DISABLE_XET         — Set to 1 to disable xet protocol (default: 1)
#   HF_DOWNLOAD_RETRY_DELAY    — Seconds between retries (default: 5)

set -euo pipefail

REPO_ID="${1:?Usage: hf-download.sh <repo_id> [local_dir] [max_retries]}"
LOCAL_DIR="${2:-$(echo "$REPO_ID" | sed 's|.*/||')}"
MAX_RETRIES="${3:-100}"
RETRY_DELAY="${HF_DOWNLOAD_RETRY_DELAY:-5}"

export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

# Load token from env or file
if [ -z "${HF_TOKEN:-}" ] && [ -f ~/.cache/huggingface/token ]; then
    export HF_TOKEN="$(cat ~/.cache/huggingface/token)"
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║  HF Robust Downloader                           ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Repo:       $REPO_ID"
echo "║  Local dir:  $LOCAL_DIR"
echo "║  Max retry:  $MAX_RETRIES"
echo "║  HF Token:   ${HF_TOKEN:+set}${HF_TOKEN:-NOT SET (may be rate-limited)}"
echo "╚══════════════════════════════════════════════════╝"
echo ""

mkdir -p "$LOCAL_DIR"

attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
    attempt=$((attempt + 1))

    # Clean stale lock files before each attempt
    find "$LOCAL_DIR" -name "*.lock" -delete 2>/dev/null || true

    echo "[$(date '+%H:%M:%S')] Attempt $attempt/$MAX_RETRIES ..."

    if hf download "$REPO_ID" --local-dir "$LOCAL_DIR" 2>&1; then
        echo ""
        echo "Download complete: $LOCAL_DIR"
        SIZE=$(du -sh "$LOCAL_DIR" | cut -f1)
        echo "Total size: $SIZE"
        exit 0
    fi

    echo "[$(date '+%H:%M:%S')] Attempt $attempt failed. Retrying in ${RETRY_DELAY}s ..."
    sleep "$RETRY_DELAY"
done

echo "ERROR: Failed after $MAX_RETRIES attempts."
exit 1
