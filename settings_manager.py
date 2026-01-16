from __future__ import annotations
from __future__ import annotations
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

# Store settings in the actual user's home directory as a Python file with a dict literal.
# Examples:
#   Linux:   /home/<user>/.pianoscript_settings.py
#   Windows: C:\\Users\\<user>\\.pianoscript_settings.py
#   macOS:   /Users/<user>/.pianoscript_settings.py
DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".pianoscript_settings.py")


@dataclass
class _SettingDef:
    default: object
    description: str


class SettingsManager:
    """Manages app settings stored as a Python dict in a `.py` file.

    File format example (~/.pianoscript_settings.py):

        # PianoScript settings
        # Global UI scale factor (0.5 .. 3.0)
        settings = {
            # Global UI scale factor (0.5 .. 3.0). Applied via QT_SCALE_FACTOR.
            'ui_scale': 0.75,

            # Recent files list (most recent first)
            'recent_files': [
                '/path/to/file.piano',
                '/path/to/another.piano',
            ],
        }

    Comments use `#` and do not affect parsing; the dict literal is parsed via ast.literal_eval for safety.
    """

    def __init__(self, path: str = DEFAULT_PATH) -> None:
        self.path = path
        self._schema: dict[str, _SettingDef] = {}
        self._values: dict[str, object] = {}

    # ---- API ----
    def register(self, key: str, default: object, description: str) -> None:
        self._schema[key] = _SettingDef(default=default, description=description)
        if key not in self._values:
            self._values[key] = default

    def get(self, key: str, default: Optional[object] = None) -> object:
        return self._values.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._values[key] = value

    def load(self) -> None:
        self._ensure_dir()
        if not os.path.exists(self.path):
            # Initialize with defaults and write file
            for k, d in self._schema.items():
                self._values.setdefault(k, d.default)
            self.save()
            return
        try:
            text = self._read_text(self.path)
            parsed = self._parse_py_settings(text)
            # Merge with defaults
            for k, d in self._schema.items():
                if k in parsed:
                    self._values[k] = self._coerce_to_type(parsed[k], d.default)
                else:
                    self._values.setdefault(k, d.default)
            # Preserve unknown keys
            for k, v in parsed.items():
                if k not in self._values:
                    self._values[k] = v
        except Exception:
            # On error, keep defaults and rewrite
            for k, d in self._schema.items():
                self._values.setdefault(k, d.default)
            self.save()

    def save(self) -> None:
        self._ensure_dir()
        content = self._emit_py_settings(self._values)
        self._write_text(self.path, content)

    def open_preferences(self) -> None:
        if not os.path.exists(self.path):
            self.save()
        if sys.platform.startswith("linux"):
            try:
                subprocess.Popen(["xdg-open", self.path])
            except Exception:
                pass
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self.path])
        elif os.name == "nt":
            try:
                os.startfile(self.path)  # type: ignore[attr-defined]
            except Exception:
                subprocess.Popen(["notepad.exe", self.path])

    # ---- internals ----
    def _ensure_dir(self):
        d = os.path.dirname(self.path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def _read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_text(self, path: str, text: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def _parse_py_settings(self, text: str) -> dict[str, object]:
        """Parse a Python file containing a top-level `settings = {...}` dict.

        Uses `ast.literal_eval` for safety and ignores all comments.
        """
        import ast
        tree = ast.parse(text, filename=self.path, mode='exec')
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'settings':
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            return value
                        return {}
        return {}

    # No per-value parser needed; values come from Python literal evaluation.

    def _coerce_to_type(self, value: object, default: object) -> object:
        # Keep parsed type unless default demands a specific type
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

    def _emit_py_settings(self, values: dict[str, object]) -> str:
        """Emit a Python file with a `settings = { ... }` dict and comments."""
        lines: list[str] = []
        lines.append("# PianoScript settings")
        lines.append("settings = {")

        indent = "    "
        # Write schema keys first (with descriptions), then unknown keys in stable order
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
            lines.append(f"{indent}{self._format_py_key(k)}: {self._format_py_value(v)},")
            lines.append("")

        # Remove trailing blank line
        if lines and not lines[-1].strip():
            lines.pop()
        lines.append("}")
        return "\n".join(lines)

    def _format_py_key(self, k: str) -> str:
        return repr(k)

    def _format_py_value(self, v: object) -> str:
        # Pretty-print lists on multiple lines when long
        if isinstance(v, list):
            if not v:
                return "[]"
            if len(v) <= 3 and all(isinstance(x, (int, float, str)) for x in v):
                return f"[{', '.join(self._format_py_value(x) for x in v)}]"
            inner = ",\n".join("        " + self._format_py_value(x) for x in v)
            return "[\n" + inner + "\n    ]"
        if isinstance(v, dict):
            if not v:
                return "{}"
            items = []
            for kk in v:
                items.append(f"        {self._format_py_key(kk)}: {self._format_py_value(v[kk])}")
            return "{\n" + ",\n".join(items) + "\n    }"
        if isinstance(v, str):
            return repr(v)
        if isinstance(v, (int, float, bool)):
            return str(v)
        # Fallback to repr
        return repr(v)


# ---- Registration hub (add new app settings here) ----
_settings: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Singleton accessor; register all app settings here for overview."""
    global _settings
    if _settings is None:
        sm = SettingsManager(DEFAULT_PATH)
        
        # Here are all global settings of the application:
        sm.register(
            key="ui_scale",
            default=0.75,
            description="Global UI scale factor (0.5 .. 3.0).\nApplied via QT_SCALE_FACTOR before QApplication is created."
        )
        sm.register(
            key="theme",
            default="light",
            description="UI theme: light | dark"
        )
        sm.register(
            key="recent_files",
            default=[],
            description="Comma-separated list of recently opened files."
        )
        sm.load()
        _settings = sm
    return _settings
