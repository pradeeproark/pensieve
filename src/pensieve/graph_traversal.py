"""Graph traversal utilities for following entry links."""

from collections import deque
from dataclasses import dataclass
from uuid import UUID

from pensieve.database import Database
from pensieve.models import EntryLink, JournalEntry, LinkType


@dataclass
class RelatedEntryMetadata:
    """Metadata about a related entry discovered during traversal."""

    entry_id: UUID
    depth: int
    path: list[tuple[LinkType, str]]  # [(link_type, direction), ...] where direction is '→' or '←'
    entry: JournalEntry


def traverse_entry_links(
    db: Database, root_entry_id: UUID, max_depth: int
) -> list[RelatedEntryMetadata]:
    """Traverse entry links using breadth-first search.

    Args:
        db: Database instance
        root_entry_id: Starting entry ID
        max_depth: Maximum depth to traverse (1 = direct links only)

    Returns:
        List of RelatedEntryMetadata for all discovered entries (excluding root)
    """
    if max_depth < 1:
        raise ValueError("max_depth must be at least 1")

    # Verify root entry exists
    root_entry = db.get_entry_by_id(root_entry_id)
    if root_entry is None:
        raise ValueError(f"Root entry '{root_entry_id}' not found")

    # Track visited entries to prevent cycles
    visited: set[UUID] = {root_entry_id}

    # Queue: (entry_id, depth, path)
    queue: deque[tuple[UUID, int, list[tuple[LinkType, str]]]] = deque()
    queue.append((root_entry_id, 0, []))

    # Results: metadata for all discovered entries (excluding root)
    results: list[RelatedEntryMetadata] = []

    # Process entries level by level
    while queue:
        # Collect all entries at current level
        current_level_size = len(queue)
        current_level_entries: list[tuple[UUID, int, list[tuple[LinkType, str]]]] = []

        for _ in range(current_level_size):
            entry_id, depth, path = queue.popleft()
            current_level_entries.append((entry_id, depth, path))

        # Stop if we've reached max depth
        if current_level_entries and current_level_entries[0][1] >= max_depth:
            break

        # Batch fetch links for all entries at this level
        entry_ids_to_fetch = [eid for eid, _, _ in current_level_entries]
        links_map = db.get_linked_entries_batch(entry_ids_to_fetch)

        # Process each entry's links
        for entry_id, depth, path in current_level_entries:
            links_from, links_to = links_map.get(entry_id, ([], []))

            # Process outgoing links (links_from)
            for link in links_from:
                target_id = link.target_entry_id
                if target_id not in visited:
                    visited.add(target_id)
                    new_path = path + [(link.link_type, "→")]

                    # Fetch the full entry for this linked entry
                    target_entry = db.get_entry_by_id(target_id)
                    if target_entry:
                        # Add to results (excluding root)
                        if target_id != root_entry_id:
                            results.append(
                                RelatedEntryMetadata(
                                    entry_id=target_id,
                                    depth=depth + 1,
                                    path=new_path,
                                    entry=target_entry,
                                )
                            )

                        # Add to queue for further traversal
                        queue.append((target_id, depth + 1, new_path))

            # Process incoming links (links_to)
            for link in links_to:
                source_id = link.source_entry_id
                if source_id not in visited:
                    visited.add(source_id)
                    new_path = path + [(link.link_type, "←")]

                    # Fetch the full entry for this linked entry
                    source_entry = db.get_entry_by_id(source_id)
                    if source_entry:
                        # Add to results (excluding root)
                        if source_id != root_entry_id:
                            results.append(
                                RelatedEntryMetadata(
                                    entry_id=source_id,
                                    depth=depth + 1,
                                    path=new_path,
                                    entry=source_entry,
                                )
                            )

                        # Add to queue for further traversal
                        queue.append((source_id, depth + 1, new_path))

    return results
