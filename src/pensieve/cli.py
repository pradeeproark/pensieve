"""Command-line interface for Pensieve."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import click

from pensieve import __version__
from pensieve.cli_helpers import (
    load_template_from_json,
    parse_field_definition,
)
from pensieve.database import Database, DatabaseError
from pensieve.migration_runner import MigrationRunner
from pensieve.models import FieldConstraints, FieldType, JournalEntry, Template, TemplateField
from pensieve.path_utils import expand_project_path, normalize_project_search, validate_project_path
from pensieve.queries import search_entries
from pensieve.validators import ValidationError


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Pensieve - Memory recording tool for Claude Code agents."""
    pass


# Template commands


@main.group()
def template() -> None:
    """Manage templates."""
    pass


@template.command("create")
@click.argument("name")
@click.option("--project", required=True, help="Project directory path")
@click.option("--description", default="", help="Template description")
@click.option("--field", "fields", multiple=True, help="Field definition (repeatable)")
@click.option("--from-file", "file_path", help="Load template from JSON file")
def template_create(
    name: str,
    project: str,
    description: str,
    fields: tuple[str, ...],
    file_path: str | None
) -> None:
    """Create a new template (non-interactive).

    Two modes:

    1. Inline field definitions:
       pensieve template create my_template --project $(pwd) \\
         --description "My template" \\
         --field "name:text:required:max_length=100:Field description" \\
         --field "url:url:optional::Optional URL"

    2. From JSON file:
       pensieve template create my_template --project $(pwd) \\
         --from-file template.json
    """
    db = Database()

    try:
        # Validate and normalize project path
        normalized_project, warning = validate_project_path(project)
        if warning:
            click.echo(warning, err=True)

        # Load from file or use inline arguments
        if file_path:
            # Load from JSON file
            try:
                data = load_template_from_json(file_path)
                template_name = data.get("name", name)
                template_description = data.get("description", "")

                # Parse fields from JSON
                field_list = []
                for field_data in data["fields"]:
                    field_list.append(TemplateField(
                        name=field_data["name"],
                        type=FieldType[field_data["type"].upper()],
                        required=field_data.get("required", False),
                        constraints=FieldConstraints(**field_data.get("constraints", {})),
                        description=field_data.get("description", "")
                    ))
            except (FileNotFoundError, ValueError) as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
        else:
            # Use inline arguments
            if not fields:
                click.echo("Error: No fields provided. Use --field or --from-file", err=True)
                sys.exit(1)

            template_name = name
            template_description = description

            # Parse field definitions
            field_list = []
            try:
                for field_str in fields:
                    field_list.append(parse_field_definition(field_str))
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        # Get agent name from environment or use default
        agent = os.environ.get("USER", "unknown")

        # Create template
        template = Template(
            name=template_name,
            description=template_description,
            created_by=agent,
            project=normalized_project,
            fields=field_list
        )

        db.create_template(template)
        click.echo(f"✓ Created template: {template.name}")
        click.echo(f"  Project: {expand_project_path(template.project)}")
        click.echo(f"  Fields: {len(template.fields)}")

    except DatabaseError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValidationError as e:
        click.echo(f"Validation error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@template.command("list")
@click.option("--project", help="Filter by project path (substring match)")
def template_list(project: str | None) -> None:
    """List all templates."""
    db = Database()

    try:
        # Normalize project search input if provided
        if project:
            project = normalize_project_search(project)

        templates = db.list_templates()

        # Filter by project if specified
        if project:
            templates = [t for t in templates if project in t.project]

        if not templates:
            click.echo("No templates found")
            return

        click.echo(f"\nFound {len(templates)} template(s):\n")

        for tmpl in templates:
            # Expand project path for display
            expanded_project = expand_project_path(tmpl.project)
            click.echo(f"  {tmpl.name}")
            click.echo(f"    Description: {tmpl.description or '(none)'}")
            click.echo(f"    Project: {expanded_project}")
            click.echo(f"    Fields: {len(tmpl.fields)}")
            click.echo(f"    Created by: {tmpl.created_by}")
            click.echo(f"    Created at: {tmpl.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()

    finally:
        db.close()


@template.command("show")
@click.argument("name")
def template_show(name: str) -> None:
    """Show template details."""
    db = Database()

    try:
        tmpl = db.get_template_by_name(name)

        if tmpl is None:
            click.echo(f"Error: Template '{name}' not found", err=True)
            sys.exit(1)

        # Expand project path for display
        expanded_project = expand_project_path(tmpl.project)

        click.echo(f"\nTemplate: {tmpl.name}")
        click.echo(f"Description: {tmpl.description or '(none)'}")
        click.echo(f"Project: {expanded_project}")
        click.echo(f"Version: {tmpl.version}")
        click.echo(f"Created by: {tmpl.created_by}")
        click.echo(f"Created at: {tmpl.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"\nFields ({len(tmpl.fields)}):\n")

        for field in tmpl.fields:
            required_str = " (required)" if field.required else ""
            click.echo(f"  {field.name}: {field.type.value}{required_str}")

            # Show constraints
            constraints = field.constraints.model_dump(exclude_none=True)
            if constraints:
                for key, value in constraints.items():
                    click.echo(f"    {key}: {value}")

    finally:
        db.close()


@template.command("export")
@click.argument("name")
@click.option("--output", "-o", help="Output file (default: stdout)")
def template_export(name: str, output: str | None) -> None:
    """Export template as JSON."""
    db = Database()

    try:
        tmpl = db.get_template_by_name(name)

        if tmpl is None:
            click.echo(f"Error: Template '{name}' not found", err=True)
            sys.exit(1)

        # Convert to dict
        data = tmpl.model_dump(mode="json")

        json_str = json.dumps(data, indent=2, default=str)

        if output:
            Path(output).write_text(json_str)
            click.echo(f"✓ Template exported to {output}")
        else:
            click.echo(json_str)

    finally:
        db.close()


# Entry commands


@main.group()
def entry() -> None:
    """Manage journal entries."""
    pass


@entry.command("create")
@click.argument("template_name")
@click.option("--agent", default="claude", help="Agent name")
@click.option("--project", required=True, help="Project directory path")
def entry_create(template_name: str, agent: str, project: str) -> None:
    """Create a journal entry."""
    db = Database()

    try:
        # Validate and normalize project path
        try:
            normalized_project, warning = validate_project_path(project)
            if warning:
                click.echo(warning, err=True)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        # Get template
        tmpl = db.get_template_by_name(template_name)

        if tmpl is None:
            click.echo(f"Error: Template '{template_name}' not found", err=True)
            sys.exit(1)

        click.echo(f"\nCreating entry for template: {tmpl.name}")
        click.echo(f"Description: {tmpl.description}\n")

        # Collect field values
        field_values: dict[str, Any] = {}

        for field in tmpl.fields:
            required_str = " (required)" if field.required else " (optional)"
            click.echo(f"Field: {field.name} [{field.type.value}]{required_str}")

            # Show constraints
            if field.constraints.max_length:
                click.echo(f"  Max length: {field.constraints.max_length}")
            if field.constraints.url_schemes:
                click.echo(f"  Allowed schemes: {', '.join(field.constraints.url_schemes)}")
            if field.constraints.file_types:
                click.echo(f"  Allowed types: {', '.join(field.constraints.file_types)}")
            if field.constraints.auto_now:
                click.echo(f"  Auto-fill: current time")

            # Get value
            if field.type == FieldType.BOOLEAN:
                value = click.confirm("Value", default=False)
            elif field.type == FieldType.TIMESTAMP and field.constraints.auto_now:
                value = "now"
                click.echo(f"  → {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                default = "" if field.required else None
                value = click.prompt("Value", default=default, show_default=False)

                # Allow skipping optional fields
                if not field.required and value == "":
                    continue

            field_values[field.name] = value

        # Create entry
        entry_obj = JournalEntry(
            template_id=tmpl.id,
            template_version=tmpl.version,
            agent=agent,
            project=normalized_project,
            field_values=field_values
        )

        db.create_entry(entry_obj, tmpl)
        click.echo(f"\n✓ Entry created successfully (ID: {entry_obj.id})")

    except (ValidationError, DatabaseError) as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@entry.command("list")
@click.option("--limit", default=50, help="Maximum number of entries to show")
@click.option("--offset", default=0, help="Number of entries to skip")
def entry_list(limit: int, offset: int) -> None:
    """List recent journal entries."""
    db = Database()

    try:
        entries = db.list_entries(limit=limit, offset=offset)

        if not entries:
            click.echo("No entries found")
            return

        click.echo(f"\nFound {len(entries)} entry(ies):\n")

        for e in entries:
            template = db.get_template_by_id(e.template_id)
            template_name = template.name if template else "(unknown)"
            expanded_project = expand_project_path(e.project)

            click.echo(f"  ID: {e.id}")
            click.echo(f"  Template: {template_name}")
            click.echo(f"  Agent: {e.agent}")
            click.echo(f"  Project: {expanded_project}")
            click.echo(f"  Timestamp: {e.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()

    finally:
        db.close()


@entry.command("show")
@click.argument("entry_id")
def entry_show(entry_id: str) -> None:
    """Show entry details."""
    db = Database()

    try:
        try:
            uuid = UUID(entry_id)
        except ValueError:
            click.echo(f"Error: Invalid entry ID format", err=True)
            sys.exit(1)

        e = db.get_entry_by_id(uuid)

        if e is None:
            click.echo(f"Error: Entry '{entry_id}' not found", err=True)
            sys.exit(1)

        template = db.get_template_by_id(e.template_id)
        template_name = template.name if template else "(unknown)"
        expanded_project = expand_project_path(e.project)

        click.echo(f"\nEntry: {e.id}")
        click.echo(f"Template: {template_name} (v{e.template_version})")
        click.echo(f"Agent: {e.agent}")
        click.echo(f"Project: {expanded_project}")
        click.echo(f"Timestamp: {e.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"\nField Values:\n")

        for field_name, field_value in e.field_values.items():
            click.echo(f"  {field_name}: {field_value}")

    finally:
        db.close()


@entry.command("search")
@click.option("--template", help="Filter by template name")
@click.option("--agent", help="Filter by agent name")
@click.option("--project", help="Filter by project path (substring match)")
@click.option("--from", "from_date", help="Filter from date (ISO format)")
@click.option("--to", "to_date", help="Filter to date (ISO format)")
@click.option("--field", help="Field name to search")
@click.option("--value", help="Field value to search (requires --field)")
@click.option("--substring", is_flag=True, help="Use substring match instead of exact")
@click.option("--limit", default=50, help="Maximum number of results")
def entry_search(
    template: str | None,
    agent: str | None,
    project: str | None,
    from_date: str | None,
    to_date: str | None,
    field: str | None,
    value: str | None,
    substring: bool,
    limit: int
) -> None:
    """Search journal entries."""
    db = Database()

    try:
        # Validate field/value pairing
        if field and not value:
            click.echo("Error: --value is required when --field is specified", err=True)
            sys.exit(1)
        if value and not field:
            click.echo("Error: --field is required when --value is specified", err=True)
            sys.exit(1)

        # Normalize project search input if provided
        if project:
            project = normalize_project_search(project)

        results = search_entries(
            db=db,
            template=template,
            agent=agent,
            project=project,
            from_date=from_date,
            to_date=to_date,
            field_name=field,
            field_value=value,
            exact=not substring,
            limit=limit
        )

        if not results:
            click.echo("No entries found matching criteria")
            return

        click.echo(f"\nFound {len(results)} entry(ies):\n")

        for e in results:
            template_obj = db.get_template_by_id(e.template_id)
            template_name = template_obj.name if template_obj else "(unknown)"
            expanded_project = expand_project_path(e.project)

            click.echo(f"  ID: {e.id}")
            click.echo(f"  Template: {template_name}")
            click.echo(f"  Agent: {e.agent}")
            click.echo(f"  Project: {expanded_project}")
            click.echo(f"  Timestamp: {e.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            # Show matching field if searched by field
            if field and field in e.field_values:
                click.echo(f"  {field}: {e.field_values[field]}")

            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


# System commands


@main.group()
def migrate() -> None:
    """Manage database migrations."""
    pass


@migrate.command("status")
def migrate_status() -> None:
    """Show migration status."""
    db = Database()

    try:
        runner = MigrationRunner(db.conn)
        status = runner.get_status()

        click.echo(f"\nCurrent schema version: {status['current_version']}")
        click.echo(f"Applied migrations: {status['applied_count']}")
        click.echo(f"Pending migrations: {status['pending_count']}")

        if status['applied_migrations']:
            click.echo("\nApplied:")
            for m in status['applied_migrations']:
                click.echo(f"  [{m['version']}] {m['name']} - {m['applied_at']}")

        if status['pending_migrations']:
            click.echo("\nPending:")
            for m in status['pending_migrations']:
                click.echo(f"  [{m['version']}] {m['name']}")

    finally:
        db.close()


@migrate.command("apply")
def migrate_apply() -> None:
    """Apply pending migrations."""
    db = Database()

    try:
        runner = MigrationRunner(db.conn)
        count = runner.apply_all_pending()

        if count == 0:
            click.echo("No pending migrations")
        else:
            click.echo(f"✓ Applied {count} migration(s)")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@main.command()
def version() -> None:
    """Show version information."""
    db = Database()

    try:
        runner = MigrationRunner(db.conn)
        schema_version = runner.get_current_version()

        click.echo(f"Pensieve v{__version__}")
        click.echo(f"Schema version: {schema_version}")
        click.echo(f"Database: {db.db_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
