---
name: hf-download
description: Use when downloading models from Hugging Face, especially large models (LLM, diffusion, VLM) that fail with timeouts or connection drops. Trigger on "download model", "hf download", "pull model from Hugging Face", or when hf download crashes with httpx.ReadTimeout / RemoteProtocolError.
---

# HF Robust Download

Auto-retry wrapper for `hf download` that handles timeouts, connection drops, and stale lock files.

## Usage

Run the script directly:

```bash
~/.claude/skills/hf-download/hf-download.sh <repo_id> [local_dir] [max_retries] [-- extra_flags...]
```

Or invoke as a Claude skill — Claude will run the script with the right arguments.

## Examples

```bash
# MLX models for oMLX
hf-download.sh mlx-community/Qwen3-32B-8bit ~/.omlx/models/Qwen3-32B-8bit

# Diffusion models
hf-download.sh stabilityai/stable-diffusion-xl-base-1.0 ~/models/sdxl

# With extra hf download flags (include/exclude, revision)
hf-download.sh bigscience/bloom ~/models/bloom 100 -- --include "*.safetensors"
hf-download.sh meta-llama/Llama-3-8B ~/models/llama 50 -- --revision main

# Background download
nohup ~/.claude/skills/hf-download/hf-download.sh black-forest-labs/FLUX.1-dev ~/models/flux > /tmp/hf-flux.log 2>&1 &
```

## What It Handles

| Problem | Solution |
|---------|----------|
| `httpx.ReadTimeout` | Auto-retry with resume |
| `httpx.RemoteProtocolError` | Auto-retry with resume |
| Stale `.lock` files | Cleaned before each attempt |
| Rate limiting (no token) | Reads `~/.cache/huggingface/token` or `HF_TOKEN` env |
| Slow downloads | Enables `hf_transfer` by default |
| xet protocol hangs | Disables xet by default |
| Need `--include`/`--exclude`/`--revision` | Pass extra flags after `--` separator |

## Prerequisites

```bash
uv tool install 'huggingface-hub' --with hf_transfer --force
```

## Environment Variables

- `HF_TOKEN` — access token (reads `~/.cache/huggingface/token` as fallback)
- `HF_DOWNLOAD_RETRY_DELAY` — initial seconds between retries, with exponential backoff (default: 5)
- `HF_HUB_ENABLE_HF_TRANSFER` — parallel downloads (default: 1)
- `HF_HUB_DISABLE_XET` — disable xet protocol (default: 1)

## Network Notes

If using Clash Verge / mihomo, add Hugging Face to DIRECT rules to avoid proxy bottleneck:

```yaml
# In rules override (prepend section)
- DOMAIN-SUFFIX,huggingface.co,DIRECT
- DOMAIN-SUFFIX,hf.co,DIRECT
- DOMAIN-SUFFIX,huggingface.com,DIRECT
```

Must use **Rule mode** (not Global) for rules to take effect.
