"""Tests for graph traversal functionality."""

import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from pensieve.database import Database
from pensieve.graph_traversal import traverse_entry_links, RelatedEntryMetadata
from pensieve.models import (
    EntryLink,
    FieldConstraints,
    FieldType,
    JournalEntry,
    LinkType,
    Template,
    TemplateField,
)


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
    """Create and store a sample template for testing."""
    template = Template(
        name="test_template",
        description="Test template",
        created_by="test_agent",
        project="/test/project",
        fields=[
            TemplateField(name="title", type=FieldType.TEXT, required=True),
            TemplateField(name="description", type=FieldType.TEXT, required=False),
        ]
    )
    temp_db.create_template(template)
    return template


@pytest.fixture
def graph_entries(temp_db: Database, sample_template: Template) -> dict[str, UUID]:
    """Create a graph of linked entries for testing.

    Graph structure:
        A (root)
        ├─→ B (supersedes)
        │   ├─→ D (relates_to)
        │   └─→ E (augments)
        └─→ C (relates_to)
            └─→ F (supersedes)

    Also: G ←─ A (incoming link to A)

    Returns dict mapping names to UUIDs
    """
    entries = {}

    # Create entries A through G
    for name in ["A", "B", "C", "D", "E", "F", "G"]:
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={
                "title": f"Entry {name}",
                "description": f"Description for {name}"
            }
        )
        temp_db.create_entry(entry, sample_template)
        entries[name] = entry.id

    # Create links to form the graph
    links = [
        (entries["A"], entries["B"], LinkType.SUPERSEDES),  # A → B
        (entries["A"], entries["C"], LinkType.RELATES_TO),  # A → C
        (entries["B"], entries["D"], LinkType.RELATES_TO),  # B → D
        (entries["B"], entries["E"], LinkType.AUGMENTS),    # B → E
        (entries["C"], entries["F"], LinkType.SUPERSEDES),  # C → F
        (entries["G"], entries["A"], LinkType.RELATES_TO),  # G → A (incoming to A)
    ]

    for source_id, target_id, link_type in links:
        link = EntryLink(
            source_entry_id=source_id,
            target_entry_id=target_id,
            link_type=link_type,
            created_by="test_agent"
        )
        temp_db.create_entry_link(link)

    return entries


