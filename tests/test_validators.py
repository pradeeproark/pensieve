"""Tests for field validators."""

from datetime import datetime

import pytest

from pensieve.models import FieldConstraints, FieldType
from pensieve.validators import (
    ValidationError,
    validate_boolean,
    validate_field_value,
    validate_file_reference,
    validate_text,
    validate_timestamp,
    validate_url,
)


class TestValidateBoolean:
    """Tests for boolean validation."""

    def test_valid_boolean_true(self) -> None:
        """Test valid True values."""
        constraints = FieldConstraints()
        assert validate_boolean(True, constraints) is True
        assert validate_boolean("true", constraints) is True
        assert validate_boolean("True", constraints) is True
        assert validate_boolean("yes", constraints) is True
        assert validate_boolean("1", constraints) is True
        assert validate_boolean(1, constraints) is True

    def test_valid_boolean_false(self) -> None:
        """Test valid False values."""
        constraints = FieldConstraints()
        assert validate_boolean(False, constraints) is False
        assert validate_boolean("false", constraints) is False
        assert validate_boolean("False", constraints) is False
        assert validate_boolean("no", constraints) is False
        assert validate_boolean("0", constraints) is False
        assert validate_boolean(0, constraints) is False

    def test_invalid_boolean(self) -> None:
        """Test invalid boolean values."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError):
            validate_boolean("invalid", constraints)
        with pytest.raises(ValidationError):
            validate_boolean(2, constraints)


class TestValidateText:
    """Tests for text validation."""

    def test_valid_text(self) -> None:
        """Test valid text."""
        constraints = FieldConstraints()
        assert validate_text("hello", constraints) == "hello"
        assert validate_text("", constraints) == ""

    def test_text_max_length(self) -> None:
        """Test text max_length constraint."""
        constraints = FieldConstraints(max_length=5)
        assert validate_text("hello", constraints) == "hello"

        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_text("toolong", constraints)

    def test_invalid_text_type(self) -> None:
        """Test non-string values."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError):
            validate_text(123, constraints)  # type: ignore[arg-type]


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_url(self) -> None:
        """Test valid URLs."""
        constraints = FieldConstraints()
        assert validate_url("https://example.com", constraints) == "https://example.com"
        assert validate_url("http://example.com/path", constraints) == "http://example.com/path"
        assert validate_url("file:///path/to/file", constraints) == "file:///path/to/file"

    def test_url_scheme_constraint(self) -> None:
        """Test URL scheme restrictions."""
        constraints = FieldConstraints(url_schemes=["https"])
        assert validate_url("https://example.com", constraints) == "https://example.com"

        with pytest.raises(ValidationError, match="scheme.*not allowed"):
            validate_url("http://example.com", constraints)

    def test_invalid_url(self) -> None:
        """Test invalid URL format."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError, match="Invalid URL"):
            validate_url("not a url", constraints)


class TestValidateTimestamp:
    """Tests for timestamp validation."""

    def test_valid_timestamp_string(self) -> None:
        """Test valid timestamp strings."""
        constraints = FieldConstraints()
        result = validate_timestamp("2024-01-15T10:30:00Z", constraints)
        assert "2024-01-15" in result

    def test_valid_timestamp_datetime(self) -> None:
        """Test datetime objects."""
        constraints = FieldConstraints()
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = validate_timestamp(dt, constraints)
        assert "2024-01-15" in result

    def test_timestamp_auto_now(self) -> None:
        """Test auto_now constraint."""
        constraints = FieldConstraints(auto_now=True)
        result = validate_timestamp("", constraints)
        # Should be current time
        assert isinstance(result, str)
        assert "T" in result

    def test_timestamp_now_keyword(self) -> None:
        """Test 'now' keyword."""
        constraints = FieldConstraints()
        result = validate_timestamp("now", constraints)
        assert isinstance(result, str)

    def test_invalid_timestamp(self) -> None:
        """Test invalid timestamp format."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError, match="Invalid timestamp"):
            validate_timestamp("not a date", constraints)


class TestValidateFileReference:
    """Tests for file reference validation."""

    def test_valid_file_path(self) -> None:
        """Test valid file paths."""
        constraints = FieldConstraints()
        assert validate_file_reference("/path/to/file.py", constraints) == "/path/to/file.py"
        assert validate_file_reference("relative/path.js", constraints) == "relative/path.js"

    def test_file_type_constraint(self) -> None:
        """Test file type restrictions."""
        constraints = FieldConstraints(file_types=[".py", ".js"])
        assert validate_file_reference("test.py", constraints) == "test.py"
        assert validate_file_reference("test.js", constraints) == "test.js"

        with pytest.raises(ValidationError, match="extension.*not allowed"):
            validate_file_reference("test.txt", constraints)

    def test_invalid_file_path_type(self) -> None:
        """Test non-string path."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError):
            validate_file_reference(123, constraints)  # type: ignore[arg-type]


class TestValidateFieldValue:
    """Tests for the generic validate_field_value function."""

    def test_validate_each_type(self) -> None:
        """Test validation for each field type."""
        # Boolean
        assert validate_field_value(FieldType.BOOLEAN, True, FieldConstraints()) is True

        # Text
        assert validate_field_value(FieldType.TEXT, "test", FieldConstraints()) == "test"

        # URL
        result = validate_field_value(FieldType.URL, "https://example.com", FieldConstraints())
        assert result == "https://example.com"

        # Timestamp
        result = validate_field_value(FieldType.TIMESTAMP, "now", FieldConstraints())
        assert isinstance(result, str)

        # File reference
        result = validate_field_value(FieldType.FILE_REFERENCE, "test.py", FieldConstraints())
        assert result == "test.py"
