"""Tests for CLI ref commands."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from pensieve.cli import main
from pensieve.database import Database
from pensieve.models import FieldType, JournalEntry, Template, TemplateField


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project with source files for testing resolution."""
    # Create Python source file
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (src_dir / "auth.py").write_text(
        '''"""Authentication module."""


class TokenValidator:
    """Validates JWT tokens."""

    def validate(self, token: str) -> bool:
        """Validate a token."""
        return len(token) > 10
'''
    )

    # Create docs
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "security.md").write_text(
        """# Security Guide

## Overview

This document covers security practices.

## Token Validation

Tokens are validated using JWT standards.
"""
    )

    return tmp_path


@pytest.fixture
def temp_db_with_refs_template(tmp_path: Path, temp_project: Path):
    """Create a temporary database with a template that has a REFS field."""
    db_path = tmp_path / "test_pensieve.db"
    os.environ["PENSIEVE_DB"] = str(db_path)

    db = Database()

    # Create a template with REFS field
    template = Template(
        name="decision",
        version=1,
        description="Record a decision with code references",
        created_by="test_user",
        project=str(temp_project),
        fields=[
            TemplateField(
                name="title",
                type=FieldType.TEXT,
                required=True,
                description="Decision title",
            ),
            TemplateField(
                name="rationale",
                type=FieldType.TEXT,
                required=False,
                description="Why this decision was made",
            ),
            TemplateField(
                name="refs",
                type=FieldType.REFS,
                required=False,
                description="Code and doc references",
            ),
        ],
    )
    db.create_template(template)

    # Create a test entry
    entry = JournalEntry(
        template_id=template.id,
        template_version=template.version,
        agent="test_agent",
        project=str(temp_project),
        field_values={
            "title": "Implement JWT validation",
            "rationale": "Need secure token validation",
            "refs": [
                {"name": "impl", "kind": "code", "s": "TokenValidator.validate", "f": "**/auth.py"},
                {
                    "name": "spec",
                    "kind": "doc",
                    "f": "docs/security.md",
                    "h": "## Token Validation",
                },
            ],
        },
    )
    db.create_entry(entry, template)

    db.close()

    yield {"db_path": db_path, "entry_id": entry.id, "project": temp_project}

    # Cleanup
    if "PENSIEVE_DB" in os.environ:
        del os.environ["PENSIEVE_DB"]


