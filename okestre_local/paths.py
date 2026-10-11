"""Path confinement, including pinned directories on Windows and dirfd on POSIX."""
import fnmatch
import os
import re
import stat
from contextlib import contextmanager, ExitStack
from pathlib import Path, PureWindowsPath

from .protocol import BridgeError, MAX_FILE

BLOCKED_DIRS = {".git", ".gitide", ".okestre-local", "node_modules", "__pycache__", ".venv", "venv", "env", ".next", "dist", "build", ".idea", ".vscode", "tmp", ".gemini"}
SECRET_NAMES = {".npmrc", ".pypirc", ".netrc", "id_rsa", "id_ed25519", "credentials", "credentials.json", "tokens.json"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".ppk", ".kdbx", ".age", ".db", ".sqlite", ".sqlite3"}


def parts_for(relative, policy=True):
    if not isinstance(relative, str) or not relative or len(relative) > 2000:
        raise BridgeError("invalid_path")
    relative = relative.replace("\\", "/")
    if relative.startswith("/") or PureWindowsPath(relative).drive:
        raise BridgeError("invalid_path")
    parts = relative.split("/")
    for part in parts:
        if (part in {"", ".", ".."} or part.endswith((".", " ")) or
                any(ord(c) < 32 or c in ':<>"|?*' for c in part) or
                re.match(r"(?i)^(CON|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³])(?:\.|$)", part)):
            raise BridgeError("invalid_path")
        lower = part.casefold()
        if policy and (lower in BLOCKED_DIRS or lower in SECRET_NAMES or lower.startswith(".okestre-") or
                       (lower.startswith(".env") and lower not in {".env.example", ".env.sample"}) or
                       Path(lower).suffix in SECRET_SUFFIXES or lower == ".gitideignore"):
            raise BridgeError("path_blocked")
    return parts


if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    class Info(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("creation", wintypes.FILETIME),
                    ("access", wintypes.FILETIME), ("write", wintypes.FILETIME),
                    ("volume", wintypes.DWORD), ("size_hi", wintypes.DWORD),
                    ("size_lo", wintypes.DWORD), ("links", wintypes.DWORD),
                    ("index_hi", wintypes.DWORD), ("index_lo", wintypes.DWORD)]
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]

    def win_open(path, directory=False):
        # No FILE_SHARE_DELETE: pin this component against rename/replacement.
        handle = kernel.CreateFileW(str(path), 0 if directory else 0x80000000,
                                    3, None, 3, 0x02000000 | 0x00200000, None)
        if handle == wintypes.HANDLE(-1).value:
            raise OSError(ctypes.get_last_error(), "local_access_failed")
        info = Info()
        if (not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)) or
                info.attributes & 0x400 or bool(info.attributes & 0x10) != directory or
                (not directory and info.links != 1)):
            kernel.CloseHandle(handle)
            raise BridgeError("unsafe_path")
        return handle


class SafeRoot:
    def __init__(self, path):
        # Do not resolve links away: every original ancestor must be checked.
        self.path = Path(os.path.abspath(path))
        if os.name == "nt" and (str(self.path).startswith("\\\\") or not self.path.drive):
            raise BridgeError("invalid_root")

    @contextmanager
    def parent(self, relative, policy=True):
        parts = parts_for(relative, policy)
        with ExitStack() as stack:
            if os.name == "nt":
                current = Path(self.path.anchor)
                handle = win_open(current, True)
                stack.callback(kernel.CloseHandle, handle)
                for part in self.path.parts[1:] + tuple(parts[:-1]):
                    current /= part
                    handle = win_open(current, True)
                    stack.callback(kernel.CloseHandle, handle)
                yield current, parts[-1]
            else:
                fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
                stack.callback(os.close, fd)
                for part in self.path.parts[1:] + tuple(parts[:-1]):
                    fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    stack.callback(os.close, fd)
                yield fd, parts[-1]

    def read(self, relative, policy=True):
        with self.open_file(relative, policy) as stream:
            data = stream.read(MAX_FILE + 1)
            if len(data) > MAX_FILE or b"\x00" in data:
                raise BridgeError("unsupported_file")
            data.decode("utf-8")
            return data

    @contextmanager
    def open_file(self, relative, policy=True):
        with self.parent(relative, policy) as (parent, leaf):
            if os.name == "nt":
                handle = win_open(parent / leaf)
                try:
                    fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
                except Exception:
                    kernel.CloseHandle(handle)
                    raise
            else:
                fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise BridgeError("unsafe_path")
                yield stream

    def allowed(self, relative):
        parts_for(relative)
        try:
            rules = self.read(".gitideignore", policy=False).decode("utf-8").splitlines()
        except FileNotFoundError:
            rules = []
        except OSError as exc:
            # Windows missing-file errors aren't always FileNotFoundError.
            if os.name == "nt" and exc.errno in (2, 3):
                rules = []
            else:
                raise BridgeError("ignore_policy_unavailable") from None
        path = relative.replace("\\", "/").casefold()
        for rule in rules:
            rule = rule.strip().replace("\\", "/").casefold()
            if rule and not rule.startswith("#") and (fnmatch.fnmatchcase(path, rule) or
                    fnmatch.fnmatchcase(path.rsplit("/", 1)[-1], rule) or path.startswith(rule.rstrip("/") + "/")):
                raise BridgeError("path_blocked")
        return relative.replace("\\", "/")
