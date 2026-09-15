"""Bounded non-interactive shell execution for explicitly approved MCP calls."""
import os
import signal
import subprocess
import threading
import time


def execute(command, cwd, timeout=30, max_output=64000):
    options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NO_WINDOW}
    process = subprocess.Popen(command, shell=True, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **options)
    output = bytearray()
    truncated = [False]

    def drain():
        with process.stdout:
            while chunk := process.stdout.read(4096):
                remaining = max_output - len(output)
                output.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated[0] = True

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        process.wait(timeout=timeout)
        reader.join(max(0, deadline - time.monotonic()))
        timed_out = reader.is_alive()
    except subprocess.TimeoutExpired:
        timed_out = True
    if timed_out:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        reader.join(1)
    return {"exit_code": process.returncode, "output": bytes(output).decode("utf-8", errors="replace"),
            "truncated": truncated[0] or reader.is_alive(), "timed_out": timed_out}
