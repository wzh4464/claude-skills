---
name: diff-eval-func
description: Evaluate agent-generated code changes against a human-approved PR with deterministic file coverage and function-level coverage analysis. Extracts function/symbol changes from diff hunk headers and compares at granular level. Use when evaluating agent code generation quality, benchmarking AI coding tools, or comparing generated patches against human-approved pull requests. Trigger on "/diff-eval-func", "evaluate diff with function coverage", "function-level diff eval".
argument-hint: <pr-link> <requirements-link> <repo-path-or-patch-file>
---

# Diff Eval (Function-Level): Agent-Generated Code Evaluation

Evaluate how well agent-generated code changes match a human-approved PR, with **deterministic file coverage**, **function-level coverage analysis**, structured scoring, auto-generated file filtering, and dual semantic + data-based coverage analysis.

Key improvements over basic diff-eval:
1. **Deterministic file coverage** -- File set operations are computed via bash scripts, not LLM judgment. This ensures consistent, reproducible results across runs.
2. **Function-level coverage** -- Extracts function/symbol names from diff `@@` hunk headers to compare WHICH functions were modified, not just which files.

## Inputs

The user provides:
1. **PR link** (required) - GitHub PR URL, e.g. `https://github.com/org/repo/pull/123`
2. **Requirements link** (required) - URL to the issue/spec/requirements document
3. **Patch source** (required) - One of:
   - Local repo path containing agent-generated changes (will use `git diff`)
   - Path to a `.patch` or `.diff` file (will read directly)

Parse these from arguments:
- URL containing `/pull/` -> PR link
- Other URL -> requirements link
- Path ending in `.patch` or `.diff` -> patch file path
- Other non-URL path -> repo path
- If any required input is missing, ask the user for it before proceeding

**Optional user-provided metadata:**
- **Handwritten files list** - If the user provides a list of "handwritten files", use this as the authoritative non-auto-generated file list for the PR side, overriding auto-detection in Step 2.

## CRITICAL: Working Directory Rule

**All git commands MUST use `git -C <REPO_PATH>` to explicitly specify the repository directory.**

The shell working directory resets between tool calls. If you run `git diff` without `-C`, it may execute outside the repo and fail with `fatal: not a git repository`. Never rely on `cd` persisting across separate Bash tool calls.

```bash
# WRONG -- will fail if cwd is not the repo
git diff <BASE_COMMIT>

# CORRECT -- always use -C to specify the repo
git -C <REPO_PATH> diff <BASE_COMMIT>

# ALSO CORRECT -- cd && git in the same command
cd <REPO_PATH> && git diff <BASE_COMMIT>
```

Apply this rule to EVERY `git` command in the entire workflow below.

## CRITICAL: Deterministic Coverage Rule

**File coverage and function coverage MUST be computed via deterministic bash set operations, NOT by LLM judgment.**

File coverage is a factual metric -- the patch either modifies a file or it doesn't. This must never vary between runs. Use the bash scripts provided in Steps 3 and 3.5 exactly as written.

The LLM's role is to:
- Classify files as auto-generated vs handwritten (Step 2)
- Perform semantic/qualitative analysis (Step 4)
- Score and write the report (Steps 5-6)

The LLM must NOT:
- Manually count or list file intersections (use the bash script)
- Judge whether a file is "in" a diff by reading the diff (use `--name-only`)
- Compute function coverage by reading hunks (use the `@@` extraction script)

## Workflow

### Step 1: Gather the Three Inputs

#### 1a. Determine the Base Commit (merge base from PR)

First, fetch PR metadata to find the base commit -- the commit the PR was merged onto (or branched from):

```bash
# Get the base ref name and merge commit details
gh pr view <PR_NUMBER> --repo <OWNER/REPO> --json baseRefName,mergeCommit,headRefOid,title,body,files,additions,deletions,changedFiles
```

Then determine the merge base commit hash in the local repo. **All git commands must use `-C <REPO_PATH>`**:

