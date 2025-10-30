#!/usr/bin/env python3
"""
PreToolUse hook for TodoWrite - Automatically adds Pensieve search todo
This hook fires BEFORE todos are updated, allowing modification of input
Triggers on: pending todos created OR todos marked completed

STATE MANAGEMENT:
- Maintains project-specific state files at ~/.claude/state/<project-hash>/current_todos.json
- Each project (working directory) gets its own isolated todo state
- Merges input todos with state todos to preserve hook-added items
- Input todos take precedence (allows Claude to update status)
- State todos not in input are preserved (prevents accidental deletion)
"""

import json
import sys
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".claude" / "logs"
log_dir.mkdir(exist_ok=True, mode=0o755)
log_file = log_dir / "todo-memory-check.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_state_file():
    """
    Get project-specific state file based on current working directory.

    Creates a unique state directory for each project using a hash of the
    working directory path. This ensures todos don't leak between projects.

    Returns:
        Path: Path to the current_todos.json file for this project
    """
    cwd = Path.cwd()

    # Create stable hash of project path (use first 16 chars for readability)
    project_hash = hashlib.md5(str(cwd).encode()).hexdigest()[:16]

    # Create project-specific state directory
    state_dir = Path.home() / ".claude" / "state" / project_hash
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

    # Store metadata file for debugging/inspection
    metadata_file = state_dir / "project.txt"
    if not metadata_file.exists():
        metadata_file.write_text(str(cwd))
        logging.info(f"Created metadata file for project: {cwd}")

    state_file = state_dir / "current_todos.json"
    logging.debug(f"Using state file: {state_file} (project: {cwd})")

    return state_file


def load_state():
    """Load current todo state from file. Returns empty list if file doesn't exist."""
    state_file = get_state_file()
    try:
        if not state_file.exists():
            logging.info("State file does not exist, returning empty list")
            return []

        with open(state_file, 'r') as f:
            state = json.load(f)
            logging.info(f"Loaded {len(state)} todos from state file")
            return state
    except json.JSONDecodeError as e:
        logging.error(f"State file corrupted: {e}, returning empty list")
        return []
    except Exception as e:
        logging.error(f"Error loading state: {e}", exc_info=True)
        return []


def save_state(todos):
    """Save current todo state to file."""
    state_file = get_state_file()
    try:
        # State directory is already created by get_state_file()
        with open(state_file, 'w') as f:
            json.dump(todos, f, indent=2)
        logging.info(f"Saved {len(todos)} todos to state file")
    except Exception as e:
        logging.error(f"Error saving state: {e}", exc_info=True)


def merge_todos(state_todos, input_todos):
    """
    Merge state todos with input todos intelligently.

    Logic:
    1. Input todos represent Claude's explicit intent (new todos, status updates)
    2. Start with input todos (they take precedence)
    3. Add state todos that aren't in input (preserves hook-added items)

    Matching: By exact content field match
    """
    logging.info(f"Merging {len(state_todos)} state todos with {len(input_todos)} input todos")

    # Build map of input todos by content for fast lookup
    input_content_set = {todo.get('content') for todo in input_todos}
    logging.info(f"Input todos: {list(input_content_set)}")

    # Start with all input todos (Claude's intent)
    result = list(input_todos)

    # Add state todos that aren't mentioned in input (preserves hook-added items)
    preserved_count = 0
    for state_todo in state_todos:
        state_content = state_todo.get('content')
        if state_content and state_content not in input_content_set:
            result.append(state_todo)
            preserved_count += 1
            logging.info(f"Preserved state todo: {state_content}")

    logging.info(f"Merge result: {len(result)} todos ({len(input_todos)} from input, {preserved_count} preserved from state)")
    return result


def main():
    try:
        logging.info("=" * 80)
        logging.info("Hook triggered")

        # Load current state
        state_todos = load_state()

        # Read JSON input from stdin
        input_data = sys.stdin.read()
        logging.info(f"Raw input received: {input_data}")

        try:
            data = json.loads(input_data)
            logging.info(f"Parsed input JSON: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse input JSON: {e}")
            sys.exit(0)

        # Extract todos from tool_input
        tool_input = data.get("tool_input", {})
        input_todos = tool_input.get("todos", [])
        logging.info(f"Found {len(input_todos)} todos in input")

        # Merge input todos with state (preserves hook-added items)
        merged_todos = merge_todos(state_todos, input_todos)

        # Check if there are any pending todos in merged result
        has_pending = any(todo.get("status") == "pending" for todo in merged_todos)
        logging.info(f"Has pending todos after merge: {has_pending}")

        # Check if "Search Pensieve" todo already exists in merged result
        has_pensieve_todo = any(
            "Search Pensieve for related memories" in todo.get("content", "")
            for todo in merged_todos
        )
        logging.info(f"Already has Pensieve todo: {has_pensieve_todo}")

        # Add Pensieve todo if needed
        if has_pending and not has_pensieve_todo:
            pensieve_todo = {
                "content": "Search Pensieve for related memories",
                "activeForm": "Searching Pensieve for related memories",
                "status": "pending"
            }
            merged_todos = [pensieve_todo] + merged_todos
            logging.info(f"Prepended Pensieve todo. New todo count: {len(merged_todos)}")

        # Save merged result to state (exclude completed todos to prevent accumulation)
        todos_to_persist = [todo for todo in merged_todos if todo.get("status") != "completed"]
        filtered_count = len(merged_todos) - len(todos_to_persist)
        if filtered_count > 0:
            logging.info(f"Filtered out {filtered_count} completed todo(s) before saving to state")
        save_state(todos_to_persist)

        # Build response with updated todos
        updated_input = {"todos": merged_todos}

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Merged todos with state to preserve hook-added items",
                "updatedInput": updated_input
            }
        }

        # Add system message if todos were added/preserved
        preserved_count = len(merged_todos) - len(input_todos)
        if preserved_count > 0:
            output["systemMessage"] = f"💾 Preserved {preserved_count} todo(s) from previous state"
            logging.info(f"Added system message about {preserved_count} preserved todos")

        # Check for completed status - suggest recording learnings
        has_completed = any(todo.get("status") == "completed" for todo in merged_todos)
        logging.info(f"Has completed todos: {has_completed}")

        if has_completed:
            memory_reminder = """✅ MEMORY CHECK: Evaluate if you should record learnings to Pensieve

Apply the 3-question rubric:
   1. Complexity: Did this take >30 minutes or involve non-obvious solution?
   2. Novelty: Is this documented elsewhere (README, comments, obvious from code)?
   3. Reusability: Will this help in 3+ months, or on similar tasks?

If 2/3 or 3/3 YES: Use memory-management skill to record to Pensieve
Templates: problem_solved, pattern_discovered, workaround_learned, key_resource"""

            # Append to existing systemMessage or set it
            if "systemMessage" in output:
                output["systemMessage"] += "\n\n" + memory_reminder
            else:
                output["systemMessage"] = memory_reminder
            logging.info("Added memory check reminder for completed todos")

        output_json = json.dumps(output, indent=2)
        logging.info(f"Sending output: {output_json}")
        print(output_json)
        logging.info("Hook completed successfully")
        sys.exit(0)

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
