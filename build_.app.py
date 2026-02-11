#!/usr/bin/env python3
"""Build a signed macOS .app bundle for keyTAB using PyInstaller.

The script runs PyInstaller inside a dedicated output directory, ensures a .app
bundle is produced (not a CLI binary), embeds the project icon, and cleans up all
intermediate artifacts so only the resulting .app remains.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ENTRY = PROJECT_ROOT / "keyTAB.py"
DEFAULT_ICON = PROJECT_ROOT / "icons" / "keyTAB.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a macOS .app bundle with PyInstaller.")
    parser.add_argument(
        "--entry",
        type=Path,
        default=DEFAULT_ENTRY,
        help="Path to the Python entry point (default: keyTAB.py).",
    )
    parser.add_argument(
        "--name",
        default="keyTAB",
        help="Name for the resulting .app bundle (default: keyTAB).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "build" / "macos",
        help="Directory where PyInstaller runs and where the final .app is stored.",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        default=DEFAULT_ICON,
        help="Path to an icon image (PNG or ICNS) to embed into the app bundle.",
    )
    return parser.parse_args()


def ensure_command(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"Required command '{name}' was not found in PATH.")
    return path


def prepare_icon(icon_path: Path, work_dir: Path) -> tuple[Path, bool]:
    icon_path = icon_path.resolve()
    if not icon_path.exists():
        raise SystemExit(f"Icon not found: {icon_path}")
    if icon_path.suffix.lower() == ".icns":
        return icon_path, False

    sips = ensure_command("sips")
    iconutil = ensure_command("iconutil")

    iconset_dir = work_dir / "keytab.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir(parents=True, exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512]
    for size in sizes:
        for scale in (1, 2):
            px = size * scale
            suffix = "@2x" if scale == 2 else ""
            out_file = iconset_dir / f"icon_{size}x{size}{suffix}.png"
            subprocess.run(
                [sips, "-z", str(px), str(px), str(icon_path), "--out", str(out_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    icns_path = work_dir / "keytab.icns"
    subprocess.run(
        [iconutil, "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    shutil.rmtree(iconset_dir, ignore_errors=True)
    return icns_path, True


def run_pyinstaller(entry: Path, name: str, work_dir: Path, icon: Path) -> Path:
    entry_path = entry.resolve()
    if not entry_path.exists():
        raise SystemExit(f"Entry file not found: {entry_path}")

    work_dir.mkdir(parents=True, exist_ok=True)
    icon_to_use, generated = prepare_icon(icon, work_dir)

    python_cmd = ensure_command("python3")
    cmd = [
        python_cmd,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        name,
        "--icon",
        str(icon_to_use),
        str(entry_path),
    ]

    print(f"Running: {' '.join(cmd)} (cwd={work_dir})")
    try:
        subprocess.run(cmd, cwd=work_dir, check=True)
    finally:
        if generated and icon_to_use.exists():
            icon_to_use.unlink()

    produced = work_dir / "dist" / f"{name}.app"
    if not produced.exists():
        raise SystemExit("PyInstaller finished but the .app bundle was not found.")

    final_target = work_dir / f"{name}.app"
    if final_target.exists():
        shutil.rmtree(final_target, ignore_errors=True)
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
    work_dir = args.output_dir.resolve()

    result_path: Path | None = None
    try:
        result_path = run_pyinstaller(args.entry, args.name, work_dir, args.icon)
        print(f"App bundle created at: {result_path}")
    finally:
        clean_pyinstaller_artifacts(work_dir, args.name)
        print(f"Cleaned PyInstaller artifacts in {work_dir}.")

    if result_path is None or not result_path.exists():
        raise SystemExit("Build failed: .app bundle missing after cleanup.")


if __name__ == "__main__":
    if sys.platform != "darwin":
        print("Warning: This script is intended to run on macOS (darwin).", file=sys.stderr)
    main()
