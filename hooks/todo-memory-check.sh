#!/bin/bash
# PreToolUse hook for TodoWrite - Automatically adds Pensieve search todo
# This hook fires BEFORE todos are updated, allowing modification of input
# Triggers on: pending todos created OR todos marked completed

# PreToolUse hooks receive tool input as JSON via stdin
# For TodoWrite, the input contains: {"todos": [{"content": "...", "status": "...", "activeForm": "..."}]}

# Read JSON input from stdin
input=$(cat)

# Check if there are any pending todos (new work starting)
if echo "$input" | grep -q '"status":\s*"pending"'; then
    # Check if "Search Pensieve" todo already exists
    if ! echo "$input" | grep -q "Search Pensieve for related memories"; then
        # First, prepend the Pensieve todo to the input
        updated_input=$(echo "$input" | jq '.todos |= [{"content": "Search Pensieve for related memories", "activeForm": "Searching Pensieve for related memories", "status": "pending"}] + .')

        # Then construct the hook output JSON
        jq -n \
          --argjson updated "$updated_input" \
          '{
            hookSpecificOutput: {
              hookEventName: "PreToolUse",
              permissionDecision: "allow",
              permissionDecisionReason: "Auto-added Pensieve search todo to prevent reinventing solutions",
              updatedInput: $updated
            },
            systemMessage: "💡 Automatically added '\''Search Pensieve for related memories'\'' todo"
          }'
        exit 0
    fi
fi

# Check for completed status - suggest recording learnings to Pensieve
if echo "$input" | grep -q '"status":\s*"completed"'; then
    echo "✅ MEMORY CHECK: Evaluate if you should record learnings to Pensieve"
    echo ""
    echo "Apply the 3-question rubric:"
    echo "   1. Complexity: Did this take >30 minutes or involve non-obvious solution?"
    echo "   2. Novelty: Is this documented elsewhere (README, comments, obvious from code)?"
    echo "   3. Reusability: Will this help in 3+ months, or on similar tasks?"
    echo ""
    echo "If 2/3 or 3/3 YES: Use memory-management skill to record to Pensieve"
    echo "Templates: problem_solved, pattern_discovered, workaround_learned, key_resource"
fi

exit 0
