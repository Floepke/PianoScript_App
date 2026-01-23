

# my json structure design for *.piano files.
from __future__ import annotations
from dataclasses import dataclass, field, fields, MISSING
from typing import List, get_args, get_origin, get_type_hints
import json
from datetime import datetime

from file_model.events.note import Note
from file_model.events.grace_note import GraceNote
from file_model.events.pedal import Pedal
from file_model.events.text import Text
from file_model.events.slur import Slur
from file_model.events.beam import Beam
from file_model.events.start_repeat import StartRepeat
from file_model.events.end_repeat import EndRepeat
from file_model.events.count_line import CountLine
from file_model.events.line_break import LineBreak
from file_model.layout import Layout
from utils.CONSTANT import GRACENOTE_THRESHOLD
from file_model.base_grid import BaseGrid


@dataclass
class EditorSettings:
	"""Editor-specific settings for the piano-roll style editor.

	- zoom_mm_per_quarter: how many millimeters a quarter note occupies vertically.
	"""
	zoom_mm_per_quarter: float = 25.0



@dataclass
class MetaData:
	description: str = 'This is a .piano score file created with keyTAB.'
	creator: str = 'keyTAB'
	version: int = 1
	extension: str = '.piano'
	format: str = 'json'
	creation_timestamp: str = ''
	modification_timestamp: str = ''


@dataclass
class Header:
	title: str = 'title'
	composer: str = 'composer'
	arranger: str = 'arranger'
	lyricist: str = 'lyricist'
	copyright: str = 'copyright'


@dataclass
class Events:
	note: List[Note] = field(default_factory=list)
	grace_note: List[GraceNote] = field(default_factory=list)
	pedal: List[Pedal] = field(default_factory=list)
	text: List[Text] = field(default_factory=list)
	slur: List[Slur] = field(default_factory=list)
	beam: List[Beam] = field(default_factory=list)
	start_repeat: List[StartRepeat] = field(default_factory=list)
	end_repeat: List[EndRepeat] = field(default_factory=list)
	count_line: List[CountLine] = field(default_factory=list)
	line_break: List[LineBreak] = field(default_factory=list)


