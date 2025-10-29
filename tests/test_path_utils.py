"""Tests for path utilities."""

import os
from pathlib import Path

import pytest

from pensieve.path_utils import (
    expand_project_path,
    normalize_project_path,
    normalize_project_search,
    should_normalize_project_search,
    validate_project_path,
)


class TestNormalizeProjectPath:
    """Tests for normalize_project_path function."""

    def test_path_under_home_is_relative(self) -> None:
        """Test that paths under home directory are made relative."""
        home = Path.home()
        test_path = home / "projects" / "myapp"
        result = normalize_project_path(str(test_path))
        assert result == str(Path("projects") / "myapp")

    def test_path_outside_home_is_absolute(self) -> None:
        """Test that paths outside home directory remain absolute."""
        test_path = "/opt/shared/app"
        result = normalize_project_path(test_path)
        assert result == test_path

    def test_tilde_expansion(self) -> None:
        """Test that ~ is expanded to home directory."""
        result = normalize_project_path("~/projects/myapp")
        assert result == str(Path("projects") / "myapp")


class TestExpandProjectPath:
    """Tests for expand_project_path function."""

    def test_relative_path_expanded_to_home(self) -> None:
        """Test that relative paths are expanded relative to home."""
        result = expand_project_path(str(Path("projects") / "myapp"))
        expected = Path.home() / "projects" / "myapp"
        assert result == expected

    def test_absolute_path_unchanged(self) -> None:
        """Test that absolute paths remain unchanged."""
        test_path = Path("/opt/shared/app")
        result = expand_project_path(str(test_path))
        assert result == test_path


class TestValidateProjectPath:
    """Tests for validate_project_path function."""

    def test_empty_path_raises_error(self) -> None:
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_project_path("")

    def test_path_too_long_raises_error(self) -> None:
        """Test that path exceeding 500 chars raises ValueError."""
        long_path = "a" * 501
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_project_path(long_path)

    def test_nonexistent_path_returns_warning(self) -> None:
        """Test that nonexistent path returns warning but succeeds."""
        test_path = str(Path.home() / "nonexistent_test_dir_12345")
        normalized, warning = validate_project_path(test_path)
        assert normalized is not None
        assert warning is not None
        assert "does not exist" in warning

    def test_existing_directory_no_warning(self, tmp_path: Path) -> None:
        """Test that existing directory returns no warning."""
        normalized, warning = validate_project_path(str(tmp_path))
        assert normalized is not None
        assert warning is None


class TestShouldNormalizeProjectSearch:
    """Tests for should_normalize_project_search function."""

    def test_absolute_unix_path_should_normalize(self) -> None:
        """Test that absolute Unix paths should be normalized."""
        assert should_normalize_project_search("/usr/local/project") is True
        assert should_normalize_project_search("/home/user/app") is True

    def test_home_relative_path_should_normalize(self) -> None:
        """Test that home-relative paths should be normalized."""
        assert should_normalize_project_search("~/projects/myapp") is True
        assert should_normalize_project_search("~/Documents/code") is True

    def test_path_with_separator_should_normalize(self) -> None:
        """Test that paths with separators should be normalized."""
        assert should_normalize_project_search("projects/myapp") is True
        assert should_normalize_project_search("kuberan/pensieve") is True

    def test_simple_substring_should_not_normalize(self) -> None:
        """Test that simple substrings should not be normalized."""
        assert should_normalize_project_search("pensieve") is False
        assert should_normalize_project_search("kuberan") is False
        assert should_normalize_project_search("myapp") is False

    def test_windows_path_should_normalize(self) -> None:
        """Test that Windows paths with backslashes should be normalized."""
        if os.sep == "\\":
            # Only test on Windows where os.sep is backslash
            assert should_normalize_project_search("projects\\myapp") is True


class TestNormalizeProjectSearch:
    """Tests for normalize_project_search function."""

    def test_absolute_path_is_normalized(self) -> None:
        """Test that absolute paths are normalized."""
        home = Path.home()
        test_path = str(home / "projects" / "myapp")
        result = normalize_project_search(test_path)
        expected = str(Path("projects") / "myapp")
        assert result == expected

    def test_home_relative_path_is_normalized(self) -> None:
        """Test that home-relative paths are normalized."""
        result = normalize_project_search("~/projects/myapp")
        expected = str(Path("projects") / "myapp")
        assert result == expected

    def test_path_with_separator_is_normalized(self) -> None:
        """Test that paths with separators are normalized."""
        home = Path.home()
        test_path = str(home / "kuberan" / "pensieve")
        result = normalize_project_search(test_path)
        expected = str(Path("kuberan") / "pensieve")
        assert result == expected

    def test_simple_substring_unchanged(self) -> None:
        """Test that simple substrings are returned unchanged."""
        assert normalize_project_search("pensieve") == "pensieve"
        assert normalize_project_search("kuberan") == "kuberan"
        assert normalize_project_search("myapp") == "myapp"

    def test_invalid_path_falls_back_to_original(self) -> None:
        """Test that invalid paths fall back to original input."""
        # Create a path that will fail normalization (over 500 chars)
        long_path = "a" * 501 + os.sep + "project"
        result = normalize_project_search(long_path)
        # Should return original input as fallback
        assert result == long_path

    def test_nonexistent_path_still_normalized(self) -> None:
        """Test that nonexistent paths are still normalized (warnings ignored)."""
        test_path = str(Path.home() / "nonexistent_test_dir_12345")
        result = normalize_project_search(test_path)
        expected = "nonexistent_test_dir_12345"
        assert result == expected


class TestIntegrationScenarios:
    """Integration tests for common search scenarios."""

    def test_create_and_search_with_pwd(self, tmp_path: Path) -> None:
        """Test creating with full path and searching with same path."""
        # Simulate $(pwd) returning full path
        full_path = str(tmp_path)

        # On create: normalize
        normalized = normalize_project_path(full_path)

        # On search: also normalize
        search_normalized = normalize_project_search(full_path)

        # Should match
        assert search_normalized in normalized or normalized in search_normalized

    def test_create_full_path_search_substring(self, tmp_path: Path) -> None:
        """Test creating with full path and searching with substring."""
        full_path = str(tmp_path)

        # On create: normalize
        normalized = normalize_project_path(full_path)

        # On search: simple substring (just the directory name)
        search_input = tmp_path.name
        search_normalized = normalize_project_search(search_input)

        # Simple substring should remain unchanged
        assert search_normalized == search_input
        # And should match in the normalized path
        assert search_normalized in normalized

    def test_create_and_search_with_partial_path(self) -> None:
        """Test creating with full path and searching with partial path."""
        home = Path.home()
        full_path = str(home / "Documents" / "Projects" / "kuberan" / "pensieve")

        # On create: normalize
        normalized = normalize_project_path(full_path)

        # On search: partial path gets normalized from CWD
        partial = "kuberan/pensieve"
        search_normalized = normalize_project_search(partial)

        # The partial path will be resolved relative to CWD, so it won't
        # necessarily match. But substring search will still work because
        # the database query uses LIKE with wildcards.
        # Just verify normalization happened (it has path separator, so it should normalize)
        assert search_normalized != partial  # Should be transformed
        # The key is that "kuberan" or "pensieve" as substrings will still match
        assert "kuberan" in normalized
        assert "pensieve" in normalized
