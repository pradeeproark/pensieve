# Memory Management Skill

This directory contains the **memory-management** skill for Claude Code, which guides effective use of the Pensieve memory system.

## Overview

The memory-management skill provides:
- Mandatory protocols for searching and recording memories
- 3-question rubric for deciding what to record
- Anti-rationalization warnings to prevent skipping steps
- Evidence-before-claims enforcement
- Integration with Pensieve CLI

## Files

- **SKILL.md** - Main skill definition (auto-loaded by Claude Code)
- **HOOKS_SETUP.md** - Documentation for configuring hooks
- **TEST_SCENARIOS.md** - Test scenarios for validating the skill
- **EXAMPLE_SETTINGS.json** - Example Claude Code settings with hooks configured

## Deployment

### Quick Install (Recommended)

From the repo root, run:
```bash
./install.sh
```

This installs both the skill and hooks in one command.

### Manual Deployment

To deploy just the skill:
```bash
./install-skill.sh
```

To deploy just the hooks:
```bash
./install-hooks.sh
```

### Deployment Process

The skill is **tracked in this repo** at `.claude/skills/memory-management/` and **deployed to user level** at `~/.claude/skills/memory-management/`.

**Workflow:**
1. Make changes to files in `.claude/skills/memory-management/` (repo)
2. Test changes by running `./install-skill.sh` to deploy to user directory
3. Commit changes to repo when satisfied
4. Users sync updates by running `./install-skill.sh` again

## Version Control

- **Source of truth**: This repo (`.claude/skills/memory-management/`)
- **Deployment target**: User directory (`~/.claude/skills/memory-management/`)
- **DO NOT** edit files in user directory directly - they will be overwritten on next deployment

## Recent Changes

See git history for this directory:
```bash
git log --oneline .claude/skills/memory-management/
```

## Integration with Hooks

This skill works best with the Pensieve hooks installed. The hooks provide:
- Session start reminders to search memories
- Todo-based reminders with rubric template injection
- Session end prompts to record learnings

Install hooks with `./install-hooks.sh` or use the unified `./install.sh`.

## Testing

See `TEST_SCENARIOS.md` for test cases to verify the skill works correctly.

## Superpowers Enforcement

As of the October 2025 update, this skill now uses **superpowers-style enforcement**:
- Mandatory protocols (not suggestions)
- Evidence requirements (must show search output)
- Explicit rubric evaluation (silent evaluation = no evaluation)
- Anti-rationalization warnings (13 common failure patterns)

This transforms the skill from "well-documented suggestions" to "enforced process with verification gates."
