"""Neutral Okestre presentation for the native tray application."""
import os
from pathlib import Path
from tkinter import ttk

BG = "#181818"
PANEL = "#202020"
TEXT = "#ececec"
MUTED = "#bebebe"
BORDER = "#303030"


def brand_asset(name):
    return Path(__file__).resolve().parents[1] / "resources" / "brand" / name


def apply_theme(window):
    window.iconbitmap(str(brand_asset("okestre.ico")))
    window.configure(background=BG)
    for widget in ("Label", "Button", "Entry"):
        window.option_add("*" + widget + ".Font", ("Segoe UI", 10))
    window.option_add("*Background", BG)
    window.option_add("*Foreground", TEXT)
    window.option_add("*Entry.Background", PANEL)
    window.option_add("*Entry.Foreground", TEXT)
    window.option_add("*Entry.insertBackground", TEXT)
    window.option_add("*selectBackground", "#414141")
    window.option_add("*selectForeground", TEXT)
    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Brand.TLabel", font=("Segoe UI", 11, "bold"))
    style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
    style.configure("Status.TLabel", background=PANEL, foreground=MUTED, padding=(10, 5))
    style.configure("Connected.Status.TLabel", background=PANEL, foreground="#a5cbb4", padding=(10, 5))
    style.configure("TButton", padding=(12, 8), background=PANEL, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    focuscolor=MUTED, borderwidth=1, relief="flat")
    style.map("TButton", background=[("pressed", "#313131"), ("active", "#282828")],
              foreground=[("disabled", "#717171")], bordercolor=[("focus", "#8c8c8c")])
    style.configure("Primary.TButton", background=TEXT, foreground=BG)
    style.map("Primary.TButton", background=[("pressed", "#cfcfcf"), ("active", "#ffffff")],
              foreground=[("disabled", "#717171"), ("!disabled", BG)])
    style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT, bordercolor=BORDER,
                    insertcolor=TEXT, padding=8)
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    rowheight=36, borderwidth=0, relief="flat")
    style.configure("Treeview.Heading", background=PANEL, foreground=MUTED,
                    font=("Segoe UI", 10), padding=(12, 10), borderwidth=0, relief="flat")
    style.map("Treeview", background=[("selected", "#363636")], foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", "#282828")])
    style.configure("TSeparator", background=BORDER)
    for scrollbar in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(scrollbar, background="#414141", troughcolor=BG,
                        bordercolor=BG, arrowcolor=MUTED, lightcolor=BG, darkcolor=BG,
                        gripcount=0, arrowsize=12)
        style.map(scrollbar, background=[("pressed", "#666666"), ("active", "#555555")],
                  arrowcolor=[("disabled", "#686868"), ("!disabled", MUTED)])
    window.after_idle(lambda: style_caption(window))
    window.bind("<Map>", lambda event: window.after(50, lambda: style_caption(window))
                if event.widget is window else None, add=True)


def style_caption(window):
    if os.name != "nt":
        return
    import ctypes
    try:
        ancestor = ctypes.windll.user32.GetAncestor
        ancestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        ancestor.restype = ctypes.c_void_p
        hwnd = ancestor(ctypes.c_void_p(window.winfo_id()), 2)
        for attribute, value in ((20, 1), (35, 0x181818), (36, 0xECECEC)):
            data = ctypes.c_uint(value)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), attribute,
                ctypes.byref(data), ctypes.sizeof(data))
    except (OSError, AttributeError):
        pass