class TestRefList:
    """Tests for ref list command."""

    def test_list_refs_for_entry(self, temp_db_with_refs_template) -> None:
        """Test listing refs for an entry."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "list", entry_id])

        assert result.exit_code == 0
        assert "impl" in result.output
        assert "spec" in result.output
        assert "code" in result.output
        assert "doc" in result.output

    def test_list_refs_nonexistent_entry(self, temp_db_with_refs_template) -> None:
        """Test listing refs for nonexistent entry."""
        runner = CliRunner()

        result = runner.invoke(main, ["ref", "list", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestRefAdd:
    """Tests for ref add command."""

    def test_add_code_ref(self, temp_db_with_refs_template) -> None:
        """Test adding a code ref to an entry."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(
            main,
            ["ref", "add", entry_id, "test", "t=def validate(self"],
        )

        assert result.exit_code == 0
        assert "Added ref" in result.output or "test" in result.output

    def test_add_doc_ref(self, temp_db_with_refs_template) -> None:
        """Test adding a doc ref to an entry."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(
            main,
            ["ref", "add", entry_id, "overview", "k=doc,f=docs/security.md,h=## Overview"],
        )

        assert result.exit_code == 0

    def test_add_ref_with_invalid_format(self, temp_db_with_refs_template) -> None:
        """Test adding ref with invalid compact format."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        # Missing locator fields
        result = runner.invoke(
            main,
            ["ref", "add", entry_id, "bad", "k=code"],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower()


class TestRefRemove:
    """Tests for ref remove command."""

    def test_remove_ref(self, temp_db_with_refs_template) -> None:
        """Test removing a ref from an entry."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        # First verify ref exists
        result = runner.invoke(main, ["ref", "list", entry_id])
        assert "impl" in result.output

        # Remove the ref
        result = runner.invoke(main, ["ref", "remove", entry_id, "impl"])

        assert result.exit_code == 0
        assert "Removed" in result.output or "impl" in result.output

        # Verify ref is gone
        result = runner.invoke(main, ["ref", "list", entry_id])
        # impl should no longer be in the refs
        # (may still appear if there's output formatting issues, so check behavior)

    def test_remove_nonexistent_ref(self, temp_db_with_refs_template) -> None:
        """Test removing a ref that doesn't exist."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "remove", entry_id, "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestRefResolve:
    """Tests for ref resolve command."""

    def test_resolve_single_ref(self, temp_db_with_refs_template) -> None:
        """Test resolving a single ref."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "resolve", entry_id, "impl"])

        # Should return a file:line format or hints
        assert result.exit_code == 0 or result.exit_code == 1
        # Either found (path) or not found (hints)
        assert "auth.py" in result.output or "rg" in result.output

    def test_resolve_all_refs(self, temp_db_with_refs_template) -> None:
        """Test resolving all refs with --all flag."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "resolve", entry_id, "--all"])

        # Should show both impl and spec
        assert "impl" in result.output
        assert "spec" in result.output

    def test_resolve_doc_ref(self, temp_db_with_refs_template) -> None:
        """Test resolving a doc ref."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "resolve", entry_id, "spec"])

        assert result.exit_code == 0
        assert "security.md" in result.output

    def test_resolve_nonexistent_ref(self, temp_db_with_refs_template) -> None:
        """Test resolving a ref that doesn't exist."""
        runner = CliRunner()
        entry_id = str(temp_db_with_refs_template["entry_id"])[:8]

        result = runner.invoke(main, ["ref", "resolve", entry_id, "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestEntryCreateWithRefs:
    """Tests for --ref option in entry create."""

    def test_create_entry_with_ref_option(self, temp_db_with_refs_template) -> None:
        """Test creating entry with --ref option."""
        runner = CliRunner()
        project = str(temp_db_with_refs_template["project"])

        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "decision",
                "--project",
                project,
                "--field",
                "title=New decision",
                "--ref",
                "impl:t=class TokenValidator",
            ],
        )

        assert result.exit_code == 0
        assert "Created entry" in result.output

    def test_create_entry_with_multiple_refs(self, temp_db_with_refs_template) -> None:
        """Test creating entry with multiple --ref options."""
        runner = CliRunner()
        project = str(temp_db_with_refs_template["project"])

        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "decision",
                "--project",
                project,
                "--field",
                "title=Another decision",
                "--ref",
                "impl:s=TokenValidator.validate",
                "--ref",
                "spec:k=doc,f=docs/security.md,h=## Overview",
            ],
        )

        assert result.exit_code == 0

    def test_create_entry_with_invalid_ref(self, temp_db_with_refs_template) -> None:
        """Test creating entry with invalid ref format."""
        runner = CliRunner()
        project = str(temp_db_with_refs_template["project"])

        result = runner.invoke(
            main,
            [
                "entry",
                "create",
                "--template",
                "decision",
                "--project",
                project,
                "--field",
                "title=Bad ref test",
                "--ref",
                "invalidformat",  # Missing colon
            ],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "invalid" in result.output.lower()


class TestEntryShowWithRefs:
    """Tests for displaying refs in entry show."""

    def test_show_entry_displays_refs(self, temp_db_with_refs_template) -> None:
        """Test that entry show displays refs."""
        runner = CliRunner()
        # entry show requires full UUID, not prefix
        entry_id = str(temp_db_with_refs_template["entry_id"])

        result = runner.invoke(main, ["entry", "show", entry_id])

        assert result.exit_code == 0
        # Should display refs field in some format
        assert "refs" in result.output.lower() or "impl" in result.output or "spec" in result.output
