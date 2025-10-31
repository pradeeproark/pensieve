# Proactive Memory Recording - Hooks Setup Guide

This guide explains how to configure Claude Code hooks to enable proactive memory recording with Pensieve.

## Overview

The proactive memory recording system uses targeted hooks that remind Claude to check for memory-worthy moments without being excessive:

1. **SessionStart Hook**: Reminds Claude to retrieve project memories when starting a session
2. **SessionEnd Hook**: Reminds Claude to record learnings before closing a session
3. **SubagentStop Hook**: Periodic reminder when subagents complete work
4. **PreToolUse TodoWrite Hook**: Instructs Claude to add memory-checking todo BEFORE updating the todo list

This configuration balances comprehensive coverage with minimal noise by triggering at natural checkpoints in your workflow.

## Installation

### Step 1: Verify Hook Scripts Exist

The hook scripts should be installed at:
- `~/.claude/hooks/session-memory-reminder.sh` (SessionStart)
- `~/.claude/hooks/session-end-memory-check.sh` (SessionEnd)
- `~/.claude/hooks/memory-check.sh` (SubagentStop)
- `~/.claude/hooks/todo-memory-check.sh` (PreToolUse TodoWrite)

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
    ],
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/todo-memory-check.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Grep",
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
3. Complete a todo with TodoWrite
4. You should see: `✅ Work Complete: Add a new todo item to check/update Pensieve memory as appropriate`
5. When a subagent completes, you should see: `💡 Memory Check: If you just solved a complex problem...`
6. When ending a session, you should see: `💾 Session End: Consider using memory-management skill to record any significant learnings...`

If you see these messages at the appropriate times, the hooks are working correctly!

## How It Works

### SessionStart Hook
- **When**: Fires when you start a new Claude Code session or resume an existing one
- **Purpose**: Reminds Claude to retrieve existing project memories
- **Action**: Prompts Claude to run `pensieve entry search` to refresh context from previous sessions

### SessionEnd Hook
- **When**: Fires when your Claude Code session is ending or closing
- **Purpose**: Reminds Claude to record significant learnings before context is lost
- **Action**: Encourages final memory recording for end-of-session insights

### SubagentStop Hook
- **When**: Fires when a subagent completes its task
- **Purpose**: Periodic reminder to check if work should be recorded (less frequent than every response)
- **Action**: Triggers Claude to:
  1. Invoke the memory-management skill
  2. Use the 3-question rubric to evaluate if recording is warranted
  3. Spawn a subagent to record memories if appropriate

### PreToolUse TodoWrite Hook
- **When**: Fires BEFORE Claude updates the todo list, when marking todos as completed or finishing work
- **Purpose**: Natural checkpoint to evaluate memory-worthy learnings before committing changes
- **Action**: Instructs Claude to add a new todo item for checking/updating Pensieve memory, applying the 3-question rubric
- **Detection**: Checks for `"status": "completed"` in TodoWrite input JSON to identify work about to be marked complete
- **Advantage**: PreToolUse allows Claude to respond to the instruction before executing TodoWrite, ensuring the memory-checking todo gets added

## Customization

### Adjusting Hook Frequency

The default configuration balances coverage with minimal noise. If you want to adjust:

**Option 1: More Aggressive** (add back Stop hook for every response)
```json
{
  "hooks": {
    "SessionStart": [ /* ... */ ],
    "SessionEnd": [ /* ... */ ],
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
    ],
    "SubagentStop": [ /* ... */ ],
    "PostToolUse": [ /* ... */ ]
  }
}
```

**Option 2: Minimal** (only session boundaries and todo completion)
```json
{
  "hooks": {
    "SessionStart": [ /* ... */ ],
    "SessionEnd": [ /* ... */ ],
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [ /* ... */ ]
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

The default configuration includes a TodoWrite hook (PreToolUse) that parses tool input to detect completed work. You can add more tool-specific hooks:

**Example: Adding Git Commit Hook**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [ /* ... */ ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/check-git-commit.sh"
          }
        ]
      },
      {
        "matcher": "Grep",
        "hooks": [ /* ... */ ]
      }
    ]
  }
}
```

**Example check-git-commit.sh**:
```bash
#!/bin/bash
# Check if bash command was a git commit
input=$(cat)
if echo "$input" | grep -q 'git commit'; then
    echo "💾 Git commit detected - consider recording the solution to Pensieve"
fi
exit 0
```

PostToolUse hooks receive full tool context as JSON via stdin, enabling sophisticated logic based on tool input/output.

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
