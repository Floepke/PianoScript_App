# keyTAB (Cairo + PySide6) — Starter

A minimal starter for an alternative music notation app using PySide6 with Cairo for rendering:
- Editor: Cairo-drawn in the GUI thread
- Toolbar: Vertical toolbar embedded into the splitter handle (entire area draggable)
- PrintView: Cairo rendering in a background thread
- PDF export via Cairo (vector)

## Setup (Linux)

```bash
# From project root
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
cd /home/flop/PianoScript_App_Cairo
source .venv/bin/activate
python keyTAB.py
```

## Debugging Viewport & Scroll

- Set environment variables before launching to enable diagnostics:
	- `PIANOSCRIPT_DEBUG_VIEWPORT=1`: draws a red border around the visible viewport to verify clipping edges remain fixed while content scrolls.
	- `PIANOSCRIPT_DEBUG_SCROLL=1`: logs scroll diagnostics: logical scroll px, device pixel ratio, `px_per_mm`, and computed `clip_y_mm`/`clip_h_mm`.

Example:

```bash
PIANOSCRIPT_DEBUG_VIEWPORT=1 PIANOSCRIPT_DEBUG_SCROLL=1 python3 keyTAB.py
```

Notes:
- Scrollbar steps auto-scale with zoom so wheel movement feels consistent at different zoom levels.
- On HiDPI displays, the widget uses device pixel ratio (`dpr`) properly by converting logical scrollbar values to device pixels for the clip calculation.

## Settings

- Location: `~/.pianoscript_settings.py` (Python file with a `settings` dict)
- Format:

```
# keyTAB settings
settings = {
		# Global UI scale factor (0.5 .. 3.0). Applied via QT_SCALE_FACTOR.
		'ui_scale': 0.75,

		# Recent files (most recent first)
		'recent_files': [
				'/path/to/file.piano',
				'/path/to/another.piano',
		],
}
```

- Notes:
	- Comments use `#` and are ignored by the parser.
	- Values are standard Python literals (bool, int, float, str, list, dict).
	- Edit → Preferences opens the file in:
		- Windows: Notepad
		- macOS: TextEdit
		- Linux: system default via `xdg-open`

## Structure

- `/keyTAB.py` — app entrypoint
- `/editor/` — app UI modules (e.g., `main_window.py`)
- `/widgets/` — reusable UI widgets and Cairo views (`draw_util.py`, `draw_view.py`, `cairo_views.py`, `toolbar_splitter.py`)
- `/file_model/` — document/data model (placeholder)

## Model Schema (early-stage)

- `SCORE` contains:
	- `meta_data`, `header`, `events`, `layout`, `editor`, and `base_grid`.
- `BaseGrid`:
	- `numerator`: time signature numerator (e.g., 4 in 4/4)
	- `denominator`: time signature denominator (e.g., 4 in 4/4)
	- `grid_positions`: list of beat indices to draw/enable within a measure.
		Beat 1 corresponds to the barline; higher numbers control visible beats.
	- `measure_amount`: number of measures using this grid.

Behavior:
- Denominator defines the smallest possible time step in the grid context.
	A denominator of 1 enforces drawing the barline (beat 1) per measure.
	Higher denominators subdivide the measure; `grid_positions` selects which beats are drawn.

Note:
- Legacy keys and automatic repairs are not applied in early stage; JSON should match the current schema.

## Notes
- The middle toolbar is implemented as a custom `QSplitterHandle`, so the whole area (outside the buttons) acts as a single splitter handle.
- The PrintView renders on a worker thread and blits the result safely in the GUI thread.
- The File > Export PDF action writes a vector PDF using Cairo.
- Soundfonts: user-provided `.sf2`/`.sf3` only. On first playback you’ll be prompted to select a file; the app remembers the choice. Or set `KEYTAB_SOUNDFONT` to an absolute path.
- Licensing: the app is MIT-licensed (`LICENSE`). Third-party notices live in `THIRD_PARTY_NOTICES.md` with full texts in `licenses/`. Packaging guidance for .exe/.app/.AppImage is in `docs/LICENSING_AND_PACKAGING.md`.
