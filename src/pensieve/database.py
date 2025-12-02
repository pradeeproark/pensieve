"""Database operations for Pensieve."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pensieve.migration_runner import MigrationRunner
from pensieve.models import (
    EntryLink,
    EntryStatus,
    FieldConstraints,
    FieldType,
    JournalEntry,
    LinkType,
    Template,
    TemplateField,
)
from pensieve.validators import ValidationError, validate_field_value


class DatabaseError(Exception):
    """Raised when database operations fail."""

    pass


class Database:
    """Manages database connections and operations."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses PENSIEVE_DB env var
                    or defaults to ~/.pensieve/pensieve.db
        """
        if db_path is None:
            db_path = os.environ.get("PENSIEVE_DB", str(Path.home() / ".pensieve" / "pensieve.db"))

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Run migrations
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Run any pending database migrations."""
        runner = MigrationRunner(self.conn)
        pending_count = len(runner.get_pending_migrations())

        if pending_count > 0:
            runner.apply_all_pending()

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    # Template operations

    def create_template(self, template: Template) -> None:
        """Create a new template.

        Args:
            template: Template to create

        Raises:
            DatabaseError: If template with same name already exists
        """
        try:
            # Insert template
            self.conn.execute(
                """
                INSERT INTO templates
                    (id, name, description, version, created_at, created_by, project)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(template.id),
                    template.name,
                    template.description,
                    template.version,
                    template.created_at.isoformat(),
                    template.created_by,
                    template.project,
                ),
            )

            # Insert template fields
            for field in template.fields:
                self.conn.execute(
                    """
                    INSERT INTO template_fields
                        (template_id, name, type, required, constraints_json)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        str(template.id),
                        field.name,
                        field.type.value,
                        1 if field.required else 0,
                        json.dumps(field.constraints.model_dump(exclude_none=True)),
                    ),
                )

            self.conn.commit()

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise DatabaseError(f"Template with name '{template.name}' already exists") from e

    def get_template_by_name(self, name: str) -> Template | None:
        """Get template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        cursor = self.conn.execute(
            """
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            WHERE name = ?
        """,
            (name,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return self._load_template_from_row(row)

    def get_template_by_id(self, template_id: UUID) -> Template | None:
        """Get template by ID.

        Args:
            template_id: Template UUID

        Returns:
            Template if found, None otherwise
        """
        cursor = self.conn.execute(
            """
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            WHERE id = ?
        """,
            (str(template_id),),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return self._load_template_from_row(row)

    def list_templates(self) -> list[Template]:
        """List all templates.

        Returns:
            List of all templates
        """
        cursor = self.conn.execute(
            """
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            ORDER BY created_at DESC
        """
        )

        return [self._load_template_from_row(row) for row in cursor.fetchall()]

    def get_templates_with_field(self, field_name: str) -> list[str]:
        """Return template names that have the specified field.

        Args:
            field_name: Name of the field to search for

        Returns:
            List of template names that contain the field
        """
        cursor = self.conn.execute(
            """
            SELECT DISTINCT t.name
            FROM templates t
            JOIN template_fields tf ON t.id = tf.template_id
            WHERE tf.name = ?
            """,
            (field_name,),
        )
        return [row["name"] for row in cursor.fetchall()]

    def get_common_field_names(self, limit: int = 10) -> list[str]:
        """Return the most common field names across all templates.

        Args:
            limit: Maximum number of field names to return

        Returns:
            List of field names ordered by usage count (most common first)
        """
        cursor = self.conn.execute(
            """
            SELECT name, COUNT(*) as usage_count
            FROM template_fields
            GROUP BY name
            ORDER BY usage_count DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [row["name"] for row in cursor.fetchall()]

    def _load_template_from_row(self, row: sqlite3.Row) -> Template:
        """Load template from database row.

        Args:
            row: Database row from templates table

        Returns:
            Loaded Template object
        """
        # Load template fields
        cursor = self.conn.execute(
            """
            SELECT name, type, required, constraints_json
            FROM template_fields
            WHERE template_id = ?
            ORDER BY id
        """,
            (row["id"],),
        )

        fields = []
        for field_row in cursor.fetchall():
            constraints_data = json.loads(field_row["constraints_json"])
            fields.append(
                TemplateField(
                    name=field_row["name"],
                    type=FieldType(field_row["type"]),
                    required=bool(field_row["required"]),
                    constraints=FieldConstraints(**constraints_data),
                )
            )

        return Template(
            id=UUID(row["id"]),
            name=row["name"],
            description=row["description"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
            project=row["project"],
            fields=fields,
        )

    # Journal entry operations

    def create_entry(self, entry: JournalEntry, template: Template) -> None:
        """Create a new journal entry.

        Args:
            entry: Journal entry to create
            template: Template the entry is based on

        Raises:
            ValidationError: If entry doesn't conform to template
            DatabaseError: If database operation fails
        """
        # Validate entry against template
        self._validate_entry_against_template(entry, template)

        try:
            # Insert entry
            self.conn.execute(
                """
                INSERT INTO journal_entries
                    (id, template_id, template_version, agent, project,
                     timestamp, status, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(entry.id),
                    str(entry.template_id),
                    entry.template_version,
                    entry.agent,
                    entry.project,
                    entry.timestamp.isoformat(),
                    entry.status.value,
                    json.dumps(entry.tags),
                ),
            )

            # Insert field values
            for field_name, field_value in entry.field_values.items():
                field = next(f for f in template.fields if f.name == field_name)
                self._insert_field_value(entry.id, field_name, field.type, field_value)

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to create entry: {e}") from e

    def _validate_entry_against_template(self, entry: JournalEntry, template: Template) -> None:
        """Validate that entry conforms to template.

        Args:
            entry: Entry to validate
            template: Template to validate against

        Raises:
            ValidationError: If entry doesn't conform to template
        """
        # Check all required fields are present
        for field in template.fields:
            if field.required and field.name not in entry.field_values:
                raise ValidationError(f"Required field '{field.name}' is missing")

        # Check no extra fields
        template_field_names = {f.name for f in template.fields}
        for field_name in entry.field_values.keys():
            if field_name not in template_field_names:
                raise ValidationError(f"Unknown field '{field_name}' not in template")

        # Validate each field value
        for field in template.fields:
            if field.name in entry.field_values:
                value = entry.field_values[field.name]
                # Validate will raise ValidationError if invalid
                validated = validate_field_value(field.type, value, field.constraints)
                # Update with validated value
                entry.field_values[field.name] = validated

    def _insert_field_value(
        self, entry_id: UUID, field_name: str, field_type: FieldType, value: Any
    ) -> None:
        """Insert a field value into the database.

        Args:
            entry_id: Entry UUID
            field_name: Name of the field
            field_type: Type of the field
            value: Value to store
        """
        # Determine which column to use based on type
        columns = {
            "value_text": None,
            "value_boolean": None,
            "value_url": None,
            "value_timestamp": None,
            "value_file_path": None,
        }

        if field_type == FieldType.BOOLEAN:
            columns["value_boolean"] = 1 if value else 0
        elif field_type == FieldType.TEXT:
            columns["value_text"] = value
        elif field_type == FieldType.URL:
            columns["value_url"] = value
        elif field_type == FieldType.TIMESTAMP:
            columns["value_timestamp"] = value
        elif field_type == FieldType.FILE_REFERENCE:
            columns["value_file_path"] = value
        elif field_type == FieldType.REFS:
            # Store refs as JSON in value_text column
            import json

            columns["value_text"] = json.dumps(value)

        self.conn.execute(
            """
            INSERT INTO entry_field_values (
                entry_id, field_name, field_type,
                value_text, value_boolean, value_url, value_timestamp, value_file_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(entry_id),
                field_name,
                field_type.value,
                columns["value_text"],
                columns["value_boolean"],
                columns["value_url"],
                columns["value_timestamp"],
                columns["value_file_path"],
            ),
        )

    def get_entry_by_id(self, entry_id: UUID) -> JournalEntry | None:
        """Get journal entry by ID.

        Args:
            entry_id: Entry UUID

        Returns:
            JournalEntry if found, None otherwise
        """
        cursor = self.conn.execute(
            """
            SELECT id, template_id, template_version, agent, project, timestamp, status, tags
            FROM journal_entries
            WHERE id = ?
        """,
            (str(entry_id),),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return self._load_entry_from_row(row)

    def list_entries(self, limit: int = 50, offset: int = 0) -> list[JournalEntry]:
        """List journal entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of journal entries
        """
        cursor = self.conn.execute(
            """
            SELECT id, template_id, template_version, agent, project, timestamp, status, tags
            FROM journal_entries
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )

        return [self._load_entry_from_row(row) for row in cursor.fetchall()]

    def _load_entry_from_row(self, row: sqlite3.Row) -> JournalEntry:
        """Load journal entry from database row.

        Args:
            row: Database row from journal_entries table

        Returns:
            Loaded JournalEntry object
        """
        # Load field values
        cursor = self.conn.execute(
            """
            SELECT field_name, field_type, value_text, value_boolean,
                   value_url, value_timestamp, value_file_path
            FROM entry_field_values
            WHERE entry_id = ?
        """,
            (row["id"],),
        )

        field_values = {}
        for value_row in cursor.fetchall():
            field_type = FieldType(value_row["field_type"])
            field_name = value_row["field_name"]

            # Extract value based on type
            if field_type == FieldType.BOOLEAN:
                field_values[field_name] = bool(value_row["value_boolean"])
            elif field_type == FieldType.TEXT:
                field_values[field_name] = value_row["value_text"]
            elif field_type == FieldType.URL:
                field_values[field_name] = value_row["value_url"]
            elif field_type == FieldType.TIMESTAMP:
                field_values[field_name] = value_row["value_timestamp"]
            elif field_type == FieldType.FILE_REFERENCE:
                field_values[field_name] = value_row["value_file_path"]
            elif field_type == FieldType.REFS:
                # Parse refs from JSON stored in value_text
                field_values[field_name] = (
                    json.loads(value_row["value_text"]) if value_row["value_text"] else []
                )

        # Load status and tags
        status = EntryStatus(row["status"]) if row["status"] else EntryStatus.ACTIVE
        tags = json.loads(row["tags"]) if row["tags"] else []

        # Load links from and to this entry
        entry_id = UUID(row["id"])
        links_from = self._load_links_from(entry_id)
        links_to = self._load_links_to(entry_id)

        return JournalEntry(
            id=entry_id,
            template_id=UUID(row["template_id"]),
            template_version=row["template_version"],
            agent=row["agent"],
            project=row["project"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            field_values=field_values,
            status=status,
            tags=tags,
            links_from=links_from,
            links_to=links_to,
        )

    def _load_links_from(self, entry_id: UUID) -> list[EntryLink]:
        """Load all links FROM this entry.

        Args:
            entry_id: Entry UUID

        Returns:
            List of EntryLink objects
        """
        cursor = self.conn.execute(
            """
            SELECT id, source_entry_id, target_entry_id, link_type, created_at, created_by
            FROM entry_links
            WHERE source_entry_id = ?
        """,
            (str(entry_id),),
        )

        links = []
        for row in cursor.fetchall():
            links.append(
                EntryLink(
                    id=UUID(row["id"]),
                    source_entry_id=UUID(row["source_entry_id"]),
                    target_entry_id=UUID(row["target_entry_id"]),
                    link_type=LinkType(row["link_type"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"],
                )
            )
        return links

    def _load_links_to(self, entry_id: UUID) -> list[EntryLink]:
        """Load all links TO this entry.

        Args:
            entry_id: Entry UUID

        Returns:
            List of EntryLink objects
        """
        cursor = self.conn.execute(
            """
            SELECT id, source_entry_id, target_entry_id, link_type, created_at, created_by
            FROM entry_links
            WHERE target_entry_id = ?
        """,
            (str(entry_id),),
        )

        links = []
        for row in cursor.fetchall():
            links.append(
                EntryLink(
                    id=UUID(row["id"]),
                    source_entry_id=UUID(row["source_entry_id"]),
                    target_entry_id=UUID(row["target_entry_id"]),
                    link_type=LinkType(row["link_type"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"],
                )
            )
        return links

    def get_linked_entries_batch(
        self, entry_ids: list[UUID]
    ) -> dict[UUID, tuple[list[EntryLink], list[EntryLink]]]:
        """Batch fetch all links (both from and to) for multiple entry IDs.

        Args:
            entry_ids: List of entry UUIDs to fetch links for

        Returns:
            Dictionary mapping entry_id -> (links_from, links_to)
        """
        if not entry_ids:
            return {}

        # Convert UUIDs to strings for SQL query
        id_strings = [str(eid) for eid in entry_ids]
        placeholders = ",".join("?" * len(id_strings))

        # Query for all outgoing links
        cursor_from = self.conn.execute(
            f"""
            SELECT id, source_entry_id, target_entry_id, link_type, created_at, created_by
            FROM entry_links
            WHERE source_entry_id IN ({placeholders})
        """,
            id_strings,
        )

        # Group links_from by source_entry_id
        links_from_map: dict[UUID, list[EntryLink]] = {eid: [] for eid in entry_ids}
        for row in cursor_from.fetchall():
            source_id = UUID(row["source_entry_id"])
            links_from_map[source_id].append(
                EntryLink(
                    id=UUID(row["id"]),
                    source_entry_id=source_id,
                    target_entry_id=UUID(row["target_entry_id"]),
                    link_type=LinkType(row["link_type"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"],
                )
            )

        # Query for all incoming links
        cursor_to = self.conn.execute(
            f"""
            SELECT id, source_entry_id, target_entry_id, link_type, created_at, created_by
            FROM entry_links
            WHERE target_entry_id IN ({placeholders})
        """,
            id_strings,
        )

        # Group links_to by target_entry_id
        links_to_map: dict[UUID, list[EntryLink]] = {eid: [] for eid in entry_ids}
        for row in cursor_to.fetchall():
            target_id = UUID(row["target_entry_id"])
            links_to_map[target_id].append(
                EntryLink(
                    id=UUID(row["id"]),
                    source_entry_id=UUID(row["source_entry_id"]),
                    target_entry_id=target_id,
                    link_type=LinkType(row["link_type"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    created_by=row["created_by"],
                )
            )

        # Combine into result dict
        result = {}
        for eid in entry_ids:
            result[eid] = (links_from_map[eid], links_to_map[eid])

        return result

    # Entry management operations

    def create_entry_link(self, link: EntryLink) -> None:
        """Create a link between two entries.

        Args:
            link: EntryLink to create

        Raises:
            DatabaseError: If link creation fails
        """
        # Verify both entries exist
        if self.get_entry_by_id(link.source_entry_id) is None:
            raise DatabaseError(f"Source entry '{link.source_entry_id}' not found")
        if self.get_entry_by_id(link.target_entry_id) is None:
            raise DatabaseError(f"Target entry '{link.target_entry_id}' not found")

        try:
            self.conn.execute(
                """
                INSERT INTO entry_links
                    (id, source_entry_id, target_entry_id, link_type,
                     created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    str(link.id),
                    str(link.source_entry_id),
                    str(link.target_entry_id),
                    link.link_type.value,
                    link.created_at.isoformat(),
                    link.created_by,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DatabaseError(
                    f"Link already exists between {link.source_entry_id} and "
                    f"{link.target_entry_id} with type '{link.link_type.value}'"
                ) from e
            elif "CHECK constraint failed" in str(e):
                raise DatabaseError(
                    "Cannot create self-link (source and target are the same)"
                ) from e
            raise DatabaseError(f"Failed to create link: {e}") from e
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to create link: {e}") from e

    def update_entry_status(self, entry_id: UUID, status: EntryStatus) -> None:
        """Update the status of an entry.

        Args:
            entry_id: Entry UUID
            status: New status

        Raises:
            DatabaseError: If entry not found or update fails
        """
        if self.get_entry_by_id(entry_id) is None:
            raise DatabaseError(f"Entry '{entry_id}' not found")

        try:
            self.conn.execute(
                """
                UPDATE journal_entries
                SET status = ?
                WHERE id = ?
            """,
                (status.value, str(entry_id)),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to update entry status: {e}") from e

    def add_entry_tags(self, entry_id: UUID, tags_to_add: list[str]) -> None:
        """Add tags to an entry (idempotent - no duplicates).

        Args:
            entry_id: Entry UUID
            tags_to_add: Tags to add

        Raises:
            DatabaseError: If entry not found or update fails
        """
        entry = self.get_entry_by_id(entry_id)
        if entry is None:
            raise DatabaseError(f"Entry '{entry_id}' not found")

        # Merge tags (remove duplicates)
        existing_tags = set(entry.tags)
        new_tags = existing_tags.union(tags_to_add)
        updated_tags = sorted(new_tags)  # Sort for consistency

        try:
            self.conn.execute(
                """
                UPDATE journal_entries
                SET tags = ?
                WHERE id = ?
            """,
                (json.dumps(updated_tags), str(entry_id)),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to add tags: {e}") from e

    def remove_entry_tags(self, entry_id: UUID, tags_to_remove: list[str]) -> None:
        """Remove tags from an entry (no-op if tags don't exist).

        Args:
            entry_id: Entry UUID
            tags_to_remove: Tags to remove

        Raises:
            DatabaseError: If entry not found or update fails
        """
        entry = self.get_entry_by_id(entry_id)
        if entry is None:
            raise DatabaseError(f"Entry '{entry_id}' not found")

        # Remove tags
        existing_tags = set(entry.tags)
        updated_tags = sorted(existing_tags - set(tags_to_remove))

        try:
            self.conn.execute(
                """
                UPDATE journal_entries
                SET tags = ?
                WHERE id = ?
            """,
                (json.dumps(updated_tags), str(entry_id)),
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to remove tags: {e}") from e

    def get_tag_statistics(self, project: str | None = None) -> list[tuple[str, int]]:
        """Get tag usage statistics.

        Args:
            project: Project path filter (None = all projects)

        Returns:
            List of (tag_name, entry_count) tuples, sorted by count descending,
            then alphabetically by tag name
        """
        if project is None:
            # Query all projects
            cursor = self.conn.execute(
                """
                SELECT
                    json_each.value as tag,
                    COUNT(*) as entry_count
                FROM journal_entries
                JOIN json_each(journal_entries.tags)
                GROUP BY tag
                ORDER BY entry_count DESC, tag ASC
            """
            )
        else:
            # Query specific project
            cursor = self.conn.execute(
                """
                SELECT
                    json_each.value as tag,
                    COUNT(*) as entry_count
                FROM journal_entries
                JOIN json_each(journal_entries.tags)
                WHERE project = ?
                GROUP BY tag
                ORDER BY entry_count DESC, tag ASC
            """,
                (project,),
            )

        return [(row["tag"], row["entry_count"]) for row in cursor.fetchall()]

    def search_entries_by_id_prefix(self, id_prefix: str) -> list[JournalEntry]:
        """Search for entries by ID prefix.

        Args:
            id_prefix: First 8 (or more) characters of entry UUID

        Returns:
            List of matching JournalEntry objects
        """
        cursor = self.conn.execute(
            """
            SELECT id, template_id, template_version, agent, project, timestamp, status, tags
            FROM journal_entries
            WHERE id LIKE ?
        """,
            (f"{id_prefix}%",),
        )

        entries = []
        for row in cursor.fetchall():
            entry = self._load_entry_from_row(row)
            if entry:
                entries.append(entry)
        return entries

    def _load_entry_from_row(self, row) -> JournalEntry | None:
        """Load a JournalEntry from a database row.

        Args:
            row: Database row dict

        Returns:
            JournalEntry or None if loading fails
        """
        # Load field values
        cursor = self.conn.execute(
            """
            SELECT field_name, field_type, value_text, value_boolean,
                   value_url, value_timestamp, value_file_path
            FROM entry_field_values
            WHERE entry_id = ?
        """,
            (row["id"],),
        )

        field_values = {}
        for value_row in cursor.fetchall():
            field_type = FieldType(value_row["field_type"])
            field_name = value_row["field_name"]

            # Extract value based on type
            if field_type == FieldType.BOOLEAN:
                field_values[field_name] = bool(value_row["value_boolean"])
            elif field_type == FieldType.TEXT:
                field_values[field_name] = value_row["value_text"]
            elif field_type == FieldType.URL:
                field_values[field_name] = value_row["value_url"]
            elif field_type == FieldType.TIMESTAMP:
                field_values[field_name] = value_row["value_timestamp"]
            elif field_type == FieldType.FILE_REFERENCE:
                field_values[field_name] = value_row["value_file_path"]
            elif field_type == FieldType.REFS:
                field_values[field_name] = (
                    json.loads(value_row["value_text"]) if value_row["value_text"] else []
                )

        # Load status and tags
        status = EntryStatus(row["status"]) if row["status"] else EntryStatus.ACTIVE
        tags = json.loads(row["tags"]) if row["tags"] else []

        # Load links from and to this entry
        entry_id = UUID(row["id"])
        links_from = self._load_links_from(entry_id)
        links_to = self._load_links_to(entry_id)

        return JournalEntry(
            id=entry_id,
            template_id=UUID(row["template_id"]),
            template_version=row["template_version"],
            agent=row["agent"],
            project=row["project"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            field_values=field_values,
            status=status,
            tags=tags,
            links_from=links_from,
            links_to=links_to,
        )

    def update_entry_field_values(
        self, entry_id: UUID, field_values: dict, template: Template
    ) -> None:
        """Update field values for an existing entry.

        Args:
            entry_id: Entry UUID
            field_values: New field values dict
            template: Template the entry is based on

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Delete existing field values
            self.conn.execute(
                """
                DELETE FROM entry_field_values WHERE entry_id = ?
            """,
                (str(entry_id),),
            )

            # Re-insert with new values
            for field in template.fields:
                if field.name in field_values:
                    value = field_values[field.name]
                    self._insert_field_value(entry_id, field.name, field.type, value)

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to update entry field values: {e}") from e
