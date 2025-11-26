"""Tests for Ref and RefsField Pydantic models."""

import pytest
from pensieve.models import Ref, RefsField
from pydantic import ValidationError


class TestRef:
    """Tests for Ref model - location references."""

    def test_create_valid_code_ref_with_symbol(self) -> None:
        """Test creating a valid code ref with symbol."""
        ref = Ref(
            name="impl", kind="code", s="CircuitBreaker.call", f="**/resilience.py", c="abc123"
        )
        assert ref.name == "impl"
        assert ref.kind == "code"
        assert ref.s == "CircuitBreaker.call"
        assert ref.f == "**/resilience.py"
        assert ref.c == "abc123"

    def test_create_valid_code_ref_with_text_pattern(self) -> None:
        """Test creating a valid code ref with text pattern only."""
        ref = Ref(name="impl", t="def validate_token(", c="abc123")
        assert ref.name == "impl"
        assert ref.kind == "code"  # Default
        assert ref.t == "def validate_token("
        assert ref.s is None
        assert ref.f is None

    def test_create_valid_code_ref_with_file_pattern(self) -> None:
        """Test creating a valid code ref with file pattern only."""
        ref = Ref(name="test", f="tests/test_auth.py", c="abc123")
        assert ref.name == "test"
        assert ref.f == "tests/test_auth.py"

    def test_code_ref_requires_at_least_one_locator(self) -> None:
        """Test code ref requires at least one of: s, f, t."""
        with pytest.raises(ValidationError, match="at least one of"):
            Ref(name="impl", kind="code", c="abc123")

    def test_create_valid_doc_ref_with_heading(self) -> None:
        """Test creating a valid doc ref with heading."""
        ref = Ref(
            name="spec", kind="doc", f="docs/security.md", h="## Token Validation", c="abc123"
        )
        assert ref.name == "spec"
        assert ref.kind == "doc"
        assert ref.f == "docs/security.md"
        assert ref.h == "## Token Validation"

    def test_create_valid_doc_ref_with_anchor(self) -> None:
        """Test creating a valid doc ref with anchor."""
        ref = Ref(name="rfc", kind="doc", f="docs/rfcs/auth.md", a="decision", c="abc123")
        assert ref.a == "decision"

    def test_create_valid_doc_ref_with_page(self) -> None:
        """Test creating a valid doc ref with page number (for PDFs)."""
        ref = Ref(name="pdf_spec", kind="doc", f="specs/api.pdf", p=12, c="abc123")
        assert ref.p == 12

    def test_doc_ref_requires_file_pattern(self) -> None:
        """Test doc ref requires file pattern (f)."""
        with pytest.raises(ValidationError, match="requires file pattern"):
            Ref(name="spec", kind="doc", h="## Setup", c="abc123")

    def test_ref_with_line_hint(self) -> None:
        """Test ref with line hint."""
        ref = Ref(name="impl", f="src/auth.py", l=45, c="abc123")
        assert ref.line == 45

    def test_kind_defaults_to_code(self) -> None:
        """Test kind defaults to 'code'."""
        ref = Ref(name="impl", t="def foo(", c="abc123")
        assert ref.kind == "code"

    def test_invalid_kind_rejected(self) -> None:
        """Test invalid kind value is rejected."""
        with pytest.raises(ValidationError):
            Ref(name="impl", kind="invalid", t="def foo(", c="abc123")

    def test_name_required(self) -> None:
        """Test name is required."""
        with pytest.raises(ValidationError):
            Ref(kind="code", t="def foo(", c="abc123")

    def test_all_fields_optional_except_name(self) -> None:
        """Test optional fields default to None."""
        ref = Ref(name="impl", t="def foo(", c="abc123")
        assert ref.f is None
        assert ref.line is None
        assert ref.s is None
        assert ref.h is None
        assert ref.p is None
        assert ref.a is None


class TestRefsField:
    """Tests for RefsField model - array of refs."""

    def test_create_refs_field_with_multiple_refs(self) -> None:
        """Test creating a RefsField with multiple refs."""
        refs_field = RefsField(
            refs=[
                Ref(name="impl", s="CircuitBreaker.call", c="abc123"),
                Ref(name="test", f="tests/*.py", t="def test_", c="abc123"),
                Ref(name="spec", kind="doc", f="docs/arch.md", h="## Overview", c="abc123"),
            ]
        )
        assert len(refs_field.refs) == 3
        assert refs_field.refs[0].name == "impl"
        assert refs_field.refs[1].name == "test"
        assert refs_field.refs[2].name == "spec"

    def test_create_empty_refs_field(self) -> None:
        """Test creating an empty RefsField."""
        refs_field = RefsField(refs=[])
        assert refs_field.refs == []

    def test_refs_field_validates_each_ref(self) -> None:
        """Test RefsField validates each ref in the array."""
        with pytest.raises(ValidationError):
            RefsField(
                refs=[
                    Ref(name="impl", t="def foo(", c="abc123"),  # Valid
                    Ref(name="bad", kind="code", c="abc123"),  # Invalid - no locator
                ]
            )

    def test_refs_field_coerces_dict_to_ref(self) -> None:
        """Test RefsField coerces valid dict to Ref."""
        # Pydantic coerces compatible dicts to Ref objects
        refs_field = RefsField(refs=[{"name": "impl", "t": "def foo(", "c": "abc123"}])
        assert len(refs_field.refs) == 1
        assert isinstance(refs_field.refs[0], Ref)
        assert refs_field.refs[0].name == "impl"

    def test_refs_field_rejects_invalid_dict(self) -> None:
        """Test RefsField rejects dict that doesn't match Ref schema."""
        with pytest.raises(ValidationError):
            # Missing required locator for code ref
            RefsField(refs=[{"name": "impl", "kind": "code", "c": "abc123"}])


class TestRefSerialization:
    """Tests for Ref model serialization."""

    def test_ref_to_dict(self) -> None:
        """Test Ref serializes to dict correctly."""
        ref = Ref(
            name="impl",
            kind="code",
            s="CircuitBreaker.call",
            f="**/resilience.py",
            t="def call(self",
            c="abc123",
        )
        data = ref.model_dump(exclude_none=True)
        assert data == {
            "name": "impl",
            "kind": "code",
            "s": "CircuitBreaker.call",
            "f": "**/resilience.py",
            "t": "def call(self",
            "c": "abc123",
        }

    def test_ref_from_dict(self) -> None:
        """Test Ref deserializes from dict correctly."""
        data = {
            "name": "spec",
            "kind": "doc",
            "f": "docs/arch.md",
            "h": "## Overview",
            "c": "abc123",
        }
        ref = Ref.model_validate(data)
        assert ref.name == "spec"
        assert ref.kind == "doc"
        assert ref.f == "docs/arch.md"
        assert ref.h == "## Overview"

    def test_refs_field_to_json(self) -> None:
        """Test RefsField serializes to JSON correctly."""
        refs_field = RefsField(
            refs=[
                Ref(name="impl", t="def foo(", c="abc123"),
                Ref(name="spec", kind="doc", f="docs/x.md", h="## X", c="abc123"),
            ]
        )
        json_str = refs_field.model_dump_json()
        assert "impl" in json_str
        assert "spec" in json_str
