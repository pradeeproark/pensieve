"""Initial database schema for Pensieve."""

import sqlite3

from pensieve.migration_runner import create_migration_checksum

VERSION = 1
NAME = "initial_schema"


def upgrade(conn: sqlite3.Connection) -> None:
    """Create initial database schema.

    Args:
        conn: SQLite database connection
    """
    # Templates table
    conn.execute("""
        CREATE TABLE templates (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    """)

    # Create index on template name for faster lookups
    conn.execute("""
        CREATE INDEX idx_templates_name ON templates(name)
    """)

    # Template fields table
    conn.execute("""
        CREATE TABLE template_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            required INTEGER NOT NULL DEFAULT 0,
            constraints_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
            UNIQUE(template_id, name)
        )
    """)

    # Create index on template_id for faster field lookups
    conn.execute("""
        CREATE INDEX idx_template_fields_template_id ON template_fields(template_id)
    """)

    # Journal entries table
    conn.execute("""
        CREATE TABLE journal_entries (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            template_version INTEGER NOT NULL,
            agent TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)

    # Create indexes for common query patterns
    conn.execute("""
        CREATE INDEX idx_journal_entries_template_id ON journal_entries(template_id)
    """)
    conn.execute("""
        CREATE INDEX idx_journal_entries_agent ON journal_entries(agent)
    """)
    conn.execute("""
        CREATE INDEX idx_journal_entries_timestamp ON journal_entries(timestamp)
    """)

    # Entry field values table - stores actual values with type-specific columns
    conn.execute("""
        CREATE TABLE entry_field_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            value_text TEXT,
            value_boolean INTEGER,
            value_url TEXT,
            value_timestamp TEXT,
            value_file_path TEXT,
            FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
            UNIQUE(entry_id, field_name)
        )
    """)

    # Create index for field value queries
    conn.execute("""
        CREATE INDEX idx_entry_field_values_entry_id ON entry_field_values(entry_id)
    """)
    conn.execute("""
        CREATE INDEX idx_entry_field_values_field_name ON entry_field_values(field_name)
    """)

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")


def checksum() -> str:
    """Return SHA256 checksum of this migration.

    Returns:
        Hexadecimal SHA256 checksum
    """
    # Include all SQL statements in the checksum
    content = """
    CREATE TABLE templates (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL
    )
    CREATE INDEX idx_templates_name ON templates(name)
    CREATE TABLE template_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        required INTEGER NOT NULL DEFAULT 0,
        constraints_json TEXT NOT NULL DEFAULT '{}',
        FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
        UNIQUE(template_id, name)
    )
    CREATE INDEX idx_template_fields_template_id ON template_fields(template_id)
    CREATE TABLE journal_entries (
        id TEXT PRIMARY KEY,
        template_id TEXT NOT NULL,
        template_version INTEGER NOT NULL,
        agent TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (template_id) REFERENCES templates(id)
    )
    CREATE INDEX idx_journal_entries_template_id ON journal_entries(template_id)
    CREATE INDEX idx_journal_entries_agent ON journal_entries(agent)
    CREATE INDEX idx_journal_entries_timestamp ON journal_entries(timestamp)
    CREATE TABLE entry_field_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT NOT NULL,
        field_name TEXT NOT NULL,
        field_type TEXT NOT NULL,
        value_text TEXT,
        value_boolean INTEGER,
        value_url TEXT,
        value_timestamp TEXT,
        value_file_path TEXT,
        FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
        UNIQUE(entry_id, field_name)
    )
    CREATE INDEX idx_entry_field_values_entry_id ON entry_field_values(entry_id)
    CREATE INDEX idx_entry_field_values_field_name ON entry_field_values(field_name)
    PRAGMA foreign_keys = ON
    """
    return create_migration_checksum(content)
