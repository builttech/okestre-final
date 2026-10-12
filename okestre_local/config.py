"""Local enrollment and Windows DPAPI-protected configuration."""
import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

import requests

from .paths import SafeRoot
from .protocol import BridgeError


def default_home():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "OkestreLocal"


def server_url(value):
    parsed = urlsplit(value.strip())
    if (parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or
            parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"} or
            (parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"})):
        raise BridgeError("Use HTTPS; HTTP is allowed only on localhost.")
    return value.strip().rstrip("/")


class Config:
    def __init__(self, home=None):
        self.home = (Path(home) if home else default_home()).absolute()
        self.home.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            self.home.chmod(0o700)
        self.file = self.home / "config.protected"

    def load(self):
        if not self.file.exists():
            return {"roots": {}}
        data = self.file.read_bytes()
        if os.name == "nt":
            import win32crypt
            data = win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]
        return json.loads(data)

    def save(self, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        if os.name == "nt":
            import win32crypt
            raw = win32crypt.CryptProtectData(raw, "Okestre Local", None, None, None, 0)
        temporary = self.home / ("config-" + uuid.uuid4().hex + ".tmp")
        try:
            with open(temporary, "xb") as stream:
                if os.name != "nt":
                    os.chmod(temporary, 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.file)
        finally:
            temporary.unlink(missing_ok=True)

    def pair(self, server, code):
        server = server_url(server)
        response = requests.post(server + "/api/local/claim", json={"code": code.strip()}, timeout=15, allow_redirects=False)
        if response.status_code != 200:
            raise BridgeError("Pareamento recusado. Gere um novo código no painel da VM.")
        value = response.json()
        if not isinstance(value.get("token"), str) or not isinstance(value.get("device_id"), str):
            raise BridgeError("Resposta de pareamento inválida.")
        previous = self.load()
        # Pairing with another server/account requires explicitly re-sharing folders.
        self.save({"server": server, "token": value["token"], "device_id": value["device_id"],
                   "roots": {}, "paused": previous.get("paused", False)})

    def add_root(self, path, name, writable=False):
        data = self.load()
        path = os.path.abspath(path)
        if Path(path) == Path(Path(path).anchor) or Path(path) == Path.home() or self.home.is_relative_to(Path(path)):
            raise BridgeError("Escolha uma pasta de projeto, sem incluir o diretório do agente ou todo o perfil.")
        with SafeRoot(path).parent("probe"):
            pass
        if not name.strip() or len(name.strip()) > 100:
            raise BridgeError("Informe um nome de até 100 caracteres.")
        if any(os.path.normcase(r["path"]) == os.path.normcase(path) for r in data.get("roots", {}).values()):
            raise BridgeError("Pasta já cadastrada.")
        identifier = uuid.uuid4().hex
        data.setdefault("roots", {})[identifier] = {"path": path, "name": name.strip(), "writable": bool(writable)}
        self.save(data)
        return identifier

    @contextmanager
    def single_instance(self):
        stream = open(self.home / "agent.lock", "a+b")
        try:
            stream.seek(0, 2)
            if not stream.tell():
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            stream.close()
