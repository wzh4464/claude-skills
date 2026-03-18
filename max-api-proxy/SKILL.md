---
name: max-api-proxy
description: Manage claude-max-api-proxy on localhost:3456. Start, stop, health check, system prompt override, NO_PROXY setup, and troubleshooting.
---

# Claude Max API Proxy

Manages the `claude-max-api-proxy` — a local service that translates OpenAI-format API calls into Claude Code CLI invocations, powered by the user's Claude Max/Pro subscription at zero API cost.

```
App (OpenAI format) → localhost:3456 → Claude Code CLI → Anthropic (subscription)
```

## Current setup

- **Running version**: npm `claude-max-api-proxy@1.0.0` (original author `atalovesyou`, repo deleted) with manual patch for proxy env vars
- **Upstream**: [GodYeh/claude-max-api-proxy](https://github.com/GodYeh/claude-max-api-proxy) v1.3.0 (actively maintained, openclaw integration)
- **Fork**: [wzh4464/claude-max-api-proxy](https://github.com/wzh4464/claude-max-api-proxy) (forked from GodYeh)
- **Local clone**: `/home/jie/claude-max-api-proxy/` (GodYeh version source)
- **Installed at**: `$(npm root -g)/claude-max-api-proxy/` (npm version with patch)

### Version differences

| | npm v1.0.0 (current, patched) | GodYeh v1.3.0 |
|---|---|---|
| Proxy env vars | Stripped by default, **patched** to use NO_PROXY | Passes through via `...process.env` |
| Tool calling | No | Yes (OpenAI-format external tools via text markers) |
| Bleed detection | No | Yes (prevents `[User]` tag leakage) |
| Activity timeout | 20min fixed | 10min inactivity watchdog |
| `--dangerously-skip-permissions` | No | Yes |
| openclaw integration | No | Yes (oc-tool, gateway token, Telegram/Discord/Slack) |
| Requires `~/.openclaw/workspace/` | No | Yes |

### Migrating to GodYeh version

If needed in the future:

```bash
npm uninstall -g claude-max-api-proxy
mkdir -p ~/.openclaw/workspace
cd /home/jie/claude-max-api-proxy && npm install -g .
```

## Operations

Localhost curl/requests must bypass the system HTTP proxy. Use `NO_PROXY` or prefix with cleared vars.

### Start

If behind a system proxy (e.g. `http_proxy` is set for outbound access), keep proxy vars and add `NO_PROXY`:

```bash
export NO_PROXY=localhost,127.0.0.1
export no_proxy=localhost,127.0.0.1
claude-max-api &
```

If no system proxy is needed:

```bash
http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= claude-max-api &
```

Wait ~5 seconds for startup, then verify with health check.

### Stop

```bash
pkill -f "claude-max-api"
```

### Health check

```bash
HTTP_PROXY= http_proxy= curl -s http://127.0.0.1:3456/health
```

Expected: `{"status":"ok",...}`

### List available models

```bash
HTTP_PROXY= http_proxy= curl -s http://127.0.0.1:3456/v1/models
```

Models: `claude-opus-4`, `claude-sonnet-4`, `claude-haiku-4`

### Test a completion

For longer or multi-message payloads, use a JSON file to avoid shell escaping issues (control characters in `-d '...'` cause `Bad control character in string literal` errors):

```bash
cat > /tmp/test.json << 'EOF'
{
  "model": "claude-sonnet-4",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "max_tokens": 10
}
EOF

HTTP_PROXY= http_proxy= curl -s http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @/tmp/test.json
```

Simple inline test (short payloads only):

```bash
HTTP_PROXY= http_proxy= curl -s http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-opus-4","messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'
```

## Connecting downstream apps

Any OpenAI-compatible client works with these settings:

```
OPENAI_API_KEY=not-needed
OPENAI_BASE_URL=http://localhost:3456/v1
```

The API key value is ignored — authentication is handled by the Claude Code CLI session.

**IMPORTANT: Add `NO_PROXY` to prevent system HTTP proxy from intercepting localhost in Python:**

```
NO_PROXY=localhost,127.0.0.1
no_proxy=localhost,127.0.0.1
```

Add these to `.env` or set in code before any HTTP calls. Without this, Python's `httpx`/`requests` will route localhost traffic through the system proxy, causing 503 errors.

## System Prompt Override

Claude Code CLI injects its own system prompt (coding-assistant persona). For non-coding tasks (classification, analysis, etc.), **you must send a `role: "system"` message** to override it.

The proxy extracts system messages from the OpenAI messages array and passes them to Claude CLI via `--system-prompt`, replacing the default.

### Python example

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:3456/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "system", "content": "You are a vulnerability classifier. Respond with exactly one category name."},
        {"role": "user", "content": "Classify this code:\n\nchar buf[32]; strcpy(buf, user_input);"},
    ],
    max_tokens=20,
)
```

### For libraries that only accept a prompt string

Split the prompt into system + user parts. Everything before the input placeholder is the system prompt:

```python
def split_system_user(prompt: str, code: str, marker="{input}"):
    if marker in prompt:
        idx = prompt.index(marker)
        system = prompt[:idx].rstrip()
        user = prompt[idx:].replace(marker, code)
        return system, user
    return None, prompt.replace(marker, code)
