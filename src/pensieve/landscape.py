"""Landscape visualization for Pensieve memory system.

Provides a heatmap grid visualization showing tag activity over time,
enabling agents to grasp the entire memory landscape at a glance.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pensieve.database import Database


# =============================================================================
# Pure Functions - Intensity and Recency
# =============================================================================

# Block characters for intensity visualization (indexed by level 0-4)
INTENSITY_CHARS = ("··", "░░", "▒▒", "▓▓", "██")


def get_intensity_level(count: int) -> int:
    """Map entry count to intensity level (0-4).

    Args:
        count: Number of entries

    Returns:
        Intensity level:
            0 = none (0 entries)
            1 = low (1 entry)
            2 = medium (2-3 entries)
            3 = high (4-6 entries)
            4 = peak (7+ entries)
    """
    if count == 0:
        return 0
    elif count == 1:
        return 1
    elif count <= 3:
        return 2
    elif count <= 6:
        return 3
    else:
        return 4


def get_intensity_char(level: int) -> str:
    """Get the block character for an intensity level.

    Args:
        level: Intensity level 0-4

    Returns:
        Two-character string representing the intensity
    """
    return INTENSITY_CHARS[level]


def get_recency_indicator(last_activity: datetime, now: datetime) -> str:
    """Get recency indicator based on days since last activity.

    Args:
        last_activity: Timestamp of most recent activity
        now: Current timestamp for comparison

    Returns:
        Indicator character:
            "●" = hot (< 3 days)
            "◐" = warm (3-13 days)
            "○" = cold (>= 14 days)
    """
    days_ago = (now - last_activity).days
    if days_ago < 3:
        return "●"
    elif days_ago < 14:
        return "◐"
    else:
        return "○"


def get_week_offset(timestamp: datetime, now: datetime) -> int:
    """Calculate week offset from current week.

    Args:
        timestamp: Timestamp to check
        now: Current timestamp for reference

    Returns:
        Week offset where 0 is current week, -1 is last week, etc.
    """
    days_diff = (timestamp.date() - now.date()).days
    return days_diff // 7


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class TagActivity:
    """Activity data for a single tag."""

    name: str
    total_entries: int
    last_activity: datetime
    week_counts: dict[int, int]  # week_offset -> count
    related_tags: list[str]  # Top co-occurring tags


@dataclass
class LandscapeData:
    """Complete landscape visualization data."""

    total_entries: int
    total_tags: int
    tags: list[TagActivity]
    weeks_back: int
    project_display: str


@dataclass
class EntryPreview:
    """Preview of a journal entry for cluster view."""

    entry_id: str
    summary: str
    days_ago: int


# =============================================================================
# Renderers
# =============================================================================


class LandscapeRenderer:
    """Renders landscape visualization to terminal output."""

    def __init__(self, data: LandscapeData) -> None:
        self.data = data

    def render(self) -> str:
        """Render complete landscape visualization.

        Returns:
            Multi-line string ready for terminal output
        """
        lines: list[str] = []

        # Header
        lines.append(self._render_header())
        lines.append("")

        if self.data.tags:
            # Week column headers
            lines.append(self._render_week_headers())
            lines.append(self._render_separator())

            # Tag rows with heatmap
            now = datetime.now()
            for tag in self.data.tags:
                lines.append(self._render_tag_row(tag, now))

        # Legend
        lines.append("")
        lines.append(self._render_legend())

        # Zoom guidance
        lines.append("")
        lines.append(self._render_zoom_guidance())

        return "\n".join(lines)

    def _render_header(self) -> str:
        """Render header line with totals."""
        total_e = self.data.total_entries
        total_t = self.data.total_tags
        return f"🧠 PENSIEVE LANDSCAPE │ {total_e}e │ {total_t}t"

    def _render_week_headers(self) -> str:
        """Render week column headers."""
        header = " " * 14
        header += "─" * 11 + " TIME (weeks) " + "─" * 11 + "►\n"
        header += " " * 14
        for i in range(self.data.weeks_back, 0, -1):
            header += f"W-{i}".center(4)
        header += " NOW "
        return header

    def _render_separator(self) -> str:
        """Render separator line."""
        width = 14 + (self.data.weeks_back * 4) + 10
        return "─" * width

    def _render_tag_row(self, tag: TagActivity, now: datetime) -> str:
        """Render a single tag row with heatmap cells."""
        # Tag name (truncated and left-padded)
        name = tag.name[:10].ljust(10)

        # Entry count
        count_str = f"{tag.total_entries:>3}"

        # Heatmap cells
        cells: list[str] = []
        for week_offset in range(-self.data.weeks_back + 1, 1):
            count = tag.week_counts.get(week_offset, 0)
            level = get_intensity_level(count)
            cells.append(get_intensity_char(level))

        heatmap = " ".join(cells)

        # Recency indicator
        recency = get_recency_indicator(tag.last_activity, now)

        # Related tags
        if tag.related_tags:
            related = ",".join(tag.related_tags[:2])
            related_str = f"←{related}"
        else:
            related_str = ""

        return f"{name}{count_str} │ {heatmap} │{recency}│ {related_str}"

    def _render_legend(self) -> str:
        """Render legend for heatmap symbols."""
        return "██ HIGH  ▓▓ MED  ▒▒ LOW  ░░ RARE  ·· NONE │ " "● hot<3d  ◐ warm<14d  ○ cold"

    def _render_zoom_guidance(self) -> str:
        """Render guidance for zooming in."""
        lines = [
            "━" * 50,
            "🔍 ZOOM IN:",
            "   • Explore cluster: pensieve journal --tag <tag>",
            "   • View entry:      pensieve entry show <id>",
            "   • Search memories: pensieve entry search --tag <tag>",
        ]
        return "\n".join(lines)


class ClusterRenderer:
    """Renders cluster view for --tag zoom."""

    def __init__(self, tag: TagActivity, weeks_back: int = 8) -> None:
        self.tag = tag
        self.weeks_back = weeks_back

    def render(self, recent_entries: list[EntryPreview]) -> str:
        """Render cluster view with tag heatmap and recent entries.

        Args:
            recent_entries: List of recent entry previews to display

        Returns:
            Multi-line string ready for terminal output
        """
        lines: list[str] = []

        # Header
        lines.append(self._render_header())
        lines.append("")

        # Heatmap for this tag
        lines.append(self._render_tag_heatmap())
        lines.append("")

        # Recent entries
        if recent_entries:
            lines.append("📋 RECENT ENTRIES:")
            for entry in recent_entries:
                lines.append(f"   • [{entry.days_ago}d ago] {entry.summary} (id: {entry.entry_id})")
        else:
            lines.append("📋 RECENT ENTRIES: None")

        # Actions
        lines.append("")
        lines.append(self._render_actions())

        return "\n".join(lines)

    def _render_header(self) -> str:
        """Render cluster header."""
        related = ", ".join(self.tag.related_tags[:3]) if self.tag.related_tags else "none"
        return (
            f"🔍 CLUSTER: {self.tag.name} │ {self.tag.total_entries} entries │ related: {related}"
        )

    def _render_tag_heatmap(self) -> str:
        """Render single-row heatmap for the tag."""
        now = datetime.now()
        cells: list[str] = []
        for week_offset in range(-self.weeks_back + 1, 1):
            count = self.tag.week_counts.get(week_offset, 0)
            level = get_intensity_level(count)
            cells.append(get_intensity_char(level))

        heatmap = " ".join(cells)
        recency = get_recency_indicator(self.tag.last_activity, now)

        # Week headers
        header = " " * 10
        for i in range(self.weeks_back, 0, -1):
            header += f"W-{i}".center(4)
        header += " NOW "

        return f"{header}\n{self.tag.name[:10].ljust(10)} │ {heatmap} │{recency}│"

    def _render_actions(self) -> str:
        """Render action hints."""
        lines = [
            "━" * 50,
            "🔍 ACTIONS:",
            "   • View entry:      pensieve entry show <id>",
        ]
        if self.tag.related_tags:
            related = self.tag.related_tags[0]
            lines.append(f"   • Related cluster: pensieve journal --tag {related}")
        lines.append("   • Back to map:     pensieve journal")
        return "\n".join(lines)


# =============================================================================
# Builder - Database Integration
# =============================================================================


class LandscapeBuilder:
    """Builds landscape visualization data from database."""

    def __init__(self, db: "Database", weeks_back: int = 8) -> None:
        self.db = db
        self.weeks_back = weeks_back

    def build(self, project: str | None = None, max_tags: int = 15) -> LandscapeData:
        """Build complete landscape data.

        Args:
            project: Project path filter (None for all projects)
            max_tags: Maximum number of tags to display

        Returns:
            LandscapeData with all visualization data
        """
        now = datetime.now()

        # Get tag statistics (sorted by count)
        tag_stats = self.db.get_tag_statistics(project=project)

        if not tag_stats:
            return LandscapeData(
                total_entries=0,
                total_tags=0,
                tags=[],
                weeks_back=self.weeks_back,
                project_display=project or "all projects",
            )

        # Get additional data for landscape
        tag_week_data = self._get_tag_week_counts(project)
        co_occurrences = self._get_tag_co_occurrences(project)
        last_activities = self._get_tag_last_activity(project)

        # Build TagActivity objects
        tags: list[TagActivity] = []
        total_entries = 0

        for tag_name, count in tag_stats[:max_tags]:
            total_entries += count
            tags.append(
                TagActivity(
                    name=tag_name,
                    total_entries=count,
                    last_activity=last_activities.get(tag_name, now - timedelta(days=365)),
                    week_counts=tag_week_data.get(tag_name, {}),
                    related_tags=co_occurrences.get(tag_name, []),
                )
            )

        return LandscapeData(
            total_entries=total_entries,
            total_tags=len(tags),
            tags=tags,
            weeks_back=self.weeks_back,
            project_display=project or "all projects",
        )

    def _get_tag_week_counts(self, project: str | None) -> dict[str, dict[int, int]]:
        """Query entry counts per tag per week.

        Returns:
            Dict mapping tag -> {week_offset -> count}
        """
        now = datetime.now()
        from_date = now - timedelta(weeks=self.weeks_back)

        # Build query
        query = """
            SELECT
                json_each.value as tag,
                je.timestamp
            FROM journal_entries je
            JOIN json_each(je.tags)
            WHERE je.timestamp >= ?
        """
        params: list = [from_date.isoformat()]

        if project:
            query += " AND je.project LIKE ?"
            params.append(f"%{project}%")

        cursor = self.db.conn.execute(query, params)
        rows = cursor.fetchall()

        # Aggregate by tag and week
        result: dict[str, dict[int, int]] = {}
        for tag, timestamp_str in rows:
            timestamp = datetime.fromisoformat(timestamp_str)
            week_offset = get_week_offset(timestamp, now)

            if tag not in result:
                result[tag] = {}
            result[tag][week_offset] = result[tag].get(week_offset, 0) + 1

        return result

    def _get_tag_co_occurrences(
        self, project: str | None, limit_per_tag: int = 3
    ) -> dict[str, list[str]]:
        """Query top co-occurring tags for each tag.

        Returns:
            Dict mapping tag -> [related_tag1, related_tag2, ...]
        """
        query = """
            SELECT
                t1.value as tag1,
                t2.value as tag2,
                COUNT(*) as co_count
            FROM journal_entries je
            JOIN json_each(je.tags) t1
            JOIN json_each(je.tags) t2
            WHERE t1.value < t2.value
        """
        params: list = []

        if project:
            query += " AND je.project LIKE ?"
            params.append(f"%{project}%")

        query += " GROUP BY t1.value, t2.value ORDER BY t1.value, co_count DESC"

        cursor = self.db.conn.execute(query, params)
        rows = cursor.fetchall()

        # Build co-occurrence map
        result: dict[str, list[str]] = {}
        for tag1, tag2, _ in rows:
            # Add bidirectional relationships
            if tag1 not in result:
                result[tag1] = []
            if len(result[tag1]) < limit_per_tag and tag2 not in result[tag1]:
                result[tag1].append(tag2)

            if tag2 not in result:
                result[tag2] = []
            if len(result[tag2]) < limit_per_tag and tag1 not in result[tag2]:
                result[tag2].append(tag1)

        return result

    def _get_tag_last_activity(self, project: str | None) -> dict[str, datetime]:
        """Query last activity timestamp for each tag.

        Returns:
            Dict mapping tag -> last_activity_datetime
        """
        query = """
            SELECT
                json_each.value as tag,
                MAX(je.timestamp) as last_activity
            FROM journal_entries je
            JOIN json_each(je.tags)
        """
        params: list = []

        if project:
            query += " WHERE je.project LIKE ?"
            params.append(f"%{project}%")

        query += " GROUP BY json_each.value"

        cursor = self.db.conn.execute(query, params)
        rows = cursor.fetchall()

        return {tag: datetime.fromisoformat(ts) for tag, ts in rows}
