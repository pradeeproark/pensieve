"""Field validators for different data types."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import validators
from dateutil import parser as dateparser

from pensieve.models import FieldConstraints, FieldType, Ref


class ValidationError(Exception):
    """Raised when field validation fails."""

    pass


def validate_boolean(value: Any, constraints: FieldConstraints) -> bool:
    """Validate boolean field value.

    Args:
        value: Value to validate
        constraints: Field constraints (unused for boolean)

    Returns:
        Validated boolean value

    Raises:
        ValidationError: If value is not a valid boolean
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ("true", "yes", "1", "y"):
            return True
        if lower_value in ("false", "no", "0", "n"):
            return False

    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)

    raise ValidationError(
        f"Invalid boolean value: {value}. Expected true/false, yes/no, 1/0, or boolean type."
    )


def validate_text(value: Any, constraints: FieldConstraints) -> str:
    """Validate text field value.

    Args:
        value: Value to validate
        constraints: Field constraints (max_length)

    Returns:
        Validated text value

    Raises:
        ValidationError: If value is not valid text or exceeds max_length
    """
    if not isinstance(value, str):
        raise ValidationError(f"Invalid text value: {value}. Expected string.")

    if constraints.max_length is not None:
        if len(value) > constraints.max_length:
            raise ValidationError(
                f"Text exceeds maximum length of {constraints.max_length} characters. "
                f"Got {len(value)} characters."
            )

    return value


def validate_url(value: Any, constraints: FieldConstraints) -> str:
    """Validate URL field value.

    Args:
        value: Value to validate
        constraints: Field constraints (url_schemes)

    Returns:
        Validated URL value

    Raises:
        ValidationError: If value is not a valid URL or scheme not allowed
    """
    if not isinstance(value, str):
        raise ValidationError(f"Invalid URL value: {value}. Expected string.")

    # Explicitly reject file:// URLs - use file_reference field type instead
    if value.lower().startswith("file://"):
        raise ValidationError(
            "file:// URLs are not supported in url fields. "
            "Use the file_reference field type for local files."
        )

    # Validate URL format
    if not validators.url(value):
        raise ValidationError(f"Invalid URL format: {value}")

    # Check scheme if constrained
    if constraints.url_schemes:
        parsed = urlparse(value)
        if parsed.scheme not in constraints.url_schemes:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. "
                f"Allowed schemes: {', '.join(constraints.url_schemes)}"
            )

    return value


def validate_timestamp(value: Any, constraints: FieldConstraints) -> str:
    """Validate timestamp field value.

    Args:
        value: Value to validate (ISO8601 string, datetime object, or "now")
        constraints: Field constraints (auto_now)

    Returns:
        Validated ISO8601 timestamp string

    Raises:
        ValidationError: If value is not a valid timestamp
    """
    # Handle auto_now - fill with current time
    if constraints.auto_now or value in ("now", ""):
        return datetime.utcnow().isoformat() + "Z"

    # Handle datetime objects
    if isinstance(value, datetime):
        return value.isoformat() + "Z"

    # Handle string timestamps
    if isinstance(value, str):
        try:
            # Parse the timestamp
            parsed = dateparser.isoparse(value)
            return parsed.isoformat() + "Z"
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid timestamp format: {value}. "
                "Expected ISO8601 format (e.g., 2024-01-15T10:30:00Z)"
            ) from e

    raise ValidationError(
        f"Invalid timestamp value: {value}. Expected ISO8601 string or datetime object."
    )


def validate_file_reference(value: Any, constraints: FieldConstraints) -> str:
    """Validate file reference field value.

    Args:
        value: Value to validate (file path)
        constraints: Field constraints (file_types)

    Returns:
        Validated file path string

    Raises:
        ValidationError: If value is not a valid file path or extension not allowed
    """
    if not isinstance(value, str):
        raise ValidationError(f"Invalid file reference: {value}. Expected string path.")

    # Basic path validation
    try:
        path = Path(value)
    except Exception as e:
        raise ValidationError(f"Invalid file path: {value}") from e

    # Check file extension if constrained
    if constraints.file_types:
        extension = path.suffix.lower()
        allowed_extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in constraints.file_types
        ]

        if extension not in allowed_extensions:
            raise ValidationError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {', '.join(allowed_extensions)}"
            )

    return str(path)


