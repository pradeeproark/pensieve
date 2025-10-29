"""Data models for Pensieve."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class FieldType(str, Enum):
    """Supported field types in templates."""

    BOOLEAN = "boolean"
    TEXT = "text"
    URL = "url"
    TIMESTAMP = "timestamp"
    FILE_REFERENCE = "file_reference"


class EntryStatus(str, Enum):
    """Status of a journal entry."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class LinkType(str, Enum):
    """Types of relationships between entries."""

    SUPERSEDES = "supersedes"  # New entry replaces old one
    RELATES_TO = "relates_to"  # General relationship
    AUGMENTS = "augments"  # Adds to existing entry
    DEPRECATES = "deprecates"  # Marks target as obsolete


class FieldConstraints(BaseModel):
    """Constraints for template fields."""

    max_length: int | None = None  # For text fields
    url_schemes: list[str] | None = None  # For url fields (e.g., ["http", "https"])
    file_types: list[str] | None = None  # For file_reference fields (e.g., [".py", ".js"])
    auto_now: bool = False  # For timestamp fields (auto-fill current time)

    model_config = {"extra": "forbid"}


class TemplateField(BaseModel):
    """Definition of a field in a template."""

    name: str = Field(..., min_length=1, max_length=100)
    type: FieldType
    required: bool = False
    constraints: FieldConstraints = Field(default_factory=FieldConstraints)
    description: str = Field(default="", max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate field name is alphanumeric with underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Field name must be alphanumeric with underscores")
        return v

    model_config = {"extra": "forbid"}


class Template(BaseModel):
    """Template defining structure for journal entries."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., min_length=1, max_length=100)
    project: str = Field(..., min_length=1, max_length=500)
    fields: list[TemplateField] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name is alphanumeric with underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Template name must be alphanumeric with underscores")
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_field_names(cls, v: list[TemplateField]) -> list[TemplateField]:
        """Ensure field names are unique within template."""
        names = [field.name for field in v]
        if len(names) != len(set(names)):
            raise ValueError("Field names must be unique within a template")
        return v

    model_config = {"extra": "forbid"}


class EntryLink(BaseModel):
    """Link between two journal entries."""

    id: UUID = Field(default_factory=uuid4)
    source_entry_id: UUID
    target_entry_id: UUID
    link_type: LinkType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., min_length=1, max_length=100)

    @field_validator("target_entry_id")
    @classmethod
    def validate_no_self_link(cls, v: UUID, info) -> UUID:
        """Prevent self-referential links."""
        if "source_entry_id" in info.data and v == info.data["source_entry_id"]:
            raise ValueError("Cannot create self-link (source and target are the same)")
        return v

    model_config = {"extra": "forbid"}


class JournalEntry(BaseModel):
    """A journal entry recording an event."""

    id: UUID = Field(default_factory=uuid4)
    template_id: UUID
    template_version: int = Field(..., ge=1)
    agent: str = Field(..., min_length=1, max_length=100)
    project: str = Field(..., min_length=1, max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    field_values: dict[str, Any] = Field(default_factory=dict)
    status: EntryStatus = Field(default=EntryStatus.ACTIVE)
    tags: list[str] = Field(default_factory=list)
    links_from: list[EntryLink] = Field(default_factory=list)  # Links FROM this entry
    links_to: list[EntryLink] = Field(default_factory=list)  # Links TO this entry

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty and unique."""
        if not v:
            return v
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tags must be non-empty strings")
            if len(tag) > 50:
                raise ValueError("Tags must be 50 characters or less")
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in v:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        return unique_tags

    model_config = {"extra": "forbid"}


class Migration(BaseModel):
    """Database migration record."""

    version: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=200)
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: str = Field(..., min_length=64, max_length=64)  # SHA256 hex

    model_config = {"extra": "forbid"}
