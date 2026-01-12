"""Tests for CLI commands."""

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner
from pensieve.cli import main
from pensieve.database import Database
from pensieve.models import FieldType, JournalEntry, Template, TemplateField


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

    def test_create_with_tag_option_works_on_cold_start(self, temp_db: Path) -> None:
        """Test that --tag option works on cold start (no existing tags)."""
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

        assert result.exit_code == 0
        assert "Created entry:" in result.output
        assert "Tags: test" in result.output

    def test_create_with_multiple_tags_works_on_cold_start(self, temp_db: Path) -> None:
        """Test that multiple --tag options work on cold start."""
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

        assert result.exit_code == 0
        assert "Created entry:" in result.output
        assert "Tags: cli, test" in result.output  # sorted alphabetically

    def test_create_with_unknown_tag_fails(self, temp_db: Path) -> None:
        """Test that using unknown tag fails when tags exist."""
        runner = CliRunner()

        # First create an entry with a tag to establish existing tags
        runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=First Entry",
                "--tag",
                "existing-tag",
            ],
        )

        # Now try to use a non-existent tag
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=Second Entry",
                "--tag",
                "unknown-tag",
            ],
        )

        assert result.exit_code != 0
        assert "Tag 'unknown-tag' not found" in result.output
        assert "Available tags" in result.output
        assert "existing-tag" in result.output
        assert "--new-tag" in result.output

    def test_create_with_new_tag_option(self, temp_db: Path) -> None:
        """Test that --new-tag creates new tags."""
        runner = CliRunner()

        # Create first entry with existing tag
        runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=First Entry",
                "--tag",
                "existing-tag",
            ],
        )

        # Create second entry using existing tag and creating new one
        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "test_template",
                "--field",
                "title=Second Entry",
                "--tag",
                "existing-tag",
                "--new-tag",
                "new-tag",
            ],
        )

        assert result.exit_code == 0
        assert "Created entry:" in result.output
        assert "Tags: existing-tag, new-tag" in result.output


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


@pytest.fixture
def temp_db_with_entries(tmp_path: Path):
    """Create a temporary database with test entries for journal tests."""
    db_path = tmp_path / "test_pensieve.db"
    os.environ["PENSIEVE_DB"] = str(db_path)

    db = Database()

    # Create test template
    template = Template(
        name="test_template",
        version=1,
        description="Test template for journal tests",
        created_by="test_user",
        project=str(tmp_path),
        fields=[
            TemplateField(
                name="summary", type=FieldType.TEXT, required=True, description="Summary"
            ),
        ],
    )
    db.create_template(template)

    # Create entries at different times
    now = datetime.now()
    project_path = str(tmp_path)

    # Register tags in project_tags (required for get_tag_statistics)
    for tag_name in ["recent", "test", "older", "old"]:
        db.create_tag(project_path, tag_name, "test_user")

    # Entry from today
    entry1 = JournalEntry(
        template_id=template.id,
        template_version=1,
        agent="test_user",
        project=project_path,
        field_values={"summary": "Recent entry from today"},
        tags=["recent", "test"],
    )
    db.create_entry(entry1, template)

    # Entry from 5 days ago
    entry2 = JournalEntry(
        template_id=template.id,
        template_version=1,
        agent="test_user",
        project=project_path,
        field_values={"summary": "Entry from 5 days ago"},
        tags=["older", "test"],
    )
    db.create_entry(entry2, template)
    # Manually update timestamp to 5 days ago
    db.conn.execute(
        "UPDATE journal_entries SET timestamp = ? WHERE id = ?",
        ((now - timedelta(days=5)).isoformat(), str(entry2.id)),
    )

    # Entry from 20 days ago
    entry3 = JournalEntry(
        template_id=template.id,
        template_version=1,
        agent="test_user",
        project=project_path,
        field_values={"summary": "Old entry from 20 days ago"},
        tags=["old"],
    )
    db.create_entry(entry3, template)
    # Manually update timestamp to 20 days ago
    db.conn.execute(
        "UPDATE journal_entries SET timestamp = ? WHERE id = ?",
        ((now - timedelta(days=20)).isoformat(), str(entry3.id)),
    )

    db.conn.commit()
    db.close()

    yield tmp_path

    # Cleanup
    if "PENSIEVE_DB" in os.environ:
        del os.environ["PENSIEVE_DB"]