```bash
# Ensure remote refs are up to date
git -C <REPO_PATH> fetch origin

# Option 1: If the PR is merged, use the merge commit's first parent
# (the commit on the base branch just before the merge)
git -C <REPO_PATH> rev-parse <mergeCommit>^1

# Option 2: If the PR's base branch is available locally, find the merge base
# between the PR's base branch and the PR's head commit
git -C <REPO_PATH> merge-base origin/<baseRefName> <headRefOid>

# Option 3: Fall back to finding the fork point
git -C <REPO_PATH> merge-base origin/<baseRefName> HEAD
```

Store this as `BASE_COMMIT`. This is the reference point for the generated diff -- it represents the state of the code before the PR's changes were applied.

**Important**: If `BASE_COMMIT` cannot be determined (e.g., remote branches not fetched), run `git -C <REPO_PATH> fetch origin` and retry. If still unavailable, ask the user for the base commit hash.

#### 1b. Extract the Generated Patch

**If the user provided a patch file path:**
```bash
cat <PATCH_FILE_PATH>
```
Read the patch file directly. Extract file names from `diff --git` lines.

**If the user provided a repo path:**

Get the agent's changes **relative to the base commit**:

```bash
# Get modified/staged changes vs the base commit (NOT HEAD)
git -C <REPO_PATH> diff <BASE_COMMIT>

# Get list of untracked files (excluding .claude directory)
git -C <REPO_PATH> ls-files --others --exclude-standard | grep -v '^\.claude'

# For each untracked file, show its content as a diff-like addition
# (prepend each line with "+")
```

Combine the output into a single "Generated Patch" string. Exclude any files under `.claude/`.

Also collect file-level stats:
```bash
# Files modified/added in the generated patch
git -C <REPO_PATH> diff <BASE_COMMIT> --name-only
git -C <REPO_PATH> ls-files --others --exclude-standard | grep -v '^\.claude'
```

#### 1c. Fetch the Ground Truth Patch (PR diff)

Use `gh` CLI to get the approved PR diff:

```bash
# Extract owner/repo and PR number from the URL
gh pr diff <PR_NUMBER> --repo <OWNER/REPO>
```

Also collect the PR file list:
```bash
gh pr diff <PR_NUMBER> --repo <OWNER/REPO> --name-only
```

#### 1d. Fetch the Issue Statement (requirements)

Use WebFetch to retrieve the requirements document. If it's a GitHub issue, prefer:
```bash
gh issue view <ISSUE_NUMBER> --repo <OWNER/REPO> --json title,body
```

### Step 2: Classify Auto-Generated vs Non-Auto-Generated Files

**If the user provided a "handwritten files" list:** Use that list directly as the non-auto-generated files for the PR side. All other PR files are classified as auto-generated. For the generated patch side, still apply auto-detection rules below.

**Otherwise**, classify every file in both the generated patch and ground truth PR into two categories:

**Auto-generated files** (exclude from core comparison):
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `poetry.lock`, `Gemfile.lock`, `composer.lock`, `Cargo.lock`, `go.sum`
- Build outputs: `dist/`, `build/`, `.next/`, `__pycache__/`, `*.pyc`, `*.min.js`, `*.min.css`, `*.bundle.js`
- Generated code: files with headers like `// Code generated ... DO NOT EDIT`, `# This file is autogenerated`, auto-generated protobuf (`*.pb.go`, `*_pb2.py`), GraphQL codegen, OpenAPI generated clients
- Generated code patterns: `zz_generated.*`, `*_generated.*`, `generated.pb.go`, `*_pb2.py`, `*_pb2_grpc.py`
- OpenAPI/Swagger specs that are auto-generated: `swagger.json`, `openapi.json` (in `api/` or similar directories)
- IDE/tool artifacts: `.idea/`, `.vscode/settings.json`, `.DS_Store`
- Snapshot files: `*.snap`, `__snapshots__/`
- Test data/fixtures that are auto-generated (e.g. roundtrip test data, protobuf binary test data `*.pb`)
- Migration files that are auto-numbered/auto-timestamped
- Any file that contains a clear "auto-generated" or "do not edit" marker in its first 5 lines