@dataclass
class SCORE:
	meta_data: MetaData = field(default_factory=MetaData)
	header: Header = field(default_factory=Header)
	base_grid: List[BaseGrid] = field(default_factory=list)
	events: Events = field(default_factory=Events)
	layout: Layout = field(default_factory=Layout)
	editor: EditorSettings = field(default_factory=EditorSettings)
	_next_id: int = 1

	# ---- Builders (ensure unique id) ----
	def _gen_id(self) -> int:
		i = self._next_id
		self._next_id += 1
		return i

	def new_note(self, **kwargs) -> Note:
		base = {'pitch': 40, 'time': 0.0, 'duration': 100.0, 'hand': '<'}
		base.update(kwargs)
		obj = Note(**base, id=self._gen_id())
		self.events.note.append(obj)
		return obj

	def new_grace_note(self, **kwargs) -> GraceNote:
		base = {'pitch': 41, 'time': 50.0}
		base.update(kwargs)
		obj = GraceNote(**base, id=self._gen_id())
		self.events.grace_note.append(obj)
		return obj

	def new_pedal(self, **kwargs) -> Pedal:
		base = {'type': 'v', 'time': 0.0}
		base.update(kwargs)
		obj = Pedal(**base, id=self._gen_id())
		self.events.pedal.append(obj)
		return obj

	def new_text(self, **kwargs) -> Text:
		base = {'text': '120/4', 'time': 0.0, 'side': '<', 'mm_from_side': 5.0, 'rotated': True}
		base.update(kwargs)
		obj = Text(**base, id=self._gen_id())
		self.events.text.append(obj)
		return obj

	def new_slur(self, **kwargs) -> Slur:
		# Default slur: straight line at c4 (0 semitone offset) over a short time window
		base = {
			'x1_semitones_c4': 0, 'y1_time': 0.0,
			'x2_semitones_c4': 0, 'y2_time': 25.0,
			'x3_semitones_c4': 0, 'y3_time': 75.0,
			'x4_semitones_c4': 0, 'y4_time': 100.0,
		}
		base.update(kwargs)
		obj = Slur(**base, id=self._gen_id())
		self.events.slur.append(obj)
		return obj

	def new_beam(self, **kwargs) -> Beam:
		base = {'time': 0.0, 'duration': 100.0, 'hand': '<'}
		base.update(kwargs)
		obj = Beam(**base, id=self._gen_id())
		self.events.beam.append(obj)
		return obj

	def new_start_repeat(self, **kwargs) -> StartRepeat:
		base = {'time': 0.0}
		base.update(kwargs)
		obj = StartRepeat(**base, id=self._gen_id())
		self.events.start_repeat.append(obj)
		return obj

	def new_end_repeat(self, **kwargs) -> EndRepeat:
		base = {'time': 0.0}
		base.update(kwargs)
		obj = EndRepeat(**base, id=self._gen_id())
		self.events.end_repeat.append(obj)
		return obj

	def new_count_line(self, **kwargs) -> CountLine:
		base = {'time': 0.0, 'pitch1': 40, 'pitch2': 44}
		base.update(kwargs)
		obj = CountLine(**base, id=self._gen_id())
		self.events.count_line.append(obj)
		return obj


	def new_line_break(self, **kwargs) -> LineBreak:
		base = {'time': 0.0, 'margin_mm': [0.0, 0.0], 'stave_range': [0, 0]}
		base.update(kwargs)
		obj = LineBreak(**base, id=self._gen_id())
		self.events.line_break.append(obj)
		return obj

	# ---- Dict conversion ----
	def get_dict(self) -> dict:
		def to_dict(obj):
			if isinstance(obj, list):
				return [to_dict(x) for x in obj]
			if hasattr(obj, "__dataclass_fields__"):
				out = {}
				for k in obj.__dataclass_fields__.keys():
					# Skip private/internal fields like _next_id
					if k.startswith('_'):
						continue
					out[k] = to_dict(getattr(obj, k))
				return out
			return obj
		return to_dict(self)

	# ---- Persistence ----
	def save(self, path: str) -> None:
		# Update modification timestamp before writing
		self.meta_data.modification_timestamp = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(self.get_dict(), f, indent=4, ensure_ascii=False)

	def load(self, path: str) -> "SCORE":
		with open(path, 'r', encoding='utf-8') as f:
			data = json.load(f)

		# Helper: compute dataclass defaults (respecting default_factory)
		def _defaults_for(dc_type):
			defaults = {}
			for f in fields(dc_type):
				if f.name.startswith('_'):
					continue
				if f.default is not MISSING:
					defaults[f.name] = f.default
				elif f.default_factory is not MISSING:  # type: ignore[attr-defined]
					defaults[f.name] = f.default_factory()
				else:
					defaults[f.name] = None
			return defaults

		# Helper: merge incoming dict with dataclass defaults and report repairs
		def _merge_with_defaults(dc_type, incoming: dict, context: str, skip_keys: set = {'id'}) -> dict:
			incoming = incoming or {}
			defaults = _defaults_for(dc_type)
			# Only keep keys that exist on the dataclass and are not skipped
			filtered = {k: v for k, v in incoming.items() if k in defaults and k not in skip_keys}
			merged = {**defaults, **filtered}
			return merged
		# Meta/Header
		md = data.get('meta_data', {})
		self.meta_data = MetaData(**_merge_with_defaults(MetaData, md, 'meta_data'))
		hd = data.get('header', {})
		self.header = Header(**_merge_with_defaults(Header, hd, 'header'))
		# Base grid: at least one
		bg_list = data.get('base_grid', [])
		if isinstance(bg_list, list) and bg_list:
			self.base_grid = [
				BaseGrid(**_merge_with_defaults(BaseGrid, item if isinstance(item, dict) else {}, f'base_grid[{i}]'))
				for i, item in enumerate(bg_list)
			]
		else:
			self.base_grid = [BaseGrid(**_merge_with_defaults(BaseGrid, {}, 'base_grid[0]'))]
		# Layout: simple dataclass-merge with defaults, no legacy migration
		lay = data.get('layout', {}) or {}
		self.layout = Layout(**_merge_with_defaults(Layout, lay, 'layout'))

		# Editor settings (optional)
		ed = data.get('editor', {}) or {}
		self.editor = EditorSettings(**_merge_with_defaults(EditorSettings, ed, 'editor'))

		# Events lists: generic loader based on Events dataclass field types
		ev = data.get('events', {}) or {}
		self.events = Events()
		self._next_id = 1
		# Resolve postponed annotations (from __future__ import annotations)
		_ev_hints = {}
		try:
			_ev_hints = get_type_hints(Events, globals(), locals())
		except Exception:
			_ev_hints = {}
		for f_ev in fields(Events):
			# Expect typing like List[Note]; resolve element type from hints
			ann = _ev_hints.get(f_ev.name, f_ev.type)
			origin = get_origin(ann)
			args = get_args(ann)
			elem_type = args[0] if origin is list or origin is List else None
			if elem_type is None:
				continue
			name = f_ev.name
			items = ev.get(name, []) or []
			if not isinstance(items, list):
				continue
			lst = getattr(self.events, name)
			for idx, item in enumerate(items):
				incoming = item if isinstance(item, dict) else {}
				obj = elem_type(**_merge_with_defaults(elem_type, incoming, f'events.{name}[{idx}]'))
				# Assign sequential id regardless of incoming value
				try:
					setattr(obj, 'id', self._gen_id())
				except Exception:
					pass
				lst.append(obj)

		# Normalize hand values across events to '<' or '>' (repair legacy 'l'/'r')
		try:
			# Convert very short notes to grace notes and normalize hand values
			converted_grace: List[GraceNote] = []
			remaining_notes: List[Note] = []
			for n in getattr(self.events, 'note', []) or []:
				h = str(getattr(n, 'hand', '<') or '<').strip()
				if h.lower() == 'l':
					setattr(n, 'hand', '<')
				elif h.lower() == 'r':
					setattr(n, 'hand', '>')
				elif h not in ('<', '>'):
					setattr(n, 'hand', '<')
				# Convert to grace note if shorter than threshold
				try:
					du = float(getattr(n, 'duration', 0.0) or 0.0)
					if du < float(GRACENOTE_THRESHOLD):
						converted_grace.append(GraceNote(pitch=int(getattr(n, 'pitch', 40) or 40), time=float(getattr(n, 'time', 0.0) or 0.0)))
					else:
						remaining_notes.append(n)
				except Exception:
					remaining_notes.append(n)
			# Replace lists: keep remaining notes, append converted grace notes via builder to assign ids
			self.events.note = remaining_notes
			for g in converted_grace:
				self.new_grace_note(pitch=int(g.pitch), time=float(g.time))
			for b in getattr(self.events, 'beam', []) or []:
				h = str(getattr(b, 'hand', '<') or '<').strip()
				if h.lower() == 'l':
					setattr(b, 'hand', '<')
				elif h.lower() == 'r':
					setattr(b, 'hand', '>')
				elif h not in ('<', '>'):
					setattr(b, 'hand', '<')
		except Exception:
			pass

		return self

	@classmethod
	def from_dict(cls, data: dict) -> "SCORE":
		"""Construct a SCORE from its dict representation (like load, but in-memory)."""
		self = cls()

		from dataclasses import fields, MISSING
		from typing import List, get_args, get_origin, get_type_hints

		def _defaults_for(dc_type):
			defaults = {}
			for f in fields(dc_type):
				if f.name.startswith('_'):
					continue
				if f.default is not MISSING:
					defaults[f.name] = f.default
				elif getattr(f, 'default_factory', MISSING) is not MISSING:  # type: ignore[attr-defined]
					defaults[f.name] = f.default_factory()
				else:
					defaults[f.name] = None
			return defaults

		def _merge_with_defaults(dc_type, incoming: dict, context: str, skip_keys: set = {'id'}) -> dict:
			incoming = incoming or {}
			defaults = _defaults_for(dc_type)
			filtered = {k: v for k, v in incoming.items() if k in defaults and k not in skip_keys}
			merged = {**defaults, **filtered}
			return merged

		# Meta/Header
		md = (data or {}).get('meta_data', {})
		self.meta_data = MetaData(**_merge_with_defaults(MetaData, md, 'meta_data'))
		hd = (data or {}).get('header', {})
		self.header = Header(**_merge_with_defaults(Header, hd, 'header'))

		# Base grid
		bg_list = (data or {}).get('base_grid', [])
		if isinstance(bg_list, list) and bg_list:
			self.base_grid = [
				BaseGrid(**_merge_with_defaults(BaseGrid, item if isinstance(item, dict) else {}, f'base_grid[{i}]'))
				for i, item in enumerate(bg_list)
			]
		else:
			self.base_grid = [BaseGrid(**_merge_with_defaults(BaseGrid, {}, 'base_grid[0]'))]

		# Layout
		lay = (data or {}).get('layout', {}) or {}
		self.layout = Layout(**_merge_with_defaults(Layout, lay, 'layout'))

		# Editor settings
		ed = (data or {}).get('editor', {}) or {}
		self.editor = EditorSettings(**_merge_with_defaults(EditorSettings, ed, 'editor'))

		# Events
		ev = (data or {}).get('events', {}) or {}
		self.events = Events()
		self._next_id = 1
		# Resolve postponed annotations
		try:
			_ev_hints = get_type_hints(Events, globals(), locals())
		except Exception:
			_ev_hints = {}
		for f_ev in fields(Events):
			ann = _ev_hints.get(f_ev.name, f_ev.type)
			origin = get_origin(ann)
			args = get_args(ann)
			elem_type = args[0] if origin is list or origin is List else None
			if elem_type is None:
				continue
			name = f_ev.name
			items = ev.get(name, []) or []
			if not isinstance(items, list):
				continue
			lst = getattr(self.events, name)
			for idx, item in enumerate(items):
				incoming = item if isinstance(item, dict) else {}
				obj = elem_type(**_merge_with_defaults(elem_type, incoming, f'events.{name}[{idx}]'))
				try:
					setattr(obj, 'id', self._gen_id())
				except Exception:
					pass
				lst.append(obj)

		# Normalize hand values across events to '<' or '>' (repair legacy 'l'/'r')
		try:
			# Convert very short notes to grace notes and normalize hand values
			converted_grace: List[GraceNote] = []
			remaining_notes: List[Note] = []
			for n in getattr(self.events, 'note', []) or []:
				h = str(getattr(n, 'hand', '<') or '<').strip()
				if h.lower() == 'l':
					setattr(n, 'hand', '<')
				elif h.lower() == 'r':
					setattr(n, 'hand', '>')
				elif h not in ('<', '>'):
					setattr(n, 'hand', '<')
				# Convert to grace note if shorter than threshold
				try:
					du = float(getattr(n, 'duration', 0.0) or 0.0)
					if du < float(GRACENOTE_THRESHOLD):
						converted_grace.append(GraceNote(pitch=int(getattr(n, 'pitch', 40) or 40), time=float(getattr(n, 'time', 0.0) or 0.0)))
					else:
						remaining_notes.append(n)
				except Exception:
					remaining_notes.append(n)
			self.events.note = remaining_notes
			for g in converted_grace:
				self.new_grace_note(pitch=int(g.pitch), time=float(g.time))
			for b in getattr(self.events, 'beam', []) or []:
				h = str(getattr(b, 'hand', '<') or '<').strip()
				if h.lower() == 'l':
					setattr(b, 'hand', '<')
				elif h.lower() == 'r':
					setattr(b, 'hand', '>')
				elif h not in ('<', '>'):
					setattr(b, 'hand', '<')
		except Exception:
			pass

		return self

	# ---- New minimal template ----
	def new(self) -> "SCORE":
		self.meta_data = MetaData()
		# Set creation timestamp in format dd-mm-YYYY_HH:MM:SS
		self.meta_data.creation_timestamp = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
		self.header = Header()
		self.base_grid = [BaseGrid()]
		self.events = Events()
		self.layout = Layout()
		self.editor = EditorSettings()
		self._next_id = 1
		return self
	
	# ---- Convenience methods ----