```

Then pass `system_prompt` as a kwarg to your generate/batch_generate calls.

### Without system prompt

If you do NOT send a system message, Claude Code's default system prompt will be used. This causes the model to behave as a coding assistant rather than following your task-specific instructions, leading to verbose/unhelpful responses for classification tasks.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection refused on 3456 | Proxy not running | Start it (see above) |
| 503 through system curl | HTTP proxy intercepting localhost | Prefix command with `HTTP_PROXY= http_proxy=` |
| 503 from Python httpx/requests | System proxy intercepting localhost | Add `NO_PROXY=localhost,127.0.0.1` to `.env` or environment |
| 403 "Request not allowed" from CLI subprocess | npm v1.0.0 strips proxy env vars from subprocess | Apply the subprocess env patch below |
| Model ignores instructions | Claude Code default system prompt active | Send `role: "system"` message to override (see System Prompt Override) |
| Auth errors from proxy | Claude CLI session expired | Run `claude` to re-authenticate |
| `Bad control character in string literal` | Hidden chars (newlines, tabs) in shell `-d '...'` JSON | Use `curl -d @file.json` with a JSON file instead of inline |
| Request timeout | Default 20min timeout exceeded | Edit `$(npm root -g)/claude-max-api-proxy/dist/subprocess/manager.js` — change `DEFAULT_TIMEOUT` |
| GodYeh version: spawn fails with code -2 | `~/.openclaw/workspace/` directory missing | `mkdir -p ~/.openclaw/workspace` |

### Fix: 403 when system proxy is required (npm v1.0.0 only)

The npm version's subprocess manager (`dist/subprocess/manager.js`) deletes all proxy env vars before spawning `claude` CLI. This prevents the CLI from reaching Anthropic's API when the system **requires** a proxy for outbound traffic. GodYeh v1.3.0 does NOT have this bug.

**Patch** — in `$(npm root -g)/claude-max-api-proxy/dist/subprocess/manager.js`, replace:

```javascript
// Strip proxy env vars so Claude CLI connects directly to Anthropic
const cleanEnv = { ...process.env };
delete cleanEnv.http_proxy;
delete cleanEnv.https_proxy;
delete cleanEnv.HTTP_PROXY;
delete cleanEnv.HTTPS_PROXY;
delete cleanEnv.PROXY_URL;
```

with:

```javascript
// Keep proxy env vars (needed for outbound access to Anthropic API)
// but set NO_PROXY to prevent localhost/127.0.0.1 interception
const cleanEnv = { ...process.env };
cleanEnv.NO_PROXY = "localhost,127.0.0.1";
cleanEnv.no_proxy = "localhost,127.0.0.1";
```

After patching, restart the proxy service. **This patch has been applied to the current installation.**

## Prerequisites

- Node.js 20+ (`node --version`)
- Claude Code CLI authenticated (`claude --version`)
- Active Claude Max or Pro subscription
- Install (npm): `npm install -g claude-max-api-proxy` (v1.0.0, needs patch)
- Install (GodYeh): `cd /home/jie/claude-max-api-proxy && npm install -g .`
