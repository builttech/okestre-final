"""Local process jobs. Shell commands run with the desktop user's privileges."""
import os
import secrets
import signal
import subprocess
import tempfile
import threading
from pathlib import Path

from .protocol import BridgeError

OPTIONS = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}


class Terminal:
    def __init__(self):
        self.jobs = {}

    def snapshot(self, identifier, job):
        process = job['process']
        with job['lock']:
            output = bytes(job['output']).decode('utf-8', errors='replace')
            truncated = job['truncated']
        code = process.poll()
        return {'command_id': identifier, 'status': 'running' if code is None or job['reader'].is_alive() else 'completed' if code == 0 else 'failed',
                'exit_code': code, 'output': output, 'truncated': truncated, 'timed_out': False}

    def execute(self, root_id, cwd, command, command_id=None):
        if not command.strip() or '\x00' in command:
            raise BridgeError('invalid_arguments')
        if command_id is not None:
            job = self.jobs.get(command_id)
            if not job or job['root'] != root_id or job['command'] != command:
                raise BridgeError('invalid_arguments')
            return self.snapshot(command_id, job)
        if len(self.jobs) >= 32:
            for key, value in list(self.jobs.items()):
                if value['process'].poll() is not None and not value['reader'].is_alive():
                    del self.jobs[key]
            if len(self.jobs) >= 32:
                raise BridgeError('device_busy')
        identifier = secrets.randbelow(2**52) + 1
        while identifier in self.jobs:
            identifier = secrets.randbelow(2**52) + 1
        process = subprocess.Popen(command, cwd=cwd, shell=True, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **OPTIONS)
        job = dict(process=process, root=root_id, command=command, output=bytearray(), truncated=False, lock=threading.Lock())
        def drain():
            with process.stdout:
                while chunk := process.stdout.read1(4096):
                    with job['lock']:
                        job['output'].extend(chunk)
                        if len(job['output']) > 64000:
                            del job['output'][:-64000]
                            job['truncated'] = True
        job['reader'] = threading.Thread(target=drain, daemon=True)
        self.jobs[identifier] = job
        job['reader'].start()
        job['reader'].join(.5)
        return self.snapshot(identifier, job)

    def stop(self, root_id, command_id):
        job = self.jobs.get(command_id)
        if not job or job['root'] != root_id:
            raise BridgeError('invalid_arguments')
        process = job['process']
        if process.poll() is None:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **OPTIONS)
            else:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            if process.poll() is None:
                process.kill()
            process.wait()
        job['reader'].join(1)
        return self.snapshot(command_id, job)

    def close(self):
        for identifier, job in list(self.jobs.items()):
            self.stop(job['root'], identifier)

    def git(self, cwd, arguments, field):
        env = os.environ.copy()
        for key in list(env):
            if key.startswith('GIT_'):
                del env[key]
        env.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
        base = ['git', '--no-pager', '--literal-pathspecs', '-C', str(cwd)]
        root = subprocess.run(base + ['rev-parse', '--show-toplevel'], capture_output=True, env=env, **OPTIONS)
        if root.returncode or Path(os.fsdecode(root.stdout).strip()).resolve() != Path(cwd).resolve():
            raise BridgeError('root_unavailable')
        with tempfile.TemporaryFile() as out:
            result = subprocess.run(base + arguments, stdout=out, stderr=subprocess.DEVNULL, env=env, **OPTIONS)
            if result.returncode:
                raise BridgeError('local_operation_failed')
            out.seek(0)
            data = out.read(64001)
        return {field: data[:64000].decode('utf-8', errors='replace'), 'truncated': len(data) > 64000}
