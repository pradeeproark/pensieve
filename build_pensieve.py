#!/usr/bin/env python3
"""Build script for creating frozen Pensieve executable with PyInstaller."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Build the Pensieve executable."""
    print("Building Pensieve executable...")

    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

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
    output_name = "pensieve"
    if platform.system() == "Windows":
        output_name = "pensieve.exe"

    # Build PyInstaller command
    print("\n2. Running PyInstaller...")

    pyinstaller_args = [
        "pyinstaller",
        "--name", "pensieve",
        "--onefile",  # Single executable
        "--console",  # Console application
        # Include the migrations package
        "--add-data", f"src/pensieve/migrations{os.pathsep}pensieve/migrations",
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

    # Check output
    output_path = project_root / "dist" / output_name
    if not output_path.exists():
        print(f"ERROR: Expected output not found at {output_path}")
        sys.exit(1)

    print(f"\n3. Build successful!")
    print(f"   Executable: {output_path}")
    print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Test the executable
    print("\n4. Testing executable...")
    test_result = subprocess.run(
        [str(output_path), "version"],
        capture_output=True,
        text=True
    )

    if test_result.returncode != 0:
        print("WARNING: Executable test failed!")
        print(test_result.stderr)
    else:
        print("   Test passed!")
        print(f"   {test_result.stdout.strip()}")

    print("\nDone! You can now distribute the executable.")
    print(f"\nTo install: copy {output_path} to a directory in your PATH")


if __name__ == "__main__":
    main()
