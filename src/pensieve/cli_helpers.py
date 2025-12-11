"""Helper functions for CLI argument parsing."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pensieve.models import FieldConstraints, FieldType, JournalEntry, TemplateField

if TYPE_CHECKING:
    from pensieve.database import Database


# Entry ID resolution exceptions


class AmbiguousEntryError(Exception):
    """Raised when multiple entries match a short ID prefix."""

    def __init__(self, prefix: str, candidates: list[str]):
        self.prefix = prefix
        self.candidates = candidates
        super().__init__(f"Multiple entries match '{prefix}': {', '.join(candidates)}")


class EntryNotFoundError(Exception):
    """Raised when no entry matches the given ID."""

    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        super().__init__(f"No entry found matching '{entry_id}'")


class InvalidEntryIdError(Exception):
    """Raised when the entry ID format is invalid."""

    def __init__(self, entry_id: str, reason: str):
        self.entry_id = entry_id
        self.reason = reason
        super().__init__(f"Invalid entry ID '{entry_id}': {reason}")


# UUID validation pattern - UUIDs contain hex chars and dashes
_UUID_HEX_PATTERN = re.compile(r"^[0-9a-f-]+$", re.IGNORECASE)
_MIN_SHORT_ID_LENGTH = 4


def resolve_entry_id(db: "Database", entry_id: str) -> JournalEntry:
    """
    Resolve an entry ID (full or short-form) to a JournalEntry.

    Supports:
    - Full UUIDs (e.g., "e9306c50-1234-5678-90ab-cdef12345678")
    - Short-form IDs (e.g., "e9306c50") with minimum 4 characters

    Args:
        db: Database instance
        entry_id: Full UUID or short-form prefix (minimum 4 chars)

    Returns:
        JournalEntry matching the ID

    Raises:
        InvalidEntryIdError: If ID format is invalid (too short or invalid chars)
        EntryNotFoundError: If no entry matches the ID
        AmbiguousEntryError: If multiple entries match the short ID prefix
    """
    # Validate minimum length
    if len(entry_id) < _MIN_SHORT_ID_LENGTH:
        raise InvalidEntryIdError(entry_id, f"must be at least {_MIN_SHORT_ID_LENGTH} characters")

    # Validate hex characters (UUIDs are hex + dashes)
    if not _UUID_HEX_PATTERN.match(entry_id):
        raise InvalidEntryIdError(
            entry_id, "contains invalid characters (only hex digits 0-9, a-f and dashes allowed)"
        )

    # Try exact UUID match first (more efficient)
    try:
        uuid = UUID(entry_id)
        entry = db.get_entry_by_id(uuid)
        if entry:
            return entry
        raise EntryNotFoundError(entry_id)
    except ValueError:
        # Not a valid full UUID, try prefix search
        pass

    # Prefix search
    entries = db.search_entries_by_id_prefix(entry_id)

    if not entries:
        raise EntryNotFoundError(entry_id)

    if len(entries) > 1:
        candidates = [str(e.id) for e in entries]
        raise AmbiguousEntryError(entry_id, candidates)

    return entries[0]


def parse_field_definition(field_str: str) -> TemplateField:
    """
    Parse field definition string.

    Format: name:type:required|optional:constraints:description

    Examples:
        "problem:text:required:max_length=500:Description of the problem"
        "url:url:optional::Related URL"
        "created:timestamp:required:auto_now=true:Creation timestamp"

    Args:
        field_str: Field definition string

    Returns:
        TemplateField object

    Raises:
        ValueError: If format is invalid or type is unknown
    """
    parts = field_str.split(":", 4)
    if len(parts) != 5:
        raise ValueError(
            f"Invalid field format: '{field_str}'. "
            "Expected format: name:type:required|optional:constraints:description"
        )

    name, type_str, required_str, constraints_str, description = parts

    # Parse type
    try:
        field_type = FieldType[type_str.upper()]
    except KeyError:
        valid_types = ", ".join(t.value for t in FieldType)
        raise ValueError(f"Invalid field type: '{type_str}'. Valid types: {valid_types}")

    # Parse required
    required = required_str.lower() == "required"

    # Parse constraints
    constraints = _parse_constraints(constraints_str, field_type)

    return TemplateField(
        name=name,
        type=field_type,
        required=required,
        constraints=constraints,
        description=description,
    )


def _parse_constraints(constraints_str: str, field_type: FieldType) -> FieldConstraints:
    """
    Parse constraints string based on field type.

    Args:
        constraints_str: Constraint string (e.g., "max_length=500" or "")
        field_type: Field type to determine valid constraints

    Returns:
        FieldConstraints object
    """
    constraints = FieldConstraints()

    if not constraints_str:
        return constraints

    # Parse single key=value pair (constraint string doesn't support multiple constraints)
    if "=" not in constraints_str:
        return constraints

    key, value = constraints_str.split("=", 1)
    key = key.strip()
    value = value.strip()

    if key == "max_length":
        constraints.max_length = int(value)
    elif key == "url_schemes":
        constraints.url_schemes = [s.strip() for s in value.split(",")]
    elif key == "file_types":
        constraints.file_types = [s.strip() for s in value.split(",")]
    elif key == "auto_now":
        constraints.auto_now = value.lower() == "true"

    return constraints


def parse_field_value(field_str: str) -> tuple[str, str]:
    """
    Parse field value string.

    Format: key=value

    Example: "problem=Issue description here"

    Args:
        field_str: Field value string

    Returns:
        Tuple of (key, value)

    Raises:
        ValueError: If format is invalid
    """
    if "=" not in field_str:
        raise ValueError(f"Invalid field format: '{field_str}'. Expected format: key=value")

    key, value = field_str.split("=", 1)
    return key.strip(), value.strip()


def load_entry_from_json(file_path: str) -> dict[str, Any]:
    """
    Load entry field values from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary of field values

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {file_path}, got {type(data).__name__}")

    return data


def load_template_from_json(file_path: str) -> dict[str, Any]:
    """
    Load template definition from JSON file.

    Expected format:
    {
        "name": "template_name",
        "description": "Template description",
        "fields": [
            {
                "name": "field_name",
                "type": "text",
                "required": true,
                "constraints": {"max_length": 500},
                "description": "Field description"
            }
        ]
    }

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary with template data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or missing required fields
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

    # Validate required fields
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {file_path}")

    if "name" not in data:
        raise ValueError(f"Missing required field 'name' in {file_path}")

    if "fields" not in data:
        raise ValueError(f"Missing required field 'fields' in {file_path}")

    return data
