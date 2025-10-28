# Pensieve

Memory recording tool for Claude Code agents - capture and retrieve structured memory events across sessions.

## Overview

Pensieve enables Claude Code agents to maintain context and continuity by recording significant events, decisions, and patterns in a structured format. All memories are stored using customizable templates with typed fields and can be queried efficiently.

## Installation

### Development
```bash
pip install -e ".[dev]"
```

### Building Executable
```bash
python build/build.py
```

## Quick Start

### 1. Create a Template

**Inline field definitions:**
```bash
pensieve template create problem_solved \
  --project $(pwd) \
  --description "For recording solved problems" \
  --field "problem:text:required:max_length=500:What was the issue?" \
  --field "solution:text:required:max_length=1000:How was it fixed?" \
  --field "learned:text:required:max_length=500:Key takeaway"
```

**From JSON file:**
```bash
pensieve template create problem_solved \
  --project $(pwd) \
  --from-file template.json
```

### 2. Record a Memory

**Inline field values:**
```bash
pensieve entry create problem_solved \
  --project $(pwd) \
  --field problem="Authentication failing in CI" \
  --field solution="Added environment variable" \
  --field learned="Always check CI config"
```

**From JSON file:**
```bash
pensieve entry create problem_solved \
  --project $(pwd) \
  --from-file entry.json
```

### 3. Search Memories
```bash
# Search by project
pensieve entry search --project $(pwd)

# Search by template
pensieve entry search --template problem_solved

# Search by field value
pensieve entry search --field problem --value "authentication" --substring
```

## Field Types

- **boolean**: True/False values
- **text**: String values (with optional max_length)
- **url**: Validated URLs (with optional scheme restrictions)
- **timestamp**: ISO8601 datetime (with optional auto_now)
- **file_reference**: File paths (with optional file type restrictions)

## Commands

### Templates
- `pensieve template create <name> --project <path> --field "..." [--field "..."]` - Create new template with inline fields
- `pensieve template create <name> --project <path> --from-file template.json` - Create template from JSON
- `pensieve template list` - List all templates
- `pensieve template show <name>` - Show template details
- `pensieve template export <name>` - Export template as JSON
- `pensieve template import <file>` - Import template from JSON

### Entries
- `pensieve entry create <template> --project <path> --field key=value [--field ...]` - Create entry with inline values
- `pensieve entry create <template> --project <path> --from-file entry.json` - Create entry from JSON
- `pensieve entry list` - List recent entries
- `pensieve entry show <id>` - Show entry details
- `pensieve entry search` - Search entries with filters
- `pensieve entry export` - Export entries as JSON

### System
- `pensieve migrate` - Apply pending migrations
- `pensieve migrate status` - Show migration status
- `pensieve version` - Show tool and schema version

## Database Location

By default, the database is stored at `~/.pensieve/pensieve.db`. You can override this with the `PENSIEVE_DB` environment variable:

```bash
export PENSIEVE_DB=/path/to/custom/location/pensieve.db
```

## Development

### Run Tests
```bash
pytest
```

### Format Code
```bash
black src tests
ruff check src tests
```

### Type Check
```bash
mypy src
```

## Documentation

See `docs/goals.md` for detailed project goals and use cases.

## License

MIT
