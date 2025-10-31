#!/bin/bash
# Deploy memory-management skill from repo to user-level Claude skills directory

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/.claude/skills/memory-management"
SKILL_DEST="$HOME/.claude/skills/memory-management"
BACKUP_DIR="$HOME/.claude/skills/memory-management.backup.$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo "Memory Management Skill Deployment"
echo "============================================"
echo ""

# Check if skill source directory exists
if [ ! -d "$SKILL_SRC" ]; then
    echo "❌ Error: Skill source not found at $SKILL_SRC"
    exit 1
fi

# Create parent directory if it doesn't exist
SKILL_PARENT="$HOME/.claude/skills"
if [ ! -d "$SKILL_PARENT" ]; then
    echo "📁 Creating skills directory: $SKILL_PARENT"
    mkdir -p "$SKILL_PARENT"
fi

# Backup existing skill if it exists
if [ -d "$SKILL_DEST" ]; then
    echo "💾 Backing up existing skill to: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$SKILL_DEST"/* "$BACKUP_DIR/"
fi

# Deploy skill files
echo "📋 Deploying skill files..."
if [ -d "$SKILL_DEST" ]; then
    rm -rf "$SKILL_DEST"
fi
mkdir -p "$SKILL_DEST"

for file in "$SKILL_SRC"/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        # Skip backup files
        if [[ ! "$filename" =~ \.backup\. ]]; then
            echo "  • $filename"
            cp "$file" "$SKILL_DEST/"
        fi
    fi
done

echo ""
echo "✅ Skill deployed successfully!"
echo ""
echo "Deployed files:"
ls -lh "$SKILL_DEST"
echo ""
echo "============================================"
echo "Skill Location:"
echo "============================================"
echo ""
echo "User-level skill: $SKILL_DEST"
echo "Repo source: $SKILL_SRC"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo "📦 Backup of previous skill: $BACKUP_DIR"
    echo ""
fi

echo "The memory-management skill is now available for use!"
echo ""
echo "To use it: Invoke with Skill tool or it will auto-trigger based on"
echo "its description keywords (memory, recall, remember, etc.)"
echo ""
echo "Done! 🎉"
