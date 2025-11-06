#!/bin/bash
# Run stricter pre-commit checks locally
#
# This script runs your personal strict pre-commit configuration.
# The strict config is gitignored and stays on your machine only.
#
# Setup (one-time):
#   cp .pre-commit-config.local.yaml.example .pre-commit-config.local.yaml
#   # Edit .pre-commit-config.local.yaml to customize
#
# Usage:
#   ./scripts/pre-commit-strict.sh [FILES...]
#
# Examples:
#   ./scripts/pre-commit-strict.sh                    # Check all files
#   ./scripts/pre-commit-strict.sh src/pensieve/cli.py  # Check specific file

set -e  # Exit on error

STRICT_CONFIG=".pre-commit-config.local.yaml"
EXAMPLE_CONFIG=".pre-commit-config.local.yaml.example"

# Check if strict config exists
if [ ! -f "$STRICT_CONFIG" ]; then
    echo "❌ Strict config not found: $STRICT_CONFIG"
    echo ""
    echo "To set up:"
    echo "  1. Copy the example config:"
    echo "     cp $EXAMPLE_CONFIG $STRICT_CONFIG"
    echo ""
    echo "  2. Customize it to your preferences (optional)"
    echo ""
    echo "  3. Run this script again"
    exit 1
fi

echo "🔍 Running strict pre-commit checks..."
echo ""

# Run pre-commit with strict config
if [ $# -eq 0 ]; then
    # No arguments: check all files
    pre-commit run --config "$STRICT_CONFIG" --all-files
else
    # Arguments provided: check specific files
    pre-commit run --config "$STRICT_CONFIG" --files "$@"
fi

echo ""
echo "✅ All strict checks passed!"
