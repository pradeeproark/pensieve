"""Tests for landscape visualization module."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pensieve.database import Database
from pensieve.models import FieldType, JournalEntry, Template, TemplateField

# =============================================================================
# Pure Function Tests - Intensity and Recency
# =============================================================================


class TestGetIntensityLevel:
    """Tests for get_intensity_level pure function."""

    def test_zero_count_returns_zero(self) -> None:
        """Zero entries maps to intensity level 0."""
        from pensieve.landscape import get_intensity_level

        assert get_intensity_level(0) == 0

    def test_one_count_returns_one(self) -> None:
        """Single entry maps to intensity level 1 (low)."""
        from pensieve.landscape import get_intensity_level

        assert get_intensity_level(1) == 1

    def test_two_to_three_returns_two(self) -> None:
        """2-3 entries maps to intensity level 2 (medium)."""
        from pensieve.landscape import get_intensity_level

        assert get_intensity_level(2) == 2
        assert get_intensity_level(3) == 2

    def test_four_to_six_returns_three(self) -> None:
        """4-6 entries maps to intensity level 3 (high)."""
        from pensieve.landscape import get_intensity_level

        assert get_intensity_level(4) == 3
        assert get_intensity_level(5) == 3
        assert get_intensity_level(6) == 3

    def test_seven_plus_returns_four(self) -> None:
        """7+ entries maps to intensity level 4 (peak)."""
        from pensieve.landscape import get_intensity_level

        assert get_intensity_level(7) == 4
        assert get_intensity_level(10) == 4
        assert get_intensity_level(100) == 4


class TestGetIntensityChar:
    """Tests for get_intensity_char pure function."""

    def test_level_zero_returns_dots(self) -> None:
        """Level 0 renders as '··' (no activity)."""
        from pensieve.landscape import get_intensity_char

        assert get_intensity_char(0) == "··"

    def test_level_one_returns_light_shade(self) -> None:
        """Level 1 renders as '░░' (low)."""
        from pensieve.landscape import get_intensity_char

        assert get_intensity_char(1) == "░░"

    def test_level_two_returns_medium_shade(self) -> None:
        """Level 2 renders as '▒▒' (medium)."""
        from pensieve.landscape import get_intensity_char

        assert get_intensity_char(2) == "▒▒"

    def test_level_three_returns_dark_shade(self) -> None:
        """Level 3 renders as '▓▓' (high)."""
        from pensieve.landscape import get_intensity_char

        assert get_intensity_char(3) == "▓▓"

    def test_level_four_returns_full_block(self) -> None:
        """Level 4 renders as '██' (peak)."""
        from pensieve.landscape import get_intensity_char

        assert get_intensity_char(4) == "██"


class TestGetRecencyIndicator:
    """Tests for get_recency_indicator pure function."""

    def test_hot_within_3_days(self) -> None:
        """Activity within 3 days returns hot indicator."""
        from pensieve.landscape import get_recency_indicator

        now = datetime.now()
        two_days_ago = now - timedelta(days=2)

        assert get_recency_indicator(two_days_ago, now) == "●"

    def test_hot_boundary_at_3_days(self) -> None:
        """Activity exactly 3 days ago is warm, not hot."""
        from pensieve.landscape import get_recency_indicator

        now = datetime.now()
        three_days_ago = now - timedelta(days=3)

        assert get_recency_indicator(three_days_ago, now) == "◐"

    def test_warm_between_3_and_14_days(self) -> None:
        """Activity 3-13 days ago returns warm indicator."""
        from pensieve.landscape import get_recency_indicator

        now = datetime.now()
        five_days_ago = now - timedelta(days=5)
        ten_days_ago = now - timedelta(days=10)
        thirteen_days_ago = now - timedelta(days=13)

        assert get_recency_indicator(five_days_ago, now) == "◐"
        assert get_recency_indicator(ten_days_ago, now) == "◐"
        assert get_recency_indicator(thirteen_days_ago, now) == "◐"

    def test_cold_at_14_days_and_beyond(self) -> None:
        """Activity 14+ days ago returns cold indicator."""
        from pensieve.landscape import get_recency_indicator

        now = datetime.now()
        fourteen_days_ago = now - timedelta(days=14)
        thirty_days_ago = now - timedelta(days=30)

        assert get_recency_indicator(fourteen_days_ago, now) == "○"
        assert get_recency_indicator(thirty_days_ago, now) == "○"


class TestGetWeekOffset:
    """Tests for get_week_offset pure function."""

    def test_current_week_returns_zero(self) -> None:
        """Timestamp in current week returns offset 0."""
        from pensieve.landscape import get_week_offset

        now = datetime.now()
        assert get_week_offset(now, now) == 0

    def test_one_week_ago_returns_negative_one(self) -> None:
        """Timestamp 7 days ago returns offset -1."""
        from pensieve.landscape import get_week_offset

        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        assert get_week_offset(one_week_ago, now) == -1

    def test_eight_weeks_ago_returns_negative_eight(self) -> None:
        """Timestamp 56 days ago returns offset -8."""
        from pensieve.landscape import get_week_offset

        now = datetime.now()
        eight_weeks_ago = now - timedelta(days=56)
        assert get_week_offset(eight_weeks_ago, now) == -8


# =============================================================================
# Data Structure Tests - TagActivity
# =============================================================================


class TestTagActivity:
    """Tests for TagActivity dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """TagActivity can be created with required fields."""
        from pensieve.landscape import TagActivity

        activity = TagActivity(
            name="authentication",
            total_entries=15,
            last_activity=datetime.now(),
            week_counts={0: 3, -1: 2, -2: 1},
            related_tags=["oauth", "jwt"],
        )

        assert activity.name == "authentication"
        assert activity.total_entries == 15
        assert len(activity.week_counts) == 3
        assert activity.related_tags == ["oauth", "jwt"]

    def test_empty_week_counts(self) -> None:
        """TagActivity handles empty week_counts."""
        from pensieve.landscape import TagActivity

        activity = TagActivity(
            name="unused",
            total_entries=0,
            last_activity=datetime.now() - timedelta(days=100),
            week_counts={},
            related_tags=[],
        )

        assert activity.week_counts == {}


