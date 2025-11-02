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
- **TEST_SCENARIOS.md** - Test scenarios for validating the skill
- **EXAMPLE_SETTINGS.json** - Example Claude Code settings with hooks configured
- **README.md** - This file

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

This skill works best with the Pensieve hooks installed. The streamlined 3-hook system provides:
- **Session start**: MANDATORY protocol requiring memory search before starting work
- **Session end**: Reminder to record learnings before context is lost
- **Git commits**: Prompts to evaluate if commit contains recordable learnings using 3-question rubric

Install hooks with `./install-hooks.sh`. See `hooks/README.md` for complete documentation.

## Testing

See `TEST_SCENARIOS.md` for test cases to verify the skill works correctly.

## Recent Updates

**November 2025 - Simplified & Flexible**:
- Removed detailed template examples and field specifications
- Added "Discovering Pensieve Capabilities" section pointing to `--help`
- Removed hook-specific workflows (Part 2.5)
- Kept core: 3-question rubric, subagent templates, protocols, anti-rationalizations
- Result: ~780 lines removed, more flexible for Pensieve changes

**October 2025 - Superpowers Enforcement**:
- Mandatory protocols (not suggestions)
- Evidence requirements (must show search output)
- Explicit rubric evaluation (silent evaluation = no evaluation)
- Anti-rationalization warnings (13 common failure patterns)

This skill uses enforced processes with verification gates rather than optional suggestions.
