"""Render the native layout without an agent, profile, tray icon or visible window."""
import os
import threading
import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows native UI")
def test_actions_and_footer_are_not_clipped(monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    import okestre_local.gui as gui
    original = tk.Tk
    checked = []

    class Window(original):
        def __init__(self):
            super().__init__()
            self.attributes("-alpha", 0)
            self.withdraw()

        def mainloop(self):
            try:
                self.deiconify()
                self.update()
                def descendants(widget):
                    result = []
                    for child in widget.winfo_children():
                        result.append(child)
                        result.extend(descendants(child))
                    return result
                widgets = descendants(self)
                buttons = [w for w in widgets if isinstance(w, ttk.Button)]
                assert len(buttons) == 5
                title = next(w for w in widgets if isinstance(w, ttk.Label)
                             and w.cget("text") == "Projetos compartilhados")
                assert not title.cget("font"), "Widget defaults must not override the heading style"
                for style in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
                    assert ttk.Style(self).lookup(style, "background") == "#414141"
                hint = next(w for w in widgets if isinstance(w, ttk.Label)
                            and str(w.cget("text")).startswith("Fechar a janela"))
                for width, height in ((960, 580), (720, 480), (1200, 700)):
                    self.geometry(f"{width}x{height}")
                    self.update()
                    for widget in buttons + [hint]:
                        assert widget.winfo_height() >= 15
                        assert widget.winfo_rooty() + widget.winfo_height() <= self.winfo_rooty() + self.winfo_height()
                        assert widget.winfo_rootx() + widget.winfo_width() <= self.winfo_rootx() + self.winfo_width()
                checked.append(True)
            finally:
                self.destroy()

    class Agent:
        def __init__(self, *args):
            self.stopping = threading.Event()
        async def run(self):
            pass

    class Icon:
        def __init__(self, *args):
            pass
        def run(self):
            pass

    class Config:
        def load(self):
            return {"roots": {"test": {"name": "Example", "path": "C:/example", "writable": True}}}

    monkeypatch.setattr(gui.tk, "Tk", Window)
    monkeypatch.setattr(gui, "Agent", Agent)
    monkeypatch.setattr(gui.pystray, "Icon", Icon)
    gui.run(Config())
    assert checked
