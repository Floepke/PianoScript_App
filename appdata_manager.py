from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from utils.CONSTANT import UTILS_SAVE_DIR

APPDATA_PATH: Path = Path(UTILS_SAVE_DIR) / "appdata.py"


def _ensure_dir() -> None:
    os.makedirs(UTILS_SAVE_DIR, exist_ok=True)


@dataclass
class _DataDef:
    default: object
    description: str


class AppDataManager:
    """Register and persist application data (non-preferences) in ~/ .keyTAB/appdata.py.

    This is for runtime-managed data such as recent files, last session info, etc.
    """

    def __init__(self, path: Path = APPDATA_PATH) -> None:
        self.path = path
        self._schema: Dict[str, _DataDef] = {}
        self._values: Dict[str, object] = {}

    def register(self, key: str, default: object, description: str) -> None:
        self._schema[key] = _DataDef(default=default, description=description)
        if key not in self._values:
            self._values[key] = default

    def get(self, key: str, default: Optional[object] = None) -> object:
        return self._values.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._values[key] = value

    def load(self) -> None:
        _ensure_dir()
        if not self.path.exists():
            self.save()
            return
        text = self.path.read_text(encoding="utf-8")
        parsed = self._parse_py_dict(text)
        for k, d in self._schema.items():
            if k in parsed:
                self._values[k] = parsed[k]
            else:
                self._values.setdefault(k, d.default)
        for k, v in parsed.items():
            if k not in self._values:
                self._values[k] = v

    def save(self) -> None:
        _ensure_dir()
        content = self._emit_py_file(self._values)
        self.path.write_text(content, encoding="utf-8")

    # Internals
    def _parse_py_dict(self, text: str) -> Dict:
        import ast
        tree = ast.parse(text, filename=str(self.path), mode='exec')
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'appdata':
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            return value
                        return {}
        return {}

    def _emit_py_file(self, values: Dict[str, object]) -> str:
        lines: list[str] = []
        lines.append("# keyTAB app data\n\n# Application-managed data. Editing is possible but it's not meant for that.")
        lines.append("appdata = {")
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
            inner = ", ".join(repr(x) for x in v)
            return f"[{inner}]"
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


# ---- Registration hub (add app data keys here) ----
_appdata_manager: Optional[AppDataManager] = None


def get_appdata_manager() -> AppDataManager:
    global _appdata_manager
    if _appdata_manager is None:
        adm = AppDataManager(APPDATA_PATH)
        # Register known app data here (not user preferences)
        adm.register("recent_files", [], "List of recently opened files (most recent first)")
        adm.register("last_opened_file", "", "Absolute path to the last opened/saved project file")
        adm.register("last_file_dialog_dir", "", "Last directory used in file open/save dialogs")
        adm.register("snap_base", 8, "Last selected snap base (1,2,4,8,...) for editor snapping")
        adm.register("snap_divide", 1, "Last selected snap divide (tuplets factor) for editor snapping")
        adm.register("selected_tool", "note", "Last selected tool name in the tool selector")
        # MIDI output port preference
        adm.register("midi_out_port", "", "Last selected external MIDI output port name")
        # Playback backend selection
        adm.register("playback_type", "midi_port", "Playback backend: 'midi_port' or 'internal_synth'")
        # Internal synth settings (stored as lists of floats)
        adm.register("synth_left_wavetable", [], "Left wavetable samples for internal synth (float list)")
        adm.register("synth_right_wavetable", [], "Right wavetable samples for internal synth (float list)")
        adm.register("synth_attack", 0.005, "Synth attack time (seconds)")
        adm.register("synth_decay", 0.05, "Synth decay time (seconds)")
        adm.register("synth_sustain", 0.6, "Synth sustain level (0..1)")
        adm.register("synth_release", 0.1, "Synth release time (seconds)")
        adm.register("synth_gain", 0.35, "Synth master gain (0..1.5)")
        # Audio output device name for internal synth (sounddevice)
        adm.register("audio_output_device", "", "Preferred audio output device name for internal synth")
        # Session restore preferences
        adm.register("last_session_saved", False, "Whether the last session at exit was saved to a project file")
        adm.register("last_session_path", "", "Project file path associated with the last session if it was saved")
        # Synth-related appdata removed: wavetable and ADSR are no longer used
        # Window state (session-managed)
        adm.register("window_maximized", True, "Start maximized; updated on exit")
        adm.register("window_geometry", "", "Base64-encoded Qt window geometry for normal state")
        # Removed window_state persistence to avoid saving/restoring dock/toolbar layout
        adm.load()
        # Strip any legacy 'window_state' key from stored values
        try:
            adm._values.pop("window_state", None)
        except Exception:
            pass
        _appdata_manager = adm
    return _appdata_manager
