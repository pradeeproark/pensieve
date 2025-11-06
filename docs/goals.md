# Pensieve - Memory Recording Tool for Claude Code

## Project Goal

Create a CLI tool that enables Claude Code agents to record and retrieve structured memory events across sessions. This persistent memory system helps maintain context, track decisions, and create continuity in long-running development projects.

## Core Requirements

### 1. Template System

**Purpose**: Define structured schemas for different types of memory events.

**Features**:
- Agents can create custom templates
- Templates define fields with specific types and constraints
- Templates are versioned and immutable once in use
- Templates can be exported/imported as JSON

**Field Types**:
1. **boolean**: True/False values for binary choices
2. **text**: String values with optional max_length constraint
3. **url**: Validated URLs with optional scheme restrictions (http, https, file, etc.)
4. **timestamp**: ISO8601 datetime, can auto-fill current time
5. **file_reference**: File paths with optional type validation (.py, .js, etc.)

**Field Constraints**:
- All fields can be marked as required or optional
- Text fields: max_length (integer)
- URL fields: allowed schemes (list of strings)
- File reference fields: allowed file types (list of extensions)
- Timestamp fields: auto_now (boolean) - auto-fill with current time

**Example Templates**:
- **architecture_decision**: decision (text), rationale (text), alternatives_considered (text), date (timestamp)
- **bug_fix**: bug_description (text), root_cause (text), fix_location (file_reference), fixed_at (timestamp)
- **pattern_discovered**: pattern_name (text), use_case (text), code_location (file_reference), documentation_url (url)

### 2. Journal Entry System

**Purpose**: Record actual memory events using templates.

**Features**:
- All entries must use a template
- Entries are append-only (immutable)
- Each entry records: agent name, timestamp, template used, field values
- Entries can be searched and filtered
- Entries can be exported as JSON

**Metadata Captured**:
- Unique entry ID (UUID)
- Template ID and version
- Agent identifier (who created the entry)
- Creation timestamp (ISO8601)
- All field values according to template schema

### 3. Query System

**Purpose**: Retrieve relevant memories based on context.

**Search Capabilities**:
- By template type: Find all entries of a specific template
- By date range: Find entries within a time period
- By field content: Search within specific field values
- By agent: Find all entries made by a specific agent
- Combined filters: Mix multiple search criteria

**Output Formats**:
- Human-readable list view
- Detailed single entry view
- JSON export for programmatic access

### 4. Migration System

**Purpose**: Allow the tool to evolve its schema over time.

**Features**:
- Built-in migration framework
- Version tracking in database
- Automatic migration check on startup
- Forward-only migrations (no rollback)
- Migrations embedded in frozen executable
- Migration integrity verification (checksums)

**Migration Operations**:
- Create tables and indexes
- Add/modify columns
- Transform existing data
- Update schema version

### 5. Distribution Model

**Purpose**: Prevent agents from modifying the tool itself.

**Approach**:
- Python source code during development
- Frozen executable via PyInstaller for deployment
- Agents interact only with the CLI interface
- Database stored separately from executable
- Migrations bundled within executable

## Use Cases

### Use Case 1: Recording Architecture Decisions
```bash
# Agent creates a template
pensieve template create

# Agent creates an entry
pensieve entry create --template architecture_decision
# Fills: decision, rationale, alternatives, date

# Later, another agent searches
pensieve entry search --template architecture_decision
```

### Use Case 2: Tracking Bug Fixes
```bash
# Agent records bug fix
pensieve entry create --template bug_fix
# Fills: description, root cause, file location, timestamp

# Search for all bugs in specific file
pensieve entry search --template bug_fix --field fix_location="src/auth.py"
```

### Use Case 3: Documenting Patterns
```bash
# Agent discovers a pattern
pensieve entry create --template pattern_discovered
# Fills: pattern name, use case, code location, docs URL

# Export all patterns for documentation
pensieve entry export --template pattern_discovered --format json > patterns.json
```

## Integration with Claude Code

### Superpower Skill
A Claude Code skill will be created to guide agents on:
- When to create memories (significant decisions, bugs, patterns)
- How to choose appropriate templates
- How to search for relevant context before starting tasks
- Best practices for memory capture

### Command Integration
Claude Code commands can invoke pensieve to:
- Automatically record session summaries
- Log significant events during workflows
- Retrieve context at session start

## Technical Constraints

1. **Database**: SQLite for zero-configuration persistence
2. **Immutability**: Journal entries cannot be edited (append-only)
3. **Validation**: All field values validated against template constraints
4. **Portability**: Single database file, relocatable
5. **Performance**: Fast queries even with thousands of entries (indexed)

## Success Criteria

1. Agents can create custom templates with all 5 field types
2. Agents can record journal entries conforming to templates
3. Search returns relevant entries efficiently
4. Tool can self-update schema via migrations
5. Frozen executable prevents source modification
6. Complete test coverage for all operations
7. Clear documentation and usage examples
