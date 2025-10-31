#!/usr/bin/env python3
"""
PreToolUse hook for TodoWrite - Provides memory management reminders
This hook fires BEFORE todos are updated, providing non-intrusive reminders

SIMPLE REMINDERS ONLY:
- No state tracking or todo preservation
- No modification of todo list
- Just helpful system messages to:
  1. Search Pensieve before starting work (when pending todos exist)
  2. Record learnings to Pensieve after completing work (when completed todos exist)
"""

import json
import sys
import logging
from pathlib import Path

# Setup logging (optional, for debugging)
log_dir = Path.home() / ".claude" / "logs"
log_dir.mkdir(exist_ok=True, mode=0o755)
log_file = log_dir / "todo-memory-check.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    try:
        logging.info("=" * 80)
        logging.info("Hook triggered - providing reminders only")

        # Read JSON input from stdin
        input_data = sys.stdin.read()

        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse input JSON: {e}")
            sys.exit(0)

        # Extract todos from tool_input
        tool_input = data.get("tool_input", {})
        todos = tool_input.get("todos", [])
        logging.info(f"Found {len(todos)} todos in input")

        # Check for pending and completed todos
        has_pending = any(todo.get("status") == "pending" for todo in todos)
        has_completed = any(todo.get("status") == "completed" for todo in todos)

        logging.info(f"Has pending: {has_pending}, Has completed: {has_completed}")

        # Build system message based on todo states
        messages = []

        # MANDATORY reminder to search Pensieve when starting work
        if has_pending:
            messages.append("""🔴 MANDATORY: Search Pensieve before starting work

BEFORE proceeding with ANY pending task, you MUST:
1. Run: pensieve entry search
2. Show the output (even if empty)
3. Acknowledge findings or state "No memories found"

This is NOT optional. Evidence before claims - show the search output.

Use memory-management skill for detailed guidance.""")

        # MANDATORY reminder to evaluate and record learnings
        if has_completed:
            messages.append("""✅ RECORDING DECISION REQUIRED: Apply visible rubric evaluation

You MUST output your rubric evaluation visibly (silent evaluation = no evaluation):

## Pensieve Recording Decision

**What I just completed:** [1-2 sentence summary]

**Rubric Evaluation:**
1. Complexity (>30 min, non-obvious solution): YES/NO
   - Reasoning: [Why yes or no]

2. Novelty (not documented elsewhere): YES/NO
   - Reasoning: [Why yes or no]

3. Reusability (helps in 3+ months): YES/NO
   - Reasoning: [Why yes or no]

**Score: X/3**
**Decision: RECORD / BORDERLINE / SKIP**

- Score 3/3: Spawn subagent to record immediately
- Score 2/3: Ask user with AskUserQuestion
- Score 0-1/3: Acknowledge skip with visible reasoning

Use memory-management skill for templates and detailed guidance.
Exception: Skip rubric for obviously-routine tasks (typos, imports).""")

        # Build response - allow todos through unchanged, just add reminders
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Providing memory management reminders"
            }
        }

        # Add system message if we have any reminders
        if messages:
            output["systemMessage"] = "\n\n".join(messages)
            logging.info(f"Added {len(messages)} reminder(s)")

        output_json = json.dumps(output, indent=2)
        print(output_json)
        logging.info("Hook completed successfully")
        sys.exit(0)

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        # Always allow the tool to proceed even if hook fails
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