class TestLandscapeData:
    """Tests for LandscapeData dataclass."""

    def test_creation_with_tags(self) -> None:
        """LandscapeData holds complete landscape state."""
        from pensieve.landscape import LandscapeData, TagActivity

        tags = [
            TagActivity(
                name="auth",
                total_entries=10,
                last_activity=datetime.now(),
                week_counts={0: 5},
                related_tags=["jwt"],
            ),
        ]

        data = LandscapeData(
            total_entries=10,
            total_tags=1,
            tags=tags,
            weeks_back=8,
            project_display="test/project",
        )

        assert data.total_entries == 10
        assert len(data.tags) == 1
        assert data.weeks_back == 8


# =============================================================================
# Renderer Tests
# =============================================================================


class TestLandscapeRenderer:
    """Tests for LandscapeRenderer ASCII output."""

    def test_render_header(self) -> None:
        """Header shows project summary with entry and tag counts."""
        from pensieve.landscape import LandscapeData, LandscapeRenderer

        data = LandscapeData(
            total_entries=42,
            total_tags=18,
            tags=[],
            weeks_back=8,
            project_display="test/project",
        )

        renderer = LandscapeRenderer(data)
        output = renderer.render()

        assert "PENSIEVE LANDSCAPE" in output
        assert "42e" in output
        assert "18t" in output

    def test_render_tag_row(self) -> None:
        """Tag row shows name, count, heatmap, recency, and related tags."""
        from pensieve.landscape import LandscapeData, LandscapeRenderer, TagActivity

        now = datetime.now()
        tags = [
            TagActivity(
                name="authentication",
                total_entries=15,
                last_activity=now - timedelta(days=1),  # hot
                week_counts={0: 3, -1: 2},
                related_tags=["oauth", "jwt"],
            ),
        ]

        data = LandscapeData(
            total_entries=15,
            total_tags=1,
            tags=tags,
            weeks_back=8,
            project_display="test",
        )

        renderer = LandscapeRenderer(data)
        output = renderer.render()

        # Tag name should be visible (possibly truncated)
        assert "auth" in output.lower()
        # Entry count
        assert "15" in output
        # Hot recency indicator
        assert "●" in output
        # Related tags hint
        assert "oauth" in output or "jwt" in output

    def test_render_includes_legend(self) -> None:
        """Output includes legend explaining symbols."""
        from pensieve.landscape import LandscapeData, LandscapeRenderer

        data = LandscapeData(
            total_entries=0,
            total_tags=0,
            tags=[],
            weeks_back=8,
            project_display="test",
        )

        renderer = LandscapeRenderer(data)
        output = renderer.render()

        # Legend symbols
        assert "██" in output or "HIGH" in output
        assert "●" in output or "hot" in output

    def test_render_includes_zoom_guidance(self) -> None:
        """Output includes guidance for zooming in."""
        from pensieve.landscape import LandscapeData, LandscapeRenderer

        data = LandscapeData(
            total_entries=10,
            total_tags=2,
            tags=[],
            weeks_back=8,
            project_display="test",
        )

        renderer = LandscapeRenderer(data)
        output = renderer.render()

        # Zoom guidance
        assert "ZOOM" in output or "journal --tag" in output

    def test_render_empty_landscape(self) -> None:
        """Empty landscape shows appropriate message."""
        from pensieve.landscape import LandscapeData, LandscapeRenderer

        data = LandscapeData(
            total_entries=0,
            total_tags=0,
            tags=[],
            weeks_back=8,
            project_display="test",
        )

        renderer = LandscapeRenderer(data)
        output = renderer.render()

        # Should still render without crashing
        assert "PENSIEVE" in output or "0e" in output


