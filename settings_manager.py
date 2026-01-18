from __future__ import annotations
import os
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from utils.CONSTANT import UTILS_SAVE_DIR


# Paths under the user's home folder (~/ .pianoscript)
PREFERENCES_PATH: Path = Path(UTILS_SAVE_DIR) / "preferences.py"


def _ensure_dir() -> None:
    os.makedirs(UTILS_SAVE_DIR, exist_ok=True)


@dataclass
class _PrefDef:
    default: object
    description: str


class PreferencesManager:
    """Register and persist application preferences in ~/ .pianoscript/preferences.py.

    Users can edit this file; changes take effect after restarting the app.
    """

    def __init__(self, path: Path = PREFERENCES_PATH) -> None:
        self.path = path
        self._schema: Dict[str, _PrefDef] = {}
        self._values: Dict[str, object] = {}

    def register(self, key: str, default: object, description: str) -> None:
        self._schema[key] = _PrefDef(default=default, description=description)
        if key not in self._values:
            self._values[key] = default

    def get(self, key: str, default: Optional[object] = None) -> object:
        return self._values.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._values[key] = value

    def load(self) -> None:
        _ensure_dir()
        if not self.path.exists():
            # Initialize defaults and write file
            self.save()
            return
        text = self.path.read_text(encoding="utf-8")
        parsed = self._parse_py_dict(text)
        # Merge
        for k, d in self._schema.items():
            if k in parsed:
                self._values[k] = self._coerce(parsed[k], d.default)
            else:
                self._values.setdefault(k, d.default)
        for k, v in parsed.items():
            if k not in self._values:
                self._values[k] = v

    def save(self) -> None:
        _ensure_dir()
        content = self._emit_py_file(self._values)
        self.path.write_text(content, encoding="utf-8")

    def open_in_editor(self) -> None:
        _ensure_dir()
        if not self.path.exists():
            self.save()
        try:
            fpath = str(self.path)
            if os.name == "nt":
                # Always use Notepad on Windows
                subprocess.Popen(["notepad", fpath])
                return
            if sys.platform == "darwin":
                # Always use TextEdit on macOS
                subprocess.Popen(["open", "-a", "TextEdit", fpath])
                return
            if sys.platform.startswith("linux"):
                # Always and only use xdg-open on Linux
                subprocess.Popen(["xdg-open", fpath])
                return
        except Exception as e:
            # Last-resort: log to stderr to avoid crashing UI
            try:
                import sys as _sys
                print(f"Failed to open preferences editor: {e}", file=_sys.stderr)
            except Exception:
                pass

    # Internals
    def _parse_py_dict(self, text: str) -> Dict:
        import ast
        tree = ast.parse(text, filename=str(self.path), mode='exec')
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'preferences':
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            return value
                        return {}
        return {}

    def _coerce(self, value: object, default: object) -> object:
        if isinstance(default, bool):
            return bool(value)
        if isinstance(default, int):
            try:
                return int(value)
            except Exception:
                return default
        if isinstance(default, float):
            try:
                return float(value)
            except Exception:
                return default
        if isinstance(default, str):
            return str(value)
        return value

    def _emit_py_file(self, values: Dict[str, object]) -> str:
        lines: list[str] = []
        lines.append("# PianoScript preferences\n\n# You can edit this file to change the application preferences.\n# Changes take effect after restarting the app.\n")
        lines.append("preferences = {")
        indent = "    "
        order = list(self._schema.keys()) + [k for k in values.keys() if k not in self._schema]
        seen: set[str] = set()
        for k in order:
            if k in seen:
                continue
            seen.add(k)
            desc = self._schema.get(k).description if k in self._schema else ""
            if desc:
                for dline in desc.splitlines():
                    lines.append(f"{indent}# {dline}")
            v = values.get(k)
            lines.append(f"{indent}{repr(k)}: {self._format_value(v)},")
            lines.append("")
        if lines and not lines[-1].strip():
            lines.pop()
        lines.append("}")
        return "\n".join(lines)

    def _format_value(self, v: object) -> str:
        if isinstance(v, list):
            if not v:
                return "[]"
            if len(v) <= 3 and all(isinstance(x, (int, float, str)) for x in v):
                return f"[{', '.join(self._format_value(x) for x in v)}]"
            inner = ",\n".join("        " + self._format_value(x) for x in v)
            return "[\n" + inner + "\n    ]"
        if isinstance(v, dict):
            if not v:
                return "{}"
            items = []
            for kk in v:
                items.append(f"        {repr(kk)}: {self._format_value(v[kk])}")
            return "{\n" + ",\n".join(items) + "\n    }"
        if isinstance(v, str):
            return repr(v)
        if isinstance(v, (int, float, bool)):
            return str(v)
        return repr(v)


# ---- Registration hub (add new app preferences here) ----
_prefs_manager: Optional[PreferencesManager] = None


def get_preferences_manager() -> PreferencesManager:
    global _prefs_manager
    if _prefs_manager is None:
        pm = PreferencesManager(PREFERENCES_PATH)
        # Register known preferences here
        pm.register("ui_scale", 1.0, "Global UI scale: (0.5 .. 3.0)")
        pm.register("theme", "light", "UI theme: ('light' | 'dark')")
        pm.register("editor_fps_limit", 30, "Max mouse-move dispatch rate (FPS). Set 0 to disable throttling.")
        pm.load()
        _prefs_manager = pm
    return _prefs_manager


def get_preferences() -> Dict:
    return get_preferences_manager()._values


def open_preferences() -> None:
    get_preferences_manager().open_in_editor()
