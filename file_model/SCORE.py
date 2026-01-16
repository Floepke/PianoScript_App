

# my json structure design for *.piano files.
from __future__ import annotations
from dataclasses import dataclass, field, fields, MISSING
from typing import List
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
from file_model.base_grid import BaseGrid


@dataclass
class MetaData:
	description: str = 'This is a .piano score file created with PianoScript.'
	creator: str = 'PianoScript'
	version: int = 2
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

	# image removed

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
			merged = {**defaults, **{k: v for k, v in incoming.items() if k in defaults}}
			missing_keys = [k for k in defaults.keys() if k not in incoming and k not in skip_keys]
			for k in missing_keys:
				print(f"[Repair] Missing '{context}.{k}', using default: {defaults[k]!r}")
			return merged
		# Meta/Header
		md = data.get('meta_data', {})
		self.meta_data = MetaData(**_merge_with_defaults(MetaData, md, 'meta_data'))
		hd = data.get('header', {})
		self.header = Header(**_merge_with_defaults(Header, hd, 'header'))
		# Base grid: at least one
		bg_list = data.get('base_grid', [])
		if not isinstance(bg_list, list):
			print("[Repair] 'base_grid' is not a list; resetting to empty.")
			bg_list = []
		if not bg_list:
			print("[Repair] 'base_grid' missing or empty; inserting default BaseGrid.")
			self.base_grid = [BaseGrid(**_merge_with_defaults(BaseGrid, {}, 'base_grid[0]'))]
		else:
			self.base_grid = [
				BaseGrid(**_merge_with_defaults(BaseGrid, item if isinstance(item, dict) else {}, f'base_grid[{i}]'))
				for i, item in enumerate(bg_list)
			]
		# Layout (optional)
		lay = data.get('layout', {}) or {}
		try:
			def _flatten_layout(ld: dict) -> dict:
				flat = dict(ld)
				# Note
				n = ld.get('note')
				if isinstance(n, dict):
					flat['note_enabled'] = n.get('enabled', flat.get('note_enabled', True))
					flat['note_stem_length_mm'] = n.get('stem_lenghth_mm', flat.get('note_stem_length_mm', 5.0))
					if 'stroke_width_mm' in n:
						flat['note_stroke_width_mm'] = n.get('stroke_width_mm')
				# Grace Note
				g = ld.get('grace_note')
				if isinstance(g, dict):
					flat['grace_note_enabled'] = g.get('enabled', flat.get('grace_note_enabled', True))
					if 'stroke_width_mm' in g:
						flat['grace_note_stroke_width_mm'] = g.get('stroke_width_mm')
					if 'stem_length_mm' in g:
						flat['grace_note_stem_length_mm'] = g.get('stem_length_mm')
				# Pedals
				pd = ld.get('pedal_down')
				if isinstance(pd, dict):
					flat['pedal_down_enabled'] = pd.get('enabled', True)
					flat['pedal_down_stroke_width_mm'] = pd.get('stroke_width_mm', 0.2)
					flat['pedal_down_offset_mm'] = pd.get('offset_mm', 1.0)
				pu = ld.get('pedal_up')
				if isinstance(pu, dict):
					flat['pedal_up_enabled'] = pu.get('enabled', True)
					flat['pedal_up_stroke_width_mm'] = pu.get('stroke_width_mm', 0.2)
					flat['pedal_up_offset_mm'] = pu.get('offset_mm', 1.0)
				# Text
				tx = ld.get('text')
				if isinstance(tx, dict):
					flat['text_enabled'] = tx.get('enabled', True)
					flat['text_font_family'] = tx.get('font_family', 'Sans')
					flat['text_font_size_pt'] = tx.get('font_size_pt', 10.0)
					flat['text_rotated_default'] = tx.get('rotated_default', True)
				# Slur
				sl = ld.get('slur')
				if isinstance(sl, dict):
					flat['slur_enabled'] = sl.get('enabled', True)
					flat['slur_stroke_width_mm'] = sl.get('stroke_width_mm', 0.3)
					flat['slur_curvature_factor'] = sl.get('curvature_factor', 1.0)
				# Beam
				bm = ld.get('beam')
				if isinstance(bm, dict):
					flat['beam_enabled'] = bm.get('enabled', True)
					flat['beam_thickness_mm'] = bm.get('thickness_mm', 0.5)
					flat['beam_gap_mm'] = bm.get('gap_mm', 0.8)
				# Repeat markers
				sr = ld.get('start_repeat')
				if isinstance(sr, dict):
					flat['repeat_start_enabled'] = sr.get('enabled', True)
					flat['repeat_start_thickness_mm'] = sr.get('thickness_mm', 0.4)
				er = ld.get('end_repeat')
				if isinstance(er, dict):
					flat['repeat_end_enabled'] = er.get('enabled', True)
					flat['repeat_end_thickness_mm'] = er.get('thickness_mm', 0.4)
				# Countline
				cl = ld.get('count_line')
				if isinstance(cl, dict):
					flat['countline_enabled'] = cl.get('enabled', True)
					flat['countline_thickness_mm'] = cl.get('thickness_mm', 0.4)
				# Page
				pg = ld.get('page')
				if isinstance(pg, dict):
					flat['page_width_mm'] = pg.get('width_mm', 210.0)
					flat['page_height_mm'] = pg.get('height_mm', 297.0)
					flat['page_top_margin_mm'] = pg.get('top_margin_mm', 10.0)
					flat['page_bottom_margin_mm'] = pg.get('bottom_margin_mm', 10.0)
					flat['page_left_margin_mm'] = pg.get('left_margin_mm', 10.0)
					flat['page_right_margin_mm'] = pg.get('right_margin_mm', 10.0)
				# Remove nested keys
				for k in ('note','grace_note','pedal_down','pedal_up','text','slur','beam','start_repeat','end_repeat','count_line','page'):
					flat.pop(k, None)
				return flat

			flat_lay = _flatten_layout(lay)
			allowed = Layout().__dataclass_fields__.keys()
			kwargs = {k: flat_lay[k] for k in flat_lay.keys() if k in allowed}
			self.layout = Layout(**_merge_with_defaults(Layout, kwargs, 'layout'))
		except Exception:
			print("[Repair] Layout section invalid; using default Layout.")
			self.layout = Layout()

		# Events lists: reset id counter and assign sequential ids starting from 1
		ev = data.get('events', {}) or {}
		self.events = Events()
		self._next_id = 1
		for idx, item in enumerate(ev.get('note', []) or []):
			obj = Note(**_merge_with_defaults(Note, item, f'events.note[{idx}]'))
			obj.id = self._gen_id()
			self.events.note.append(obj)
		for idx, item in enumerate(ev.get('grace_note', []) or []):
			obj = GraceNote(**_merge_with_defaults(GraceNote, item, f'events.grace_note[{idx}]'))
			obj.id = self._gen_id()
			self.events.grace_note.append(obj)
		# Pedal events
		for idx, item in enumerate(ev.get('pedal', []) or []):
			obj = Pedal(**_merge_with_defaults(Pedal, item, f'events.pedal[{idx}]'))
			obj.id = self._gen_id()
			self.events.pedal.append(obj)
		for idx, item in enumerate(ev.get('text', []) or []):
			obj = Text(**_merge_with_defaults(Text, item, f'events.text[{idx}]'))
			obj.id = self._gen_id()
			self.events.text.append(obj)
		for idx, item in enumerate(ev.get('slur', []) or []):
			obj = Slur(**_merge_with_defaults(Slur, item, f'events.slur[{idx}]'))
			obj.id = self._gen_id()
			self.events.slur.append(obj)
		for idx, item in enumerate(ev.get('beam', []) or []):
			obj = Beam(**_merge_with_defaults(Beam, item, f'events.beam[{idx}]'))
			obj.id = self._gen_id()
			self.events.beam.append(obj)
		for idx, item in enumerate(ev.get('start_repeat', []) or []):
			obj = StartRepeat(**_merge_with_defaults(StartRepeat, item, f'events.start_repeat[{idx}]'))
			obj.id = self._gen_id()
			self.events.start_repeat.append(obj)
		for idx, item in enumerate(ev.get('end_repeat', []) or []):
			obj = EndRepeat(**_merge_with_defaults(EndRepeat, item, f'events.end_repeat[{idx}]'))
			obj.id = self._gen_id()
			self.events.end_repeat.append(obj)
		for idx, item in enumerate(ev.get('count_line', []) or []):
			obj = CountLine(**_merge_with_defaults(CountLine, item, f'events.count_line[{idx}]'))
			obj.id = self._gen_id()
			self.events.count_line.append(obj)
		for idx, item in enumerate(ev.get('line_break', []) or []):
			obj = LineBreak(**_merge_with_defaults(LineBreak, item, f'events.line_break[{idx}]'))
			obj.id = self._gen_id()
			self.events.line_break.append(obj)
		return self

	# ---- New minimal template ----
	def new(self) -> "SCORE":
		self.meta_data = MetaData()
		# Set creation timestamp in format dd-mm-YYYY_HH:MM:SS
		self.meta_data.creation_timestamp = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
		self.header = Header()
		self.base_grid = [BaseGrid()]
		self.events = Events()
		self._next_id = 1
		return self