def parse_compact_ref(compact: str) -> dict:
    """Parse compact ref format into a dict.

    Format: name:k=v,k=v,...

    Args:
        compact: Compact ref string (e.g., "impl:s=CircuitBreaker.call,f=**/resilience.py")

    Returns:
        Dict with parsed ref fields

    Raises:
        ValidationError: If format is invalid
    """
    if ":" not in compact:
        raise ValidationError(f"Invalid ref format: '{compact}'. Expected 'name:key=value,...'")

    name, rest = compact.split(":", 1)
    if not name or not name.strip():
        raise ValidationError("Ref name cannot be empty")

    result: dict = {"name": name.strip()}

    if not rest.strip():
        # No key=value pairs after name
        raise ValidationError(f"Ref '{name}' has no locator fields")

    # Parse key=value pairs
    # The tricky part: values can contain commas (e.g., "t=def call(self, arg)")
    # Strategy: Split on ",<single_char>=" pattern which indicates a new key
    # Valid keys are single chars: k, s, f, t, l, c, h, p, a
    # Split on comma followed by a single letter followed by equals
    pattern = r",(?=[ksfltchpa]=)"
    parts = re.split(pattern, rest)

    for part in parts:
        if "=" not in part:
            continue  # Skip malformed parts
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Map short keys to full names and handle type conversion
        if key == "k":
            result["kind"] = value
        elif key == "l":
            try:
                result["l"] = int(value)
            except ValueError:
                raise ValidationError(f"Line hint must be integer, got: {value}")
        elif key == "p":
            try:
                result["p"] = int(value)
            except ValueError:
                raise ValidationError(f"Page number must be integer, got: {value}")
        elif key in ("s", "f", "t", "c", "h", "a"):
            result[key] = value
        else:
            # Unknown key - warn but don't fail
            pass

    # Set default kind if not specified
    if "kind" not in result:
        result["kind"] = "code"

    return result


def validate_refs(value: list, constraints: FieldConstraints) -> list[dict]:
    """Validate refs field value.

    Args:
        value: List of refs - can be compact strings (CLI input) or dicts (internal API)
        constraints: Field constraints (unused for refs)

    Returns:
        List of validated ref dicts (JSON serializable)

    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return []

    result = []
    for ref_input in value:
        if isinstance(ref_input, str):
            # Compact format from CLI: "name:k=v,k=v"
            ref_dict = parse_compact_ref(ref_input)
        elif isinstance(ref_input, dict):
            # Already a dict (from internal API or tests)
            ref_dict = ref_input
        else:
            raise ValidationError(f"Ref must be a string or dict, got: {type(ref_input)}")

        # Validate using Pydantic model
        try:
            ref = Ref.model_validate(ref_dict)
            # Convert back to dict for JSON storage, excluding None values
            result.append(ref.model_dump(exclude_none=True))
        except Exception as e:
            raise ValidationError(str(e))

    return result


def validate_field_value(field_type: FieldType, value: Any, constraints: FieldConstraints) -> Any:
    """Validate a field value based on its type and constraints.

    Args:
        field_type: Type of the field
        value: Value to validate
        constraints: Field constraints

    Returns:
        Validated value (type depends on field_type)

    Raises:
        ValidationError: If validation fails
    """
    validators_map = {
        FieldType.BOOLEAN: validate_boolean,
        FieldType.TEXT: validate_text,
        FieldType.URL: validate_url,
        FieldType.TIMESTAMP: validate_timestamp,
        FieldType.FILE_REFERENCE: validate_file_reference,
        FieldType.REFS: validate_refs,
    }

    validator_func = validators_map.get(field_type)
    if validator_func is None:
        raise ValidationError(f"Unknown field type: {field_type}")

    return validator_func(value, constraints)
