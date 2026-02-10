#!/usr/bin/env python3
"""Build an AppImage using PyInstaller + linuxdeploy.

Usage:
    python tools/build.py --output /path/to/out

The output directory is used for all build artifacts. After building,
only the final AppImage is kept.
"""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

LINUXDEPLOY_URL = (
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/"
    "linuxdeploy-x86_64.AppImage"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build keyTAB AppImage.")
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for build files and final AppImage.",
    )
    parser.add_argument(
        "--name",
        default="keyTAB",
        help="Executable name (default: keyTAB).",
    )
    parser.add_argument(
        "--entry",
        default="keyTAB.py",
        help="Entry script (default: keyTAB.py).",
    )
    parser.add_argument(
        "--icon-path",
        default="",
        help="Path to PNG icon to embed in the AppImage.",
    )
    parser.add_argument(
        "--extra-args",
        default="",
        help="Extra PyInstaller args (quoted string).",
    )
    return parser.parse_args()


def ensure_clean_output_dir(out_dir: Path) -> None:
    if out_dir.exists():
        if not out_dir.is_dir():
            raise SystemExit(f"Output path is not a directory: {out_dir}")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)


def cleanup_build_artifacts(*paths: Path) -> None:
    for p in paths:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    p.unlink()
                except Exception:
                    pass


def ensure_appimage_tools(tools_dir: Path) -> Path:
    tools_dir.mkdir(parents=True, exist_ok=True)
    linuxdeploy = tools_dir / "linuxdeploy.AppImage"
    if not linuxdeploy.exists():
        urlretrieve(LINUXDEPLOY_URL, linuxdeploy)
    for tool in (linuxdeploy,):
        try:
            mode = tool.stat().st_mode
            tool.chmod(mode | 0o111)
        except Exception:
            pass
    return linuxdeploy


def ensure_pip_dependency(package: str) -> None:
    try:
        __import__(package)
        return
    except Exception:
        pass

    pip3 = shutil.which("pip3")
    if not pip3:
        raise SystemExit("pip3 not found in PATH. Please install pip3.")
    cmd = [pip3, "install", package, "--break-system-packages"]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"Failed to install {package} with pip3")


def ensure_pip_requirements(project_root: Path) -> None:
    req_path = project_root / "requirements.txt"
    if not req_path.exists():
        return
    pip3 = shutil.which("pip3")
    if not pip3:
        raise SystemExit("pip3 not found in PATH. Please install pip3.")
    cmd = [pip3, "install", "-r", str(req_path), "--break-system-packages"]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit("Failed to install requirements.txt with pip3")


