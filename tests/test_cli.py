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


class TestEntrySearch:
    """Tests for entry search command."""

    def test_search_rejects_positional_args(self, temp_db: Path) -> None:
        """Positional arguments should show helpful error."""
        runner = CliRunner()
        result = runner.invoke(main, ["entry", "search", "oauth bug"])

        assert result.exit_code == 1
        assert "not a valid search syntax" in result.output
        assert "--tag" in result.output
        assert "--field" in result.output

    def test_search_rejects_multiple_positional_args(self, temp_db: Path) -> None:
        """Multiple positional args should be joined in error message."""
        runner = CliRunner()
        result = runner.invoke(main, ["entry", "search", "oauth", "token", "issue"])

        assert result.exit_code == 1
        assert "oauth token issue" in result.output
        assert "not a valid search syntax" in result.output

    def test_search_works_normally_with_flags(self, temp_db: Path) -> None:
        """Normal flag-based search should still work."""
        runner = CliRunner()
        result = runner.invoke(main, ["entry", "search", "--all-projects"])

        assert result.exit_code == 0
        # Either finds entries or reports none found
        assert "Found" in result.output or "No entries found" in result.output

    def test_search_hint_uses_placeholder_not_example_field(self, temp_db: Path) -> None:
        """Search hint should use placeholder <field_name> not a specific field like 'summary'."""
        runner = CliRunner()
        result = runner.invoke(main, ["entry", "search", "free form text"])

        assert result.exit_code == 1
        assert "<field_name>" in result.output
        assert "--field summary" not in result.output

    def test_search_warns_for_nonexistent_field(self, temp_db: Path) -> None:
        """Should warn when searching for a field that doesn't exist in any template."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "entry",
                "search",
                "--field",
                "nonexistent_field_xyz",
                "--value",
                "test",
                "--substring",
            ],
        )

        assert result.exit_code == 0
        # Should show warning about non-existent field
        assert "No templates have a field named 'nonexistent_field_xyz'" in result.output
        # Should suggest available fields
        assert "Available fields:" in result.output or "title" in result.output

    def test_search_shows_available_fields_on_no_results(self, temp_db: Path) -> None:
        """Should show available fields when field search returns 0 results."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["entry", "search", "--field", "title", "--value", "nomatchxyz", "--substring"],
        )

        assert result.exit_code == 0
        assert "No entries found" in result.output
        # Should show available fields since we searched by field
        assert "Available fields:" in result.output
        # Should suggest tag search as alternative
        assert "tag-based search" in result.output.lower() or "--tag" in result.output
