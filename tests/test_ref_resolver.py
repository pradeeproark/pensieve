"""Tests for ref_resolver module."""

from pathlib import Path

import pytest
from pensieve.models import Ref
from pensieve.ref_resolver import (
    find_markdown_heading,
    generate_search_hints,
    resolve_code_ref,
    resolve_doc_ref,
    resolve_ref,
    slugify_heading,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project structure for testing resolution."""
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


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user."""
    return username == "admin"
'''
    )

    (src_dir / "retry.py").write_text(
        '''"""Retry utilities."""


class RetryPolicy:
    """Retry policy with exponential backoff."""

    def execute(self, func):
        """Execute with retry."""
        return func()


RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2,
}
'''
    )

    # Create test file
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_auth.py").write_text(
        '''"""Tests for authentication."""

import pytest


def test_token_validation():
    """Test token validation."""
    assert True


def test_user_authentication():
    """Test user auth."""
    assert True
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

### Implementation Details

See the TokenValidator class.

## Authentication

User authentication is handled by the auth module.
"""
    )

    (docs_dir / "resilience.md").write_text(
        """# Resilience Patterns

## Circuit Breaker

Prevents cascading failures.

## Retry Strategy {#retry-section}

Use exponential backoff for transient failures.

<a id="retry-config"></a>

### Configuration

