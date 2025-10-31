# Pensieve Memory Management Hooks

This directory contains Claude Code hooks that integrate Pensieve memory management into your development workflow.

## Hook Scripts

### `todo-memory-check.py` (PreToolUse: TodoWrite)
**Non-intrusive memory management reminders**

- **Trigger**: Before any TodoWrite tool execution
- **Action**: Provides system message reminders only (no todo modification)
  - When **pending todos exist**: Reminds to search Pensieve for related memories
  - When **completed todos exist**: Reminds to record learnings using 3-question rubric
- **Purpose**: Gentle nudges to leverage and contribute to memory bank without interfering with todo list management
- **Logging**: Activity logs at `~/.claude/logs/todo-memory-check.log`
- **Non-intrusive**: Does not track state, merge todos, or modify the todo list in any way

### `session-memory-reminder.sh` (SessionStart)
**Session initialization reminder**

- **Trigger**: When a new Claude Code session starts
- **Action**: Displays reminder to search Pensieve for project memories
- **Purpose**: Restore context from previous sessions
- **Message**: Shows quick start command for searching memories

### `session-end-memory-check.sh` (SessionEnd)
**Session completion check**

- **Trigger**: When Claude Code session ends
- **Action**: Reminds you to record significant learnings
- **Purpose**: Capture valuable insights before they're forgotten
- **Guidance**: Provides 3-question rubric for deciding what to record

### `memory-check.sh` (SubagentStop, PostToolUse:Grep)
**Periodic memory reminder**

- **Trigger**: After subagent completes or grep operations
- **Action**: Lightweight nudge to consider recording learnings
- **Purpose**: Catch memory-worthy moments during development

### `user-prompt-memory-check.sh` (UserPrompt)
**User interaction hook**

- **Trigger**: On user prompts
- **Action**: Additional memory check trigger
- **Purpose**: Context-aware memory reminders

### `todo-memory-check.sh` (Legacy bash version)
**Deprecated - kept for reference**

- **Status**: Replaced by `todo-memory-check.py`
- **Reason**: Python version has better logging and reliability

## Installation

Run the install script from the repository root:

```bash
./install-hooks.sh
```

This will:
1. Back up existing hooks to `~/.claude/hooks.backup.TIMESTAMP/`
2. Copy all hooks to `~/.claude/hooks/`
3. Make them executable
4. Create logs directory at `~/.claude/logs/`
5. Display settings.json configuration to verify

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
            "command": "~/.claude/hooks/todo-memory-check.py"
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


## Logging

The Python hook (`todo-memory-check.py`) logs to:
- **Location**: `~/.claude/logs/todo-memory-check.log`
- **Level**: INFO - logs hook triggers and reminders provided
- **Format**: Timestamped entries
- **Use case**: Debugging hook behavior if reminders aren't appearing

### Viewing logs:

```bash
# View recent activity
tail -f ~/.claude/logs/todo-memory-check.log

# View full log
cat ~/.claude/logs/todo-memory-check.log
```

## Troubleshooting

### Hook not triggering

1. Check hook is executable: `ls -la ~/.claude/hooks/`
2. Verify settings.json configuration
3. Restart Claude Code session
4. Check logs for errors

### Python hook issues

1. Verify Python 3 is available: `python3 --version`
2. Check logs: `cat ~/.claude/logs/todo-memory-check.log`
3. Test manually:
   ```bash
   echo '{"tool_input":{"todos":[{"content":"Test","status":"pending","activeForm":"Testing"}]}}' | ~/.claude/hooks/todo-memory-check.py
   ```

### Reminders not appearing

1. Check log output shows hook is triggering: `cat ~/.claude/logs/todo-memory-check.log`
2. Verify hook returns proper JSON structure
3. Ensure `tool_input.todos` path is correct (may change with Claude Code updates)
4. Test manually to verify reminders are generated:
   ```bash
   echo '{"tool_input":{"todos":[{"content":"Test","status":"pending","activeForm":"Testing"}]}}' | ~/.claude/hooks/todo-memory-check.py
   ```

## Development

### Testing hooks locally

```bash
# Test Python hook
echo '{"tool_input":{"todos":[{"content":"Test task","status":"pending","activeForm":"Testing task"}]}}' | ./hooks/todo-memory-check.py

# Test bash hooks
./hooks/session-memory-reminder.sh
./hooks/memory-check.sh
```

### Modifying hooks

1. Edit hook file in `hooks/` directory
2. Test changes locally
3. Run `./install-hooks.sh` to deploy
4. Restart Claude Code session
5. Check logs to verify behavior

## Best Practices

1. **Always search first**: When starting new work, check Pensieve for related memories
2. **Record learnings**: Use the 3-question rubric to decide what's worth recording
3. **Check logs**: If hooks seem off, review logs before debugging
4. **Keep updated**: Pull latest hooks when updating Pensieve

## Memory Management Workflow

The hooks support this workflow:

1. **Session Start** → Reminded to search Pensieve
2. **Create Todo** → Gentle reminder to search for related memories
3. **Work on Task** → Periodic reminders during complex operations
4. **Complete Work** → Prompted to record learnings
5. **Session End** → Final reminder to capture insights

This ensures you never miss opportunities to leverage or contribute to your memory bank.
