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

## Claude Code Integration

For Claude Code users, Pensieve is available as a plugin through the Cittamaya marketplace. The plugin provides:
- **Skills**: `memory-management` skill with comprehensive guidance
- **Hooks**: Automatic reminders at session start/end and after git commits
- **Integration**: Seamless integration with Pensieve CLI

### Installation

```bash
# Install the CLI tool first
pip install pensieve

# Then install the Claude Code plugin
/plugin marketplace add cittamaya/cittamaya
/plugin install pensieve@cittamaya-marketplace
```

See the [Cittamaya marketplace repository](https://github.com/cittamaya/cittamaya) for complete plugin documentation.

## Quick Start

### 1. Create a Template

**Inline field definitions:**
```bash
pensieve template create problem_solved \
  --description "For recording solved problems" \
  --field "problem:text:required:max_length=500:What was the issue?" \
  --field "solution:text:required:max_length=1000:How was it fixed?" \
  --field "learned:text:required:max_length=500:Key takeaway"
```

**From JSON file:**
```bash
pensieve template create problem_solved \
  --from-file template.json
```

### 2. Record a Memory

**Inline field values:**
```bash
pensieve entry create problem_solved \
  --field problem="Authentication failing in CI" \
  --field solution="Added environment variable" \
  --field learned="Always check CI config"
```

**From JSON file:**
```bash
pensieve entry create problem_solved \
  --from-file entry.json
```

### 3. Search Memories
```bash
# Search all entries (project auto-detected)
pensieve entry search

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
- `pensieve template create <name> --field "..." [--field "..."]` - Create new template with inline fields (project auto-detected)
- `pensieve template create <name> --from-file template.json` - Create template from JSON (project auto-detected)
- `pensieve template list` - List all templates
- `pensieve template show <name>` - Show template details
- `pensieve template export <name>` - Export template as JSON
- `pensieve template import <file>` - Import template from JSON

### Entries
- `pensieve entry create <template> --field key=value [--field ...]` - Create entry with inline values (project auto-detected)
- `pensieve entry create <template> --from-file entry.json` - Create entry from JSON (project auto-detected)
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
