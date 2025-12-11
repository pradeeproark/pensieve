"""Tests for entry ID resolution (short-form ID support)."""

import os
from pathlib import Path
from uuid import UUID

import pytest
from click.testing import CliRunner
from pensieve.cli import main
from pensieve.cli_helpers import (
    AmbiguousEntryError,
    EntryNotFoundError,
    InvalidEntryIdError,
    resolve_entry_id,
)
from pensieve.database import Database
from pensieve.models import FieldType, JournalEntry, Template, TemplateField


@pytest.fixture
def temp_db_with_entries(tmp_path: Path):
    """Create a temporary database with test entries for resolver tests."""
    db_path = tmp_path / "test_pensieve.db"
    os.environ["PENSIEVE_DB"] = str(db_path)

    db = Database()

    # Create test template
    template = Template(
        name="test_template",
        version=1,
        description="Test template for resolver tests",
        created_by="test_user",
        project=str(tmp_path),
        fields=[
            TemplateField(name="title", type=FieldType.TEXT, required=True, description="Title"),
        ],
    )
    db.create_template(template)

    # Create test entries with known IDs (by creating them and capturing IDs)
    entry1 = JournalEntry(
        template_id=template.id,
        template_version=1,
        agent="test_user",
        project=str(tmp_path),
        field_values={"title": "Entry One"},
        tags=[],
    )
    db.create_entry(entry1, template)

    entry2 = JournalEntry(
        template_id=template.id,
        template_version=1,
        agent="test_user",
        project=str(tmp_path),
        field_values={"title": "Entry Two"},
        tags=[],
    )
    db.create_entry(entry2, template)

    db.close()

    yield {
        "db_path": db_path,
        "tmp_path": tmp_path,
        "entry1_id": str(entry1.id),
        "entry2_id": str(entry2.id),
    }

    # Cleanup
    if "PENSIEVE_DB" in os.environ:
        del os.environ["PENSIEVE_DB"]


