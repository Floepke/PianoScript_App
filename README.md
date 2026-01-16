# PianoScript (Cairo + PySide6) — Starter

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
python pianoscript.py
```

## Settings

- Location: `~/.pianoscript_settings.py` (Python file with a `settings` dict)
- Format:

```
# PianoScript settings
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

- `/pianoscript.py` — app entrypoint
- `/editor/` — app UI modules (e.g., `main_window.py`)
- `/widgets/` — reusable UI widgets and Cairo views (`draw_util.py`, `draw_view.py`, `cairo_views.py`, `toolbar_splitter.py`)
- `/file_model/` — document/data model (placeholder)

## Notes
- The middle toolbar is implemented as a custom `QSplitterHandle`, so the whole area (outside the buttons) acts as a single splitter handle.
- The PrintView renders on a worker thread and blits the result safely in the GUI thread.
- The File > Export PDF action writes a vector PDF using Cairo.