class TestClusterRenderer:
    """Tests for ClusterRenderer (--tag zoom view)."""

    def test_render_shows_cluster_header(self) -> None:
        """Cluster view shows focused tag header."""
        from pensieve.landscape import ClusterRenderer, TagActivity

        tag = TagActivity(
            name="authentication",
            total_entries=15,
            last_activity=datetime.now(),
            week_counts={0: 5},
            related_tags=["oauth", "jwt", "prod-bug"],
        )

        renderer = ClusterRenderer(tag, weeks_back=8)
        output = renderer.render(recent_entries=[])

        assert "CLUSTER" in output
        assert "auth" in output.lower()
        assert "15" in output

    def test_render_shows_recent_entries(self) -> None:
        """Cluster view lists recent entry summaries."""
        from pensieve.landscape import ClusterRenderer, EntryPreview, TagActivity

        tag = TagActivity(
            name="auth",
            total_entries=3,
            last_activity=datetime.now(),
            week_counts={0: 3},
            related_tags=[],
        )

        entries = [
            EntryPreview(
                entry_id="89376697",
                summary="OAuth token refresh failing",
                days_ago=2,
            ),
            EntryPreview(
                entry_id="29896bfa",
                summary="JWT validation timing issue",
                days_ago=5,
            ),
        ]

        renderer = ClusterRenderer(tag, weeks_back=8)
        output = renderer.render(recent_entries=entries)

        assert "OAuth token" in output or "89376697" in output
        assert "2d ago" in output or "[2d" in output

    def test_render_includes_actions(self) -> None:
        """Cluster view includes action hints."""
        from pensieve.landscape import ClusterRenderer, TagActivity

        tag = TagActivity(
            name="auth",
            total_entries=1,
            last_activity=datetime.now(),
            week_counts={},
            related_tags=["jwt"],
        )

        renderer = ClusterRenderer(tag, weeks_back=8)
        output = renderer.render(recent_entries=[])

        # Should suggest viewing entries and related clusters
        assert "entry show" in output or "ACTION" in output
        assert "journal" in output


# =============================================================================
# Builder Tests - Database Integration
# =============================================================================


@pytest.fixture
def temp_db() -> Database:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    yield db
    db.close()

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
        ],
    )
    temp_db.create_template(template)
    return template


