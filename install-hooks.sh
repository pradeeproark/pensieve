#!/bin/bash
# Install Pensieve memory management hooks for Claude Code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DEST="$HOME/.claude/hooks"
LOGS_DIR="$HOME/.claude/logs"
SETTINGS_FILE="$HOME/.claude/settings.json"
BACKUP_DIR="$HOME/.claude/hooks.backup.$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo "Pensieve Hook Installation Script"
echo "============================================"
echo ""

# Check if hooks source directory exists
if [ ! -d "$HOOKS_SRC" ]; then
    echo "❌ Error: hooks directory not found at $HOOKS_SRC"
    exit 1
fi

# Create destination directory if it doesn't exist
if [ ! -d "$HOOKS_DEST" ]; then
    echo "📁 Creating hooks directory: $HOOKS_DEST"
    mkdir -p "$HOOKS_DEST"
fi

# Create logs directory if it doesn't exist
if [ ! -d "$LOGS_DIR" ]; then
    echo "📁 Creating logs directory: $LOGS_DIR"
    mkdir -p "$LOGS_DIR"
fi

# Backup existing hooks if they exist
if [ -d "$HOOKS_DEST" ] && [ "$(ls -A $HOOKS_DEST)" ]; then
    echo "💾 Backing up existing hooks to: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$HOOKS_DEST"/* "$BACKUP_DIR/"
fi

# Copy hooks
echo "📋 Installing hook scripts..."
for hook_file in "$HOOKS_SRC"/*; do
    if [ -f "$hook_file" ]; then
        filename=$(basename "$hook_file")
        echo "  • $filename"
        cp "$hook_file" "$HOOKS_DEST/"
        chmod +x "$HOOKS_DEST/$filename"
    fi
done

echo ""
echo "✅ Hooks installed successfully!"
echo ""
echo "Installed hooks:"
ls -lh "$HOOKS_DEST"
echo ""
echo "============================================"
echo "Next Steps:"
echo "============================================"
echo ""
echo "1. Verify your ~/.claude/settings.json includes these hooks:"
echo ""
echo '   "hooks": {'
echo '     "SessionStart": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/hooks/session-memory-reminder.sh" }] }],'
echo '     "SessionEnd": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/hooks/session-end-memory-check.sh" }] }],'
echo '     "SubagentStop": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/hooks/memory-check.sh" }] }],'
echo '     "PreToolUse": [{ "matcher": "TodoWrite", "hooks": [{ "type": "command", "command": "~/.claude/hooks/todo-memory-check.py" }] }],'
echo '     "PostToolUse": [{ "matcher": "Grep", "hooks": [{ "type": "command", "command": "~/.claude/hooks/memory-check.sh" }] }]'
echo '   }'
echo ""
echo "2. Restart Claude Code for hooks to take effect"
echo ""
echo "3. Check logs at: $LOGS_DIR/todo-memory-check.log"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo "📦 Backup of previous hooks: $BACKUP_DIR"
    echo ""
fi

echo "Done! 🎉"
