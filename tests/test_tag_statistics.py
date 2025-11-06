"""Tests for tag statistics functionality."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from pensieve.cli import main
from pensieve.database import Database
from pensieve.models import FieldType, JournalEntry, Template, TemplateField


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
def sample_template(temp_db: Database) -> Template:
    """Create and persist a sample template for testing."""
    template = Template(
        name="test_template",
        description="Test template",
        created_by="test_agent",
        project="/test/project",
        fields=[
            TemplateField(name="title", type=FieldType.TEXT, required=True),
        ]
    )
    temp_db.create_template(template)
    return template


class TestGetTagStatistics:
    """Tests for get_tag_statistics database method."""

    def test_empty_database(self, temp_db: Database) -> None:
        """Returns empty list when no entries exist."""
        result = temp_db.get_tag_statistics()
        assert result == []

    def test_entries_without_tags(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Returns empty list when entries have no tags."""
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Test entry"},
            tags=[]
        )
        temp_db.create_entry(entry, sample_template)

        result = temp_db.get_tag_statistics()
        assert result == []

    def test_single_project_tags(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Tags counted correctly for single project."""
        # Create entries with various tags
        entries = [
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 1"},
                tags=["authentication", "security"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 2"},
                tags=["authentication", "bug-fix"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 3"},
                tags=["security"]
            ),
        ]

        for entry in entries:
            temp_db.create_entry(entry, sample_template)

        result = temp_db.get_tag_statistics(project="/test/project")

        # Expected: authentication=2, security=2, bug-fix=1
        # Sorted by count desc, then alphabetically
        assert result == [
            ("authentication", 2),
            ("security", 2),
            ("bug-fix", 1),
        ]

    def test_multiple_projects(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Tags aggregated correctly across multiple projects."""
        # Create entries in different projects
        entries = [
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/project/a",
                field_values={"title": "Entry 1"},
                tags=["deployment"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/project/b",
                field_values={"title": "Entry 2"},
                tags=["deployment"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/project/a",
                field_values={"title": "Entry 3"},
                tags=["testing"]
            ),
        ]

        for entry in entries:
            temp_db.create_entry(entry, sample_template)

        # Query all projects
        result = temp_db.get_tag_statistics(project=None)
        assert result == [
            ("deployment", 2),
            ("testing", 1),
        ]

        # Query specific project
        result_a = temp_db.get_tag_statistics(project="/project/a")
        assert result_a == [
            ("deployment", 1),
            ("testing", 1),
        ]

        result_b = temp_db.get_tag_statistics(project="/project/b")
        assert result_b == [("deployment", 1)]

    def test_sorting_by_count_then_alphabetically(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Tags sorted by count descending, then alphabetically."""
        entries = [
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 1"},
                tags=["zebra", "alpha", "beta"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 2"},
                tags=["zebra", "alpha"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 3"},
                tags=["zebra"]
            ),
        ]

        for entry in entries:
            temp_db.create_entry(entry, sample_template)

        result = temp_db.get_tag_statistics(project="/test/project")

        # zebra=3, alpha=2, beta=1
        # When counts tie (alpha=2, beta=1 don't tie), alphabetical order
        assert result == [
            ("zebra", 3),
            ("alpha", 2),
            ("beta", 1),
        ]

    def test_multiple_tags_per_entry(
        self,
        temp_db: Database,
        sample_template: Template
    ) -> None:
        """Each tag in an entry is counted once."""
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Test entry"},
            tags=["auth", "security", "production"]
        )
        temp_db.create_entry(entry, sample_template)

        result = temp_db.get_tag_statistics(project="/test/project")

        # Each tag should appear exactly once with count=1
        assert len(result) == 3
        assert all(count == 1 for _, count in result)
        assert set(tag for tag, _ in result) == {"auth", "security", "production"}

    def test_nonexistent_project(self, temp_db: Database) -> None:
        """Returns empty list for project with no entries."""
        result = temp_db.get_tag_statistics(project="/nonexistent/project")
        assert result == []


class TestTagListCLI:
    """Tests for 'pensieve tag list' CLI command."""

    def test_tag_list_empty_database(self, temp_db: Database, monkeypatch) -> None:
        """Friendly message when no tags exist."""
        monkeypatch.setenv("PENSIEVE_DB", str(temp_db.db_path))
        runner = CliRunner()
        result = runner.invoke(main, ["tag", "list"])

        assert result.exit_code == 0
        assert "No tags found." in result.output

    def test_tag_list_formatting(
        self,
        temp_db: Database,
        sample_template: Template,
        monkeypatch
    ) -> None:
        """Output properly aligned and pluralized."""
        monkeypatch.setenv("PENSIEVE_DB", str(temp_db.db_path))

        # Create entries with tags
        entries = [
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 1"},
                tags=["authentication"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/test/project",
                field_values={"title": "Entry 2"},
                tags=["authentication", "bug"]
            ),
        ]

        for entry in entries:
            temp_db.create_entry(entry, sample_template)

        runner = CliRunner()
        result = runner.invoke(main, ["tag", "list", "--project", "/test/project"])

        assert result.exit_code == 0
        # Check pluralization
        assert "2 entries" in result.output  # authentication appears twice
        assert "1 entry" in result.output    # bug appears once
        # Check tags are displayed
        assert "authentication" in result.output
        assert "bug" in result.output

    def test_tag_list_current_project_vs_all_projects(
        self,
        temp_db: Database,
        sample_template: Template,
        monkeypatch
    ) -> None:
        """Tag list filters by project correctly."""
        monkeypatch.setenv("PENSIEVE_DB", str(temp_db.db_path))

        # Create entries in different projects
        entries = [
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/project/a",
                field_values={"title": "Entry 1"},
                tags=["tag-a"]
            ),
            JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project="/project/b",
                field_values={"title": "Entry 2"},
                tags=["tag-b"]
            ),
        ]

        for entry in entries:
            temp_db.create_entry(entry, sample_template)

        runner = CliRunner()

        # Test specific project
        result_a = runner.invoke(main, ["tag", "list", "--project", "/project/a"])
        assert result_a.exit_code == 0
        assert "tag-a" in result_a.output
        assert "tag-b" not in result_a.output

        # Test all projects
        result_all = runner.invoke(main, ["tag", "list", "--all-projects"])
        assert result_all.exit_code == 0
        assert "Tags across all projects:" in result_all.output
        assert "tag-a" in result_all.output
        assert "tag-b" in result_all.output

    def test_tag_list_path_normalization(
        self,
        temp_db: Database,
        sample_template: Template,
        monkeypatch
    ) -> None:
        """Tag list normalizes project paths to match storage format."""
        monkeypatch.setenv("PENSIEVE_DB", str(temp_db.db_path))

        # Note: Database stores paths relative to home (e.g., "Documents/Projects/...")
        # but CLI might receive absolute paths from auto-detection

        # Create entry with normalized path (as database stores it)
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="Documents/Projects/test",  # Normalized format
            field_values={"title": "Entry 1"},
            tags=["test-tag"]
        )
        temp_db.create_entry(entry, sample_template)

        runner = CliRunner()

        # Query with normalized path should work
        result = runner.invoke(main, ["tag", "list", "--project", "Documents/Projects/test"])
        assert result.exit_code == 0
        assert "test-tag" in result.output
