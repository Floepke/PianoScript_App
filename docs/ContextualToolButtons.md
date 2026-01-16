# Adding Contextual Tool Buttons

This app shows a small, per-tool toolbar in the splitter handle (left side), below the default controls. Those buttons are defined by the active Tool class and routed back to that Tool when clicked.

Summary of the flow:
- The `ToolManager` asks the active tool for its button definitions via `toolbar_spec()` and renders them in the handle.
- When a contextual button is clicked, `ToolManager` calls `on_toolbar_button(name)` on the active tool.
- You implement both in your Tool class (e.g., `NoteTool`) and perform the actual action inside `on_toolbar_button()`.

See wiring:
- Context UI container: [ui/widgets/toolbar_splitter.py](ui/widgets/toolbar_splitter.py)
- Manager that binds tool → buttons → click events: [editor/tool_manager.py](editor/tool_manager.py)
- Active tool is switched by the editor controller: [editor/editor.py](editor/editor.py#L51-L70)
- Tool selection UI: [ui/widgets/tool_selector.py](ui/widgets/tool_selector.py)

## Tool API

Implement these two methods in your tool class (subclass of `BaseTool`).
- `toolbar_spec()` → returns a list of button definitions.
- `on_toolbar_button(name)` → event handler for a button click.

Base contract: [editor/tool/base_tool.py](editor/tool/base_tool.py)

Button definition shape:
- `name`: unique string identifier used in callbacks
- `icon`: icon key from the icons package (see below)
- `tooltip`: short help text

## Minimal Example (NoteTool)

Add one or more buttons by overriding `toolbar_spec()` and handle clicks in `on_toolbar_button()`.

```python
# In editor/tool/note_tool.py
from editor.tool.base_tool import BaseTool

class NoteTool(BaseTool):
    TOOL_NAME = 'note'

    def toolbar_spec(self) -> list[dict]:
        return [
            { 'name': 'insert_c4', 'icon': 'note', 'tooltip': 'Insert C4 note' },
            { 'name': 'delete_selection', 'icon': 'stop', 'tooltip': 'Delete selection' },
        ]

    def on_toolbar_button(self, name: str) -> None:
        if name == 'insert_c4':
            self._insert_note('C4')
        elif name == 'delete_selection':
            self._delete_selection()

    # Example helpers — put the actual logic you need here
    def _insert_note(self, pitch: str) -> None:
        print(f'NoteTool: inserting note {pitch}')
        # TODO: integrate with editor/model to create a note at current cursor/position

    def _delete_selection(self) -> None:
        print('NoteTool: deleting current selection')
        # TODO: integrate with editor/model to delete current selection
```

That’s it — when you select "Note" in the tool list, the handle shows these two buttons, and clicking them calls your `on_toolbar_button()`.

## Where the buttons render

The handle class builds the contextual area and emits a signal per button:
- Layout and creation: [ui/widgets/toolbar_splitter.py](ui/widgets/toolbar_splitter.py#L101-L147)
- Signal emission (`contextButtonClicked(name)`): [ui/widgets/toolbar_splitter.py](ui/widgets/toolbar_splitter.py#L133-L145)
- Manager updates the button set when the tool changes: [editor/tool_manager.py](editor/tool_manager.py#L18-L38)
- Manager forwards clicks to the tool: [editor/tool_manager.py](editor/tool_manager.py#L40-L48)

## Choosing Icons

Icons are loaded by name from the icons package.
- Icon helper: [icons/icons.py](icons/icons.py#L88-L134)
- The generated map of `name → base64` is in: [icons/icons_byte64.py](icons/icons_byte64.py)
- Available icon keys include: `note`, `grace_note`, `count_line`, `line_break`, `beam`, `slur`, `repeats`, `text`, etc.

If you add a new PNG into [icons](icons), regenerate the mapping:

```bash
python3 icons/icons.py
```

## FAQ

- Is `on_toolbar_button()` a “callback”? Yes — you can think of it as the tool’s click callback or event handler. The manager invokes it when the UI button is clicked.
- Can buttons be toggle/checkable? The current UI uses plain `QToolButton` clicks. For toggles, store state in your tool (e.g., `self._snap_enabled = True`) and branch in `on_toolbar_button()`; if you need the visual toggled state, we can extend the button spec to include `checkable` and `checked` and refresh the contextual area.
- How does a Tool access selection or the model? Tools receive mouse events via `Editor` (see [editor/editor.py](editor/editor.py)), and you can connect tool actions to your editor/model integration points. The scaffolding prints debug hooks; wire them up to the relevant functions in your app.

## Quick Checklist

- Implement `toolbar_spec()` with one or more buttons for your tool.
- Implement `on_toolbar_button(name)` and call your own helpers to perform the action.
- Ensure your tool is selectable in the list (see [ui/widgets/tool_selector.py](ui/widgets/tool_selector.py)).
- Provide a valid icon key present in [icons/icons_byte64.py](icons/icons_byte64.py) or generate one.
- Run the app and verify the contextual buttons appear for the selected tool.
