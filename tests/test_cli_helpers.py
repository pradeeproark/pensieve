"""Tests for CLI helper functions."""

import pytest

from pensieve.cli_helpers import parse_field_definition, parse_field_value
from pensieve.models import FieldType, FieldConstraints


class TestParseFieldDefinition:
    """Tests for parse_field_definition function."""

    def test_text_field_with_max_length(self) -> None:
        """Test parsing text field with max_length constraint."""
        result = parse_field_definition("problem:text:required:max_length=500")

        assert result.name == "problem"
        assert result.type == FieldType.TEXT
        assert result.required is True
        assert result.constraints.max_length == 500

    def test_optional_field_no_constraints(self) -> None:
        """Test parsing optional field without constraints."""
        result = parse_field_definition("notes:text:optional:")

        assert result.name == "notes"
        assert result.type == FieldType.TEXT
        assert result.required is False

    def test_boolean_field(self) -> None:
        """Test parsing boolean field."""
        result = parse_field_definition("resolved:boolean:required:")

        assert result.name == "resolved"
        assert result.type == FieldType.BOOLEAN
        assert result.required is True

    def test_url_field_with_schemes(self) -> None:
        """Test parsing URL field with scheme constraints."""
        result = parse_field_definition("link:url:optional:url_schemes=http,https")

        assert result.name == "link"
        assert result.type == FieldType.URL
        assert result.constraints.url_schemes == ["http", "https"]

    def test_file_reference_with_types(self) -> None:
        """Test parsing file reference with file type constraints."""
        result = parse_field_definition("log:file_reference:optional:file_types=.log,.txt")

        assert result.name == "log"
        assert result.type == FieldType.FILE_REFERENCE
        assert result.constraints.file_types == [".log", ".txt"]

    def test_timestamp_with_auto_now(self) -> None:
        """Test parsing timestamp with auto_now constraint."""
        result = parse_field_definition("created:timestamp:required:auto_now=true")

        assert result.name == "created"
        assert result.type == FieldType.TIMESTAMP
        assert result.constraints.auto_now is True

    def test_invalid_format_raises_error(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid field format"):
            parse_field_definition("invalid")

    def test_invalid_type_raises_error(self) -> None:
        """Test that invalid field type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid field type"):
            parse_field_definition("field:invalid_type:required::Description")


class TestParseFieldValue:
    """Tests for parse_field_value function."""

    def test_simple_key_value(self) -> None:
        """Test parsing simple key=value pair."""
        key, value = parse_field_value("problem=Issue description")
        assert key == "problem"
        assert value == "Issue description"

    def test_value_with_equals_sign(self) -> None:
        """Test parsing value containing equals sign."""
        key, value = parse_field_value("equation=a=b+c")
        assert key == "equation"
        assert value == "a=b+c"

    def test_value_with_spaces(self) -> None:
        """Test parsing value with leading/trailing spaces."""
        key, value = parse_field_value("name = value with spaces ")
        assert key == "name"
        assert value == "value with spaces"

    def test_empty_value(self) -> None:
        """Test parsing empty value."""
        key, value = parse_field_value("key=")
        assert key == "key"
        assert value == ""

    def test_invalid_format_raises_error(self) -> None:
        """Test that format without = raises ValueError."""
        with pytest.raises(ValueError, match="Invalid field format"):
            parse_field_value("no_equals_sign")
