"""Tests for CLI helper functions."""

import json
import pytest
from pathlib import Path

from pensieve.cli_helpers import (
    load_entry_from_json,
    load_template_from_json,
    parse_field_definition,
    parse_field_value,
)
from pensieve.models import FieldType, FieldConstraints


class TestParseFieldDefinition:
    """Tests for parse_field_definition function."""

    def test_text_field_with_max_length(self) -> None:
        """Test parsing text field with max_length constraint."""
        result = parse_field_definition("problem:text:required:max_length=500:Description of the problem")

        assert result.name == "problem"
        assert result.type == FieldType.TEXT
        assert result.required is True
        assert result.constraints.max_length == 500
        assert result.description == "Description of the problem"

    def test_optional_field_no_constraints(self) -> None:
        """Test parsing optional field without constraints."""
        result = parse_field_definition("notes:text:optional::Optional notes")

        assert result.name == "notes"
        assert result.type == FieldType.TEXT
        assert result.required is False
        assert result.description == "Optional notes"

    def test_boolean_field(self) -> None:
        """Test parsing boolean field."""
        result = parse_field_definition("resolved:boolean:required::Whether the issue is resolved")

        assert result.name == "resolved"
        assert result.type == FieldType.BOOLEAN
        assert result.required is True
        assert result.description == "Whether the issue is resolved"

    def test_url_field_with_schemes(self) -> None:
        """Test parsing URL field with scheme constraints."""
        result = parse_field_definition("link:url:optional:url_schemes=http,https:Related URL")

        assert result.name == "link"
        assert result.type == FieldType.URL
        assert result.constraints.url_schemes == ["http", "https"]
        assert result.description == "Related URL"

    def test_file_reference_with_types(self) -> None:
        """Test parsing file reference with file type constraints."""
        result = parse_field_definition("log:file_reference:optional:file_types=.log,.txt:Log file reference")

        assert result.name == "log"
        assert result.type == FieldType.FILE_REFERENCE
        assert result.constraints.file_types == [".log", ".txt"]
        assert result.description == "Log file reference"

    def test_timestamp_with_auto_now(self) -> None:
        """Test parsing timestamp with auto_now constraint."""
        result = parse_field_definition("created:timestamp:required:auto_now=true:Creation timestamp")

        assert result.name == "created"
        assert result.type == FieldType.TIMESTAMP
        assert result.constraints.auto_now is True
        assert result.description == "Creation timestamp"

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


class TestLoadEntryFromJson:
    """Tests for load_entry_from_json function."""

    def test_load_valid_entry(self, tmp_path: Path) -> None:
        """Test loading valid entry JSON."""
        entry_file = tmp_path / "entry.json"
        entry_file.write_text(json.dumps({
            "problem": "Test problem",
            "solution": "Test solution",
            "learned": "Test learning"
        }))

        result = load_entry_from_json(str(entry_file))
        assert result["problem"] == "Test problem"
        assert result["solution"] == "Test solution"
        assert result["learned"] == "Test learning"

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_entry_from_json("/nonexistent/file.json")

    def test_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid JSON raises ValueError."""
        entry_file = tmp_path / "bad.json"
        entry_file.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_entry_from_json(str(entry_file))


class TestLoadTemplateFromJson:
    """Tests for load_template_from_json function."""

    def test_load_valid_template(self, tmp_path: Path) -> None:
        """Test loading valid template JSON."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps({
            "name": "test_template",
            "description": "Test description",
            "fields": [
                {
                    "name": "field1",
                    "type": "text",
                    "required": True,
                    "constraints": {"max_length": 100},
                    "description": "First field"
                }
            ]
        }))

        result = load_template_from_json(str(template_file))
        assert result["name"] == "test_template"
        assert result["description"] == "Test description"
        assert len(result["fields"]) == 1
        assert result["fields"][0]["name"] == "field1"

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_template_from_json("/nonexistent/template.json")

    def test_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid JSON raises ValueError."""
        template_file = tmp_path / "bad.json"
        template_file.write_text("not json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_template_from_json(str(template_file))
