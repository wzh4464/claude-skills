#!/bin/bash
# hf-download.sh — Robust Hugging Face model downloader with auto-retry
# Handles timeouts, connection drops, and lock file cleanup automatically.
#
# Usage:
#   hf-download.sh <repo_id> [local_dir] [max_retries] [-- extra_hf_flags...]
#
# Examples:
#   hf-download.sh mlx-community/Qwen3-32B-8bit
#   hf-download.sh mlx-community/Qwen3-32B-8bit ~/.omlx/models/Qwen3-32B-8bit
#   hf-download.sh stabilityai/stable-diffusion-xl-base-1.0 ~/models/sdxl 50
#   hf-download.sh bigscience/bloom ~/models/bloom 100 -- --include "*.safetensors"
#
# Environment variables:
#   HF_TOKEN                    — Hugging Face access token (required for gated models)
#   HF_HUB_ENABLE_HF_TRANSFER  — Set to 1 for faster parallel downloads (default: 1)
#   HF_HUB_DISABLE_XET         — Set to 1 to disable xet protocol (default: 1)
#   HF_DOWNLOAD_RETRY_DELAY    — Initial seconds between retries (default: 5)

set -euo pipefail

# Temp file tracking for cleanup on exit/interrupt
output_file=""
last_output_file=""
cleanup() {
    rm -f "${output_file:-}" "${last_output_file:-}" 2>/dev/null
}
trap cleanup EXIT INT TERM

# Check that hf CLI is available
if ! command -v hf >/dev/null 2>&1; then
    echo "ERROR: 'hf' CLI not found on PATH." >&2
    echo "Install it with: uv tool install 'huggingface-hub' --with hf_transfer --force" >&2
    exit 1
fi

# Parse positional args, consuming with shift until "--"
REPO_ID="${1:?Usage: hf-download.sh <repo_id> [local_dir] [max_retries] [-- extra_flags...]}"
shift
LOCAL_DIR="${1:-$(echo "$REPO_ID" | sed 's|.*/||')}"
[ $# -gt 0 ] && shift
MAX_RETRIES="${1:-100}"
[ $# -gt 0 ] && shift

# Skip the "--" separator if present
if [ "${1:-}" = "--" ]; then
    shift
fi
# Everything remaining is extra flags for hf download
EXTRA_FLAGS=("$@")

# Validate MAX_RETRIES
case "$MAX_RETRIES" in
    ''|*[!0-9]*)
        echo "MAX_RETRIES must be a positive integer, got: $MAX_RETRIES" >&2
        exit 1
        ;;
esac
if [ "$MAX_RETRIES" -lt 1 ]; then
    echo "MAX_RETRIES must be >= 1, got: $MAX_RETRIES" >&2
    exit 1
fi

# Validate RETRY_DELAY
RETRY_DELAY="${HF_DOWNLOAD_RETRY_DELAY:-5}"
case "$RETRY_DELAY" in
    ''|*[!0-9]*)
        echo "WARNING: HF_DOWNLOAD_RETRY_DELAY='$RETRY_DELAY' is not a valid integer, using default 5" >&2
        RETRY_DELAY=5
        ;;
esac

MAX_DELAY=300  # cap exponential backoff at 5 minutes

export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

# Load token from env or file
if [ -z "${HF_TOKEN:-}" ] && [ -f ~/.cache/huggingface/token ]; then
    export HF_TOKEN="$(cat ~/.cache/huggingface/token)"
fi

# Display token status without leaking the value
if [ -n "${HF_TOKEN:-}" ]; then
    TOKEN_STATUS="[SET]"
else
    TOKEN_STATUS="[NOT SET] (may be rate-limited)"
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║  HF Robust Downloader                           ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Repo:       $REPO_ID"
echo "║  Local dir:  $LOCAL_DIR"
echo "║  Max retry:  $MAX_RETRIES"
echo "║  HF Token:   $TOKEN_STATUS"
if [ ${#EXTRA_FLAGS[@]} -gt 0 ]; then
echo "║  Extra args: ${EXTRA_FLAGS[*]}"
fi
echo "╚══════════════════════════════════════════════════╝"
echo ""

mkdir -p "$LOCAL_DIR"

# is_transient_error: inspect captured output for non-recoverable errors
# Returns 1 (false) if the error is clearly non-transient, 0 (true) otherwise
is_transient_error() {
    local file="$1"
    # 401/403 auth errors — no point retrying without fixing the token
    if grep -qiE '401|403|unauthorized|forbidden|access denied' "$file"; then
        return 1
    fi
    # 404 — repo or revision doesn't exist
    if grep -qiE '404|not found|repository not found' "$file"; then
        return 1
    fi
    # Invalid repo ID format
    if grep -qiE 'invalid repo|invalid repository' "$file"; then
        return 1
    fi
    return 0
}

attempt=0
current_delay="$RETRY_DELAY"
# Persistent file for storing output of the last failed attempt
last_output_file=$(mktemp)
while [ $attempt -lt $MAX_RETRIES ]; do
    attempt=$((attempt + 1))

    # Clean stale HF download lock files before each attempt
    find "$LOCAL_DIR" -maxdepth 3 -name "*.lock" -type f -delete 2>/dev/null || true

    echo "[$(date '+%H:%M:%S')] Attempt $attempt/$MAX_RETRIES ..."

    # Capture output to inspect for non-transient errors
    output_file=$(mktemp)
    if hf download "$REPO_ID" --local-dir "$LOCAL_DIR" "${EXTRA_FLAGS[@]}" 2>&1 | tee "$output_file"; then
        rm -f "$output_file"
        echo ""
        echo "Download complete: $LOCAL_DIR"
        SIZE=$(du -sh "$LOCAL_DIR" | cut -f1)
        echo "Total size: $SIZE"
        exit 0
    fi

    # Keep last output for final error summary (avoid large shell variable)
    cp "$output_file" "$last_output_file"

    # Short-circuit on non-transient errors
    if ! is_transient_error "$output_file"; then
        echo ""
        echo "ERROR: Non-transient failure detected — not retrying."
        echo "--- Error output (last 10 lines) ---"
        tail -10 "$output_file"
        echo "---"
        echo "Check your token, repo ID, or permissions and try again."
        rm -f "$output_file"
        exit 1
    fi

    rm -f "$output_file"

    echo "[$(date '+%H:%M:%S')] Attempt $attempt failed. Retrying in ${current_delay}s ..."
    sleep "$current_delay"

    # Exponential backoff: double the delay, capped at MAX_DELAY
    current_delay=$((current_delay * 2))
    if [ $current_delay -gt $MAX_DELAY ]; then
        current_delay=$MAX_DELAY
    fi
done

echo ""
echo "ERROR: Failed after $MAX_RETRIES attempts."
if [ -s "$last_output_file" ]; then
    echo "--- Last error output (last 10 lines) ---"
    tail -10 "$last_output_file"
    echo "---"
fi
exit 1