def _is_debian_pkg_installed(pkg: str) -> bool:
    result = subprocess.run(["dpkg", "-s", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def ensure_system_packages(packages: list[str]) -> None:
    missing = [p for p in packages if not _is_debian_pkg_installed(p)]
    if not missing:
        return
    apt_get = shutil.which("apt-get")
    if not apt_get:
        raise SystemExit("apt-get not found. Please install system packages manually.")
    subprocess.run(["sudo", apt_get, "update"], check=False)
    cmd = ["sudo", apt_get, "install", "-y", *missing]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"Failed to install system packages: {', '.join(missing)}")


def ensure_system_package_alternatives(options: list[str]) -> None:
    for pkg in options:
        if _is_debian_pkg_installed(pkg):
            return
    apt_get = shutil.which("apt-get")
    if not apt_get:
        raise SystemExit("apt-get not found. Please install system packages manually.")
    subprocess.run(["sudo", apt_get, "update"], check=False)
    for pkg in options:
        result = subprocess.run(["sudo", apt_get, "install", "-y", pkg])
        if result.returncode == 0:
            return
    raise SystemExit(f"Failed to install any of: {', '.join(options)}")


def write_desktop_file(appdir: Path, name: str) -> Path:
    desktop_dir = appdir / "usr" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = desktop_dir / f"{name}.desktop"
    desktop_path.write_text(
        "[Desktop Entry]\n"
        f"Name={name}\n"
        "Comment=Create keyTAB MIDI music notation sheets by importing MIDI or writing with the mouse.\n"
        f"Exec={name}\n"
        f"Icon={name}\n"
        "Type=Application\n"
        "Categories=Graphics;AudioVideo;Music;\n"
        "Terminal=false\n",
        encoding="utf-8",
    )
    return desktop_path


def copy_png_icon(icon_path: Path, target_path: Path) -> None:
    if not icon_path.exists():
        raise SystemExit(f"Icon not found: {icon_path}")
    if icon_path.suffix.lower() != ".png":
        raise SystemExit("Icon must be a PNG file.")
    try:
        from PIL import Image
    except Exception:
        raise SystemExit("Pillow is required to resize icon. Install via requirements.txt.")
    img = Image.open(icon_path).convert("RGBA")
    if img.size != (512, 512):
        img = img.resize((512, 512), resample=Image.LANCZOS)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(target_path, format="PNG")


def write_apprun(appdir: Path, name: str) -> Path:
    apprun = appdir / "AppRun"
    apprun.write_text(
        "#!/bin/sh\n"
        "HERE=\"$(dirname \"$(readlink -f \"$0\")\")\"\n"
        f"exec \"$HERE/usr/bin/{name}\" \"$@\"\n",
        encoding="utf-8",
    )
    try:
        mode = apprun.stat().st_mode
        apprun.chmod(mode | 0o111)
    except Exception:
        pass
    return apprun


def remove_qt_plugins_for_portability(app_bundle: Path) -> None:
    qtiff = app_bundle / "_internal" / "PySide6" / "Qt" / "plugins" / "imageformats" / "libqtiff.so"
    if qtiff.exists():
        try:
            qtiff.unlink()
        except Exception:
            pass


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    entry_script = project_root / args.entry
    if not entry_script.exists():
        raise SystemExit(f"Entry script not found: {entry_script}")

    out_dir = Path(args.output).expanduser().resolve()
    ensure_clean_output_dir(out_dir)

    if platform.system().lower() != "linux":
        raise SystemExit("AppImage builds are supported on Linux only.")
    if platform.machine().lower() not in ("x86_64", "amd64"):
        raise SystemExit("AppImage build currently supports x86_64 only.")

    ensure_system_packages(["patchelf", "desktop-file-utils", "file", "libfuse2"])
    ensure_system_package_alternatives(["libtiff5", "libtiff6"])
    ensure_pip_requirements(project_root)
    ensure_pip_dependency("PyInstaller")

    work_dir = out_dir / "_build"
    spec_dir = out_dir / "_spec"
    dist_dir = out_dir / "_dist"
    appdir = out_dir / "_appdir"
    tools_dir = out_dir / "_tools"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        f"--name={args.name}",
        f"--distpath={str(dist_dir)}",
        f"--workpath={str(work_dir)}",
        f"--specpath={str(spec_dir)}",
        str(entry_script),
    ]
    if args.extra_args.strip():
        cmd.extend(shlex.split(args.extra_args))

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(project_root))
    if result.returncode != 0:
        return result.returncode

    exe_name = args.name
    app_bundle = dist_dir / exe_name
    exe_path = app_bundle / exe_name
    if not exe_path.exists():
        raise SystemExit(f"Build succeeded but executable not found: {exe_path}")

    if appdir.exists():
        shutil.rmtree(appdir, ignore_errors=True)
    bin_dir = appdir / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    lib_app_dir = appdir / "usr" / "lib" / exe_name
    if lib_app_dir.exists():
        shutil.rmtree(lib_app_dir, ignore_errors=True)
    shutil.copytree(app_bundle, lib_app_dir)
    remove_qt_plugins_for_portability(lib_app_dir)
    launcher = bin_dir / exe_name
    if launcher.exists():
        launcher.unlink()
    launcher.symlink_to(Path("../lib") / exe_name / exe_name)

    icon_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon_path = icon_dir / f"{exe_name}.png"
    if args.icon_path:
        icon_src = Path(args.icon_path).expanduser().resolve()
    else:
        icon_src = project_root / "icons" / "pianoscript.png"
    copy_png_icon(icon_src, icon_path)

    desktop_file = write_desktop_file(appdir, exe_name)
    write_apprun(appdir, exe_name)

    linuxdeploy = ensure_appimage_tools(tools_dir)
    env = os.environ.copy()
    env["PATH"] = f"{tools_dir}:{env.get('PATH', '')}"
    env.setdefault("VERSION", "dev")
    # Avoid FUSE mount requirement when running AppImage tools.
    env.setdefault("APPIMAGE_EXTRACT_AND_RUN", "1")

    appimage_cmd = [
        str(linuxdeploy),
        "--appdir",
        str(appdir),
        "--executable",
        str(bin_dir / exe_name),
        "--desktop-file",
        str(desktop_file),
        "--icon-file",
        str(icon_path),
        "--output",
        "appimage",
    ]
    result = subprocess.run(appimage_cmd, cwd=str(out_dir), env=env)
    if result.returncode != 0:
        return result.returncode

    produced = sorted(out_dir.glob("*.AppImage"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not produced:
        raise SystemExit("AppImage build finished but no AppImage was produced.")
    final_appimage = out_dir / f"{exe_name}.AppImage"
    if final_appimage.exists():
        try:
            final_appimage.unlink()
        except Exception:
            pass
    shutil.move(str(produced[0]), str(final_appimage))
    try:
        mode = final_appimage.stat().st_mode
        final_appimage.chmod(mode | 0o111)
    except Exception:
        pass

    try:
        if exe_path.exists():
            exe_path.unlink()
    except Exception:
        pass

    cleanup_build_artifacts(work_dir, spec_dir, dist_dir, appdir, tools_dir)
    print(f"Build complete: {final_appimage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