**Non-auto-generated (handwritten) files** (core comparison targets):
- Source code, test files, configuration files, documentation, CI/CD configs, Dockerfiles, Makefiles
- Manually written migration files
- Everything not classified as auto-generated above

Present the classification:

| File | Source | Classification | Reason |
|------|--------|---------------|--------|
| `src/foo.go` | Both | Non-auto | Source code |
| `zz_generated.deepcopy.go` | PR only | **Auto-generated** | zz_generated pattern |
| `api/openapi-spec/swagger.json` | PR only | **Auto-generated** | Auto-generated OpenAPI |

**Important**: If uncertain about a file, default to non-auto-generated (conservative approach). If the project has unusual conventions, note them.

### Step 3: Deterministic File Coverage (MUST use bash)

**This step MUST be computed deterministically via bash.** Do NOT manually list or count files.

Save the file lists to temp files and compute set operations:

```bash
# Step 3.1: Save PR non-auto file list (one file per line, sorted)
# If user provided handwritten files list, use that directly
cat <<'EOF' | sort > /tmp/diff-eval-pr-files.txt
<paste each non-auto PR file path, one per line>
EOF

# Step 3.2: Save generated patch file list (one file per line, sorted)
# Extract from patch: grep for 'diff --git' lines, extract b/ path
grep '^diff --git' <PATCH_FILE_OR_DIFF_OUTPUT> | sed 's|^diff --git a/.* b/||' | sort > /tmp/diff-eval-gen-files.txt

# Step 3.3: Compute set operations deterministically
echo "=== PR non-auto files ==="
wc -l < /tmp/diff-eval-pr-files.txt

echo "=== Generated patch files ==="
wc -l < /tmp/diff-eval-gen-files.txt

echo "=== Intersection (covered) ==="
comm -12 /tmp/diff-eval-pr-files.txt /tmp/diff-eval-gen-files.txt

echo "=== Missing from generated (in PR only) ==="
comm -23 /tmp/diff-eval-pr-files.txt /tmp/diff-eval-gen-files.txt

echo "=== Extra in generated (not in PR) ==="
comm -13 /tmp/diff-eval-pr-files.txt /tmp/diff-eval-gen-files.txt

echo "=== Coverage rate ==="
TOTAL=$(wc -l < /tmp/diff-eval-pr-files.txt)
COVERED=$(comm -12 /tmp/diff-eval-pr-files.txt /tmp/diff-eval-gen-files.txt | wc -l)
echo "${COVERED}/${TOTAL}"
```

Use the output of these commands EXACTLY as the file coverage data. Do NOT re-interpret or re-count.

### Step 3.5: Function-Level Coverage (MUST use bash)

**This is a key addition over basic diff-eval.** Even when a file is "covered" (appears in both patches), the generated patch may modify the WRONG functions. This step catches that.

#### 3.5a: Extract function signatures from diff hunk headers

Unified diff `@@` hunk headers include the enclosing function/class name (for languages that support it -- Go, C, Python, Java, etc.). Extract these to identify WHICH functions each diff touches.

