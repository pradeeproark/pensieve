"""Field validators for different data types."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import validators
from dateutil import parser as dateparser

from pensieve.models import FieldConstraints, FieldType


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
                f"Invalid timestamp format: {value}. Expected ISO8601 format (e.g., 2024-01-15T10:30:00Z)"
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
        allowed_extensions = [ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                             for ext in constraints.file_types]

        if extension not in allowed_extensions:
            raise ValidationError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {', '.join(allowed_extensions)}"
            )

    return str(path)


def validate_field_value(
    field_type: FieldType,
    value: Any,
    constraints: FieldConstraints
) -> Any:
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
    }

    validator_func = validators_map.get(field_type)
    if validator_func is None:
        raise ValidationError(f"Unknown field type: {field_type}")

    return validator_func(value, constraints)
