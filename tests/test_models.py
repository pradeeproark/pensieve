"""Tests for Pydantic models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pensieve.models import (
    FieldConstraints,
    FieldType,
    JournalEntry,
    Template,
    TemplateField,
)


class TestTemplateField:
    """Tests for TemplateField model."""

    def test_create_valid_field(self) -> None:
        """Test creating a valid template field."""
        field = TemplateField(
            name="test_field",
            type=FieldType.TEXT,
            required=True,
            constraints=FieldConstraints(max_length=100)
        )
        assert field.name == "test_field"
        assert field.type == FieldType.TEXT
        assert field.required is True
        assert field.constraints.max_length == 100

    def test_field_name_validation(self) -> None:
        """Test field name must be alphanumeric with underscores."""
        # Valid names
        TemplateField(name="valid_name", type=FieldType.TEXT)
        TemplateField(name="valid123", type=FieldType.TEXT)

        # Invalid names
        with pytest.raises(ValidationError):
            TemplateField(name="invalid-name", type=FieldType.TEXT)
        with pytest.raises(ValidationError):
            TemplateField(name="invalid name", type=FieldType.TEXT)

    def test_default_values(self) -> None:
        """Test default field values."""
        field = TemplateField(name="test", type=FieldType.TEXT)
        assert field.required is False
        assert isinstance(field.constraints, FieldConstraints)


class TestTemplate:
    """Tests for Template model."""

    def test_create_valid_template(self) -> None:
        """Test creating a valid template."""
        fields = [
            TemplateField(name="field1", type=FieldType.TEXT),
            TemplateField(name="field2", type=FieldType.BOOLEAN)
        ]
        template = Template(
            name="test_template",
            description="Test description",
            created_by="agent",
            project="/test/project",
            fields=fields
        )
        assert template.name == "test_template"
        assert template.description == "Test description"
        assert template.created_by == "agent"
        assert template.project == "/test/project"
        assert len(template.fields) == 2
        assert template.version == 1

    def test_template_name_validation(self) -> None:
        """Test template name must be alphanumeric with underscores."""
        fields = [TemplateField(name="field", type=FieldType.TEXT)]

        # Valid names
        Template(name="valid_name", created_by="agent", project="/test/project", fields=fields)
        Template(name="valid123", created_by="agent", project="/test/project", fields=fields)

        # Invalid names
        with pytest.raises(ValidationError):
            Template(name="invalid-name", created_by="agent", project="/test/project", fields=fields)

    def test_unique_field_names(self) -> None:
        """Test template fields must have unique names."""
        fields = [
            TemplateField(name="field1", type=FieldType.TEXT),
            TemplateField(name="field1", type=FieldType.BOOLEAN)  # Duplicate
        ]

        with pytest.raises(ValidationError, match="unique"):
            Template(name="test", created_by="agent", project="/test/project", fields=fields)

    def test_at_least_one_field_required(self) -> None:
        """Test template must have at least one field."""
        with pytest.raises(ValidationError):
            Template(name="test", created_by="agent", project="/test/project", fields=[])


class TestJournalEntry:
    """Tests for JournalEntry model."""

    def test_create_valid_entry(self) -> None:
        """Test creating a valid journal entry."""
        template_id = uuid4()
        entry = JournalEntry(
            template_id=template_id,
            template_version=1,
            agent="test_agent",
            project="/test/project",
            field_values={"field1": "value1", "field2": True}
        )
        assert entry.template_id == template_id
        assert entry.template_version == 1
        assert entry.agent == "test_agent"
        assert entry.project == "/test/project"
        assert entry.field_values["field1"] == "value1"
        assert entry.field_values["field2"] is True

    def test_default_values(self) -> None:
        """Test default entry values."""
        template_id = uuid4()
        entry = JournalEntry(
            template_id=template_id,
            template_version=1,
            agent="agent",
            project="/test/project"
        )
        assert isinstance(entry.id, type(uuid4()))
        assert isinstance(entry.timestamp, datetime)
        assert entry.field_values == {}


class TestFieldConstraints:
    """Tests for FieldConstraints model."""

    def test_create_constraints(self) -> None:
        """Test creating field constraints."""
        constraints = FieldConstraints(
            max_length=100,
            url_schemes=["https"],
            file_types=[".py", ".js"],
            auto_now=True
        )
        assert constraints.max_length == 100
        assert constraints.url_schemes == ["https"]
        assert constraints.file_types == [".py", ".js"]
        assert constraints.auto_now is True

    def test_default_constraints(self) -> None:
        """Test default constraint values."""
        constraints = FieldConstraints()
        assert constraints.max_length is None
        assert constraints.url_schemes is None
        assert constraints.file_types is None
        assert constraints.auto_now is False
