"""Pensieve - Memory recording tool for Claude Code agents."""

try:
    from importlib.metadata import version

    __version__ = version("pensieve")
except Exception:
    # Fallback for development/editable installs
    __version__ = "dev"