class TestGraphTraversal:
    """Tests for BFS graph traversal."""

    def test_traverse_depth_1(self, temp_db: Database, graph_entries: dict[str, UUID]) -> None:
        """Test traversal with depth 1 (direct links only)."""
        root_id = graph_entries["A"]
        related = traverse_entry_links(temp_db, root_id, max_depth=1)

        # Should find: B, C (outgoing from A), and G (incoming to A)
        found_ids = {r.entry_id for r in related}
        expected_ids = {graph_entries["B"], graph_entries["C"], graph_entries["G"]}

        assert found_ids == expected_ids

        # All should be at depth 1
        for r in related:
            assert r.depth == 1
            assert len(r.path) == 1

    def test_traverse_depth_2(self, temp_db: Database, graph_entries: dict[str, UUID]) -> None:
        """Test traversal with depth 2."""
        root_id = graph_entries["A"]
        related = traverse_entry_links(temp_db, root_id, max_depth=2)

        # Should find: B, C, G (depth 1) + D, E, F (depth 2)
        found_ids = {r.entry_id for r in related}
        expected_ids = {
            graph_entries["B"], graph_entries["C"], graph_entries["G"],  # depth 1
            graph_entries["D"], graph_entries["E"], graph_entries["F"],  # depth 2
        }

        assert found_ids == expected_ids

        # Check depths
        depth_1_ids = {r.entry_id for r in related if r.depth == 1}
        depth_2_ids = {r.entry_id for r in related if r.depth == 2}

        assert depth_1_ids == {graph_entries["B"], graph_entries["C"], graph_entries["G"]}
        assert depth_2_ids == {graph_entries["D"], graph_entries["E"], graph_entries["F"]}

    def test_traverse_depth_3(self, temp_db: Database, graph_entries: dict[str, UUID]) -> None:
        """Test traversal with depth 3 (should be same as depth 2 for this graph)."""
        root_id = graph_entries["A"]
        related = traverse_entry_links(temp_db, root_id, max_depth=3)

        # Graph only goes to depth 2, so should be same result
        found_ids = {r.entry_id for r in related}
        expected_ids = {
            graph_entries["B"], graph_entries["C"], graph_entries["G"],  # depth 1
            graph_entries["D"], graph_entries["E"], graph_entries["F"],  # depth 2
        }

        assert found_ids == expected_ids

    def test_traverse_with_cycle(self, temp_db: Database, sample_template: Template) -> None:
        """Test traversal correctly handles cycles."""
        # Create a cycle: A → B → C → A
        entry_a = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry A"}
        )
        temp_db.create_entry(entry_a, sample_template)

        entry_b = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry B"}
        )
        temp_db.create_entry(entry_b, sample_template)

        entry_c = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry C"}
        )
        temp_db.create_entry(entry_c, sample_template)

        # Create cycle
        temp_db.create_entry_link(EntryLink(
            source_entry_id=entry_a.id,
            target_entry_id=entry_b.id,
            link_type=LinkType.RELATES_TO,
            created_by="test_agent"
        ))
        temp_db.create_entry_link(EntryLink(
            source_entry_id=entry_b.id,
            target_entry_id=entry_c.id,
            link_type=LinkType.RELATES_TO,
            created_by="test_agent"
        ))
        temp_db.create_entry_link(EntryLink(
            source_entry_id=entry_c.id,
            target_entry_id=entry_a.id,
            link_type=LinkType.RELATES_TO,
            created_by="test_agent"
        ))

        # Traverse from A with high depth
        related = traverse_entry_links(temp_db, entry_a.id, max_depth=10)

        # Should only find B and C once each (no infinite loop)
        found_ids = {r.entry_id for r in related}
        assert found_ids == {entry_b.id, entry_c.id}

        # Each entry should appear exactly once
        assert len(related) == 2

    def test_traverse_no_links(self, temp_db: Database, sample_template: Template) -> None:
        """Test traversal with entry that has no links."""
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Isolated Entry"}
        )
        temp_db.create_entry(entry, sample_template)

        related = traverse_entry_links(temp_db, entry.id, max_depth=5)

        # Should find nothing
        assert len(related) == 0

    def test_traverse_bidirectional(self, temp_db: Database, sample_template: Template) -> None:
        """Test that traversal follows both outgoing and incoming links."""
        # Create: A ← B → C
        entry_a = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry A"}
        )
        temp_db.create_entry(entry_a, sample_template)

        entry_b = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry B"}
        )
        temp_db.create_entry(entry_b, sample_template)

        entry_c = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/test/project",
            field_values={"title": "Entry C"}
        )
        temp_db.create_entry(entry_c, sample_template)

        # B → A
        temp_db.create_entry_link(EntryLink(
            source_entry_id=entry_b.id,
            target_entry_id=entry_a.id,
            link_type=LinkType.SUPERSEDES,
            created_by="test_agent"
        ))

        # B → C
        temp_db.create_entry_link(EntryLink(
            source_entry_id=entry_b.id,
            target_entry_id=entry_c.id,
            link_type=LinkType.RELATES_TO,
            created_by="test_agent"
        ))

        # Traverse from B - should find both A (incoming) and C (outgoing)
        related = traverse_entry_links(temp_db, entry_b.id, max_depth=1)

        found_ids = {r.entry_id for r in related}
        assert found_ids == {entry_a.id, entry_c.id}

        # Check directions in paths
        a_metadata = next(r for r in related if r.entry_id == entry_a.id)
        c_metadata = next(r for r in related if r.entry_id == entry_c.id)

        # A is reached via outgoing link (→)
        assert a_metadata.path[0][1] == "→"

        # C is reached via outgoing link (→)
        assert c_metadata.path[0][1] == "→"

    def test_traverse_path_tracking(self, temp_db: Database, graph_entries: dict[str, UUID]) -> None:
        """Test that paths are correctly tracked."""
        root_id = graph_entries["A"]
        related = traverse_entry_links(temp_db, root_id, max_depth=2)

        # Find entry D (A → B → D)
        d_metadata = next(r for r in related if r.entry_id == graph_entries["D"])

        # Path should be: supersedes →, relates_to →
        assert len(d_metadata.path) == 2
        assert d_metadata.path[0] == (LinkType.SUPERSEDES, "→")  # A → B
        assert d_metadata.path[1] == (LinkType.RELATES_TO, "→")  # B → D

    def test_invalid_depth(self, temp_db: Database, graph_entries: dict[str, UUID]) -> None:
        """Test that invalid depth raises error."""
        root_id = graph_entries["A"]

        with pytest.raises(ValueError, match="max_depth must be at least 1"):
            traverse_entry_links(temp_db, root_id, max_depth=0)

        with pytest.raises(ValueError, match="max_depth must be at least 1"):
            traverse_entry_links(temp_db, root_id, max_depth=-1)

    def test_nonexistent_entry(self, temp_db: Database) -> None:
        """Test traversal with nonexistent entry raises error."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            traverse_entry_links(temp_db, fake_id, max_depth=1)

    def test_entry_metadata_includes_full_entry(
        self, temp_db: Database, graph_entries: dict[str, UUID]
    ) -> None:
        """Test that metadata includes full entry object."""
        root_id = graph_entries["A"]
        related = traverse_entry_links(temp_db, root_id, max_depth=1)

        # Check that entries have field values
        for metadata in related:
            assert metadata.entry is not None
            assert metadata.entry.field_values is not None
            assert "title" in metadata.entry.field_values