class TestLandscapeBuilder:
    """Tests for LandscapeBuilder database integration."""

    def test_build_empty_database(self, temp_db: Database) -> None:
        """Builder handles empty database gracefully."""
        from pensieve.landscape import LandscapeBuilder

        builder = LandscapeBuilder(temp_db, weeks_back=8)
        data = builder.build(project="/test/project")

        assert data.total_entries == 0
        assert data.total_tags == 0
        assert data.tags == []

    def test_build_aggregates_by_tag(self, temp_db: Database, sample_template: Template) -> None:
        """Builder aggregates entries by tag correctly."""
        from pensieve.landscape import LandscapeBuilder

        project = "/test/project"

        # Create tags
        temp_db.create_tag(project, "auth", "test_agent")
        temp_db.create_tag(project, "deploy", "test_agent")

        # Create entries with tags
        for i in range(5):
            entry = JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project=project,
                field_values={"title": f"Auth entry {i}"},
                tags=["auth"],
            )
            temp_db.create_entry(entry, sample_template)

        for i in range(3):
            entry = JournalEntry(
                template_id=sample_template.id,
                template_version=sample_template.version,
                agent="test_agent",
                project=project,
                field_values={"title": f"Deploy entry {i}"},
                tags=["deploy"],
            )
            temp_db.create_entry(entry, sample_template)

        builder = LandscapeBuilder(temp_db, weeks_back=8)
        data = builder.build(project=project)

        assert data.total_entries == 8
        assert data.total_tags == 2

        # Tags should be sorted by count
        tag_names = [t.name for t in data.tags]
        assert tag_names[0] == "auth"  # 5 entries
        assert tag_names[1] == "deploy"  # 3 entries

    def test_build_computes_week_counts(self, temp_db: Database, sample_template: Template) -> None:
        """Builder computes per-week activity counts."""
        from pensieve.landscape import LandscapeBuilder

        project = "/test/project"
        temp_db.create_tag(project, "test-tag", "test_agent")

        # Create entry (will be in current week)
        entry = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project=project,
            field_values={"title": "Test"},
            tags=["test-tag"],
        )
        temp_db.create_entry(entry, sample_template)

        builder = LandscapeBuilder(temp_db, weeks_back=8)
        data = builder.build(project=project)

        assert len(data.tags) == 1
        tag = data.tags[0]
        # Current week should have count
        assert 0 in tag.week_counts
        assert tag.week_counts[0] >= 1

    def test_build_finds_co_occurrences(self, temp_db: Database, sample_template: Template) -> None:
        """Builder identifies co-occurring tags."""
        from pensieve.landscape import LandscapeBuilder

        project = "/test/project"
        temp_db.create_tag(project, "auth", "test_agent")
        temp_db.create_tag(project, "oauth", "test_agent")
        temp_db.create_tag(project, "jwt", "test_agent")

        # Create entries where auth co-occurs with oauth and jwt
        entry1 = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project=project,
            field_values={"title": "Entry 1"},
            tags=["auth", "oauth"],
        )
        entry2 = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project=project,
            field_values={"title": "Entry 2"},
            tags=["auth", "jwt"],
        )
        entry3 = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project=project,
            field_values={"title": "Entry 3"},
            tags=["auth", "oauth", "jwt"],
        )

        temp_db.create_entry(entry1, sample_template)
        temp_db.create_entry(entry2, sample_template)
        temp_db.create_entry(entry3, sample_template)

        builder = LandscapeBuilder(temp_db, weeks_back=8)
        data = builder.build(project=project)

        # Find auth tag
        auth_tag = next(t for t in data.tags if t.name == "auth")
        # Should have oauth and jwt as related
        assert "oauth" in auth_tag.related_tags or "jwt" in auth_tag.related_tags

    def test_build_respects_project_filter(
        self, temp_db: Database, sample_template: Template
    ) -> None:
        """Builder filters by project correctly."""
        from pensieve.landscape import LandscapeBuilder

        # Create entries in different projects
        temp_db.create_tag("/project/a", "tag-a", "test_agent")
        temp_db.create_tag("/project/b", "tag-b", "test_agent")

        entry_a = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/project/a",
            field_values={"title": "Entry A"},
            tags=["tag-a"],
        )
        entry_b = JournalEntry(
            template_id=sample_template.id,
            template_version=sample_template.version,
            agent="test_agent",
            project="/project/b",
            field_values={"title": "Entry B"},
            tags=["tag-b"],
        )

        temp_db.create_entry(entry_a, sample_template)
        temp_db.create_entry(entry_b, sample_template)

        builder = LandscapeBuilder(temp_db, weeks_back=8)

        # Query project A only
        data_a = builder.build(project="/project/a")
        tag_names_a = [t.name for t in data_a.tags]
        assert "tag-a" in tag_names_a
        assert "tag-b" not in tag_names_a
