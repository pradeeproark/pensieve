"""Tests for database operations."""

import tempfile
from pathlib import Path

import pytest

from pensieve.database import Database, DatabaseError
from pensieve.models import FieldConstraints, FieldType, JournalEntry, Template, TemplateField
from pensieve.validators import ValidationError


@pytest.fixture
def temp_db() -> Database:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    yield db
    db.close()

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_template() -> Template:
    """Create a sample template for testing."""
    return Template(
        name="test_template",
        description="Test template",
        created_by="test_agent",
        project="/test/project",
        fields=[
            TemplateField(name="title", type=FieldType.TEXT, required=True),
            TemplateField(name="completed", type=FieldType.BOOLEAN, required=False),
            TemplateField(name="url", type=FieldType.URL, required=False),
        ]
    )


class TestTemplateOperations:
    """Tests for template database operations."""

    def test_create_template(self, temp_db: Database, sample_template: Template) -> None:
        """Test creating a template."""
        temp_db.create_template(sample_template)

        # Verify it was created
        retrieved = temp_db.get_template_by_name(sample_template.name)
        assert retrieved is not None
        assert retrieved.name == sample_template.name
        assert retrieved.description == sample_template.description
        assert len(retrieved.fields) == len(sample_template.fields)

    def test_create_duplicate_template(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Test creating a template with duplicate name fails."""
        temp_db.create_template(sample_template)

        # Try to create another with same name
        duplicate = Template(
            name=sample_template.name,
            description="Different",
            created_by="agent",
            project="/test/project",
            fields=[TemplateField(name="field", type=FieldType.TEXT)]
        )

        with pytest.raises(DatabaseError, match="already exists"):
            temp_db.create_template(duplicate)

    def test_get_template_by_name(self, temp_db: Database, sample_template: Template) -> None:
        """Test retrieving template by name."""
        temp_db.create_template(sample_template)

        retrieved = temp_db.get_template_by_name(sample_template.name)
        assert retrieved is not None
        assert retrieved.id == sample_template.id

    def test_get_nonexistent_template(self, temp_db: Database) -> None:
        """Test getting a template that doesn't exist."""
        result = temp_db.get_template_by_name("nonexistent")
        assert result is None

    def test_list_templates(self, temp_db: Database) -> None:
        """Test listing all templates."""
        # Create multiple templates
        for i in range(3):
            template = Template(
                name=f"template_{i}",
                description=f"Template {i}",
                created_by="agent",
                project="/test/project",
                fields=[TemplateField(name="field", type=FieldType.TEXT)]
            )
            temp_db.create_template(template)

        templates = temp_db.list_templates()
        assert len(templates) == 3
        assert all(t.name.startswith("template_") for t in templates)

    def test_template_with_all_field_types(self, temp_db: Database) -> None:
        """Test template with all supported field types."""
        template = Template(
            name="all_types",
            description="Template with all field types",
            created_by="agent",
            project="/test/project",
            fields=[
                TemplateField(name="bool_field", type=FieldType.BOOLEAN),
                TemplateField(name="text_field", type=FieldType.TEXT),
                TemplateField(name="url_field", type=FieldType.URL),
                TemplateField(name="timestamp_field", type=FieldType.TIMESTAMP),
                TemplateField(name="file_field", type=FieldType.FILE_REFERENCE),
            ]
        )

        temp_db.create_template(template)
        retrieved = temp_db.get_template_by_name("all_types")

        assert retrieved is not None
        assert len(retrieved.fields) == 5

        # Check each field type
        field_types = {f.name: f.type for f in retrieved.fields}
        assert field_types["bool_field"] == FieldType.BOOLEAN
        assert field_types["text_field"] == FieldType.TEXT
        assert field_types["url_field"] == FieldType.URL
        assert field_types["timestamp_field"] == FieldType.TIMESTAMP
        assert field_types["file_field"] == FieldType.FILE_REFERENCE


class TestEntryOperations:
    """Tests for journal entry database operations."""

    def test_create_entry(self, temp_db: Database, sample_template: Template) -> None:
        """Test creating a journal entry."""
        temp_db.create_template(sample_template)

        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={
                "title": "Test Entry",
                "completed": True,
                "url": "https://example.com"
            }
        )

        temp_db.create_entry(entry, sample_template)

        # Verify it was created
        retrieved = temp_db.get_entry_by_id(entry.id)
        assert retrieved is not None
        assert retrieved.agent == entry.agent
        assert retrieved.field_values["title"] == "Test Entry"
        assert retrieved.field_values["completed"] is True
        assert retrieved.field_values["url"] == "https://example.com"

    def test_create_entry_missing_required_field(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Test creating entry without required field fails."""
        temp_db.create_template(sample_template)

        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="agent",
            project="/test/project",
            field_values={"completed": True}  # Missing required "title"
        )

        with pytest.raises(ValidationError, match="Required field"):
            temp_db.create_entry(entry, sample_template)

    def test_create_entry_with_extra_field(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Test creating entry with field not in template fails."""
        temp_db.create_template(sample_template)

        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="agent",
            project="/test/project",
            field_values={
                "title": "Test",
                "unknown_field": "value"  # Not in template
            }
        )

        with pytest.raises(ValidationError, match="Unknown field"):
            temp_db.create_entry(entry, sample_template)

    def test_list_entries(self, temp_db: Database, sample_template: Template) -> None:
        """Test listing journal entries."""
        temp_db.create_template(sample_template)

        # Create multiple entries
        for i in range(5):
            entry = JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent=f"agent_{i}",
                project="/test/project",
                field_values={"title": f"Entry {i}"}
            )
            temp_db.create_entry(entry, sample_template)

        entries = temp_db.list_entries()
        assert len(entries) == 5

    def test_list_entries_with_limit(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Test listing entries with limit."""
        temp_db.create_template(sample_template)

        # Create 10 entries
        for i in range(10):
            entry = JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="agent",
                project="/test/project",
                field_values={"title": f"Entry {i}"}
            )
            temp_db.create_entry(entry, sample_template)

        entries = temp_db.list_entries(limit=5)
        assert len(entries) == 5

    def test_entry_with_all_field_types(self, temp_db: Database) -> None:
        """Test entry with all field types."""
        template = Template(
            name="all_types",
            description="All types",
            created_by="agent",
            project="/test/project",
            fields=[
                TemplateField(name="bool_field", type=FieldType.BOOLEAN, required=True),
                TemplateField(name="text_field", type=FieldType.TEXT, required=True),
                TemplateField(name="url_field", type=FieldType.URL, required=True),
                TemplateField(name="timestamp_field", type=FieldType.TIMESTAMP, required=True),
                TemplateField(name="file_field", type=FieldType.FILE_REFERENCE, required=True),
            ]
        )

        temp_db.create_template(template)

        entry = JournalEntry(
            template_id=template.id,
            template_version=template.version,
            agent="agent",
            project="/test/project",
            field_values={
                "bool_field": True,
                "text_field": "Test text",
                "url_field": "https://example.com",
                "timestamp_field": "2024-01-15T10:30:00Z",
                "file_field": "/path/to/file.py"
            }
        )

        temp_db.create_entry(entry, template)
        retrieved = temp_db.get_entry_by_id(entry.id)

        assert retrieved is not None
        assert retrieved.field_values["bool_field"] is True
        assert retrieved.field_values["text_field"] == "Test text"
        assert retrieved.field_values["url_field"] == "https://example.com"
        assert "2024-01-15" in retrieved.field_values["timestamp_field"]
        assert retrieved.field_values["file_field"] == "/path/to/file.py"
