"""Tests for field validators."""

from datetime import datetime

import pytest
from pensieve.models import FieldConstraints, FieldType
from pensieve.validators import (
    ValidationError,
    parse_compact_ref,
    validate_boolean,
    validate_field_value,
    validate_file_reference,
    validate_refs,
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

    def test_file_url_rejected(self) -> None:
        """Test that file:// URLs are explicitly rejected."""
        constraints = FieldConstraints()
        with pytest.raises(ValidationError) as exc_info:
            validate_url("file:///path/to/file", constraints)
        error_message = str(exc_info.value)
        assert "file:// URLs are not supported" in error_message
        assert "file_reference field type" in error_message

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


class TestParseCompactRef:
    """Tests for compact ref format parser."""

    def test_parse_code_ref_with_symbol(self) -> None:
        """Test parsing code ref with symbol."""
        ref = parse_compact_ref("impl:s=CircuitBreaker.call,f=**/resilience.py")
        assert ref["name"] == "impl"
        assert ref["kind"] == "code"  # Default
        assert ref["s"] == "CircuitBreaker.call"
        assert ref["f"] == "**/resilience.py"

    def test_parse_code_ref_with_text_pattern(self) -> None:
        """Test parsing code ref with text pattern only."""
        ref = parse_compact_ref("impl:t=def validate_token(")
        assert ref["name"] == "impl"
        assert ref["t"] == "def validate_token("

    def test_parse_doc_ref(self) -> None:
        """Test parsing doc ref with heading."""
        ref = parse_compact_ref("spec:k=doc,f=docs/security.md,h=## Token Validation")
        assert ref["name"] == "spec"
        assert ref["kind"] == "doc"
        assert ref["f"] == "docs/security.md"
        assert ref["h"] == "## Token Validation"

    def test_parse_doc_ref_with_anchor(self) -> None:
        """Test parsing doc ref with anchor."""
        ref = parse_compact_ref("rfc:k=doc,f=docs/rfcs/auth.md,a=decision")
        assert ref["a"] == "decision"

    def test_parse_ref_with_line_hint(self) -> None:
        """Test parsing ref with line hint."""
        ref = parse_compact_ref("impl:f=src/auth.py,l=45")
        assert ref["l"] == 45  # Should be int

    def test_parse_ref_with_page(self) -> None:
        """Test parsing doc ref with page number."""
        ref = parse_compact_ref("pdf:k=doc,f=specs/api.pdf,p=12")
        assert ref["p"] == 12  # Should be int

    def test_parse_ref_with_commit(self) -> None:
        """Test parsing ref with explicit commit."""
        ref = parse_compact_ref("impl:t=def foo(,c=abc123")
        assert ref["c"] == "abc123"

    def test_parse_invalid_format_no_colon(self) -> None:
        """Test parsing invalid format without colon."""
        with pytest.raises(ValidationError, match="Invalid ref format"):
            parse_compact_ref("invalidformat")

    def test_parse_invalid_format_empty_name(self) -> None:
        """Test parsing invalid format with empty name."""
        with pytest.raises(ValidationError, match="name"):
            parse_compact_ref(":t=def foo(")

    def test_parse_with_special_chars_in_value(self) -> None:
        """Test parsing with special characters in text pattern."""
        ref = parse_compact_ref("impl:t=def call(self, func:")
        assert ref["t"] == "def call(self, func:"

    def test_parse_minimal_ref(self) -> None:
        """Test parsing minimal ref with just name and one field."""
        ref = parse_compact_ref("test:f=tests/test_auth.py")
        assert ref["name"] == "test"
        assert ref["f"] == "tests/test_auth.py"


class TestValidateRefs:
    """Tests for refs field validation."""

    def test_validate_single_ref(self) -> None:
        """Test validating a single ref."""
        result = validate_refs(["impl:s=CircuitBreaker.call,t=def call(self"], FieldConstraints())
        assert len(result) == 1
        assert result[0]["name"] == "impl"
        assert result[0]["s"] == "CircuitBreaker.call"

    def test_validate_multiple_refs(self) -> None:
        """Test validating multiple refs."""
        result = validate_refs(
            [
                "impl:s=RetryPolicy.execute",
                "test:f=tests/*.py,t=def test_",
                "spec:k=doc,f=docs/arch.md,h=## Overview",
            ],
            FieldConstraints(),
        )
        assert len(result) == 3
        assert result[0]["name"] == "impl"
        assert result[1]["name"] == "test"
        assert result[2]["name"] == "spec"
        assert result[2]["kind"] == "doc"

    def test_validate_empty_refs(self) -> None:
        """Test validating empty refs list."""
        result = validate_refs([], FieldConstraints())
        assert result == []

    def test_validate_refs_rejects_invalid_code_ref(self) -> None:
        """Test that invalid code ref (no locator) is rejected."""
        with pytest.raises(ValidationError, match="at least one of"):
            validate_refs(["impl:k=code"], FieldConstraints())

    def test_validate_refs_rejects_invalid_doc_ref(self) -> None:
        """Test that invalid doc ref (no file) is rejected."""
        with pytest.raises(ValidationError, match="requires file"):
            validate_refs(["spec:k=doc,h=## Setup"], FieldConstraints())

    def test_validate_refs_returns_json_serializable(self) -> None:
        """Test that result is JSON serializable (list of dicts)."""
        import json

        result = validate_refs(["impl:t=def foo("], FieldConstraints())
        # Should not raise
        json_str = json.dumps(result)
        assert "impl" in json_str

    def test_validate_refs_in_validate_field_value(self) -> None:
        """Test refs validation through validate_field_value."""
        result = validate_field_value(FieldType.REFS, ["impl:t=def foo("], FieldConstraints())
        assert len(result) == 1
        assert result[0]["name"] == "impl"
