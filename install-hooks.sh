#!/bin/bash
# Install Pensieve memory management hooks for Claude Code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DEST="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
BACKUP_DIR="$HOME/.claude/hooks.backup.$(date +%Y%m%d_%H%M%S)"

# Active hook files to install
ACTIVE_HOOKS=(
    "session-memory-reminder.sh"
    "session-end-memory-check.sh"
    "git-commit-memory-check.sh"
)

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


# Backup existing hooks if they exist
if [ -d "$HOOKS_DEST" ] && [ "$(ls -A $HOOKS_DEST)" ]; then
    echo "💾 Backing up existing hooks to: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$HOOKS_DEST"/* "$BACKUP_DIR/"
fi

# Copy active hooks only
echo "📋 Installing hook scripts..."
for hook_name in "${ACTIVE_HOOKS[@]}"; do
    hook_file="$HOOKS_SRC/$hook_name"
    if [ -f "$hook_file" ]; then
        echo "  • $hook_name"
        cp "$hook_file" "$HOOKS_DEST/"
        chmod +x "$HOOKS_DEST/$hook_name"
    else
        echo "  ⚠️  Warning: $hook_name not found"
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
echo '     "SessionStart": ['
echo '       { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/hooks/session-memory-reminder.sh" }] }'
echo '     ],'
echo '     "SessionEnd": ['
echo '       { "matcher": "*", "hooks": [{ "type": "command", "command": "~/.claude/hooks/session-end-memory-check.sh" }] }'
echo '     ],'
echo '     "PostToolUse": ['
echo '       { "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/git-commit-memory-check.sh" }] }'
echo '     ]'
echo '   }'
echo ""
echo "2. Restart Claude Code for hooks to take effect"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo "📦 Backup of previous hooks: $BACKUP_DIR"
    echo ""
fi

echo "Done! 🎉"
