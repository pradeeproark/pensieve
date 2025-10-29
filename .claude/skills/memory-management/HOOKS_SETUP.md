# Proactive Memory Recording - Hooks Setup Guide

This guide explains how to configure Claude Code hooks to enable proactive memory recording with Pensieve.

## Overview

The proactive memory recording system uses two simple hooks that remind Claude to check for memory-worthy moments:

1. **SessionStart Hook**: Reminds Claude to retrieve project memories when starting a session
2. **Stop Hook**: Periodic reminder to check if recent work should be recorded

## Installation

### Step 1: Verify Hook Scripts Exist

The hook scripts should be installed at:
- `~/.claude/hooks/session-memory-reminder.sh`
- `~/.claude/hooks/memory-check.sh`

If they don't exist, they were created during the memory-management skill setup.

### Step 2: Configure Hooks in Claude Code Settings

Add the following configuration to `~/.claude/settings.json`:

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
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/memory-check.sh"
          }
        ]
      }
    ]
  }
}
```

**NOTE**: The `~/` notation will expand to your home directory automatically.

### Step 3: Verify Hooks Are Working

1. Start a new Claude Code session
2. You should see: `📝 Session Start: Use memory-management skill to retrieve and record project memories`
3. Complete any Claude interaction
4. You should see: `💡 Memory Check: If you just solved a complex problem...`

If you see these messages, the hooks are working correctly!

## How It Works

### SessionStart Hook
- **When**: Fires when you start a new Claude Code session or resume an existing one
- **Purpose**: Reminds Claude to retrieve existing project memories
- **Action**: Prompts Claude to run `pensieve entry search --project $(pwd)` to refresh context

### Stop Hook
- **When**: Fires when Claude finishes responding to you
- **Purpose**: Reminds Claude to check if recent work should be recorded
- **Action**: Triggers Claude to:
  1. Invoke the memory-management skill
  2. Use the 3-question rubric to evaluate if recording is warranted
  3. Spawn a subagent to record memories if appropriate

## Customization

### Adjusting Hook Frequency

The Stop hook fires after every Claude response, which might feel too frequent. You can:

**Option 1: Disable Stop Hook** (rely on SessionStart only)
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
    ]
  }
}
```

**Option 2: Use SubagentStop Instead** (only remind when subagents complete)
```json
{
  "hooks": {
    "SessionStart": [ /* ... */ ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/memory-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Custom Hook Messages

Edit the hook scripts directly to change the reminder messages:

```bash
# Example: More concise Stop hook
echo "💾 Check: Worth recording to Pensieve?"
```

## Troubleshooting

### Hooks Not Firing

1. **Check file permissions**: Hooks must be executable
   ```bash
   chmod +x ~/.claude/hooks/*.sh
   ```

2. **Check settings.json syntax**: Validate JSON with `jq`
   ```bash
   jq . ~/.claude/settings.json
   ```

3. **Check absolute paths**: Ensure paths in settings.json are correct
   ```bash
   ls -l ~/.claude/hooks/
   ```

### Hook Errors

If you see hook error messages:

1. **Test hooks manually**:
   ```bash
   ~/.claude/hooks/session-memory-reminder.sh
   ~/.claude/hooks/memory-check.sh
   ```

2. **Check hook exit codes**: Hooks should exit with code 0 (success)

3. **Review hook output**: Hooks should only output reminder messages, nothing else

## Advanced: Tool-Specific Hooks

You can make hooks more targeted by using PostToolUse hooks:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "echo '💡 Task completed - consider recording learnings'"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/check-git-commit.sh"
          }
        ]
      }
    ]
  }
}
```

This approach requires more sophisticated hook scripts that parse tool context from stdin.

## Next Steps

After setting up hooks:

1. Review the [memory-management skill](SKILL.md) for the full workflow
2. Test the system by solving a complex problem and observing if Claude records it
3. Adjust hook frequency and messages based on your preferences
4. Create project-specific templates for your codebases

## Resources

- [Claude Code Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [memory-management Skill](SKILL.md)
- [Pensieve Documentation](https://github.com/yourusername/pensieve)
