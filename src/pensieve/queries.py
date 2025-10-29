"""Query system for searching journal entries."""

import sqlite3
from datetime import datetime
from typing import Any
from uuid import UUID

from dateutil import parser as dateparser

from pensieve.database import Database
from pensieve.models import JournalEntry


class QueryBuilder:
    """Builds SQL queries for searching journal entries."""

    def __init__(self, db: Database) -> None:
        """Initialize query builder.

        Args:
            db: Database instance
        """
        self.db = db
        self.where_clauses: list[str] = []
        self.params: list[Any] = []

    def by_template(self, template_name: str) -> "QueryBuilder":
        """Filter by template name.

        Args:
            template_name: Name of the template

        Returns:
            Self for chaining
        """
        # First get the template ID
        template = self.db.get_template_by_name(template_name)
        if template is None:
            # Return a query that will match nothing
            self.where_clauses.append("1 = 0")
            return self

        self.where_clauses.append("journal_entries.template_id = ?")
        self.params.append(str(template.id))
        return self

    def by_agent(self, agent: str) -> "QueryBuilder":
        """Filter by agent name.

        Args:
            agent: Agent name

        Returns:
            Self for chaining
        """
        self.where_clauses.append("journal_entries.agent = ?")
        self.params.append(agent)
        return self

    def by_date_range(
        self,
        from_date: str | datetime | None = None,
        to_date: str | datetime | None = None
    ) -> "QueryBuilder":
        """Filter by date range.

        Args:
            from_date: Start date (inclusive). Can be ISO string or datetime.
            to_date: End date (inclusive). Can be ISO string or datetime.

        Returns:
            Self for chaining
        """
        if from_date:
            if isinstance(from_date, str):
                from_date = dateparser.isoparse(from_date)
            self.where_clauses.append("journal_entries.timestamp >= ?")
            self.params.append(from_date.isoformat())

        if to_date:
            if isinstance(to_date, str):
                to_date = dateparser.isoparse(to_date)
            self.where_clauses.append("journal_entries.timestamp <= ?")
            self.params.append(to_date.isoformat())

        return self

    def by_project(self, project: str, exact: bool = False) -> "QueryBuilder":
        """Filter by project path.

        Args:
            project: Project path or substring to search for
            exact: If True, exact match. If False, substring match (default).

        Returns:
            Self for chaining
        """
        if exact:
            self.where_clauses.append("journal_entries.project = ?")
            self.params.append(project)
        else:
            self.where_clauses.append("journal_entries.project LIKE ?")
            self.params.append(f"%{project}%")

        return self

    def by_field_value(
        self,
        field_name: str,
        value: Any,
        exact: bool = True
    ) -> "QueryBuilder":
        """Filter by field value.

        Args:
            field_name: Name of the field to search
            value: Value to search for
            exact: If True, exact match. If False, substring match (for text fields)

        Returns:
            Self for chaining
        """
        if exact:
            # Exact match across all value columns
            self.where_clauses.append("""
                journal_entries.id IN (
                    SELECT entry_id FROM entry_field_values
                    WHERE field_name = ?
                    AND (
                        value_text = ? OR
                        value_boolean = ? OR
                        value_url = ? OR
                        value_timestamp = ? OR
                        value_file_path = ?
                    )
                )
            """)
            # Convert value to appropriate types for comparison
            bool_val = 1 if value else 0 if isinstance(value, bool) else None
            str_val = str(value) if not isinstance(value, bool) else None
            self.params.extend([
                field_name,
                str_val, bool_val, str_val, str_val, str_val
            ])
        else:
            # Substring match for text fields
            self.where_clauses.append("""
                journal_entries.id IN (
                    SELECT entry_id FROM entry_field_values
                    WHERE field_name = ?
                    AND (
                        value_text LIKE ? OR
                        value_url LIKE ? OR
                        value_file_path LIKE ?
                    )
                )
            """)
            pattern = f"%{value}%"
            self.params.extend([field_name, pattern, pattern, pattern])

        return self

    def execute(self, limit: int = 50, offset: int = 0) -> list[JournalEntry]:
        """Execute the query and return results.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching journal entries
        """
        # Build the WHERE clause
        where_sql = ""
        if self.where_clauses:
            where_sql = "WHERE " + " AND ".join(self.where_clauses)

        # Build and execute the query
        sql = f"""
            SELECT id, template_id, template_version, agent, project, timestamp
            FROM journal_entries
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """

        cursor = self.db.conn.execute(sql, self.params + [limit, offset])
        rows = cursor.fetchall()

        return [self.db._load_entry_from_row(row) for row in rows]

    def count(self) -> int:
        """Count matching entries without retrieving them.

        Returns:
            Number of matching entries
        """
        where_sql = ""
        if self.where_clauses:
            where_sql = "WHERE " + " AND ".join(self.where_clauses)

        sql = f"""
            SELECT COUNT(*) FROM journal_entries
            {where_sql}
        """

        cursor = self.db.conn.execute(sql, self.params)
        return cursor.fetchone()[0]


def search_entries(
    db: Database,
    template: str | None = None,
    agent: str | None = None,
    project: str | None = None,
    from_date: str | datetime | None = None,
    to_date: str | datetime | None = None,
    field_name: str | None = None,
    field_value: Any = None,
    exact: bool = True,
    limit: int = 50,
    offset: int = 0
) -> list[JournalEntry]:
    """Search for journal entries with various filters.

    Args:
        db: Database instance
        template: Filter by template name
        agent: Filter by agent name
        project: Filter by project path (substring match)
        from_date: Filter entries from this date (inclusive)
        to_date: Filter entries to this date (inclusive)
        field_name: Filter by field name (requires field_value)
        field_value: Filter by field value (requires field_name)
        exact: If True, exact field match. If False, substring match.
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of matching journal entries
    """
    query = QueryBuilder(db)

    if template:
        query.by_template(template)

    if agent:
        query.by_agent(agent)

    if project:
        query.by_project(project, exact=False)  # Always use substring for project

    if from_date or to_date:
        query.by_date_range(from_date, to_date)

    if field_name and field_value is not None:
        query.by_field_value(field_name, field_value, exact)

    return query.execute(limit, offset)
