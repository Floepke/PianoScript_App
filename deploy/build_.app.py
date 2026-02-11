#!/usr/bin/env python3
"""Build a macOS executable of keyTAB using PyInstaller.

This script keeps the build artifacts confined to the specified output directory
and removes the temporary clutter, leaving only the final executable behind.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ENTRY = PROJECT_ROOT / "keyTAB.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a macOS executable with PyInstaller.")
    parser.add_argument(
        "--entry",
        type=Path,
        default=DEFAULT_ENTRY,
        help="Path to the Python entry point (default: keyTAB.py).",
    )
    parser.add_argument(
        "--name",
        default="keyTAB",
        help="Executable name to produce (default: keyTAB).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "build" / "macos",
        help="Directory where the build runs and the final executable is stored.",
    )
    return parser.parse_args()


def ensure_pyinstaller_available() -> None:
    try:
        import PyInstaller  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "PyInstaller is not installed. Install it first, e.g. 'pip install pyinstaller'."
        ) from exc


def run_pyinstaller(entry: Path, name: str, work_dir: Path) -> Path:
    entry_path = entry.resolve()
    if not entry_path.exists():
        raise SystemExit(f"Entry file not found: {entry_path}")

    work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        name,
        str(entry_path),
    ]

    print(f"Running: {' '.join(cmd)} (cwd={work_dir})")
    subprocess.run(cmd, cwd=work_dir, check=True)

    produced = work_dir / "dist" / name
    if sys.platform == "darwin":
        # PyInstaller may append .app for GUI builds; handle either case.
        if not produced.exists():
            app_path = produced.with_suffix(".app")
            if app_path.exists():
                produced = app_path
    if not produced.exists():
        raise SystemExit("PyInstaller finished but the executable was not found.")

    final_target = work_dir / produced.name
    # If the executable already exists, overwrite it to keep the directory clean.
    if final_target.exists():
        if final_target.is_dir():
            shutil.rmtree(final_target)
        else:
            final_target.unlink()
    shutil.move(str(produced), final_target)
    return final_target


def clean_pyinstaller_artifacts(work_dir: Path, name: str) -> None:
    for folder in (work_dir / "build", work_dir / "dist"):
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
    spec_file = work_dir / f"{name}.spec"
    if spec_file.exists():
        spec_file.unlink()


def main() -> None:
    args = parse_args()
    ensure_pyinstaller_available()

    work_dir = args.output_dir.resolve()
    result_path: Path | None = None

    try:
        result_path = run_pyinstaller(args.entry, args.name, work_dir)
        print(f"Executable created at: {result_path}")
    finally:
        clean_pyinstaller_artifacts(work_dir, args.name)
        print(f"Cleaned PyInstaller artifacts in {work_dir}.")


if __name__ == "__main__":
    main()