```bash
# Extract file + function pairs from the PR diff
# Format: "file_path :: function_signature"
cat <PR_DIFF> | awk '
  /^diff --git/ {
    # Parse "diff --git a/... b/..." robustly via regex, not field splitting
    # This handles file paths containing spaces correctly
    match($0, / b\/(.+)$/, m); file = m[1]
  }
  /^@@.*@@/ {
    func_ctx = $0;
    sub(/^@@[^@]*@@ ?/, "", func_ctx);
    if (func_ctx != "") print file " :: " func_ctx
  }
' | sort -u > /tmp/diff-eval-pr-funcs.txt

# Extract file + function pairs from the generated patch
cat <GEN_PATCH> | awk '
  /^diff --git/ {
    match($0, / b\/(.+)$/, m); file = m[1]
  }
  /^@@.*@@/ {
    func_ctx = $0;
    sub(/^@@[^@]*@@ ?/, "", func_ctx);
    if (func_ctx != "") print file " :: " func_ctx
  }
' | sort -u > /tmp/diff-eval-gen-funcs.txt

# Filter to only non-auto files (using the PR handwritten file list)
# Uses awk field-aware join on the file prefix (before " :: ") to avoid
# substring false positives (e.g., "foo.go" matching "xfoo.go :: func")
awk -F ' :: ' 'NR==FNR {files[$1]; next} ($1 in files)' /tmp/diff-eval-pr-files.txt /tmp/diff-eval-pr-funcs.txt > /tmp/diff-eval-pr-funcs-filtered.txt
awk -F ' :: ' 'NR==FNR {files[$1]; next} ($1 in files)' /tmp/diff-eval-pr-files.txt /tmp/diff-eval-gen-funcs.txt > /tmp/diff-eval-gen-funcs-filtered.txt

echo "=== PR functions (non-auto files) ==="
cat /tmp/diff-eval-pr-funcs-filtered.txt

echo "=== Generated functions (non-auto files) ==="
cat /tmp/diff-eval-gen-funcs-filtered.txt

echo "=== Function intersection ==="
comm -12 /tmp/diff-eval-pr-funcs-filtered.txt /tmp/diff-eval-gen-funcs-filtered.txt

echo "=== Functions missing from generated ==="
comm -23 /tmp/diff-eval-pr-funcs-filtered.txt /tmp/diff-eval-gen-funcs-filtered.txt

echo "=== Extra functions in generated ==="
comm -13 /tmp/diff-eval-pr-funcs-filtered.txt /tmp/diff-eval-gen-funcs-filtered.txt

# Function coverage rate
TOTAL_FUNCS=$(wc -l < /tmp/diff-eval-pr-funcs-filtered.txt)
COVERED_FUNCS=$(comm -12 /tmp/diff-eval-pr-funcs-filtered.txt /tmp/diff-eval-gen-funcs-filtered.txt | wc -l)
echo "Function coverage: ${COVERED_FUNCS}/${TOTAL_FUNCS}"
```

#### 3.5b: Semantic function-level analysis (LLM judgment)

After deterministic extraction, the LLM evaluates the QUALITY of function-level matches:

For each function that appears in BOTH diffs (intersection):
1. **Same function, same intent?** Does the generated change serve the same purpose?
2. **Same function, wrong logic?** The function is touched but the change is semantically incorrect (e.g., wrong feature gate, wrong field name, wrong condition)

Classify each matched function as:
- **Correct**: Same function, semantically equivalent change
- **Wrong logic**: Same function, but the change is incorrect or serves a different purpose
- **Partial**: Same function, partially correct change

This produces the **Effective Function Coverage** = functions with Correct status / total PR functions.

**Important distinction:**
- **Deterministic function coverage** (from bash) = which functions are touched = structural coverage
- **Effective function coverage** (from LLM) = which functions are correctly changed = semantic coverage
- Both are reported separately. The deterministic number is the factual upper bound.

### Step 4: Deep Analysis (Semantic-Based)

This is the qualitative counterpart to Steps 3 and 3.5. Instead of counting files/functions, evaluate **what requirements/changes were actually accomplished**.

#### 4a. Requirements Checklist

Based on the issue statement and PR changes, decompose the task into discrete requirements or change items. Then check each:

| # | Requirement / Change Item | In PR? | In Generated? | Status |
|---|--------------------------|:---:|:---:|--------|
| 1 | Fix null pointer in `processOrder()` | Y | Y | Done |
| 2 | Add validation for negative quantities | Y | Y | Done |
| 3 | Update error messages to include order ID | Y | N | **Missing** |
| 4 | Add unit tests for edge cases | Y | N | **Missing** |
| 5 | (Extra) Add logging to `processOrder()` | N | Y | Extra |

Summarize: **X out of Y requirements completed** (semantic completion rate).

#### 4b. Detailed Comparison for Shared Files

For each non-auto file that appears in both patches, compare:

1. **Change scope**: Does the generated patch modify the same functions/classes/blocks? Or does it touch different parts of the same file?

