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

### Placeholder glossary

| Placeholder | Meaning |
|---|---|
| `<default-branch>` | The repo's primary branch (e.g., `main`, `master`). Detect dynamically or ask the user. |
| `<feature-branch>` | The branch being created for the current work (e.g., `fix/login-bug`). |

## Worktree Setup (Optional)

Use a git worktree when you want an isolated workspace without affecting the current working directory. Skip this section if working directly on the repo.

### 1. Choose worktree directory

Priority order:
1. Use existing `.worktrees/` or `worktrees/` directory (`.worktrees/` wins if both exist)
2. Check CLAUDE.md for a preference
3. Ask user: `.worktrees/` (project-local, hidden) or `~/.config/superpowers/worktrees/<project>/` (global)

### 2. Verify gitignore (project-local only)

If using a project-local worktree directory (e.g., `.worktrees/`), it must be gitignored. Use a rooted pattern (`/.worktrees/`) so only the project-root directory is ignored -- nested paths with the same name are unaffected.

**Always confirm with the user before modifying `.gitignore` and committing**, especially in shared repositories.

If `.gitignore` does not exist yet, create it. If you cannot commit repo-wide ignore changes (e.g., forked or restricted repos), use `.git/info/exclude` instead -- this is local-only and does not require a commit.

#### Bash

```bash
git check-ignore -q .worktrees 2>/dev/null
# If NOT ignored, tell the user:
#   "I need to add /.worktrees/ to .gitignore and commit. Proceed? [y/N]"
# On confirmation:
#   echo '/.worktrees/' >> .gitignore
#   git add .gitignore && git commit -m 'chore: gitignore .worktrees'
# Alternative (no commit needed): echo '/.worktrees/' >> .git/info/exclude
```

#### PowerShell

```powershell
git check-ignore -q .worktrees 2>$null
if ($LASTEXITCODE -ne 0) {
  # Ask user: "I need to add /.worktrees/ to .gitignore and commit. Proceed? [y/N]"
  # On confirmation:
  Add-Content -Path .gitignore -Value '/.worktrees/'
  git add .gitignore
  git commit -m 'chore: gitignore .worktrees'
  # Alternative (no commit needed): Add-Content -Path .git/info/exclude -Value '/.worktrees/'
}
```

### 3. Detect default branch and create worktree

First, detect the default branch. This logic is shared by all worktree creation paths below.

#### Detect default branch (Bash)

```bash
default_branch=$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p')
if [ -z "$default_branch" ]; then
  echo "Could not detect default branch. Please specify (e.g., main, master):"
  read default_branch
  default_branch=${default_branch:-main}
fi
git fetch origin --prune
```

#### Detect default branch (PowerShell)

```powershell
$defaultBranch = (git remote show origin 2>$null | Select-String 'HEAD branch:').Line -replace '.*HEAD branch:\s*', ''
if (-not $defaultBranch) {
  $defaultBranch = Read-Host 'Could not detect default branch. Please specify (e.g., main, master)'
  if (-not $defaultBranch) { $defaultBranch = 'main' }
}
git fetch origin --prune
```

Then create the worktree. The target path depends on the choice made in step 1:
- **Project-local**: `.worktrees/<feature-branch>` (relative to repo root)
- **Global**: `~/.config/superpowers/worktrees/<project>/<feature-branch>`

**Note:** For global paths, derive the project name from the repo root (`git rev-parse --show-toplevel`), not the current directory, to avoid surprises when running from a subdirectory.

#### Create worktree (Bash, project-local)

```bash
git worktree add .worktrees/<feature-branch> -b <feature-branch> origin/$default_branch
cd .worktrees/<feature-branch>
```

#### Create worktree (Bash, global)

```bash
repo_name=$(basename "$(git rev-parse --show-toplevel)")
worktree_dir="$HOME/.config/superpowers/worktrees/$repo_name/<feature-branch>"
git worktree add "$worktree_dir" -b <feature-branch> origin/$default_branch
cd "$worktree_dir"
```

#### Create worktree (PowerShell, project-local)

