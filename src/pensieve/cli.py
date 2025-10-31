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
    load_entry_from_json,
    load_template_from_json,
    parse_field_definition,
    parse_field_value,
)
from pensieve.database import Database, DatabaseError
from pensieve.graph_traversal import traverse_entry_links
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
from pensieve.path_utils import (
    auto_detect_project,
    expand_project_path,
    normalize_project_search,
    validate_project_path,
)
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
@click.option("--project", required=False, help="Project directory path (auto-detected if omitted)")
@click.option("--description", default="", help="Template description")
@click.option("--field", "fields", multiple=True, help="Field definition (repeatable)")
@click.option("--from-file", "file_path", help="Load template from JSON file")
def template_create(
    name: str,
    project: str | None,
    description: str,
    fields: tuple[str, ...],
    file_path: str | None
) -> None:
    """Create a new template (non-interactive).

    Project is auto-detected from git repository root or current directory.
    Use --project to override.

    Two modes:

    1. Inline field definitions:
       pensieve template create my_template \\
         --description "My template" \\
         --field "name:text:required:max_length=100:Field description" \\
         --field "url:url:optional::Optional URL"

    2. From JSON file:
       pensieve template create my_template --from-file template.json

    Override project:
       pensieve template create my_template --project /custom/path --field "..."
    """
    db = Database()

    try:
        # Auto-detect project if not provided
        if project is None:
            project = auto_detect_project()

        # Validate and normalize project path
        normalized_project, warning = validate_project_path(project)
        if warning:
            click.echo(warning, err=True)

        # Validate mutual exclusivity
        if file_path and fields:
            click.echo("Error: Cannot use both --field and --from-file. Choose one input method.", err=True)
            sys.exit(1)

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
@click.option("--project", required=False, help="Project directory path (auto-detected if omitted)")
@click.option("--field", "fields", multiple=True, help="Field value key=value (repeatable)")
@click.option("--from-file", "file_path", help="Load entry from JSON file")
def entry_create(
    template_name: str,
    project: str | None,
    fields: tuple[str, ...],
    file_path: str | None
) -> None:
    """Create a new journal entry (non-interactive).

    Project is auto-detected from git repository root or current directory.
    Use --project to override.

    Two modes:

    1. Inline field values:
       pensieve entry create problem_solved \\
         --field problem="Issue description" \\
         --field solution="How it was fixed"

    2. From JSON file:
       pensieve entry create problem_solved --from-file entry.json

    Override project:
       pensieve entry create problem_solved --project /custom/path --field "..."
    """
    db = Database()

    try:
        # Auto-detect project if not provided
        if project is None:
            project = auto_detect_project()

        # Validate and normalize project path
        normalized_project, warning = validate_project_path(project)
        if warning:
            click.echo(warning, err=True)

        # Validate mutual exclusivity
        if file_path and fields:
            click.echo("Error: Cannot use both --field and --from-file. Choose one input method.", err=True)
            sys.exit(1)

        # Get template
        template = db.get_template_by_name(template_name)
        if not template:
            click.echo(f"Error: Template '{template_name}' not found", err=True)
            click.echo("\nAvailable templates:")
            for tmpl in db.list_templates():
                click.echo(f"  - {tmpl.name}")
            sys.exit(1)

        # Load from file or use inline arguments
        if file_path:
            # Load from JSON file
            try:
                field_values = load_entry_from_json(file_path)
            except (FileNotFoundError, ValueError) as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
        else:
            # Parse inline field values
            if not fields:
                click.echo("Error: No fields provided. Use --field or --from-file", err=True)
                sys.exit(1)

            field_values = {}
            try:
                for field_str in fields:
                    key, value = parse_field_value(field_str)
                    field_values[key] = value
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        # Validate all required fields are present
        required_fields = {f.name for f in template.fields if f.required}
        provided_fields = set(field_values.keys())
        missing_fields = required_fields - provided_fields

        if missing_fields:
            click.echo(f"Error: Missing required fields: {', '.join(sorted(missing_fields))}", err=True)
            click.echo(f"\nRequired fields for template '{template_name}':")
            for field in template.fields:
                if field.required:
                    click.echo(f"  - {field.name}: {field.description}")
            sys.exit(1)

        # Get agent name from environment or use default
        agent = os.environ.get("USER", "unknown")

        # Create entry
        entry = JournalEntry(
            template_id=template.id,
            template_version=template.version,
            agent=agent,
            project=normalized_project,
            field_values=field_values
        )

        db.create_entry(entry, template)
        click.echo(f"\n✓ Created entry: {entry.id}")
        click.echo(f"  Template: {template_name}")
        click.echo(f"  Project: {expand_project_path(entry.project)}")
        click.echo(f"\n💡 Management options:")
        click.echo(f"  • Link to related entries:  pensieve entry link {entry.id} <other-id> --type <type>")
        click.echo(f"  • Add tags:                 pensieve entry tag {entry.id} --add <tag>")
        click.echo(f"  • Supersede old entry:      pensieve entry link {entry.id} <old-id> --type supersedes")
        click.echo(f"\n  Run 'pensieve entry show {entry.id}' to view this entry")

    except DatabaseError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValidationError as e:
        click.echo(f"Validation error: {e}", err=True)
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
@click.option("--follow-links", "-f", is_flag=True, help="Follow and display related entries")
@click.option("--depth", type=int, default=1, help="Maximum depth for link traversal (default: 1)")
def entry_show(entry_id: str, follow_links: bool, depth: int) -> None:
    """Show entry details."""
    # Validate depth
    if depth < 1:
        click.echo(f"Error: depth must be at least 1", err=True)
        sys.exit(1)

    # Warn if depth specified without follow_links
    if depth != 1 and not follow_links:
        click.echo(f"Warning: --depth specified without --follow-links, ignoring depth parameter", err=True)

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

        # Show status with visual indicator
        status_indicator = "✓" if e.status == EntryStatus.ACTIVE else "⚠️"
        click.echo(f"Status: {status_indicator} {e.status.value}")

        # Show tags if present
        if e.tags:
            click.echo(f"Tags: {', '.join(e.tags)}")

        click.echo(f"\nField Values:\n")

        for field_name, field_value in e.field_values.items():
            click.echo(f"  {field_name}: {field_value}")

        # Show links FROM this entry
        if e.links_from:
            click.echo(f"\nLinks from this entry:\n")
            for link in e.links_from:
                target = db.get_entry_by_id(link.target_entry_id)
                if target:
                    target_template = db.get_template_by_id(target.template_id)
                    target_template_name = target_template.name if target_template else "(unknown)"
                    click.echo(f"  {link.link_type.value} → {link.target_entry_id} ({target_template_name})")

        # Show links TO this entry
        if e.links_to:
            click.echo(f"\nLinks to this entry:\n")
            for link in e.links_to:
                source = db.get_entry_by_id(link.source_entry_id)
                if source:
                    source_template = db.get_template_by_id(source.template_id)
                    source_template_name = source_template.name if source_template else "(unknown)"
                    click.echo(f"  {link.link_type.value} ← {link.source_entry_id} ({source_template_name})")

        # Handle --follow-links flag
        has_links = bool(e.links_from or e.links_to)

        if follow_links:
            # Traverse and display related entries
            related = traverse_entry_links(db, uuid, depth)

            if related:
                click.echo("\n" + "━" * 60)
                click.echo(f"Related Entries (depth {depth}):")
                click.echo("━" * 60 + "\n")

                for metadata in related:
                    rel_template = db.get_template_by_id(metadata.entry.template_id)
                    rel_template_name = rel_template.name if rel_template else "(unknown)"
                    rel_expanded_project = expand_project_path(metadata.entry.project)

                    # Status indicator
                    rel_status_indicator = "✓" if metadata.entry.status == EntryStatus.ACTIVE else "⚠️"

                    # Format path
                    path_str = " ".join([f"{lt.value} {dir}" for lt, dir in metadata.path])

                    # Header line with depth, id, template, timestamp, status
                    click.echo(
                        f"[Depth {metadata.depth}] {metadata.entry_id} ({rel_template_name}) • "
                        f"{metadata.entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} • "
                        f"{rel_status_indicator} {metadata.entry.status.value}"
                    )

                    # Path line
                    click.echo(f"  Path: {path_str}")

                    # Field values
                    if metadata.entry.field_values:
                        click.echo(f"  Fields:")
                        for field_name, field_value in metadata.entry.field_values.items():
                            click.echo(f"    {field_name}: {field_value}")

                    click.echo()  # Blank line between entries
            else:
                click.echo(f"\nNo related entries found within depth {depth}.")

            # Hint about depth if using default
            if depth == 1:
                click.echo(f"\n💡 Hint: Showing links at depth 1 (default). Use --depth N to see deeper relationships.")

        elif has_links:
            # Show hint about --follow-links if entry has links and flag not used
            click.echo(f"\n💡 Hint: This entry has linked entries. Use --follow-links to see related entries.")

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
@click.option("--status", type=click.Choice(["active", "deprecated", "superseded"]), help="Filter by entry status")
@click.option("--tag", "tags", multiple=True, help="Filter by tag (entries with ANY of these tags, repeatable)")
@click.option("--linked-to", help="Filter entries that link TO this entry ID")
@click.option("--linked-from", help="Filter entries linked FROM this entry ID")
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
    status: str | None,
    tags: tuple[str, ...],
    linked_to: str | None,
    linked_from: str | None,
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

        # Validate linked-to/linked-from are valid UUIDs if provided
        linked_to_uuid = None
        if linked_to:
            try:
                linked_to_uuid = UUID(linked_to)
            except ValueError:
                click.echo(f"Error: Invalid UUID format for --linked-to", err=True)
                sys.exit(1)

        linked_from_uuid = None
        if linked_from:
            try:
                linked_from_uuid = UUID(linked_from)
            except ValueError:
                click.echo(f"Error: Invalid UUID format for --linked-from", err=True)
                sys.exit(1)

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
            status=status,
            tags=list(tags) if tags else None,
            linked_to=linked_to_uuid,
            linked_from=linked_from_uuid,
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

            # Show status with visual indicator if not active
            if e.status != EntryStatus.ACTIVE:
                status_indicator = "⚠️"
                click.echo(f"  Status: {status_indicator} {e.status.value}")

                # If superseded, show what supersedes it
                if e.status == EntryStatus.SUPERSEDED:
                    for link in e.links_to:
                        if link.link_type == LinkType.SUPERSEDES:
                            click.echo(f"  → Superseded by: {link.source_entry_id}")
                            break

            # Show tags if present
            if e.tags:
                click.echo(f"  Tags: {', '.join(e.tags)}")

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


