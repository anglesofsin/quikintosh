#!/usr/bin/env python3
"""Keep Darling requests in one subordinate user/mount namespace.

Only the owning desktop user can submit requests. Privilege exists inside the
namespace, never as host root. Standard descriptors are passed, not proxied, so
interactive terminals retain their TTY behavior.
"""
import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import shutil
import stat
import struct
import subprocess
import sys
import time
import tempfile


def ensure_base():
    source = Path(os.environ['QUICKINTOSH_DARLING_SOURCE'])
    root = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'quickintosh/darling'
    root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(source).encode()).hexdigest()[:16]
    base = root / ('runtime-' + key)
    with (root / '.runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not base.exists():
            with tempfile.TemporaryDirectory(prefix='.runtime-', dir=root) as temporary:
                target = Path(temporary) / 'base'
                shutil.copytree(source, target, symlinks=True)
                for directory, directories, files in os.walk(target):
                    os.chmod(directory, 0o755)
                    for name in files:
                        path = Path(directory) / name
                        if not path.is_symlink():
                            os.chmod(path, stat.S_IMODE(path.stat().st_mode) | 0o200)
                target.rename(base)
    os.environ['QUICKINTOSH_DARLING_BASE'] = str(base)


def location():
    root = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + os.environ['QUICKINTOSH_HOST_UID'])) / 'quickintosh-darling'
    root.mkdir(mode=0o700, exist_ok=True)
    if root.is_symlink() or root.stat().st_uid != int(os.environ['QUICKINTOSH_HOST_UID']):
        raise RuntimeError('Invalid Darling runtime directory owner.')
    key = hashlib.sha256(os.environ['DPREFIX'].encode()).hexdigest()[:16]
    return root / (key + '.sock')


def server():
    uid, gid = int(os.environ['QUICKINTOSH_HOST_UID']), int(os.environ['QUICKINTOSH_HOST_GID'])
    command = [os.environ['QUICKINTOSH_SETPRIV'], '--ruid', str(uid), '--rgid', str(gid),
               '--euid', '0', '--egid', '0', '--clear-groups', '/usr/bin/darling']
    # Bootstrap metadata without invoking the release's recursive ownership repair.
    if not (Path(os.environ['DPREFIX']) / 'private/etc/passwd').exists():
        subprocess.run(command + ['--help'], check=True, stdout=subprocess.DEVNULL)
    # darlingserver inherits the initial command's descriptors. Bootstrap with
    # the session log, so it cannot keep a caller's captured stdout pipe open.
    subprocess.run(command + ['shell', '/usr/bin/true'], check=True,
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=30)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            peer = struct.unpack('3i', self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer[1] != uid:
                return
            payload, ancillary, flags, _ = self.request.recvmsg(65536, socket.CMSG_SPACE(3 * array.array('i').itemsize))
            descriptors = array.array('i')
            try:
                for level, kind, data in ancillary:
                    if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                        descriptors.frombytes(data[:len(data) - len(data) % descriptors.itemsize])
                if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC) or len(descriptors) != 3:
                    raise ValueError('Invalid request descriptors.')
                request = json.loads(payload)
                args = request['args']
                if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
                    raise ValueError('Invalid command arguments.')
                stopping = args == ['--stop']
                if request.get('runtime') != os.environ['QUICKINTOSH_DARLING_FHS'] and not stopping:
                    raise ValueError('Darling was updated while its session was running. Close macOS apps, run darling --stop, then retry.')
                environment = os.environ.copy()
                for name in ('DISPLAY', 'XAUTHORITY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'LANG'):
                    value = request.get('environment', {}).get(name)
                    if isinstance(value, str):
                        environment[name] = value
                    else:
                        environment.pop(name, None)
                result = subprocess.run(command + (['shutdown'] if stopping else args), env=environment,
                                        stdin=descriptors[0], stdout=descriptors[1], stderr=descriptors[2],
                                        cwd=request.get('cwd', str(Path.home())))
                self.request.sendall(str(result.returncode).encode())
                if stopping:
                    os._exit(0)
            except Exception as error:
                if len(descriptors) == 3:
                    os.write(descriptors[2], (str(error) + '\n').encode())
                self.request.sendall(b'1')
            finally:
                for fd in descriptors:
                    os.close(fd)

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = True

    os.seteuid(uid)
    path = location()
    path.unlink(missing_ok=True)
    listener = Server(str(path), Handler)
    os.chmod(path, 0o600)
    os.seteuid(0)
    try:
        listener.serve_forever(poll_interval=1)
    finally:
        listener.server_close()


def client():
    path = location()
    connection = socket.socket(socket.AF_UNIX)
    with open(str(path) + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            connection.connect(str(path))
        except (FileNotFoundError, ConnectionRefusedError):
            connection.close()
            ensure_base()
            log = Path.home() / '.local/state/quickintosh'
            log.mkdir(parents=True, exist_ok=True)
            with (log / 'darling.log').open('ab') as output:
                subprocess.Popen(['unshare', '--user', '--map-auto', '--map-current-user', '--setuid=0', '--setgid=0',
                                  os.environ['QUICKINTOSH_DARLING_FHS']], stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=output, start_new_session=True)
            for _ in range(350):
                connection = socket.socket(socket.AF_UNIX)
                try:
                    connection.connect(str(path))
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    connection.close()
                    time.sleep(0.1)
            else:
                raise RuntimeError('Darling could not initialize. Inspect ~/.local/state/quickintosh/darling.log')
    fds = array.array('i', [0, 1, 2])
    environment = {name: os.environ[name] for name in ('DISPLAY', 'XAUTHORITY', 'WAYLAND_DISPLAY',
                   'DBUS_SESSION_BUS_ADDRESS', 'LANG') if name in os.environ}
    connection.sendmsg([json.dumps({'args': sys.argv[1:], 'runtime': os.environ['QUICKINTOSH_DARLING_FHS'],
                                   'cwd': os.getcwd(), 'environment': environment}).encode()], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fds)])
    result = connection.recv(32)
    return int(result) if result else 1


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--namespace-server']:
            server()
        else:
            sys.exit(client())
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
