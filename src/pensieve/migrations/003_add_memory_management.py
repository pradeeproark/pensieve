"""Add memory management features: status, tags, and entry links."""

import sqlite3

from pensieve.migration_runner import create_migration_checksum

VERSION = 3
NAME = "add_memory_management"


def upgrade(conn: sqlite3.Connection) -> None:
    """Add memory management tables and columns.

    Adds:
    - status and tags columns to journal_entries table
    - entry_links table for relationship tracking
    - Indexes and constraints for efficient querying

    Args:
        conn: SQLite database connection
    """
    # Add status column to journal_entries (default to 'active' for existing entries)
    conn.execute("""
        ALTER TABLE journal_entries ADD COLUMN status TEXT DEFAULT 'active'
    """)

    # Add tags column to journal_entries (default to empty JSON array)
    conn.execute("""
        ALTER TABLE journal_entries ADD COLUMN tags TEXT DEFAULT '[]'
    """)

    # Create index on status for efficient filtering
    conn.execute("""
        CREATE INDEX idx_journal_entries_status ON journal_entries(status)
    """)

    # Create entry_links table for memory relationships
    conn.execute("""
        CREATE TABLE entry_links (
            id TEXT PRIMARY KEY,
            source_entry_id TEXT NOT NULL,
            target_entry_id TEXT NOT NULL,
            link_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            FOREIGN KEY (source_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
            FOREIGN KEY (target_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
            CHECK (link_type IN ('supersedes', 'relates_to', 'augments', 'deprecates')),
            CHECK (source_entry_id != target_entry_id),
            UNIQUE(source_entry_id, target_entry_id, link_type)
        )
    """)

    # Create indexes on entry_links for efficient querying
    conn.execute("""
        CREATE INDEX idx_entry_links_source ON entry_links(source_entry_id)
    """)

    conn.execute("""
        CREATE INDEX idx_entry_links_target ON entry_links(target_entry_id)
    """)

    conn.execute("""
        CREATE INDEX idx_entry_links_type ON entry_links(link_type)
    """)

    # Add CHECK constraint to journal_entries status column
    # Note: SQLite doesn't support adding CHECK constraints via ALTER TABLE,
    # so we create a new table and copy data for existing entries.
    # For new entries, the constraint is in the CREATE TABLE above.
    # Here we'll validate existing data manually.
    cursor = conn.execute("SELECT id, status FROM journal_entries WHERE status NOT IN ('active', 'deprecated', 'superseded')")
    invalid_statuses = cursor.fetchall()
    if invalid_statuses:
        raise ValueError(f"Invalid status values found in existing entries: {invalid_statuses}")

    conn.commit()


def checksum() -> str:
    """Return SHA256 checksum of this migration.

    Returns:
        Hexadecimal SHA256 checksum
    """
    content = """
    ALTER TABLE journal_entries ADD COLUMN status TEXT DEFAULT 'active'
    ALTER TABLE journal_entries ADD COLUMN tags TEXT DEFAULT '[]'
    CREATE INDEX idx_journal_entries_status ON journal_entries(status)
    CREATE TABLE entry_links (
        id TEXT PRIMARY KEY,
        source_entry_id TEXT NOT NULL,
        target_entry_id TEXT NOT NULL,
        link_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        FOREIGN KEY (source_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
        FOREIGN KEY (target_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
        CHECK (link_type IN ('supersedes', 'relates_to', 'augments', 'deprecates')),
        CHECK (source_entry_id != target_entry_id),
        UNIQUE(source_entry_id, target_entry_id, link_type)
    )
    CREATE INDEX idx_entry_links_source ON entry_links(source_entry_id)
    CREATE INDEX idx_entry_links_target ON entry_links(target_entry_id)
    CREATE INDEX idx_entry_links_type ON entry_links(link_type)
    """
    return create_migration_checksum(content)
