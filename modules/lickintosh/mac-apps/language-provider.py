#!/usr/bin/env python3
"""Private, local CLD2/ICU bridge for Darwin NaturalLanguage clients.

No text is logged, saved or sent over a network. Only this user's Unix socket
and its assigned subordinate-UID namespace can submit requests.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import socket
import socketserver
import stat
import struct
import subprocess
import sys
import time

LIMIT = 4 * 1024 * 1024
UNIT = 'quickintosh-darling-language.service'


def analyze(request):
    import icu
    import pycld2
    operation = request.get('operation')
    if operation == 'ping':
        return {'version': 1, 'provider': str(Path(__file__).resolve())}
    text = request.get('text')
    if not isinstance(text, str) or len(text.encode('utf-8')) > LIMIT // 2:
        raise ValueError('Invalid text size or type')
    if operation == 'detect':
        if not any(c.isalpha() for c in text):
            return {'languages': [], 'weight': 0}
        reliable, byte_count, details = pycld2.detect(text.replace('\x00', ' '), isPlainText=True, bestEffort=True)
        aliases = {'zh': 'zh-Hans', 'zh-Hant': 'zh-Hant', 'no': 'nb', 'iw': 'he'}
        languages = [[aliases.get(code, code), percentage / 100.0]
                     for name, code, percentage, score in details if code != 'un' and percentage > 0]
        return {'languages': languages, 'weight': len(text), 'reliable': reliable}
    if operation != 'tokens':
        raise ValueError('Unknown operation')
    unit = request.get('unit')
    if type(unit) is not int or unit not in (0, 1, 2, 3):
        raise ValueError('Invalid token unit')
    language = request.get('language', 'und')
    if not isinstance(language, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', language):
        raise ValueError('Invalid language')
    unicode = icu.UnicodeString(text)
    if not text:
        return {'tokens': []}
    if unit == 3:
        return {'tokens': [[0, unicode.length(), 0]]}
    if unit == 2:
        # Paragraph boundaries include the separator, with CRLF as one break.
        result, start, position = [], 0, 0
        for match in re.finditer(r'\r\n|[\r\n\u2028\u2029]', text):
            end = start + len(text[position:match.end()].encode('utf-16-le')) // 2
            result.append([start, end-start, 0]); start = end; position = match.end()
        if start < unicode.length():
            result.append([start, unicode.length()-start, 0])
        return {'tokens': result}
    iterator = (icu.BreakIterator.createWordInstance if unit == 0
                else icu.BreakIterator.createSentenceInstance)(icu.Locale(language))
    iterator.setText(unicode)
    emoji = icu.UnicodeSet('[:Extended_Pictographic:]')
    symbolic = icu.UnicodeSet('[:Symbol:]')
    result, start = [], iterator.first()
    for end in iterator:
        status = iterator.getRuleStatus()
        piece = str(unicode[start:end])
        has_emoji = any(emoji.contains(c) for c in piece)
        has_symbol = any(symbolic.contains(c) for c in piece)
        if unit != 0 or status >= 100 or has_emoji or has_symbol:
            flags = (1 if 100 <= status < 200 else 0) | (4 if has_emoji else 2 if has_symbol else 0)
            result.append([start, end-start, flags])
            if len(result) > 100000:
                raise ValueError('Too many tokens')
        start = end
    return {'tokens': result}


def read_exact(stream, count):
    chunks = bytearray()
    while len(chunks) < count:
        data = stream.recv(count-len(chunks))
        if not data:
            raise ConnectionError('Incomplete request')
        chunks.extend(data)
    return bytes(chunks)


def exchange(path, request, timeout=3):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(timeout); client.connect(str(path))
        payload = json.dumps(request, ensure_ascii=False).encode()
        client.sendall(struct.pack('>I', len(payload)) + payload)
        length, = struct.unpack('>I', read_exact(client, 4))
        if length > LIMIT:
            raise ValueError('Response too large')
        return json.loads(read_exact(client, length))


def permitted_uids():
    uid = os.getuid()
    allowed = {uid}
    username = pwd.getpwuid(uid).pw_name
    path = Path('/etc/subuid')
    if path.exists():
        for line in path.read_text().splitlines():
            parts = line.split(':')
            if len(parts) == 3 and parts[0] in (username, str(uid)):
                allowed.add(int(parts[1]))
    return allowed


def serve(path):
    # Complete lazy model/ICU rule initialization before reporting readiness.
    # Constant fixture text is used; no application content is retained.
    analyze({'operation': 'detect', 'text': 'This sentence warms the local language model.'})
    for unit in (0, 1):
        analyze({'operation': 'tokens', 'unit': unit, 'text': 'Warmup 123. 😀', 'language': 'und'})
    allowed = permitted_uids()
    if path.exists():
        if not path.is_socket() or path.stat().st_uid != os.getuid():
            raise RuntimeError('Invalid socket ownership')
        path.unlink()

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            peer = struct.unpack('3i', self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer[1] not in allowed:
                return
            self.request.settimeout(3)
            try:
                length, = struct.unpack('>I', read_exact(self.request, 4))
                if length > LIMIT or length == 0:
                    raise ValueError('Invalid frame size')
                request = json.loads(read_exact(self.request, length))
                if not isinstance(request, dict):
                    raise ValueError('Invalid request')
                response = {'result': analyze(request)}
            except Exception as error:
                # Never include text, model inputs, or exception messages.
                response = {'error': type(error).__name__}
            payload = json.dumps(response, ensure_ascii=False).encode()
            if len(payload) > LIMIT:
                payload = b'{"error":"ResponseTooLarge"}'
            try:
                self.request.sendall(struct.pack('>I', len(payload)) + payload)
            except OSError:
                pass

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = True

    os.umask(0o077)
    with Server(str(path), Handler) as server:
        os.chmod(path, 0o600)
        server.serve_forever()


def ensure():
    root = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / 'quickintosh-language'
    root.mkdir(mode=0o700, exist_ok=True)
    if root.is_symlink() or root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise RuntimeError('Invalid private runtime directory')
    path = root / 'v1.sock'
    if len(str(path).encode()) >= 108:
        raise RuntimeError('Unix socket path is too long')
    with (root / 'startup.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            response = exchange(path, {'operation': 'ping'})
            if response['result']['provider'] == str(Path(__file__).resolve()):
                print(path); return
        except (OSError, ValueError, KeyError, ConnectionError):
            pass
        directory = root.parent / 'systemd/user'
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / UNIT
        def quote(value):
            return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'
        content = ('# Quickintosh managed runtime unit\n[Unit]\nDescription=Quickintosh Darwin language provider\n'
                   '[Service]\nExecStart=' + ' '.join(map(quote, [sys.executable, str(Path(__file__).resolve()), '--serve', str(path)])) +
                   '\nRestart=on-failure\nRestartSec=1\nNoNewPrivileges=true\nUMask=0077\nMemoryMax=256M\nStandardOutput=null\n')
        if target.exists() and not target.read_text().startswith('# Quickintosh managed runtime unit\n'):
            raise RuntimeError('Refusing to overwrite another unit')
        subprocess.run(['systemctl', '--user', 'stop', UNIT], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        target.write_text(content); target.chmod(0o600)
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['systemctl', '--user', 'start', UNIT], check=True, stdout=subprocess.DEVNULL)
        for attempt in range(200):
            try:
                if exchange(path, {'operation': 'ping'}, timeout=1).get('result', {}).get('version') == 1:
                    print(path); return
            except (OSError, ValueError, ConnectionError):
                time.sleep(.05)
        raise RuntimeError('Language provider did not become ready')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ensure', action='store_true')
    parser.add_argument('--serve', type=Path)
    args = parser.parse_args()
    if args.ensure:
        ensure()
    elif args.serve:
        serve(args.serve)
    else:
        parser.error('Choose --ensure or --serve')
