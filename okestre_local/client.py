"""Outbound WSS connection; heartbeat and bounded reconnect, no remote shell."""
import asyncio
import random
import threading
import time

from websockets.asyncio.client import connect

from .config import server_url
from .executor import Executor
from .protocol import BridgeError, MAX_MESSAGE, encode, decode


class Agent:
    def __init__(self, config, status=None):
        self.config = config
        self.stopping = threading.Event()
        self.status = status or (lambda message: None)
        self.executor = Executor({}, config.home)

    async def session(self, settings):
        base = server_url(settings["server"])
        url = ("wss" if base.startswith("https:") else "ws") + base[base.index(":"):] + "/api/local/connect"
        roots = settings.get("roots", {})
        self.executor.roots = roots
        version = self.config.file.stat().st_mtime_ns
        async with connect(url, additional_headers={"Authorization": "Bearer " + settings["token"]},
                           max_size=MAX_MESSAGE, max_queue=8, open_timeout=15, close_timeout=3,
                           ping_interval=15, ping_timeout=20, compression=None) as socket:
            lock = asyncio.Lock()
            async def send(message):
                async with lock:
                    await socket.send(encode(message))
            await send({"type": "hello", "version": 1, "roots": [
                {"id": identifier, "name": root["name"], "writable": root.get("writable", False)}
                for identifier, root in roots.items() if not root.get("paused", False)]})
            ready = decode(await asyncio.wait_for(socket.recv(), 10))
            if ready.get("type") != "ready" or ready.get("version") != 1:
                raise BridgeError("invalid_handshake")
            self.status("Conectado")
            async def heartbeat():
                ticks = 0
                while True:
                    await asyncio.sleep(1)
                    if self.stopping.is_set() or self.config.file.stat().st_mtime_ns != version:
                        await socket.close()
                        return
                    ticks += 1
                    if ticks % 15 == 0:
                        await send({"type": "ping"})
            beat = asyncio.create_task(heartbeat())
            try:
                async for raw in socket:
                    message = decode(raw)
                    if message.get("type") == "pong":
                        continue
                    if message.get("type") != "call":
                        raise BridgeError("invalid_message")
                    response = {"type": "result", "version": 1, "request_id": message.get("request_id")}
                    try:
                        # Recheck local pause/config changes before accepting any new operation.
                        if self.config.file.stat().st_mtime_ns != version or self.stopping.is_set():
                            raise BridgeError("root_unavailable")
                        result = await asyncio.to_thread(self.executor.dispatch, message)
                        response.update(ok=True, result=result)
                    except BridgeError as exc:
                        response.update(ok=False, error=str(exc))
                    except Exception:
                        response.update(ok=False, error="local_operation_failed")
                    await send(response)
            finally:
                await asyncio.to_thread(self.executor.terminal.close)
                beat.cancel()
                await asyncio.gather(beat, return_exceptions=True)

    async def run(self):
        delay = 1
        while not self.stopping.is_set():
            try:
                settings = self.config.load()
                if not settings.get("token") or settings.get("paused"):
                    self.status("Pausado" if settings.get("paused") else "Configure o pareamento")
                    await asyncio.sleep(1)
                    continue
                started = time.monotonic()
                await self.session(settings)
                if time.monotonic() - started > 30:
                    delay = 1
            except Exception:
                self.status("Desconectado — tentando reconectar; confira a VM e a autorização")
            for _ in range(int((delay + random.random()) * 5)):
                if self.stopping.is_set():
                    break
                await asyncio.sleep(.2)
            delay = min(30, delay * 2)
        self.status("Encerrado")