2. **Approach differences**: Does the generated patch use a fundamentally different approach? (e.g., different algorithm, different API, different pattern)

3. **Missing logic**: Key logic present in the ground truth but absent from the generated patch. Be precise -- name the function, the file, the condition.

4. **Unnecessary changes**: Changes in the generated patch with no counterpart in the ground truth. Assess: harmless, over-engineering, or potentially harmful?

#### 4c. Test Coverage Gap

If the ground truth includes test changes, analyze whether the generated patch's lack of tests (or different tests) is a significant gap. List specific test scenarios covered by the PR but missing from the generated patch.

#### 4d. Dependency & Config Differences

Note any differences in non-auto-generated package dependencies, configuration files, or build scripts.

### Step 5: Scoring

Read the scoring rubric from [references/scoring_rubric.md](references/scoring_rubric.md).

Score each criterion independently on a 0-5 scale. Do NOT compute a weighted total or overall score -- each dimension is reported separately so downstream consumers can apply their own weighting.

- **A. Functional Correctness** (0-5)
- **B. Completeness & Coverage** (0-5)
- **C. Behavioral Equivalence to Ground Truth** (0-5)

For each score, provide a 2-4 sentence justification referencing specific code changes or gaps.

Determine verdict per rubric rules (PASS / PARTIAL / FAIL), based on the individual scores.

### Step 6: Save and Output Report

Save the report as a markdown file at the location specified by the user (or default to `<repo-path>/eval_report.md`). Then present the same content to the user.

Report structure:

