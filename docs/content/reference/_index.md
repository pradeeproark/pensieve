---
title: "Reference"
---

## Integration with AI Agents

### Claude Code Plugin

Pensieve integrates seamlessly with Claude Code through the plugin system. When installed, Claude can automatically search and recall relevant memories at the start of each session.

**Installation:**

1. Install Pensieve (see [Getting Started](/getting-started/))

2. The Pensieve plugin is automatically available in Claude Code's plugin marketplace

3. Configure the plugin to enable automatic memory search:
   ```bash
   # Plugin configuration location
   ~/.claude/plugins/pensieve/config.yaml
   ```

**Features:**
- Automatic memory search at session start
- Context-aware recall based on current project
- Seamless integration with Claude's workflow
- Session memory recording prompts

### Other CLI Agents

**Coming soon:** Integration guides for other AI agent platforms.

---

## Standalone CLI Usage

Pensieve can be used as a standalone command-line tool for managing your working knowledge scratchpad.

### Basic Workflow

1. **Initialize** in your project directory
2. **Create entries** as you discover patterns or solutions
3. **Search** when you need to recall past learnings
4. **Link entries** to build knowledge graphs

### Quick Reference

See the [Command Reference](#command-reference) below for detailed command documentation.

---

## Command Reference

### Entry Management

Manage journal entries - the core of your Pensieve scratchpad.

#### `pensieve entry create`
Create a new entry using a template.

```bash
pensieve entry create --template TEMPLATE_NAME
```

**Options:**
- `--template, -t`: Template to use (required)
- `--interactive, -i`: Interactive mode with prompts

**Example:**
```bash
pensieve entry create --template problem_solved
```

#### `pensieve entry search`
Search for entries by content, tags, or metadata.

```bash
pensieve entry search [OPTIONS] [QUERY]
```

**Options:**
- `--tag`: Filter by tag
- `--limit, -n`: Limit number of results (default: 10)
- `--follow-links`: Follow linked entries
- `--all-projects`: Search across all projects

**Example:**
```bash
pensieve entry search --tag debugging --limit 5
```

#### `pensieve entry show`
Display a specific entry by ID.

```bash
pensieve entry show ENTRY_ID
```

**Options:**
- `--follow-links`: Show linked entries as well

**Example:**
```bash
pensieve entry show 1a0501ad-48ad-41c2-b73a-c85d711dd6d2
```

#### `pensieve entry list`
List all entries in the current project.

```bash
pensieve entry list [OPTIONS]
```

**Options:**
- `--limit, -n`: Limit number of results
- `--status`: Filter by status (active/archived)

#### `pensieve entry link`
Link two entries to build knowledge graphs.

```bash
pensieve entry link SOURCE_ID TARGET_ID --relationship TYPE
```

**Relationship types:**
- `augments`: Target builds on source
- `relates_to`: General relationship
- `contradicts`: Target contradicts source
- `supersedes`: Target replaces source

**Example:**
```bash
pensieve entry link abc123 def456 --relationship augments
```

#### `pensieve entry tag`
Add tags to an entry.

```bash
pensieve entry tag ENTRY_ID TAG [TAG ...]
```

#### `pensieve entry update-status`
Update an entry's status.

```bash
pensieve entry update-status ENTRY_ID STATUS
```

**Status values:** `active`, `archived`

---

### Template Management

Manage entry templates to structure your knowledge capture.

#### `pensieve template list`
List all available templates.

```bash
pensieve template list
```

#### `pensieve template show`
Display a template's structure.

```bash
pensieve template show TEMPLATE_NAME
```

#### `pensieve template create`
Create a new custom template.

```bash
pensieve template create TEMPLATE_NAME
```

**Example:**
```bash
pensieve template create code_review
```

#### `pensieve template export`
Export a template for sharing.

```bash
pensieve template export TEMPLATE_NAME
```

---

### Tag Management

Organize and explore your tags.

#### `pensieve tag list`
List all tags used in entries.

```bash
pensieve tag list
```

Shows all tags with usage counts.

---

### Database Management

#### `pensieve migrate apply`
Apply pending database migrations.

```bash
pensieve migrate apply
```

#### `pensieve migrate status`
Check migration status.

```bash
pensieve migrate status
```

---

### Utility Commands

#### `pensieve version`
Display version information.

```bash
pensieve version
```

#### `pensieve --help`
Show help for any command.

```bash
pensieve --help
pensieve entry --help
pensieve entry create --help
```
