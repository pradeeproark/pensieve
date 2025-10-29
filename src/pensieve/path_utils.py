"""Path utilities for handling project directory paths."""

import os
from pathlib import Path


def normalize_project_path(path: str) -> str:
    """Normalize project path to be relative to home when possible.

    Args:
        path: Project directory path (can be relative or absolute)

    Returns:
        Normalized path string (relative to home if under home, absolute otherwise)

    Examples:
        /Users/john/projects/myapp -> projects/myapp
        /opt/shared/app -> /opt/shared/app
        ./myapp -> projects/myapp (if pwd is ~/projects)
    """
    # Convert to Path object and resolve to absolute path
    abs_path = Path(path).expanduser().resolve()
    home = Path.home()

    # Try to make relative to home directory
    try:
        rel_path = abs_path.relative_to(home)
        return str(rel_path)
    except ValueError:
        # Path is not under home directory, return absolute
        return str(abs_path)


def expand_project_path(path: str) -> Path:
    """Expand project path back to absolute path.

    Args:
        path: Normalized project path (from database)

    Returns:
        Absolute Path object

    Examples:
        projects/myapp -> /Users/john/projects/myapp
        /opt/shared/app -> /opt/shared/app
    """
    p = Path(path)

    # If already absolute, return as-is
    if p.is_absolute():
        return p

    # Otherwise, it's relative to home
    return Path.home() / p


def validate_project_path(path: str) -> tuple[str, str | None]:
    """Validate project path and check if directory exists.

    Args:
        path: Project directory path to validate

    Returns:
        Tuple of (normalized_path, warning_message)
        warning_message is None if directory exists, otherwise contains warning

    Raises:
        ValueError: If path is invalid format
    """
    if not path or not path.strip():
        raise ValueError("Project path cannot be empty")

    if len(path) > 500:
        raise ValueError("Project path exceeds maximum length of 500 characters")

    # Normalize the path
    try:
        normalized = normalize_project_path(path)
    except Exception as e:
        raise ValueError(f"Invalid project path: {e}") from e

    # Check if directory exists
    expanded = expand_project_path(normalized)
    warning = None

    if not expanded.exists():
        warning = f"Warning: Project directory does not exist: {expanded}"
    elif not expanded.is_dir():
        warning = f"Warning: Project path exists but is not a directory: {expanded}"

    return normalized, warning


def should_normalize_project_search(project_input: str) -> bool:
    """Determine if search input should be normalized as a path.

    Args:
        project_input: Search input from user

    Returns:
        True if input looks like a path (should be normalized),
        False if it's a simple substring (use as-is)

    Examples:
        /Users/john/projects/app -> True (absolute path)
        ~/Documents/pensieve -> True (home-relative)
        kuberan/pensieve -> True (has path separator)
        pensieve -> False (simple substring)
        kuberan -> False (simple substring)
    """
    return (
        project_input.startswith('/') or
        project_input.startswith('~') or
        os.sep in project_input
    )


def normalize_project_search(project_input: str) -> str:
    """Normalize project search input if it looks like a path.

    This ensures search inputs match the normalized storage format.
    Paths are normalized, simple substrings are preserved.

    Args:
        project_input: Search input from user

    Returns:
        Normalized path if input is a path, otherwise original input

    Examples:
        /Users/john/projects/app -> projects/app (normalized)
        kuberan/pensieve -> Documents/Projects/.../kuberan/pensieve (normalized)
        pensieve -> pensieve (unchanged, simple substring)
    """
    if should_normalize_project_search(project_input):
        # It's a path - normalize it
        try:
            normalized, _ = validate_project_path(project_input)
            return normalized
        except Exception:
            # If normalization fails, fall back to original input
            # This allows the search to still work as a substring match
            return project_input
    else:
        # It's a simple substring - return as-is
        return project_input