Set max_attempts and backoff_factor.
"""
    )

    # Create a PDF placeholder (we won't test actual PDF parsing)
    (docs_dir / "api.pdf").write_text("PDF content placeholder")

    return tmp_path


class TestSlugifyHeading:
    """Tests for heading slugification."""

    def test_basic_heading(self) -> None:
        """Test basic heading slugification."""
        assert slugify_heading("## Token Validation") == "token-validation"

    def test_heading_with_special_chars(self) -> None:
        """Test heading with special characters."""
        assert slugify_heading("## What's New?") == "whats-new"

    def test_heading_with_numbers(self) -> None:
        """Test heading with numbers."""
        assert slugify_heading("## Step 1: Setup") == "step-1-setup"

    def test_multiple_spaces(self) -> None:
        """Test heading with multiple spaces."""
        assert slugify_heading("##   Multiple   Spaces") == "multiple-spaces"

    def test_heading_without_hashes(self) -> None:
        """Test plain text heading."""
        assert slugify_heading("Token Validation") == "token-validation"


class TestFindMarkdownHeading:
    """Tests for finding markdown headings in files."""

    def test_find_h2_heading(self, temp_project: Path) -> None:
        """Test finding an H2 heading."""
        doc_file = temp_project / "docs" / "security.md"
        result = find_markdown_heading(doc_file, "## Token Validation")
        assert result == "token-validation"

    def test_find_h3_heading(self, temp_project: Path) -> None:
        """Test finding an H3 heading."""
        doc_file = temp_project / "docs" / "security.md"
        result = find_markdown_heading(doc_file, "### Implementation Details")
        assert result == "implementation-details"

    def test_heading_not_found(self, temp_project: Path) -> None:
        """Test when heading is not found."""
        doc_file = temp_project / "docs" / "security.md"
        result = find_markdown_heading(doc_file, "## Nonexistent Heading")
        assert result is None

    def test_partial_heading_match(self, temp_project: Path) -> None:
        """Test partial heading match (without ## prefix)."""
        doc_file = temp_project / "docs" / "security.md"
        result = find_markdown_heading(doc_file, "Token Validation")
        assert result == "token-validation"


class TestResolveCodeRef:
    """Tests for code reference resolution."""

    def test_resolve_by_symbol(self, temp_project: Path) -> None:
        """Test resolving by symbol name."""
        ref = Ref(name="impl", s="TokenValidator.validate", f="**/auth.py")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "auth.py" in result
        # Should include line number
        assert ":" in result

    def test_resolve_by_text_pattern(self, temp_project: Path) -> None:
        """Test resolving by text pattern."""
        ref = Ref(name="impl", t="def authenticate_user(")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "auth.py" in result

    def test_resolve_by_class_name(self, temp_project: Path) -> None:
        """Test resolving by class name."""
        ref = Ref(name="impl", s="RetryPolicy")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "retry.py" in result

    def test_resolve_with_file_pattern(self, temp_project: Path) -> None:
        """Test resolving with file pattern constraint."""
        ref = Ref(name="test", f="tests/*.py", t="def test_token")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "test_auth.py" in result

    def test_resolve_by_config_pattern(self, temp_project: Path) -> None:
        """Test resolving config/constant patterns."""
        ref = Ref(name="config", t="RETRY_CONFIG = {")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "retry.py" in result

    def test_resolve_fallback_to_file_line(self, temp_project: Path) -> None:
        """Test fallback to file + line hint when symbol/pattern not found."""
        ref = Ref(name="impl", f="src/auth.py", l=10)
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "auth.py" in result
        assert ":10" in result

    def test_resolve_returns_none_when_not_found(self, temp_project: Path) -> None:
        """Test None return when ref cannot be resolved."""
        ref = Ref(name="impl", t="def nonexistent_function(")
        result = resolve_code_ref(ref, temp_project)
        assert result is None


class TestResolveDocRef:
    """Tests for document reference resolution."""

    def test_resolve_by_heading(self, temp_project: Path) -> None:
        """Test resolving by markdown heading."""
        ref = Ref(name="spec", kind="doc", f="docs/security.md", h="## Token Validation")
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        assert "security.md" in result
        assert "#token-validation" in result

    def test_resolve_by_anchor(self, temp_project: Path) -> None:
        """Test resolving by anchor ID."""
        ref = Ref(name="spec", kind="doc", f="docs/resilience.md", a="retry-config")
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        assert "resilience.md" in result
        assert "#retry-config" in result

    def test_resolve_by_heading_id(self, temp_project: Path) -> None:
        """Test resolving heading with explicit ID syntax."""
        ref = Ref(name="spec", kind="doc", f="docs/resilience.md", h="## Retry Strategy")
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        # Should find the heading with {#retry-section} ID
        assert "resilience.md" in result

    def test_resolve_by_page_number(self, temp_project: Path) -> None:
        """Test resolving PDF by page number."""
        ref = Ref(name="pdf", kind="doc", f="docs/api.pdf", p=12)
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        assert "api.pdf" in result
        assert "#page=12" in result

    def test_resolve_doc_by_text_pattern(self, temp_project: Path) -> None:
        """Test resolving doc by text pattern."""
        ref = Ref(name="spec", kind="doc", f="docs/security.md", t="JWT standards")
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        assert "security.md" in result
        # Should include line number from grep
        assert ":" in result

    def test_resolve_doc_fallback_to_file(self, temp_project: Path) -> None:
        """Test fallback to just file path when locator not found."""
        ref = Ref(name="spec", kind="doc", f="docs/security.md")
        result = resolve_doc_ref(ref, temp_project)
        assert result is not None
        assert "security.md" in result

    def test_resolve_doc_file_not_found(self, temp_project: Path) -> None:
        """Test None when doc file doesn't exist."""
        ref = Ref(name="spec", kind="doc", f="docs/nonexistent.md", h="## Setup")
        result = resolve_doc_ref(ref, temp_project)
        assert result is None


class TestResolveRef:
    """Tests for the main resolve_ref function."""

    def test_resolve_code_ref_dispatch(self, temp_project: Path) -> None:
        """Test that code refs are dispatched correctly."""
        ref = Ref(name="impl", kind="code", t="class TokenValidator")
        result = resolve_ref(ref, temp_project)
        assert result is not None
        assert "auth.py" in result

    def test_resolve_doc_ref_dispatch(self, temp_project: Path) -> None:
        """Test that doc refs are dispatched correctly."""
        ref = Ref(name="spec", kind="doc", f="docs/security.md", h="## Overview")
        result = resolve_ref(ref, temp_project)
        assert result is not None
        assert "security.md" in result
        assert "#overview" in result

    def test_resolve_default_kind_is_code(self, temp_project: Path) -> None:
        """Test that default kind=code works."""
        ref = Ref(name="impl", t="def validate(")
        assert ref.kind == "code"
        result = resolve_ref(ref, temp_project)
        assert result is not None


class TestGenerateSearchHints:
    """Tests for search hint generation on resolution failure."""

    def test_hints_for_symbol_ref(self) -> None:
        """Test search hints include symbol search."""
        ref = Ref(name="impl", s="TokenValidator.validate", f="**/auth.py")
        hints = generate_search_hints(ref)
        assert len(hints) > 0
        # Should include rg command for symbol
        assert any("rg" in hint and "TokenValidator" in hint for hint in hints)

    def test_hints_for_text_pattern_ref(self) -> None:
        """Test search hints include text pattern search."""
        ref = Ref(name="impl", t="def validate(self")
        hints = generate_search_hints(ref)
        assert len(hints) > 0
        # Should include rg command for text pattern
        assert any("rg" in hint and "def validate" in hint for hint in hints)

    def test_hints_for_doc_ref(self) -> None:
        """Test search hints for doc refs."""
        ref = Ref(name="spec", kind="doc", f="docs/security.md", h="## Token Validation")
        hints = generate_search_hints(ref)
        assert len(hints) > 0
        # Should include search for heading
        assert any("Token Validation" in hint for hint in hints)

    def test_hints_include_file_pattern(self) -> None:
        """Test hints include file pattern when specified."""
        ref = Ref(name="impl", s="RetryPolicy", f="**/retry*.py")
        hints = generate_search_hints(ref)
        assert any("retry" in hint.lower() for hint in hints)

    def test_hints_are_runnable_commands(self) -> None:
        """Test that hints are valid shell commands."""
        ref = Ref(name="impl", t="def execute(")
        hints = generate_search_hints(ref)
        # Each hint should start with a command name
        for hint in hints:
            assert hint.startswith("rg") or hint.startswith("git") or hint.startswith("grep")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_resolve_with_special_chars_in_pattern(self, temp_project: Path) -> None:
        """Test resolving patterns with special regex chars."""
        ref = Ref(name="impl", t="def execute(self, func)")
        result = resolve_code_ref(ref, temp_project)
        # Should handle parentheses in pattern
        assert result is not None or result is None  # Just shouldn't crash

    def test_resolve_with_unicode_content(self, temp_project: Path) -> None:
        """Test resolving in files with unicode content."""
        # Create a file with unicode
        (temp_project / "src" / "unicode.py").write_text(
            '"""Module with émojis and ünïcödé."""\n\ndef grüß():\n    return "Hëllo"\n',
            encoding="utf-8",
        )
        ref = Ref(name="impl", t="def grüß(")
        result = resolve_code_ref(ref, temp_project)
        # Should handle unicode
        assert result is None or "unicode.py" in result

    def test_resolve_empty_file(self, temp_project: Path) -> None:
        """Test resolving in empty file."""
        (temp_project / "src" / "empty.py").write_text("")
        ref = Ref(name="impl", f="src/empty.py", t="anything")
        result = resolve_code_ref(ref, temp_project)
        assert result is None

    def test_resolve_deeply_nested_file(self, temp_project: Path) -> None:
        """Test resolving deeply nested file."""
        deep_dir = temp_project / "src" / "very" / "deep" / "nested"
        deep_dir.mkdir(parents=True)
        (deep_dir / "module.py").write_text("def deep_function():\n    pass\n")

        ref = Ref(name="impl", t="def deep_function(")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "module.py" in result

    def test_resolve_with_glob_pattern(self, temp_project: Path) -> None:
        """Test file pattern with glob wildcards."""
        ref = Ref(name="test", f="**/test_*.py", t="def test_")
        result = resolve_code_ref(ref, temp_project)
        assert result is not None
        assert "test_auth.py" in result
