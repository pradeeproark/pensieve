"""Reference resolver for code and document locations.

This module implements a tiered resolution strategy:

Code refs (kind=code):
  Tier 1: Symbol lookup (if s provided) - search for class/def/function
  Tier 2: Text pattern grep (if t provided) - search for exact text
  Tier 3: File + line hint - return file:line if file exists
  Failure: Return None, caller uses generate_search_hints()

Doc refs (kind=doc):
  Tier 1: Heading match (if h provided) - find markdown heading
  Tier 2: Anchor match (if a provided) - find anchor ID in file
  Tier 3: Page number (if p provided) - return file#page=N
  Tier 4: Text pattern (if t provided) - grep for text
  Failure: Return file path if exists, else None
"""

import re
import subprocess
from pathlib import Path

from pensieve.models import Ref


def slugify_heading(heading: str) -> str:
    """Convert a markdown heading to a URL-friendly slug.

    Args:
        heading: Markdown heading (e.g., "## Token Validation")

    Returns:
        Slugified version (e.g., "token-validation")
    """
    # Remove markdown heading markers
    text = re.sub(r"^#+\s*", "", heading)
    # Convert to lowercase
    text = text.lower()
    # Remove special characters except alphanumeric and spaces
    text = re.sub(r"[^\w\s-]", "", text)
    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    return text


def find_markdown_heading(file_path: Path, heading: str) -> str | None:
    """Find a markdown heading in a file and return its slug.

    Args:
        file_path: Path to the markdown file
        heading: Heading to find (with or without # prefix)

    Returns:
        Slugified heading if found, None otherwise
    """
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Normalize the search heading (remove # prefix for comparison)
    search_text = re.sub(r"^#+\s*", "", heading).lower().strip()

    # Search for headings in the file
    for line in content.splitlines():
        # Check if line is a markdown heading
        match = re.match(r"^(#+)\s+(.+)$", line)
        if match:
            heading_text = match.group(2)
            # Remove any heading ID syntax {#id}
            heading_text = re.sub(r"\s*\{#[^}]+\}\s*$", "", heading_text)
            if heading_text.lower().strip() == search_text:
                return slugify_heading(line)

    return None


def find_anchor_in_file(file_path: Path, anchor: str) -> bool:
    """Check if an anchor ID exists in a file.

    Args:
        file_path: Path to the file
        anchor: Anchor ID to find

    Returns:
        True if anchor is found
    """
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False

    # Look for common anchor patterns:
    # - <a id="anchor">
    # - <a name="anchor">
    # - {#anchor} (markdown heading ID syntax)
    # - id="anchor" (HTML attribute)
    patterns = [
        rf'<a\s+id=["\']?{re.escape(anchor)}["\']?\s*>',
        rf'<a\s+name=["\']?{re.escape(anchor)}["\']?\s*>',
        rf"\{{#{re.escape(anchor)}\}}",
        rf'id=["\']?{re.escape(anchor)}["\']?',
    ]

    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def run_ripgrep(
    pattern: str,
    project_root: Path,
    file_glob: str | None = None,
    fixed_string: bool = False,
) -> str | None:
    """Run ripgrep and return the first match location.

    Args:
        pattern: Search pattern
        project_root: Root directory to search in
        file_glob: Optional glob pattern to filter files
        fixed_string: If True, treat pattern as literal string

    Returns:
        File:line string if found, None otherwise
    """
    cmd = ["rg", "--line-number", "--no-heading", "--max-count=1"]

    if fixed_string:
        cmd.append("--fixed-strings")

    if file_glob:
        cmd.extend(["--glob", file_glob])

    # Use "." as the search path and run from project_root directory
    # This makes relative globs work correctly
    cmd.append(pattern)
    cmd.append(".")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),  # Run from project root
        )
        if result.returncode == 0 and result.stdout.strip():
            # Output format: ./file:line:content
            # We want absolute path:line
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(":", 2)
            if len(parts) >= 2:
                # Convert relative path to absolute
                file_path = project_root / parts[0].lstrip("./")
                return f"{file_path}:{parts[1]}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def resolve_code_ref(ref: Ref, project_root: Path) -> str | None:
    """Resolve a code reference to a file:line location.

    Resolution tiers:
    1. Symbol lookup (if s provided)
    2. Text pattern grep (if t provided)
    3. File + line hint fallback

    Args:
        ref: Code reference to resolve
        project_root: Root directory of the project

    Returns:
        File:line string if resolved, None otherwise
    """
    file_glob = ref.f

    # Tier 1: Symbol lookup
    if ref.s:
        # Try to find class or function definition
        symbol = ref.s
        # Handle ClassName.method format
        if "." in symbol:
            parts = symbol.split(".")
            class_name = parts[0]
            method_name = parts[-1]
            # Search for the method within context of the class
            pattern = rf"(class\s+{class_name}|def\s+{method_name})"
        else:
            # Single symbol - could be class or function
            pattern = rf"(class|def|function)\s+{symbol}"

        result = run_ripgrep(pattern, project_root, file_glob)
        if result:
            return result

    # Tier 2: Text pattern grep
    if ref.t:
        result = run_ripgrep(ref.t, project_root, file_glob, fixed_string=True)
        if result:
            return result
        # Text pattern was specified but not found - don't fall back to file
        # This prevents returning false positives
        return None

    # Tier 3: File + line hint fallback (only when no symbol or text pattern)
    if ref.f and ref.line:
        # Try to resolve the file pattern to an actual file
        if "*" in ref.f or "?" in ref.f:
            # Glob pattern - find matching files
            matches = list(project_root.glob(ref.f.lstrip("*/")))
            if matches:
                return f"{matches[0]}:{ref.line}"
        else:
            # Direct path
            file_path = project_root / ref.f
            if file_path.exists():
                return f"{file_path}:{ref.line}"

    # Tier 3b: File pattern only (no line hint)
    if ref.f:
        if "*" in ref.f or "?" in ref.f:
            matches = list(project_root.glob(ref.f.lstrip("*/")))
            if matches:
                return str(matches[0])
        else:
            file_path = project_root / ref.f
            if file_path.exists():
                return str(file_path)

    return None


