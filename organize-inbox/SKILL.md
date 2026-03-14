---
name: organize-inbox
description: Use when user says "整理 inbox" or asks to organize, triage, or file notes from the 0-Inbox directory into the knowledge base.
---

# Organize Inbox

Process files in `0-Inbox/`, categorize, format to project conventions, and move to the correct directory.

## Workflow

1. **List** all files in `0-Inbox/` (ignore `.DS_Store`)
2. **Skip** empty files (0 bytes) — ask user whether to delete
3. For each file with content:
   a. **Read** content, determine topic category
   b. **Rename** with the correct prefix and a descriptive English name (PascalCase with underscores)
   c. **Reformat** content to match project conventions (see below)
   d. **Move** to the target directory (usually `Notes/`)

## File Naming Convention

Pattern: `{prefix}-{Descriptive_Name}.md`

| Prefix | Topic |
|--------|-------|
| `research-` | Research notes, experiment analysis, literature |
| `meeting-` | Meeting minutes |
| `code-` | Programming tips, tools, libraries |
| `math-` | Math derivations, theorems |
| `linux-` | Linux/DevOps |
| `macos-` | macOS tips |
| `hpc-` | HPC / cluster |
| `latex-` | LaTeX |
| `nlp-` | NLP / ML |
| `cfa-` | CFA finance |
| `cityu-` | CityU work |
| `english-` | English learning |
| `rust-` / `cpp-` | Language-specific |

Use existing prefixes. Only introduce a new prefix if none fits.

## Formatting Convention

Every note MUST have:

```markdown
---
toc: true
documentclass: "ctexart"
classoption: "UTF8"
---

# Title

## 一、First Section

Content...

---

## 二、Second Section

Content...
```

### Rules

- **YAML front matter**: `toc: true`, `documentclass: "ctexart"`, `classoption: "UTF8"` — always present
- **Title**: single `#` heading right after front matter
- **Sections**: use `##` with Chinese numbering (一、二、三…) for major sections
- **Sub-sections**: use `###`
- **Section separators**: `---` between major sections
- **Tables**: standard Markdown tables, NEVER ASCII box-drawing
- **Bold**: use `**keyword**` for emphasis on key terms
- **Code**: use backtick `` ` `` for inline code (commands, variables, file names)
- **Lists**: proper Markdown `-` or `1.` with correct indentation
- **No leading spaces**: content lines must not have extra indentation outside of list/code contexts
- **No conversational tone**: remove chatbot-style prompts like "想让我继续吗？"; convert to a proper section (e.g., "改进方向")

## Target Directories

| Content Type | Directory |
|-------------|-----------|
| General notes | `Notes/` |
| Literature with citekey | `Literature/` (use literature-template) |
| Project-specific | `Projects/{project}/` |

## Quick Checklist

- [ ] YAML front matter present
- [ ] Single `#` title
- [ ] `##` sections with Chinese numbering
- [ ] `---` separators between sections
- [ ] Markdown tables (no ASCII art)
- [ ] No leading whitespace on content lines
- [ ] No chatbot-style prompts
- [ ] Correct prefix in filename
- [ ] Moved to correct directory
