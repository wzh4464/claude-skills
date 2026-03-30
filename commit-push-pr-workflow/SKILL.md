---
name: commit-push-pr-workflow
description: Full dev workflow - worktree setup, commit, push, PR, and post-merge cleanup. Use when starting feature work, committing, opening PRs, or cleaning up after merge.
---

# Commit, Push & PR Workflow

Applies to this repo's conventions:
- Do not commit directly to `main`; use a feature branch and a PR.
- PR/issue titles: English. PR bodies/comments: Simplified Chinese by default (unless the request starts with `[EN]`).
- Avoid GitHub CLI `--body` with escaped newlines; prefer `--body-file` or stdin to prevent literal `\\n`.

This skill is written to work well on Windows (PowerShell 5.1+). Bash examples are optional.

## Worktree Setup (Optional)

Use a git worktree when you want an isolated workspace without affecting the current working directory. Skip this section if working directly on the repo.

### 1. Choose worktree directory

Priority order:
1. Use existing `.worktrees/` or `worktrees/` directory (`.worktrees/` wins if both exist)
2. Check CLAUDE.md for a preference
3. Ask user: `.worktrees/` (project-local, hidden) or `~/.config/superpowers/worktrees/<project>/` (global)

### 2. Verify gitignore (project-local only)

```bash
git check-ignore -q .worktrees 2>/dev/null
# If NOT ignored: add to .gitignore and commit before proceeding
```

### 3. Create worktree

```bash
git fetch origin --prune
git worktree add .worktrees/<branch-name> -b <branch-name> origin/main
cd .worktrees/<branch-name>
```

### 4. Run project setup + verify baseline

```bash
# Auto-detect: npm install / pip install -e . / cargo build / etc.
# Run tests to confirm clean baseline
```

## Branch (without worktree)

- Create a feature branch from `main` before making changes:
  - `git fetch origin --prune`
  - `git switch main`
  - `git pull --ff-only`
  - `git switch -c docs/example-change`

## Commit

- Confirm required checks have run for the current change scope before committing (record the exact commands).
- Stage intended files only (prefer `git add -p`).
- Write commit messages using a file (avoid multi-`-m` formatting pitfalls).
- Commit title: `prefix: subject` or `prefix(scope): subject`, English only, ideally <= 50 chars (hard wrap <= 72), no trailing period.
- Include a body for non-trivial changes: blank line after title, wrap at 72 columns, include risk/verification notes.

### Template (PowerShell, UTF-8 without BOM)

```powershell
$msg = @'
fix(scope): concise subject

What changed, why, how (if relevant). Wrap at 72 columns.
Risks/side effects if any.
'@

$path = Join-Path $env:TEMP 'commit_msg.txt'
[System.IO.File]::WriteAllText($path, $msg, [System.Text.UTF8Encoding]::new($false))
git commit -F $path
Remove-Item -Force $path
```

### Template (Bash, optional)

```bash
cat <<'EOF' > /tmp/commit_msg.txt
fix(scope): concise subject

What changed, why, how (if relevant). Wrap at 72 columns.
Risks/side effects if any.
EOF

git commit -F /tmp/commit_msg.txt
rm -f /tmp/commit_msg.txt
```

## Push

- Push only after checks pass.
- Prefer `git push -u origin <branch>` for a new branch.
- Avoid force-push.
  - If history rewrite is required (e.g., credential leak removal), confirm explicitly and expect branch rules (e.g., default-branch non-fast-forward) to block force-push unless temporarily adjusted.
  - If `git-filter-repo` was used: it may remove `origin` automatically; re-add it before pushing.

## Pre-push checklist

- Checks executed (exact commands recorded).
- Commit title/body comply with repo rules.
- User explicitly approved the push (especially for `--force`).

## PR

- Default to a draft PR.

### Option A: GitHub CLI (`gh`)

```powershell
gh --version
gh auth status

@'
Summary:
- ...

Verification:
- ...
'@ | gh pr create --draft --base main --title "docs: ..." --body-file -
```