def resolve_doc_ref(ref: Ref, project_root: Path) -> str | None:
    """Resolve a document reference to a file#anchor location.

    Resolution tiers:
    1. Heading match (if h provided)
    2. Anchor match (if a provided)
    3. Page number (if p provided, for PDFs)
    4. Text pattern grep (if t provided)
    Fallback: File path if exists

    Args:
        ref: Document reference to resolve
        project_root: Root directory of the project

    Returns:
        File path with optional anchor/page if resolved, None otherwise
    """
    if not ref.f:
        return None

    # Resolve file pattern to actual file
    if "*" in ref.f or "?" in ref.f:
        matches = list(project_root.glob(ref.f.lstrip("*/")))
        if not matches:
            return None
        file_path = matches[0]
    else:
        file_path = project_root / ref.f
        if not file_path.exists():
            return None

    # Tier 1: Heading match
    if ref.h:
        slug = find_markdown_heading(file_path, ref.h)
        if slug:
            return f"{file_path}#{slug}"
        # Even if heading not found exactly, return file with slugified heading
        return f"{file_path}#{slugify_heading(ref.h)}"

    # Tier 2: Anchor match
    if ref.a:
        if find_anchor_in_file(file_path, ref.a):
            return f"{file_path}#{ref.a}"
        # Return anchor anyway (might be valid even if not found in simple search)
        return f"{file_path}#{ref.a}"

    # Tier 3: Page number (for PDFs)
    if ref.p:
        return f"{file_path}#page={ref.p}"

    # Tier 4: Text pattern
    if ref.t:
        # Search within the specific file
        result = run_ripgrep(ref.t, file_path.parent, file_path.name, fixed_string=True)
        if result:
            return result
        # Text pattern specified but not found - don't fall back
        return str(file_path)

    # Fallback: Just return the file path (only if no specific locator was requested)
    return str(file_path)


def resolve_ref(ref: Ref, project_root: Path) -> str | None:
    """Resolve a reference to its location.

    Args:
        ref: Reference to resolve (code or doc)
        project_root: Root directory of the project

    Returns:
        Location string if resolved, None otherwise
    """
    if ref.kind == "doc":
        return resolve_doc_ref(ref, project_root)
    else:
        return resolve_code_ref(ref, project_root)


def generate_search_hints(ref: Ref) -> list[str]:
    """Generate search command hints when resolution fails.

    These hints help users manually locate moved/changed code.

    Args:
        ref: Reference that failed to resolve

    Returns:
        List of shell commands to try
    """
    hints = []
    file_glob = ref.f if ref.f else "**/*"

    if ref.kind == "code":
        # Symbol search hints
        if ref.s:
            symbol = ref.s
            if "." in symbol:
                class_name, method_name = symbol.rsplit(".", 1)
                hints.append(f'rg "(class|def) {class_name}" --glob "{file_glob}"')
                hints.append(f'rg "def {method_name}" --glob "{file_glob}"')
            else:
                hints.append(f'rg "(class|def|function) {symbol}" --glob "{file_glob}"')

        # Text pattern hints
        if ref.t:
            # Escape special chars for shell
            escaped_pattern = ref.t.replace('"', '\\"')
            hints.append(f'rg "{escaped_pattern}" --glob "{file_glob}"')

        # Git history hints if we have a commit
        if ref.c:
            hints.append(f"git show {ref.c} -- {file_glob}")

    else:  # doc
        if ref.h:
            # Search for heading
            heading_text = re.sub(r"^#+\s*", "", ref.h)
            hints.append(f'rg "^#.*{heading_text}" --glob "{file_glob}"')

        if ref.t:
            escaped_pattern = ref.t.replace('"', '\\"')
            hints.append(f'rg "{escaped_pattern}" --glob "{file_glob}"')

        if ref.a:
            hints.append(f'rg "(id|name)=.?{ref.a}" --glob "{file_glob}"')

    # Add generic file search if we have a pattern
    if ref.f and "*" not in ref.f:
        hints.append(f'rg --files --glob "**/{Path(ref.f).name}"')

    return hints