class TestJournal:
    """Tests for journal command."""

    def test_journal_shows_entries_in_date_range(self, temp_db_with_entries: Path) -> None:
        """Journal should show entries within the default 14-day range."""
        runner = CliRunner()
        # Use --all-projects since test entries have different project path
        result = runner.invoke(main, ["journal", "--all-projects"])

        assert result.exit_code == 0
        assert "Project Journal:" in result.output
        assert "Recent entry from today" in result.output
        assert "Entry from 5 days ago" in result.output
        # Entry from 20 days ago should NOT appear (outside 14-day default)
        assert "Old entry from 20 days ago" not in result.output

    def test_journal_days_flag_expands_range(self, temp_db_with_entries: Path) -> None:
        """--days flag should include older entries."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--days", "30", "--all-projects"])

        assert result.exit_code == 0
        assert "Last 30 days" in result.output
        # Now should include the 20-day-old entry
        assert "Old entry from 20 days ago" in result.output

    def test_journal_days_flag_narrows_range(self, temp_db_with_entries: Path) -> None:
        """--days 3 should exclude 5-day-old entry."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--days", "3", "--all-projects"])

        assert result.exit_code == 0
        assert "Last 3 days" in result.output
        assert "Recent entry from today" in result.output
        # 5-day-old entry should NOT appear
        assert "Entry from 5 days ago" not in result.output

    def test_journal_invalid_days_fails(self, temp_db_with_entries: Path) -> None:
        """--days 0 or negative should fail with helpful error."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--days", "0"])

        assert result.exit_code == 1
        assert "must be a positive integer" in result.output

    def test_journal_empty_result_suggests_longer_range(self, temp_db_with_entries: Path) -> None:
        """When no entries found, should suggest expanding range."""
        runner = CliRunner()
        # Use a fresh empty database
        os.environ["PENSIEVE_DB"] = str(temp_db_with_entries / "empty.db")
        db = Database()
        db.close()

        result = runner.invoke(main, ["journal", "--days", "1", "--all-projects"])

        assert result.exit_code == 0
        assert "No entries in the last 1 days" in result.output
        assert "pensieve journal --days 30" in result.output

        # Restore original DB
        os.environ["PENSIEVE_DB"] = str(temp_db_with_entries / "test_pensieve.db")

    def test_journal_shows_stats_and_focus_areas(self, temp_db_with_entries: Path) -> None:
        """Journal should show aggregate statistics and focus areas."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--all-projects"])

        assert result.exit_code == 0
        assert "entries" in result.output
        assert "templates" in result.output
        assert "unique tags" in result.output
        # Should show focus areas with tag counts
        assert "Focus areas:" in result.output

    def test_journal_shows_contextual_hints(self, temp_db_with_entries: Path) -> None:
        """Journal should show actionable next steps with real values."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--all-projects"])

        assert result.exit_code == 0
        assert "Next steps:" in result.output
        # Should have pensieve entry show with an actual ID
        assert "pensieve entry show" in result.output
        # Should suggest tag search with actual tag
        assert "pensieve entry search --tag" in result.output
        # Should suggest template search
        assert "pensieve entry search --template" in result.output


class TestJournalLandscape:
    """Tests for new landscape journal view."""

    def test_journal_landscape_shows_header(self, temp_db_with_entries: Path) -> None:
        """Landscape journal shows header with totals."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--landscape", "--all-projects"])

        assert result.exit_code == 0
        assert "PENSIEVE LANDSCAPE" in result.output

    def test_journal_landscape_shows_legend(self, temp_db_with_entries: Path) -> None:
        """Landscape journal shows heatmap legend."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--landscape", "--all-projects"])

        assert result.exit_code == 0
        # Should have intensity legend
        assert "HIGH" in result.output or "██" in result.output
        # Should have recency indicators
        assert "hot" in result.output or "●" in result.output

    def test_journal_landscape_shows_zoom_guidance(self, temp_db_with_entries: Path) -> None:
        """Landscape journal shows zoom guidance."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--landscape", "--all-projects"])

        assert result.exit_code == 0
        # Should show zoom guidance
        assert "ZOOM" in result.output or "journal --tag" in result.output

    def test_journal_landscape_weeks_flag(self, temp_db_with_entries: Path) -> None:
        """--weeks flag controls landscape lookback period."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--landscape", "--weeks", "4", "--all-projects"])

        assert result.exit_code == 0
        # Should render without errors with fewer weeks
        assert "PENSIEVE" in result.output

    def test_journal_landscape_tag_zoom(self, temp_db_with_entries: Path) -> None:
        """--tag flag shows cluster zoom view."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["journal", "--landscape", "--tag", "recent", "--all-projects"]
        )

        assert result.exit_code == 0
        # Should show cluster header
        assert "CLUSTER" in result.output
        # Should show recent entries
        assert "RECENT ENTRIES" in result.output or "ENTRIES:" in result.output

    def test_journal_landscape_empty_project(self, temp_db: Path) -> None:
        """Landscape handles empty project gracefully."""
        runner = CliRunner()
        result = runner.invoke(main, ["journal", "--landscape", "--all-projects"])

        assert result.exit_code == 0
        # Should show empty state without crashing
        assert "PENSIEVE" in result.output or "0e" in result.output
