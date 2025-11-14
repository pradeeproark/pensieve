"""Tests for CLI commands."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from pensieve.cli import main
from pensieve.database import Database
from pensieve.models import FieldType, Template, TemplateField


@pytest.fixture
def temp_db(tmp_path: Path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_pensieve.db"
    os.environ["PENSIEVE_DB"] = str(db_path)

    # Create database and add a test template
    db = Database()
    template = Template(
        name="test_template",
        version=1,
        description="Test template for CLI tests",
        created_by="test_user",
        project=str(tmp_path),
        fields=[
            TemplateField(
                name="title", type=FieldType.TEXT, required=True, description="Title of the entry"
            ),
            TemplateField(
                name="description",
                type=FieldType.TEXT,
                required=False,
                description="Optional description",
            ),
        ],
    )
    db.create_template(template)
    db.close()

    yield db_path

    # Cleanup
    if "PENSIEVE_DB" in os.environ:
        del os.environ["PENSIEVE_DB"]


class TestEntryCreate:
    """Tests for entry create command."""

    def test_create_with_template_option_success(self, temp_db: Path) -> None:
        """Test entry create with --template option works correctly."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["entry", "create", "--template", "test_template", "--field", "title=Test Entry"]
        )

        assert result.exit_code == 0
        assert "✓ Created entry:" in result.output
        assert "Template: test_template" in result.output

    def test_create_without_template_fails(self, temp_db: Path) -> None:
        """Test that omitting --template fails with clear error."""
        runner = CliRunner()
        result = runner.invoke(main, ["entry", "create", "--field", "title=Test Entry"])

        assert result.exit_code != 0
        assert "Error" in result.output or "Missing option" in result.output

    def test_create_with_template_and_fields(self, temp_db: Path) -> None:
        """Test creating entry with multiple fields."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=Test Title",
                "--field",
                "description=Test Description",
            ],
        )

        assert result.exit_code == 0
        assert "✓ Created entry:" in result.output

    def test_create_with_nonexistent_template_fails(self, temp_db: Path) -> None:
        """Test that using nonexistent template fails with helpful error."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["entry", "create", "--template", "nonexistent_template", "--field", "title=Test"]
        )

        assert result.exit_code != 0
        assert "Error: Template 'nonexistent_template' not found" in result.output
        assert "Available templates:" in result.output
        assert "test_template" in result.output

    def test_create_with_missing_required_field_fails(self, temp_db: Path) -> None:
        """Test that missing required fields fails with clear error."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "description=Only optional field provided",
            ],
        )

        assert result.exit_code != 0
        assert "Error: Missing required fields: title" in result.output

    def test_create_with_tag_option_fails(self, temp_db: Path) -> None:
        """Test that --tag option during creation fails with helpful workflow guidance."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=Test Entry",
                "--tag",
                "test",
            ],
        )

        assert result.exit_code != 0
        assert "❌ Error: Cannot use --tag during entry creation" in result.output
        assert "📋 Proper workflow for adding tags:" in result.output
        assert "1. Check existing tags:  pensieve tag list" in result.output
        assert "2. Create entry:" in result.output
        assert "3. Add tags after:       pensieve entry tag <entry-id> --add <tag>" in result.output
        assert "prevents tag proliferation" in result.output
        assert "If no suitable tag exists, you can create a new one" in result.output

    def test_create_with_multiple_tags_fails(self, temp_db: Path) -> None:
        """Test that multiple --tag options during creation fails."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=Test Entry",
                "--tag",
                "test",
                "--tag",
                "cli",
            ],
        )

        assert result.exit_code != 0
        assert "❌ Error: Cannot use --tag during entry creation" in result.output
