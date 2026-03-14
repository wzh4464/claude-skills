# Claude Skills

Personal Claude Code skills collection.

## Setup on a new machine

```bash
mv ~/.claude/skills ~/.claude/skills.bak && git clone https://github.com/wzh4464/claude-skills.git ~/.claude/skills
```

## Symlinks

Some skills are symlinks to external repos. Recreate them after cloning if needed:

```bash
ln -sf ~/.agents/skills/academic-researcher ~/.claude/skills/academic-researcher
ln -sf ~/.agents/skills/find-skills ~/.claude/skills/find-skills
ln -sf /path/to/evoprompt-skills/skills/detect-vulnerability ~/.claude/skills/detect-vulnerability
```
