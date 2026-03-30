#!/bin/bash
# hf-download.sh — Robust Hugging Face model downloader with auto-retry
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
#   HF_TOKEN                    — Hugging Face access token (required for gated models)
#   HF_HUB_ENABLE_HF_TRANSFER  — Set to 1 for faster parallel downloads (default: 1)
#   HF_HUB_DISABLE_XET         — Set to 1 to disable xet protocol (default: 1)
#   HF_DOWNLOAD_RETRY_DELAY    — Initial seconds between retries (default: 5)

set -euo pipefail

REPO_ID="${1:?Usage: hf-download.sh <repo_id> [local_dir] [max_retries]}"
LOCAL_DIR="${2:-$(echo "$REPO_ID" | sed 's|.*/||')}"
MAX_RETRIES="${3:-100}"

case "$MAX_RETRIES" in
    ''|*[!0-9]*)
        echo "MAX_RETRIES must be a positive integer, got: $MAX_RETRIES" >&2
        exit 1
        ;;
esac

RETRY_DELAY="${HF_DOWNLOAD_RETRY_DELAY:-5}"
MAX_DELAY=300  # cap exponential backoff at 5 minutes

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
echo "║  HF Token:   ${HF_TOKEN:+(set)}${HF_TOKEN:-(NOT SET, may be rate-limited)}"
echo "╚══════════════════════════════════════════════════╝"
echo ""

mkdir -p "$LOCAL_DIR"

# is_transient_error: inspect captured output for non-recoverable errors
# Returns 1 (false) if the error is clearly non-transient, 0 (true) otherwise
is_transient_error() {
    local output="$1"
    # 401/403 auth errors — no point retrying without fixing the token
    if echo "$output" | grep -qiE '401|403|unauthorized|forbidden|access denied'; then
        return 1
    fi
    # 404 — repo or revision doesn't exist
    if echo "$output" | grep -qiE '404|not found|repository not found'; then
        return 1
    fi
    # Invalid repo ID format
    if echo "$output" | grep -qiE 'invalid repo|invalid repository'; then
        return 1
    fi
    return 0
}

attempt=0
current_delay="$RETRY_DELAY"
while [ $attempt -lt $MAX_RETRIES ]; do
    attempt=$((attempt + 1))

    # Clean stale lock files before each attempt
    find "$LOCAL_DIR" -name "*.lock" -delete 2>/dev/null || true

    echo "[$(date '+%H:%M:%S')] Attempt $attempt/$MAX_RETRIES ..."

    # Capture output to inspect for non-transient errors
    output_file=$(mktemp)
    if hf download "$REPO_ID" --local-dir "$LOCAL_DIR" 2>&1 | tee "$output_file"; then
        rm -f "$output_file"
        echo ""
        echo "Download complete: $LOCAL_DIR"
        SIZE=$(du -sh "$LOCAL_DIR" | cut -f1)
        echo "Total size: $SIZE"
        exit 0
    fi

    captured_output=$(cat "$output_file")
    rm -f "$output_file"

    # Short-circuit on non-transient errors
    if ! is_transient_error "$captured_output"; then
        echo ""
        echo "ERROR: Non-transient failure detected — not retrying."
        echo "Check your token, repo ID, or permissions and try again."
        exit 1
    fi

    echo "[$(date '+%H:%M:%S')] Attempt $attempt failed. Retrying in ${current_delay}s ..."
    sleep "$current_delay"

    # Exponential backoff: double the delay, capped at MAX_DELAY
    current_delay=$((current_delay * 2))
    if [ $current_delay -gt $MAX_DELAY ]; then
        current_delay=$MAX_DELAY
    fi
done

echo "ERROR: Failed after $MAX_RETRIES attempts."
exit 1