### Option B: Browser (no extra tools)

- Push the branch, then open:
  - `https://github.com/<owner>/<repo>/pull/new/<branch>`

### Option C: GitHub API (PowerShell, encoding-safe)

- Prefer using an env var token (do not echo it in logs):
  - `$env:GITHUB_TOKEN = '...'`

```powershell
$headers = @{
  Authorization = "token $env:GITHUB_TOKEN"
  'User-Agent' = 'codex-cli'
  Accept = 'application/vnd.github+json'
}

$payload = @{
  title = 'docs: ...'
  head  = '<branch>'
  base  = 'main'
  body  = @"
Summary:
- ...

Verification:
- ...
"@
  draft = $true
} | ConvertTo-Json

$bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
Invoke-RestMethod -Method Post `
  -Uri 'https://api.github.com/repos/<owner>/<repo>/pulls' `
  -Headers $headers `
  -ContentType 'application/json; charset=utf-8' `
  -Body $bytes
```

### Option D: GitHub API via git credential (PowerShell, no env token)

- If `gh` is not installed and you do not have `GITHUB_TOKEN` set, you can reuse the GitHub credential that `git` already has:

```powershell
$cred = "protocol=https`nhost=github.com`n`n" | git credential fill
$token = (($cred | Select-String -Pattern '^password=').Line).Substring(9)

$headers = @{
  Authorization = "token $token"
  'User-Agent'  = 'codex-cli'
  Accept        = 'application/vnd.github+json'
}

$payloadObj = @{
  title = 'docs: ...'
  head  = '<branch>'
  base  = 'main'
  body  = "Summary:`n- ...`n"
  draft = $true
}

$json  = $payloadObj | ConvertTo-Json -Depth 5
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

Invoke-RestMethod -Method Post `
  -Uri 'https://api.github.com/repos/<owner>/<repo>/pulls' `
  -Headers $headers `
  -ContentType 'application/json; charset=utf-8' `
  -Body $bytes
```

If editing PR bodies via GitHub API from PowerShell:
- Serialize JSON as UTF-8 bytes (no BOM) to preserve Chinese text reliably.
- Avoid printing tokens or Authorization headers.

## Post-PR: Automated Code Review

After the PR is created, automatically invoke `/sourcery-review-loop` to:
1. Trigger Sourcery AI code review on the PR
2. Iteratively address review comments, push fixes, and re-trigger review
3. Repeat until the PR is approved by Sourcery

This step is mandatory — do not skip it unless the user explicitly opts out.

## Post-Merge Cleanup

After the PR is merged (or work is otherwise completed), clean up the branch and worktree.

### 1. Verify tests pass

```bash
# Run project test suite before any merge/cleanup
npm test / pytest / cargo test / go test ./...
```

Do NOT proceed if tests fail.

### 2. Present completion options

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request (if not already done)
3. Keep the branch as-is (I'll handle it later)
4. Discard this work
```

### 3. Execute chosen option

#### Option 1: Merge locally

```bash
git switch main
git pull --ff-only
git merge <feature-branch>
# Verify tests on merged result
git branch -d <feature-branch>
```

#### Option 2: Push + PR

(Covered by the Push and PR sections above)

#### Option 3: Keep as-is

No cleanup. Worktree preserved.

#### Option 4: Discard

**Requires explicit confirmation.** Show what will be deleted (branch name, commits, worktree path) and wait for user to type "discard".

```bash
git switch main
git branch -D <feature-branch>
```

### 4. Clean up worktree (Options 1, 2 after merge, 4)

```bash
# Return to main repo if inside worktree
cd <main-repo-path>

# Remove the worktree
git worktree remove .worktrees/<branch-name>

# Prune stale worktree references
git worktree prune
```

Skip worktree cleanup for Option 3 (keep as-is).

### 5. Clean up remote branch (after PR merge)

```bash
# Delete remote branch (usually auto-deleted by GitHub on merge)
git push origin --delete <feature-branch> 2>/dev/null

# Prune remote tracking refs
git fetch origin --prune
```