```powershell
git worktree add .worktrees/<feature-branch> -b <feature-branch> origin/$defaultBranch
Set-Location .worktrees/<feature-branch>
```

#### Create worktree (PowerShell, global)

```powershell
$repoName = Split-Path -Leaf (git rev-parse --show-toplevel)
$worktreeDir = Join-Path $HOME '.config/superpowers/worktrees' $repoName '<feature-branch>'
git worktree add $worktreeDir -b <feature-branch> origin/$defaultBranch
Set-Location $worktreeDir
```

### 4. Run project setup + verify baseline

```bash
# Auto-detect: npm install / pip install -e . / cargo build / etc.
# Run tests to confirm clean baseline
```

## Branch (without worktree)

- Create a feature branch from `<default-branch>` before making changes (usually `main`):
  - `git fetch origin --prune`
  - `git switch <default-branch>`
  - `git pull --ff-only`
  - `git switch -c <feature-branch>`

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
- Prefer `git push -u origin <feature-branch>` for a new branch.
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
'@ | gh pr create --draft --base <default-branch> --title "docs: ..." --body-file -
```

### Option B: Browser (no extra tools)

- Push the branch, then open:
  - `https://github.com/<owner>/<repo>/pull/new/<feature-branch>`

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
  head  = '<feature-branch>'
  base  = '<default-branch>'
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
  head  = '<feature-branch>'
  base  = '<default-branch>'
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

### 1. When to run tests

- **Local merge (Option 1)**: Run the project test suite **before** merging to `<default-branch>`, and again **after** the merge to verify the integrated result.
- **PR already merged via GitHub (Option 2 after merge)**: Tests were already verified by CI before merge. Run tests locally only if you need to confirm your local checkout is clean before cleanup.
- **Discard (Option 4)**: No tests needed -- work is being thrown away.
- **Keep as-is (Option 3)**: No tests needed at cleanup time (branch is preserved for later work).

### 2. Present completion options

```
Implementation complete. What would you like to do?

1. Merge back to <default-branch> locally (run tests, merge, delete branch)
2. Push and create a Pull Request (for branches that were never pushed/PR'd)
3. Keep the branch as-is (I'll handle it later)
4. Discard this work (requires confirmation)
```

### 3. Execute chosen option

#### Option 1: Merge locally

```bash
# Run tests BEFORE merging
npm test / pytest / cargo test / go test ./...

git switch <default-branch>
git pull --ff-only
git merge <feature-branch>

# Verify tests AFTER merge
npm test / pytest / cargo test / go test ./...

git branch -d <feature-branch>
```

#### Option 2: Push + PR

Use this when the branch was developed locally and never pushed or had a PR created. Follow the Push and PR sections above to push the branch and open a PR. After the PR is merged on GitHub, return here for cleanup (steps 4-5).

#### Option 3: Keep as-is

No cleanup. Branch and worktree (if any) are preserved.

#### Option 4: Discard

**Requires explicit confirmation.** Show what will be deleted (branch name, commits, worktree path) and wait for user to type "discard".

```bash
git switch <default-branch>
git branch -D <feature-branch>
```

### 4. Clean up worktree (if one was used)

**Skip this step entirely if no worktree was created** (i.e., you worked directly on the repo). This applies to Options 1, 2 (after PR merge), and 4.

The path depends on where the worktree was created (see step 1 of Worktree Setup).

**Note:** `git worktree remove` requires a clean worktree (no uncommitted changes). If there are uncommitted changes, either commit/stash them first or use `--force` to discard them.

#### Project-local worktree

```bash
# Return to main repo if inside worktree
cd <main-repo-path>

# Remove the worktree (requires clean worktree; use --force to override)
git worktree remove .worktrees/<feature-branch>

# Prune stale worktree references
git worktree prune
```

#### Global worktree

```bash
cd <main-repo-path>

git worktree remove ~/.config/superpowers/worktrees/<project>/<feature-branch>

git worktree prune
```

### 5. Clean up remote branch (after PR merge)

```bash
# Delete remote branch (usually auto-deleted by GitHub on merge)
git push origin --delete <feature-branch> 2>/dev/null

# Prune remote tracking refs
git fetch origin --prune
```
