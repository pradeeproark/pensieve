"""Add project field to templates and journal_entries."""

import sqlite3

from pensieve.migration_runner import create_migration_checksum

VERSION = 2
NAME = "add_project_field"


def upgrade(conn: sqlite3.Connection) -> None:
    """Add project column to templates and journal_entries tables.

    Args:
        conn: SQLite database connection
    """
    # Add project column to templates table
    conn.execute("""
        ALTER TABLE templates ADD COLUMN project TEXT NOT NULL DEFAULT '(no project)'
    """)

    # Add project column to journal_entries table
    conn.execute("""
        ALTER TABLE journal_entries ADD COLUMN project TEXT NOT NULL DEFAULT '(no project)'
    """)

    # Create indexes for efficient project-based queries
    conn.execute("""
        CREATE INDEX idx_templates_project ON templates(project)
    """)

    conn.execute("""
        CREATE INDEX idx_journal_entries_project ON journal_entries(project)
    """)

    conn.commit()


def checksum() -> str:
    """Return SHA256 checksum of this migration.

    Returns:
        Hexadecimal SHA256 checksum
    """
    content = """
    ALTER TABLE templates ADD COLUMN project TEXT NOT NULL DEFAULT '(no project)'
    ALTER TABLE journal_entries ADD COLUMN project TEXT NOT NULL DEFAULT '(no project)'
    CREATE INDEX idx_templates_project ON templates(project)
    CREATE INDEX idx_journal_entries_project ON journal_entries(project)
    """
    return create_migration_checksum(content)
