"""Helper functions for CLI argument parsing."""

from pensieve.models import FieldConstraints, FieldType, TemplateField


def parse_field_definition(field_str: str) -> TemplateField:
    """
    Parse field definition string.

    Format: name:type:required|optional:constraints

    Examples:
        "problem:text:required:max_length=500"
        "url:url:optional:"
        "created:timestamp:required:auto_now=true"

    Args:
        field_str: Field definition string

    Returns:
        TemplateField object

    Raises:
        ValueError: If format is invalid or type is unknown
    """
    parts = field_str.split(":", 3)
    if len(parts) != 4:
        raise ValueError(
            f"Invalid field format: '{field_str}'. "
            "Expected format: name:type:required|optional:constraints"
        )

    name, type_str, required_str, constraints_str = parts

    # Parse type
    try:
        field_type = FieldType[type_str.upper()]
    except KeyError:
        valid_types = ", ".join(t.value for t in FieldType)
        raise ValueError(
            f"Invalid field type: '{type_str}'. Valid types: {valid_types}"
        )

    # Parse required
    required = required_str.lower() == "required"

    # Parse constraints
    constraints = _parse_constraints(constraints_str, field_type)

    return TemplateField(
        name=name,
        type=field_type,
        required=required,
        constraints=constraints
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
        raise ValueError(
            f"Invalid field format: '{field_str}'. Expected format: key=value"
        )

    key, value = field_str.split("=", 1)
    return key.strip(), value.strip()
