# Pensieve

Contextual scratchpad for AI agents - capture and retrieve working knowledge across sessions.

## Overview

Pensieve enables AI agents to maintain context and continuity by recording significant events, decisions, and patterns in a structured format. Use it standalone via CLI or integrate with your AI agent workflow. All memories are stored using customizable templates with typed fields and can be queried efficiently.

**Agent Integration:** While Pensieve can be used with any AI agent or CLI tool, we provide a tested, production-ready integration for **Claude Code** (see below).

## Installation

### Homebrew (macOS)
```bash
brew tap cittamaya/pensieve
brew install pensieve
```

### Build from Source
```bash
# Clone the repository
git clone https://github.com/pradeeproark/pensieve.git
cd pensieve

# Install for development
pip install -e ".[dev]"

# Or build executable
python build/build.py
```

**Platform availability:** Currently macOS only. Windows and Linux builds coming soon.

## AI Agent Integration

### Claude Code (Tested Integration)

For Claude Code users, Pensieve is available as a plugin through the Cittamaya marketplace. The plugin provides:
- **Automatic session hooks**: Memory search at session start
- **Natural language triggers**: Responds to "remember", "recall", "note", etc.
- **Slash commands**: `/pensieve:remember` and `/pensieve:recall`
- **Memory management skill**: Comprehensive guidance for effective memory usage

**Installation:**
```bash
# Option 1: Interactive (recommended)
/plugin

# Option 2: CLI
claude plugin marketplace add https://github.com/cittamaya/cittamaya.git
claude plugin install pensieve
```

See the [plugin documentation](https://cittamaya.github.io/cittamaya/) for complete details.

### Other AI Agents

Pensieve can be integrated with any AI agent that can execute CLI commands. The agent needs to:
1. Run `pensieve entry search` to recall relevant memories
2. Run `pensieve entry create` to record new learnings
3. Parse the human-readable output (structured text)

Example integration pattern:
```bash
# At session start: search for relevant context
pensieve entry search --tag authentication --limit 5

# During session: record learnings
pensieve entry create --template pattern_discovered \
  --field pattern="Always validate tokens" \
  --field context="Auth middleware"
```

For custom integrations, see the [CLI reference](#commands) below.

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
pensieve entry create --template problem_solved \
  --field problem="Authentication failing in CI" \
  --field solution="Added environment variable" \
  --field learned="Always check CI config"
```

**From JSON file:**
```bash
pensieve entry create --template problem_solved \
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
- `pensieve entry create --template <template> --field key=value [--field ...]` - Create entry with inline values (project auto-detected)
- `pensieve entry create --template <template> --from-file entry.json` - Create entry from JSON (project auto-detected)
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