```
## Evaluation Report

### Summary
[1-3 sentence high-level summary]

### Verdict: [PASS / PARTIAL / FAIL]

### Base Commit
`<BASE_COMMIT>` -- determined from PR merge base on `<baseRefName>`

### Scores

#### A. Functional Correctness: [X]/5
[2-4 sentence justification. Reference specific functions, logic, or code paths.]

#### B. Completeness & Coverage: [X]/5
[2-4 sentence justification. Reference specific missing/extra files, tests, or config.]

#### C. Behavioral Equivalence to Ground Truth: [X]/5
[2-4 sentence justification. Reference specific semantic differences or similarities.]

### Auto-Generated File Classification

| File | Source | Classification | Reason |
|------|--------|---------------|--------|
| ... | ... | ... | ... |

[X auto-generated files excluded from comparison. Y non-auto files used for analysis.]

### Data-Based Coverage (Non-Auto Files Only)

#### File Set Coverage Rate (Deterministic)
Non-auto PR files: X | Non-auto Generated files: Y | Intersection: Z
**File Coverage Rate: Z/X = XX%**

*(Computed via deterministic bash set operations -- reproducible across runs)*

#### Stats Comparison (Non-Auto Files)
| Metric | Generated Patch | Ground Truth PR |
|--------|----------------|-----------------|
| Non-auto files changed | X | Y |
| Lines added (non-auto) | X | Y |
| Lines deleted (non-auto) | X | Y |
| Test files changed | X | Y |
| Auto-generated files (excluded) | X | Y |

#### File-Level Comparison
| File | Auto? | Generated? | Ground Truth? | Status |
|------|:---:|:---:|:---:|--------|
| ... | ... | ... | ... | ... |

### Function-Level Coverage

#### Deterministic Function Coverage (from hunk headers)
PR functions (non-auto): X | Generated functions: Y | Intersection: Z
**Structural Function Coverage: Z/X = XX%**

*(Extracted from `@@` hunk headers -- deterministic, reproducible)*

| File | PR Function/Context | In Generated? | Status |
|------|-------------------|:---:|--------|
| `pkg/foo.go` | `func ProcessOrder(...)` | Y | Covered |
| `pkg/foo.go` | `func ValidateInput(...)` | N | **Missing** |
| `pkg/bar.go` | `type Config struct` | Y | Covered |

#### Effective Function Coverage (semantic analysis)

For functions in the intersection (touched by both patches):

| File | Function | Structural | Semantic Status | Notes |
|------|----------|:---:|--------|-------|
| `pkg/foo.go` | `ProcessOrder` | Covered | **Correct** | Same fix applied |
| `pkg/foo.go` | `ValidateInput` | Covered | **Wrong logic** | Uses wrong validation rule |

**Effective Function Coverage: X/Y = XX%**
(Only functions with "Correct" semantic status count)

#### Missing Functions (not touched by generated patch)
[List of functions modified in PR but completely absent from generated patch,
grouped by file. These represent the true functional gaps.]

#### Extra Functions (only in generated patch)
[List of functions modified by generated patch but not in PR.
Assess: harmless, over-engineering, or harmful?]

### Semantic Coverage (Requirements-Based)

#### Requirements Checklist
| # | Requirement / Change Item | In PR? | In Generated? | Status |
|---|--------------------------|:---:|:---:|--------|
| ... | ... | ... | ... | ... |

**Semantic Completion: X/Y requirements completed (XX%)**

### Deep Analysis

#### Approach Comparison
[How does the generated patch's approach differ from the ground truth?
Compare at the level of algorithms, patterns, and architectural decisions.]

#### Shared Files: Scope Comparison
[For non-auto files modified by both patches, compare which
functions/classes/blocks are touched. Highlight differences in granularity.]

#### Missing Logic
[Specific functions, conditions, error handling, or edge cases present in
the ground truth but absent from the generated patch. Be precise -- name
the function, the file, the condition.]

#### Unnecessary Changes
[Changes in the generated patch with no ground truth counterpart.
Assess: harmless noise, over-engineering, or potentially harmful?]

#### Test Coverage Gap
[If ground truth includes tests: what test scenarios are covered by
ground truth but missing from generated? If ground truth has no tests,
note that.]

#### Dependency & Config Differences
[Any differences in non-auto-generated package configs, CI, Makefile, etc.]

### Coverage Summary

| Coverage Type | Value | Method |
|--------------|-------|--------|
| File coverage (structural) | X/Y (ZZ%) | Deterministic (bash) |
| Function coverage (structural) | X/Y (ZZ%) | Deterministic (bash) |
| Function coverage (effective/semantic) | X/Y (ZZ%) | LLM analysis |
| Requirements completion | X/Y (ZZ%) | LLM analysis |

### Strengths
- [Bullet list of what the generated patch does well]

### Weaknesses
- [Bullet list of what the generated patch misses or does poorly]

### Recommendations
- [Concrete, actionable suggestions for improving the generated patch]

### Confidence: [0.0-1.0]
[Why this confidence level -- what information was clear vs ambiguous?]
```

## Important Notes

- Always exclude `.claude/` directory from the generated diff
- The base commit for diffing is derived from the PR's merge base, NOT from HEAD -- this ensures the generated diff captures the same scope of changes as the PR
- Auto-generated files are classified and excluded from the core coverage metrics, but listed for transparency
- **File coverage and function coverage are computed deterministically** via bash set operations. These numbers MUST be identical across multiple runs. If they differ, the implementation is buggy.
- Function-level coverage uses the `@@` context line from unified diff format, which includes the enclosing function/class/struct name for supported languages (Go, C, C++, Python, Java, etc.)
- Two levels of function coverage are reported:
  - **Structural**: Was the same function touched? (deterministic)
  - **Effective/Semantic**: Was the same function touched with correct logic? (LLM-judged)
- Three complementary coverage views are provided:
  - **File-level**: File set intersection ratio (deterministic)
  - **Function-level**: Function set intersection ratio (deterministic + semantic)
  - **Requirements-level**: Requirements completion checklist (LLM-judged)
- If the PR or requirements link is inaccessible, inform the user and ask for alternatives
- For very large diffs, focus analysis on the most significant non-auto-generated changes
- When the generated patch takes a completely different approach, still evaluate whether it achieves the same functional outcome
- Score honestly -- a fundamentally different but equally correct approach can still score well on A and B, even if C is lower
- If the user provides a patch file instead of a repo path, the deterministic coverage steps still apply -- just extract file/function lists from the patch file directly