@entry.command("update-status")
@click.argument("entry_id")
@click.argument("status", type=click.Choice(["active", "deprecated", "superseded"]))
def entry_update_status(entry_id: str, status: str) -> None:
    """Update entry status.

    Examples:
        pensieve entry update-status abc123 deprecated
        pensieve entry update-status abc123 superseded
    """
    db = Database()

    try:
        try:
            uuid = UUID(entry_id)
        except ValueError:
            click.echo(f"Error: Invalid entry ID format", err=True)
            sys.exit(1)

        # Verify entry exists
        entry = db.get_entry_by_id(uuid)
        if entry is None:
            click.echo(f"Error: Entry '{entry_id}' not found", err=True)
            sys.exit(1)

        # Update status
        new_status = EntryStatus(status)
        db.update_entry_status(uuid, new_status)

        click.echo(f"Updated entry {entry_id} status to '{status}'")

    except DatabaseError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@entry.command("link")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--type", "link_type", type=click.Choice(["supersedes", "relates_to", "augments", "deprecates"]), required=True, help="Link type")
def entry_link(from_id: str, to_id: str, link_type: str) -> None:
    """Create a link between two entries.

    Examples:
        pensieve entry link new-id old-id --type supersedes
        pensieve entry link entry1 entry2 --type relates_to
    """
    db = Database()

    try:
        # Parse UUIDs
        try:
            from_uuid = UUID(from_id)
            to_uuid = UUID(to_id)
        except ValueError:
            click.echo(f"Error: Invalid UUID format", err=True)
            sys.exit(1)

        # Get agent name from environment or use default
        agent = os.environ.get("USER", "unknown")

        # Create link
        link = EntryLink(
            source_entry_id=from_uuid,
            target_entry_id=to_uuid,
            link_type=LinkType(link_type),
            created_by=agent
        )

        db.create_entry_link(link)

        click.echo(f"Created link: {from_id} --{link_type}--> {to_id}")

    except DatabaseError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@entry.command("tag")
