#!/bin/bash
# PostToolUse:Bash hook - Fires after git commits
# Reminds Claude to record significant learnings after committing code

# Read JSON input from stdin
input=$(cat)

# Check if the bash command was a git commit
if echo "$input" | grep -q 'git commit'; then
    cat << 'EOF'
💾 Git Commit Detected - Recording Decision Required

You just made a git commit. Apply the 3-question rubric:

1. Complexity: >30 min, non-obvious solution?
2. Novelty: Not documented elsewhere?
3. Reusability: Helps in 3+ months?

Score 3/3: Record to Pensieve immediately
Score 2/3: Ask user if worth recording
Score 0-1/3: Skip (too routine)

Use memory-management skill for recording guidance.
EOF
fi

exit 0
