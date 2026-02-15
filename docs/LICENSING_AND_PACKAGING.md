# Licensing and Packaging Checklist

Use this checklist when producing distributable builds (.exe, .app, .AppImage).

## Project license
- keyTAB is MIT licensed (`LICENSE`). Keep this file in every bundle.

## Third-party components
- PySide6 / Qt — LGPL-3.0. Ship Qt/PySide as dynamic libraries, not statically
  linked. Include `licenses/LGPL-3.0.txt`.
- FluidSynth — LGPL-2.1-or-later. Ship `libfluidsynth` as a dynamic library
  (DLL/.dylib/.so) that users can replace. Include `licenses/LGPL-2.1.txt`.
- No SoundFont is bundled; users supply their own `.sf2/.sf3`.
- Other Python deps (numpy, mido, pretty_midi, python-rtmidi) are permissive
  (BSD/MIT). No copyleft obligations.

## Recommended attribution text (About / NOTICE)
Include in About and/or a NOTICE file:

```
User-provided SoundFont (.sf2/.sf3)
FluidSynth — licensed under LGPL 2.1 or later
PySide6 / Qt — licensed under LGPL 3.0
```

## Soundfonts
- No soundfont is bundled. Users must choose their own `.sf2`/`.sf3` at first
  playback or set `KEYTAB_SOUNDFONT=/absolute/path/to/font.sf2`.

## Platform notes
- Windows (.exe):
  - Keep Qt, shiboken, PySide6, and `libfluidsynth.dll` as separate dynamic
    libraries. Ship `licenses/` and `THIRD_PARTY_NOTICES.md` in the install
    dir. Ensure the DLL search path finds your bundled soundfont.
- macOS (.app):
  - Place `libfluidsynth.dylib` and Qt frameworks in `Contents/Frameworks`.
    Include `licenses/` and `THIRD_PARTY_NOTICES.md` in `Contents/Resources`.
    Keep them replaceable (do not statically link FluidSynth).
- Linux (.AppImage):
  - Bundle `libfluidsynth.so` and Qt libs in the AppImage. Place
    `licenses/` and `THIRD_PARTY_NOTICES.md` inside the AppDir so they are
    accessible in the mounted image. Users supply their own soundfonts.

## How to obtain FluidSynth binaries for bundling
- Windows: build or install via vcpkg (`vcpkg install fluidsynth`), MSYS2
  (`pacman -S mingw-w64-x86_64-fluidsynth`), or download a prebuilt DLL. Copy
  `libfluidsynth-*.dll` (and its runtime deps like `libsndfile`/`glib`) next
  to your executable and keep `licenses/LGPL-2.1.txt`.
- macOS: `brew install fluidsynth` or `port install fluidsynth`, then copy
  `libfluidsynth.dylib` into `Contents/Frameworks` and fix rpaths with
  `install_name_tool`/`otool -L` as needed.
- Linux: install dev packages (`apt install libfluidsynth3` or build from
  source) and copy `libfluidsynth.so.*` into your AppDir `usr/lib`. Ensure
  the AppRun sets `LD_LIBRARY_PATH` so FluidSynth is found at runtime.

## Where to surface notices in-app
- About dialog (implemented in `ui/about_dialog.py`) shows the MIT license
  and major third-party credits (user-provided SoundFont, FluidSynth, Qt/PySide6).
- Keep `THIRD_PARTY_NOTICES.md` and `licenses/` in the bundle so users can
  view full texts.

## No legal advice
This document is informational and not legal advice.
