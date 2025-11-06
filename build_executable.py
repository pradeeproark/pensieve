#!/usr/bin/env python3
"""Build script for creating frozen Pensieve executable with PyInstaller."""

import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform_name() -> str:
    """Get platform name for binary filename."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    else:
        return system.lower()


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main() -> None:
    """Build the Pensieve executable."""
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Import version from package (requires package to be installed)
    try:
        # First try to install the package in development mode
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."], capture_output=True, check=True
        )
        from pensieve import __version__

        version = __version__
    except Exception as e:
        print(f"WARNING: Could not import version from package: {e}")
        print("         Using fallback: reading pyproject.toml")
        # Fallback: simple parsing of pyproject.toml
        try:
            with open(project_root / "pyproject.toml") as f:
                for line in f:
                    if line.startswith("version ="):
                        version = line.split("=")[1].strip().strip('"')
                        break
                else:
                    version = "0.1.0"
        except Exception:
            version = "0.1.0"

    print(f"Building Pensieve v{version} executable...")

    # Clean previous builds
    print("\n1. Cleaning previous builds...")
    for path in ["build", "dist", "pensieve.spec"]:
        path_obj = project_root / path
        if path_obj.exists():
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
            else:
                path_obj.unlink()
            print(f"   Removed {path}")

    # Determine output name based on platform
    platform_name = get_platform_name()
    base_name = f"pensieve-{version}-{platform_name}"
    pyinstaller_output = "pensieve"

    if platform.system() == "Windows":
        pyinstaller_output = "pensieve.exe"
        final_output = f"{base_name}.exe"
    else:
        final_output = base_name

    # Build PyInstaller command
    print("\n2. Running PyInstaller...")

    pyinstaller_args = [
        "pyinstaller",
        "--name",
        "pensieve",
        "--onefile",  # Single executable
        "--console",  # Console application
        # Include the migrations package
        "--add-data",
        f"src/pensieve/migrations{os.pathsep}pensieve/migrations",
        # Entry point
        "src/pensieve/cli.py",
    ]

    # Run PyInstaller
    result = subprocess.run(pyinstaller_args, capture_output=True, text=True)

    if result.returncode != 0:
        print("ERROR: PyInstaller failed!")
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print("   PyInstaller completed successfully")

    # Rename output to include version and platform
    pyinstaller_path = project_root / "dist" / pyinstaller_output
    final_path = project_root / "dist" / final_output

    if not pyinstaller_path.exists():
        print(f"ERROR: Expected output not found at {pyinstaller_path}")
        sys.exit(1)

    print("\n3. Renaming executable with version and platform...")
    pyinstaller_path.rename(final_path)
    print(f"   Renamed to: {final_output}")

    # Calculate and save SHA256 checksum
    print("\n4. Generating SHA256 checksum...")
    checksum = calculate_sha256(final_path)
    checksum_file = final_path.with_suffix(final_path.suffix + ".sha256")

    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  {final_output}\n")

    print(f"   SHA256: {checksum}")
    print(f"   Saved to: {checksum_file.name}")

    print("\n5. Build successful!")
    print(f"   Executable: {final_path}")
    print(f"   Size: {final_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Test the executable
    print("\n6. Testing executable...")
    test_result = subprocess.run([str(final_path), "version"], capture_output=True, text=True)

    if test_result.returncode != 0:
        print("WARNING: Executable test failed!")
        print(test_result.stderr)
    else:
        print("   Test passed!")
        print(f"   {test_result.stdout.strip()}")

    print("\nDone! You can now distribute the executable.")
    print("\nFiles created:")
    print(f"  - {final_path}")
    print(f"  - {checksum_file}")
    print("\nFor Homebrew formula, use:")
    print(
        f"  url: https://github.com/pradeeproark/pensieve/releases/download/v{version}/{final_output}"
    )
    print(f"  sha256: {checksum}")


if __name__ == "__main__":
    main()