class TestResolveEntryId:
    """Tests for resolve_entry_id function."""

    def test_exact_match_returns_entry(self, temp_db_with_entries: dict) -> None:
        """Full UUID should return the entry."""
        db = Database()
        try:
            entry_id = temp_db_with_entries["entry1_id"]
            result = resolve_entry_id(db, entry_id)
            assert result.id == UUID(entry_id)
            assert result.field_values["title"] == "Entry One"
        finally:
            db.close()

    def test_unique_prefix_match_returns_entry(self, temp_db_with_entries: dict) -> None:
        """Short ID that uniquely matches should return the entry."""
        db = Database()
        try:
            full_id = temp_db_with_entries["entry1_id"]
            short_id = full_id[:8]  # First 8 characters

            result = resolve_entry_id(db, short_id)
            assert result.id == UUID(full_id)
        finally:
            db.close()

    def test_ambiguous_prefix_raises_error(self, tmp_path: Path) -> None:
        """Ambiguous prefix should raise AmbiguousEntryError with candidates."""
        # Create database with entries that share a prefix
        db_path = tmp_path / "ambiguous_test.db"
        os.environ["PENSIEVE_DB"] = str(db_path)

        db = Database()
        template = Template(
            name="test_template",
            version=1,
            description="Test",
            created_by="test",
            project=str(tmp_path),
            fields=[
                TemplateField(
                    name="title", type=FieldType.TEXT, required=True, description="Title"
                ),
            ],
        )
        db.create_template(template)

        # Create two entries with UUIDs that share the same 8-char prefix
        # We do this by creating entries then manually updating their IDs in the DB
        entry1 = JournalEntry(
            template_id=template.id,
            template_version=1,
            agent="test",
            project=str(tmp_path),
            field_values={"title": "Entry 1"},
            tags=[],
        )
        entry2 = JournalEntry(
            template_id=template.id,
            template_version=1,
            agent="test",
            project=str(tmp_path),
            field_values={"title": "Entry 2"},
            tags=[],
        )
        db.create_entry(entry1, template)
        db.create_entry(entry2, template)

        # Update both entries to have UUIDs that share the prefix "aaaa"
        # We need to disable foreign key checks temporarily to update the IDs
        id1 = "aaaa0001-0000-0000-0000-000000000001"
        id2 = "aaaa0002-0000-0000-0000-000000000002"
        db.conn.execute("PRAGMA foreign_keys = OFF")
        db.conn.execute("UPDATE journal_entries SET id = ? WHERE id = ?", (id1, str(entry1.id)))
        db.conn.execute(
            "UPDATE entry_field_values SET entry_id = ? WHERE entry_id = ?", (id1, str(entry1.id))
        )
        db.conn.execute("UPDATE journal_entries SET id = ? WHERE id = ?", (id2, str(entry2.id)))
        db.conn.execute(
            "UPDATE entry_field_values SET entry_id = ? WHERE entry_id = ?", (id2, str(entry2.id))
        )
        db.conn.commit()
        db.conn.execute("PRAGMA foreign_keys = ON")

        # Now searching for "aaaa" should return AmbiguousEntryError
        with pytest.raises(AmbiguousEntryError) as exc_info:
            resolve_entry_id(db, "aaaa")

        assert "aaaa" in str(exc_info.value)
        assert len(exc_info.value.candidates) == 2
        assert id1 in exc_info.value.candidates
        assert id2 in exc_info.value.candidates

        db.close()

    def test_no_match_raises_error(self, temp_db_with_entries: dict) -> None:
        """Non-existent ID should raise EntryNotFoundError."""
        db = Database()
        try:
            with pytest.raises(EntryNotFoundError) as exc_info:
                resolve_entry_id(db, "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            assert "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in str(exc_info.value)
        finally:
            db.close()

    def test_short_id_too_short_raises_error(self, temp_db_with_entries: dict) -> None:
        """Short ID less than 4 characters should raise InvalidEntryIdError."""
        db = Database()
        try:
            with pytest.raises(InvalidEntryIdError) as exc_info:
                resolve_entry_id(db, "abc")  # Only 3 chars
            assert "abc" in str(exc_info.value)
            assert "at least 4 characters" in str(exc_info.value).lower()
        finally:
            db.close()

    def test_prefix_length_4_is_minimum(self, temp_db_with_entries: dict) -> None:
        """4-character prefix should be accepted (boundary test)."""
        db = Database()
        try:
            full_id = temp_db_with_entries["entry1_id"]
            short_id = full_id[:4]  # Exactly 4 characters

            # Should not raise InvalidEntryIdError for length
            # (may raise EntryNotFoundError or AmbiguousEntryError depending on data)
            try:
                result = resolve_entry_id(db, short_id)
                # If we get here, it resolved successfully
                assert str(result.id).startswith(short_id)
            except Exception as e:
                # It's OK if it raises Ambiguous or NotFound, just not Invalid
                assert not isinstance(
                    e, InvalidEntryIdError
                ), f"4-char ID should not raise InvalidEntryIdError: {e}"
        finally:
            db.close()

    def test_invalid_hex_characters_raises_error(self, temp_db_with_entries: dict) -> None:
        """Non-hex characters in short ID should raise InvalidEntryIdError."""
        db = Database()
        try:
            with pytest.raises(InvalidEntryIdError) as exc_info:
                resolve_entry_id(db, "ghij1234")  # g, h, i, j are not hex
            assert "ghij1234" in str(exc_info.value)
        finally:
            db.close()


class TestEntryShowShortId:
    """Tests for entry show command with short-form IDs."""

    def test_entry_show_with_short_id(self, temp_db_with_entries: dict) -> None:
        """entry show should work with 8-char short ID."""
        runner = CliRunner()
        full_id = temp_db_with_entries["entry1_id"]
        short_id = full_id[:8]

        result = runner.invoke(main, ["entry", "show", short_id])

        assert result.exit_code == 0
        assert "Entry One" in result.output
        assert full_id in result.output  # Full ID should be displayed

    def test_entry_show_with_full_id(self, temp_db_with_entries: dict) -> None:
        """entry show should still work with full UUID."""
        runner = CliRunner()
        full_id = temp_db_with_entries["entry1_id"]

        result = runner.invoke(main, ["entry", "show", full_id])

        assert result.exit_code == 0
        assert "Entry One" in result.output

    def test_entry_show_short_id_not_found(self, temp_db_with_entries: dict) -> None:
        """entry show with non-existent short ID should show error."""
        runner = CliRunner()

        result = runner.invoke(main, ["entry", "show", "deadbeef"])

        assert result.exit_code == 1
        assert "No entry found matching 'deadbeef'" in result.output

    def test_entry_show_short_id_too_short(self, temp_db_with_entries: dict) -> None:
        """entry show with <4 char ID should show error."""
        runner = CliRunner()

        result = runner.invoke(main, ["entry", "show", "abc"])

        assert result.exit_code == 1
        assert "at least 4 characters" in result.output.lower()


class TestEntryTagShortId:
    """Tests for entry tag command with short-form IDs."""

    def test_entry_tag_add_with_short_id(self, temp_db_with_entries: dict) -> None:
        """entry tag --add should work with short ID."""
        runner = CliRunner()
        full_id = temp_db_with_entries["entry1_id"]
        short_id = full_id[:8]

        result = runner.invoke(main, ["entry", "tag", short_id, "--add", "test-tag"])

        assert result.exit_code == 0
        assert "Added tags: test-tag" in result.output

    def test_entry_tag_short_id_not_found(self, temp_db_with_entries: dict) -> None:
        """entry tag with non-existent short ID should show error."""
        runner = CliRunner()

        result = runner.invoke(main, ["entry", "tag", "deadbeef", "--add", "tag"])

        assert result.exit_code == 1
        assert "No entry found matching 'deadbeef'" in result.output


class TestEntryUpdateStatusShortId:
    """Tests for entry update-status command with short-form IDs."""

    def test_entry_update_status_with_short_id(self, temp_db_with_entries: dict) -> None:
        """entry update-status should work with short ID."""
        runner = CliRunner()
        full_id = temp_db_with_entries["entry1_id"]
        short_id = full_id[:8]

        result = runner.invoke(main, ["entry", "update-status", short_id, "deprecated"])

        assert result.exit_code == 0
        assert "Updated entry" in result.output
        assert "deprecated" in result.output.lower()

    def test_entry_update_status_short_id_not_found(self, temp_db_with_entries: dict) -> None:
        """entry update-status with non-existent short ID should show error."""
        runner = CliRunner()

        result = runner.invoke(main, ["entry", "update-status", "deadbeef", "deprecated"])

        assert result.exit_code == 1
        assert "No entry found matching 'deadbeef'" in result.output


class TestEntryLinkShortId:
    """Tests for entry link command with short-form IDs."""

    def test_entry_link_with_short_ids(self, temp_db_with_entries: dict) -> None:
        """entry link should work with short IDs for both from and to."""
        runner = CliRunner()
        id1 = temp_db_with_entries["entry1_id"]
        id2 = temp_db_with_entries["entry2_id"]
        short_id1 = id1[:8]
        short_id2 = id2[:8]

        result = runner.invoke(
            main, ["entry", "link", short_id1, short_id2, "--type", "relates_to"]
        )

        assert result.exit_code == 0
        assert "Created link" in result.output
        assert "relates_to" in result.output

    def test_entry_link_from_id_not_found(self, temp_db_with_entries: dict) -> None:
        """entry link with non-existent from ID should show error."""
        runner = CliRunner()
        id2 = temp_db_with_entries["entry2_id"]
        short_id2 = id2[:8]

        result = runner.invoke(
            main, ["entry", "link", "deadbeef", short_id2, "--type", "relates_to"]
        )

        assert result.exit_code == 1
        assert "No entry found matching 'deadbeef'" in result.output

    def test_entry_link_to_id_not_found(self, temp_db_with_entries: dict) -> None:
        """entry link with non-existent to ID should show error."""
        runner = CliRunner()
        id1 = temp_db_with_entries["entry1_id"]
        short_id1 = id1[:8]

        result = runner.invoke(
            main, ["entry", "link", short_id1, "deadbeef", "--type", "relates_to"]
        )

        assert result.exit_code == 1
        assert "No entry found matching 'deadbeef'" in result.output
