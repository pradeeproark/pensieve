# Pensieve Memory Management Hooks

This directory contains Claude Code hooks that integrate Pensieve memory management into your development workflow.

## Hook Scripts

### `session-memory-reminder.sh` (SessionStart)
**Mandatory session initialization protocol**

- **Trigger**: When a new Claude Code session starts
- **Action**: Displays MANDATORY protocol checklist
  - Invoke memory-management skill
  - Search Pensieve for project memories
  - Show search output (even if empty)
  - Acknowledge findings
- **Purpose**: Restore context from previous sessions and prevent duplicate work
- **Enforcement**: Most critical hook - ensures memory search happens first

### `session-end-memory-check.sh` (SessionEnd)
**Session completion reminder**

- **Trigger**: When Claude Code session ends
- **Action**: Reminds to record significant learnings before context is lost
- **Purpose**: Capture valuable insights before session closes
- **Guidance**: Quick reminder to use memory-management skill

### `git-commit-memory-check.sh` (PostToolUse:Bash)
**Post-commit recording reminder**

- **Trigger**: After git commits are made
- **Action**: Detects git commit commands and displays recording decision prompt
- **Purpose**: Catch memory-worthy moments at natural checkpoints
- **Message**: Shows 3-question rubric for deciding whether to record

## Installation

Run the install script from the repository root:

```bash
./install-hooks.sh
```

This will:
1. Back up existing hooks to `~/.claude/hooks.backup.TIMESTAMP/`
2. Copy all active hooks to `~/.claude/hooks/`
3. Make them executable
4. Display settings.json configuration to verify

## Configuration

The hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/session-memory-reminder.sh"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/session-end-memory-check.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/git-commit-memory-check.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Behavior

### Session Start Hook
Fires once per session at the beginning. Shows MANDATORY checklist requiring:
1. Memory-management skill invocation
2. Pensieve search execution
3. Evidence display (output shown)
4. Explicit acknowledgment of results

**Critical**: This is not a suggestion. Claude MUST complete this protocol before responding to user requests.

### Session End Hook
Fires once per session at the end. Simple reminder to record learnings using the memory-management skill before context is lost.

### Git Commit Hook
Fires after every Bash tool execution. The hook script:
1. Parses JSON stdin from PostToolUse event
2. Checks if command contains "git commit"
3. Only displays reminder if git commit detected
4. Shows 3-question rubric for recording decision

**Lightweight**: No performance impact. Only shows message after actual commits.

## Troubleshooting

### Hook not triggering

1. Check hook is executable: `ls -la ~/.claude/hooks/`
2. Verify settings.json configuration
3. Restart Claude Code session

### Git commit hook not showing

1. Verify hook detects commits: `echo '{"tool_input":{"command":"git commit -m test"}}' | ~/.claude/hooks/git-commit-memory-check.sh`
2. Check hook is executable
3. Verify PostToolUse:Bash is configured in settings.json

### Hooks triggering but messages not appearing

1. Check that hooks exit with code 0: `echo $?` after manual execution
2. Verify JSON output format for hooks that return structured data
3. Restart Claude Code session

## Development

### Testing hooks locally

```bash
# Test session hooks
./hooks/session-memory-reminder.sh
./hooks/session-end-memory-check.sh

# Test git commit hook
echo '{"tool_input":{"command":"git commit -m test"}}' | ./hooks/git-commit-memory-check.sh
```

### Modifying hooks

1. Edit hook file in `hooks/` directory
2. Test changes locally
3. Run `./install-hooks.sh` to deploy
4. Restart Claude Code session

## Best Practices

1. **Always search first**: When starting new work, check Pensieve for related memories
2. **Apply the rubric**: Use the 3-question evaluation to decide what's worth recording
3. **Record at commits**: Git commits are natural checkpoints for memory evaluation
4. **Keep hooks lightweight**: Hooks should exit quickly to avoid workflow delays

## Memory Management Workflow

The hooks support this streamlined workflow:

1. **Session Start** → MANDATORY memory search protocol
2. **Work on Task** → Normal development workflow
3. **Git Commit** → Prompted to evaluate if commit contains recordable learnings
4. **Session End** → Final reminder to capture any missed insights

This ensures you never miss opportunities to leverage or contribute to your memory bank without being intrusive during active development.
