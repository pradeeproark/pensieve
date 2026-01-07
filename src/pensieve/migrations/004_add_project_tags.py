"""Add project_tags table for tag management and migrate existing tags."""

import sqlite3

from pensieve.migration_runner import create_migration_checksum

VERSION = 4
NAME = "add_project_tags"


def upgrade(conn: sqlite3.Connection) -> None:
    """Add project_tags table and migrate existing tags from entries.

    Creates a dedicated table for project tags, enabling:
    - Tag validation during entry creation
    - Pre-creation of tags before using them
    - Tag descriptions and metadata

    Also migrates all existing tags from journal_entries to project_tags.

    Args:
        conn: SQLite database connection
    """
    # Create project_tags table
    conn.execute(
        """
        CREATE TABLE project_tags (
            id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            description TEXT,
            UNIQUE(project, name)
        )
    """
    )

    # Create indexes for efficient querying
    conn.execute(
        """
        CREATE INDEX idx_project_tags_project ON project_tags(project)
    """
    )

    conn.execute(
        """
        CREATE INDEX idx_project_tags_name ON project_tags(name)
    """
    )

    # Migrate existing tags from journal_entries to project_tags
    # Extract unique (project, tag) pairs and insert into project_tags
    conn.execute(
        """
        INSERT INTO project_tags (id, project, name, created_at, created_by)
        SELECT
            lower(hex(randomblob(8))),
            project,
            json_each.value,
            datetime('now'),
            'migration'
        FROM journal_entries
        JOIN json_each(journal_entries.tags)
        GROUP BY project, json_each.value
    """
    )

    conn.commit()


def checksum() -> str:
    """Return SHA256 checksum of this migration.

    Returns:
        Hexadecimal SHA256 checksum
    """
    content = """
    CREATE TABLE project_tags (
        id TEXT PRIMARY KEY,
        project TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        description TEXT,
        UNIQUE(project, name)
    )
    CREATE INDEX idx_project_tags_project ON project_tags(project)
    CREATE INDEX idx_project_tags_name ON project_tags(name)
    INSERT INTO project_tags (id, project, name, created_at, created_by)
    SELECT lower(hex(randomblob(8))), project, json_each.value, datetime('now'), 'migration'
    FROM journal_entries JOIN json_each(journal_entries.tags) GROUP BY project, json_each.value
    """
    return create_migration_checksum(content)
