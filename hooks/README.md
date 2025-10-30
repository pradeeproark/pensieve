# Pensieve Memory Management Hooks

This directory contains Claude Code hooks that integrate Pensieve memory management into your development workflow.

## Hook Scripts

### `todo-memory-check.py` (PreToolUse: TodoWrite)
**Primary hook for automatic memory integration with stateful todo preservation**

- **Trigger**: Before any TodoWrite tool execution
- **Action**:
  - Maintains state file at `~/.claude/state/current_todos.json`
  - Merges input todos with state to preserve hook-added items
  - Automatically prepends "Search Pensieve for related memories" to any todo list with pending items
  - Input todos take precedence (allows Claude to update status)
  - State todos not in input are preserved (prevents accidental deletion)
  - **Filters out completed todos before saving to state** (prevents accumulation)
- **Purpose**: Ensures you check for existing solutions before starting new work, while preserving todos from being lost when Claude creates new lists
- **Logging**: Detailed logs at `~/.claude/logs/todo-memory-check.log`
- **Smart detection**: Only adds Pensieve todo once, checks if already present
- **State cleanup**: Completed todos appear in current response but don't persist in state

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

## State Management

The `todo-memory-check.py` hook maintains a state file to preserve todos between invocations:

- **Location**: `~/.claude/state/current_todos.json`
- **Purpose**: Prevents accidentally losing todos when Claude creates new lists
- **Merge Logic**:
  1. Load current state from file
  2. Merge input todos (from Claude) with state todos
  3. Input todos take precedence (allows status updates)
  4. State todos not mentioned in input are preserved
  5. **Filter out completed todos** (prevents accumulation)
  6. Save filtered result back to state file
- **State Cleanup**: Completed todos appear in the current hook response but are not persisted to state, preventing indefinite accumulation of completed tasks

### State File Example:

```json
[
  {
    "content": "Search Pensieve for related memories",
    "activeForm": "Searching Pensieve for related memories",
    "status": "pending"
  },
  {
    "content": "Fix authentication bug",
    "status": "in_progress",
    "activeForm": "Fixing authentication bug"
  }
]
```

### Managing State:

```bash
# View current state
cat ~/.claude/state/current_todos.json

# Clear state (resets todo list)
rm ~/.claude/state/current_todos.json

# Backup state
cp ~/.claude/state/current_todos.json ~/.claude/state/current_todos.backup.json
```

## Logging

The Python hook (`todo-memory-check.py`) logs to:
- **Location**: `~/.claude/logs/todo-memory-check.log`
- **Level**: DEBUG - captures all input/output
- **Format**: Timestamped entries with full JSON structures
- **Use case**: Debugging hook behavior and understanding input structure

### Viewing logs:

```bash
# View recent activity
tail -f ~/.claude/logs/todo-memory-check.log

# View full log
cat ~/.claude/logs/todo-memory-check.log

# Search for specific session
grep "session_id" ~/.claude/logs/todo-memory-check.log
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

### Todos not being modified

1. Check log output shows "Merged todos with state"
2. Verify hook returns proper JSON structure
3. Ensure `tool_input.todos` path is correct (may change with Claude Code updates)

### State issues (todos accumulating or not preserving)

1. Check state file exists and is valid JSON: `cat ~/.claude/state/current_todos.json`
2. View merge operations in logs: `grep "Merge result" ~/.claude/logs/todo-memory-check.log`
3. Verify completed todos are being filtered: `grep "Filtered out" ~/.claude/logs/todo-memory-check.log`
4. Count completed todos in state (should be 0): `cat ~/.claude/state/current_todos.json | jq 'map(select(.status == "completed")) | length'`
5. Clear state if needed: `rm ~/.claude/state/current_todos.json`
6. Check state directory permissions: `ls -la ~/.claude/state/`

**Note**: Completed todos should NOT accumulate in the state file. If you see completed todos persisting across sessions, check that you're running the latest version of `todo-memory-check.py`.

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
2. **Create Todo** → "Search Pensieve" automatically added
3. **Work on Task** → Periodic reminders during complex operations
4. **Complete Work** → Prompted to record learnings
5. **Session End** → Final reminder to capture insights

This ensures you never miss opportunities to leverage or contribute to your memory bank.
