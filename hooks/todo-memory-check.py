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

        # Reminder to search Pensieve when starting work
        if has_pending:
            messages.append("""💡 TIP: Search Pensieve for related memories before starting work
   Quick: pensieve entry search
   Or use the memory-management skill for guided search""")

        # Reminder to record learnings when completing work
        if has_completed:
            messages.append("""✅ MEMORY CHECK: Consider recording learnings to Pensieve

Apply the 3-question rubric:
   1. Complexity: Did this take >30 minutes or involve non-obvious solution?
   2. Novelty: Is this documented elsewhere (README, comments, obvious from code)?
   3. Reusability: Will this help in 3+ months, or on similar tasks?

If 2/3 or 3/3 YES: Use memory-management skill to record to Pensieve
Templates: problem_solved, pattern_discovered, workaround_learned, key_resource""")

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
