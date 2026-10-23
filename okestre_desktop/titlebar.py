"""Match the Windows caption to the workspace without replacing native controls."""
import ctypes
import sys


class TitlebarTheme:
    def __init__(self):
        self._window = None

    def minimize(self):
        self._window.minimize()

    def toggle_maximize(self):
        if int(self._window.native.WindowState) == 2:
            self._window.restore()
            return False
        self._window.maximize()
        return True

    def close(self):
        self._window.destroy()

    def set_theme(self, theme):
        if sys.platform != "win32" or theme not in ("dark", "light") or self._window is None:
            return False
        native = self._window.native
        if native is None:
            return False
        hwnd = ctypes.c_void_p(native.Handle.ToInt64())
        dark = theme == "dark"
        # COLORREF is 0x00BBGGRR; neutral colors share all three components.
        values = {20: int(dark), 35: 0x181818 if dark else 0xF7F7F7,
                  36: 0xECECEC if dark else 0x202020}
        applied = False
        for attribute, value in values.items():
            data = ctypes.c_uint(value)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(data), ctypes.sizeof(data))
            applied = applied or result == 0
        return applied


THEME_OBSERVER = """
(() => {
    const update = () => window.pywebview.api.set_theme(
        document.documentElement.dataset.theme === 'light' ? 'light' : 'dark');
    const start = () => {
        update();
        new MutationObserver(update).observe(document.documentElement,
            {attributes: true, attributeFilter: ['data-theme']});
    };
    if (window.pywebview && window.pywebview.api) start();
    else window.addEventListener('pywebviewready', start, {once: true});
})();
"""