@click.argument("entry_id")
@click.option("--add", "add_tags", multiple=True, help="Tag to add (repeatable)")
@click.option("--remove", "remove_tags", multiple=True, help="Tag to remove (repeatable)")
def entry_tag(entry_id: str, add_tags: tuple[str, ...], remove_tags: tuple[str, ...]) -> None:
    """Add or remove tags from an entry.

    Examples:
        pensieve entry tag abc123 --add authentication --add security
        pensieve entry tag abc123 --remove outdated
        pensieve entry tag abc123 --add bug-fix --remove workaround
    """
    db = Database()

    try:
        # Validate at least one operation
        if not add_tags and not remove_tags:
            click.echo("Error: Must specify at least one --add or --remove option", err=True)
            sys.exit(1)

        # Parse UUID
        try:
            uuid = UUID(entry_id)
        except ValueError:
            click.echo(f"Error: Invalid entry ID format", err=True)
            sys.exit(1)

        # Verify entry exists
        entry = db.get_entry_by_id(uuid)
        if entry is None:
            click.echo(f"Error: Entry '{entry_id}' not found", err=True)
            sys.exit(1)

        # Add tags
        if add_tags:
            db.add_entry_tags(uuid, list(add_tags))
            click.echo(f"Added tags: {', '.join(add_tags)}")

        # Remove tags
        if remove_tags:
            db.remove_entry_tags(uuid, list(remove_tags))
            click.echo(f"Removed tags: {', '.join(remove_tags)}")

        # Show current tags
        updated_entry = db.get_entry_by_id(uuid)
        if updated_entry and updated_entry.tags:
            click.echo(f"Current tags: {', '.join(updated_entry.tags)}")
        else:
            click.echo("Current tags: (none)")

    except DatabaseError as e:
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
