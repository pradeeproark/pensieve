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
    FieldConstraints,
    FieldType,
    JournalEntry,
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
            db_path = os.environ.get(
                "PENSIEVE_DB",
                str(Path.home() / ".pensieve" / "pensieve.db")
            )

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
            self.conn.execute("""
                INSERT INTO templates (id, name, description, version, created_at, created_by, project)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(template.id),
                template.name,
                template.description,
                template.version,
                template.created_at.isoformat(),
                template.created_by,
                template.project
            ))

            # Insert template fields
            for field in template.fields:
                self.conn.execute("""
                    INSERT INTO template_fields (template_id, name, type, required, constraints_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(template.id),
                    field.name,
                    field.type.value,
                    1 if field.required else 0,
                    json.dumps(field.constraints.model_dump(exclude_none=True))
                ))

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
        cursor = self.conn.execute("""
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            WHERE name = ?
        """, (name,))

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
        cursor = self.conn.execute("""
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            WHERE id = ?
        """, (str(template_id),))

        row = cursor.fetchone()
        if row is None:
            return None

        return self._load_template_from_row(row)

    def list_templates(self) -> list[Template]:
        """List all templates.

        Returns:
            List of all templates
        """
        cursor = self.conn.execute("""
            SELECT id, name, description, version, created_at, created_by, project
            FROM templates
            ORDER BY created_at DESC
        """)

        return [self._load_template_from_row(row) for row in cursor.fetchall()]

    def _load_template_from_row(self, row: sqlite3.Row) -> Template:
        """Load template from database row.

        Args:
            row: Database row from templates table

        Returns:
            Loaded Template object
        """
        # Load template fields
        cursor = self.conn.execute("""
            SELECT name, type, required, constraints_json
            FROM template_fields
            WHERE template_id = ?
            ORDER BY id
        """, (row["id"],))

        fields = []
        for field_row in cursor.fetchall():
            constraints_data = json.loads(field_row["constraints_json"])
            fields.append(TemplateField(
                name=field_row["name"],
                type=FieldType(field_row["type"]),
                required=bool(field_row["required"]),
                constraints=FieldConstraints(**constraints_data)
            ))

        return Template(
            id=UUID(row["id"]),
            name=row["name"],
            description=row["description"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
            project=row["project"],
            fields=fields
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
            self.conn.execute("""
                INSERT INTO journal_entries (id, template_id, template_version, agent, project, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(entry.id),
                str(entry.template_id),
                entry.template_version,
                entry.agent,
                entry.project,
                entry.timestamp.isoformat()
            ))

            # Insert field values
            for field_name, field_value in entry.field_values.items():
                field = next(f for f in template.fields if f.name == field_name)
                self._insert_field_value(entry.id, field_name, field.type, field_value)

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Failed to create entry: {e}") from e

    def _validate_entry_against_template(
        self,
        entry: JournalEntry,
        template: Template
    ) -> None:
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
        self,
        entry_id: UUID,
        field_name: str,
        field_type: FieldType,
        value: Any
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

        self.conn.execute("""
            INSERT INTO entry_field_values (
                entry_id, field_name, field_type,
                value_text, value_boolean, value_url, value_timestamp, value_file_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(entry_id),
            field_name,
            field_type.value,
            columns["value_text"],
            columns["value_boolean"],
            columns["value_url"],
            columns["value_timestamp"],
            columns["value_file_path"]
        ))

    def get_entry_by_id(self, entry_id: UUID) -> JournalEntry | None:
        """Get journal entry by ID.

        Args:
            entry_id: Entry UUID

        Returns:
            JournalEntry if found, None otherwise
        """
        cursor = self.conn.execute("""
            SELECT id, template_id, template_version, agent, project, timestamp
            FROM journal_entries
            WHERE id = ?
        """, (str(entry_id),))

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
        cursor = self.conn.execute("""
            SELECT id, template_id, template_version, agent, project, timestamp
            FROM journal_entries
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [self._load_entry_from_row(row) for row in cursor.fetchall()]

    def _load_entry_from_row(self, row: sqlite3.Row) -> JournalEntry:
        """Load journal entry from database row.

        Args:
            row: Database row from journal_entries table

        Returns:
            Loaded JournalEntry object
        """
        # Load field values
        cursor = self.conn.execute("""
            SELECT field_name, field_type, value_text, value_boolean,
                   value_url, value_timestamp, value_file_path
            FROM entry_field_values
            WHERE entry_id = ?
        """, (row["id"],))

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

        return JournalEntry(
            id=UUID(row["id"]),
            template_id=UUID(row["template_id"]),
            template_version=row["template_version"],
            agent=row["agent"],
            project=row["project"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            field_values=field_values
        )
