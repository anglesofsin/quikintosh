#!/usr/bin/env python3
"""Quickintosh macOS application library (Darling compatibility runtime)."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile

DATA = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'quickintosh/mac-apps'
APPLICATIONS = DATA / 'Applications'
DESKTOPS = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
PREFIX = Path(os.environ.get('DPREFIX', Path.home() / '.local/share/quickintosh/darling/prefix'))
GUI = False
DARLING_COMMAND = 'darling'


@contextmanager
def disk_image(source):
    """Mount HFS images on the host, outside Darling's user namespace.

    Never remove a directory while it is mounted. Unsupported images and
    hosts without FUSE retain the existing 7-Zip extraction path.
    """
    DATA.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='.image-', dir=DATA))
    mount = root / 'volume'
    mount.mkdir()
    try:
        tool = shutil.which('darling-dmg')
        if tool and Path('/dev/fuse').exists():
            try:
                result = subprocess.run([tool, str(source), str(mount), '-o', 'ro'],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, timeout=20)
                if result.returncode and not mount.is_mount():
                    print('DMG mount unavailable; trying extraction.\n' + result.stdout[-1500:], file=sys.stderr)
            except (OSError, subprocess.TimeoutExpired) as error:
                print('DMG mount unavailable; trying extraction: ' + str(error), file=sys.stderr)
        if mount.is_mount():
            yield mount
        else:
            image = root / 'image'
            extract_image(source, image)
            # Some UDIF images expose a filesystem image before its files.
            if not any(image.rglob('*.app')):
                images = [p for p in image.rglob('*') if p.is_file() and
                          p.suffix.lower() in ('.hfs', '.hfsx', '.apfs')]
                for index, inner in enumerate(images):
                    extract_image(inner, image / ('filesystem-' + str(index)))
            yield image
    finally:
        try:
            if mount.is_mount():
                # Prefer the host's privileged FUSE helper, never a guest tool.
                helper = next((str(p) for p in (Path('/run/wrappers/bin/fusermount'),
                                                Path('/usr/bin/fusermount'), Path('/usr/bin/fusermount3'))
                               if p.is_file()), None) or shutil.which('fusermount') or shutil.which('fusermount3')
                if not helper:
                    raise RuntimeError('FUSE unmount helper missing. Image retained at ' + str(mount))
                subprocess.run([helper, '-u', str(mount)], check=True, timeout=15)
        finally:
            if not mount.is_mount():
                shutil.rmtree(root)


def extract_image(image, destination):
    destination.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['7zz', 'x', '-y', '-bd', '-bb0', '-o' + str(destination), '--', str(image)],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    if result.returncode > 1:
        raise RuntimeError('Cannot read this disk image.\n' + result.stdout[-2500:])


def guest(path):
    return '/Volumes/SystemRoot' + str(Path(path).resolve())


def run(*args, capture=False):
    # Distinguish guest command failure from runtime/transport initialization.
    import uuid
    marker = '__QUICKINTOSH_STATUS_' + uuid.uuid4().hex + '__'
    command = ' '.join(shlex.quote(str(arg)) for arg in args)
    script = command + '; result=$?; printf "\\n' + marker + '%s\\n" "$result"; exit "$result"'
    process = subprocess.Popen([DARLING_COMMAND, 'shell', '/bin/sh', '-c', script], text=True, stdout=subprocess.PIPE)
    progress = None
    try:
        try:
            stdout, _ = process.communicate(timeout=0.75)
        except subprocess.TimeoutExpired:
            if GUI:
                progress = subprocess.Popen(['zenity', '--progress', '--title=macOS Applications',
                                             '--text=Preparing macOS application…', '--pulsate',
                                             '--auto-close', '--no-cancel'], stdin=subprocess.PIPE,
                                            stdout=subprocess.DEVNULL, text=True)
            stdout, _ = process.communicate()
    finally:
        if progress is not None:
            try:
                progress.communicate('100\n', timeout=2)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                progress.terminate()
    output, separator, status = stdout.rpartition('\n' + marker)
    if not separator:
        raise RuntimeError('Darling did not complete the command. Inspect ~/.local/state/quickintosh/darling.log')
    if int(status.strip()) != 0:
        raise RuntimeError('The macOS command failed: ' + str(args[0]) + '\n' + output)
    if capture:
        return output
    if output:
        print(output, end='')


def metadata(path):
    path = Path(path).resolve()
    if any(character in str(path) for character in ('\n', '\r', '\0')):
        raise ValueError('Application paths must not contain control characters.')
    if not path.is_dir() or path.suffix.lower() != '.app':
        raise ValueError('Select a macOS .app bundle.')
    with (path / 'Contents/Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    executable = str(info.get('CFBundleExecutable', ''))
    if not executable or Path(executable).name != executable:
        raise ValueError('The bundle has no valid CFBundleExecutable.')
    if not (path / 'Contents/MacOS' / executable).is_file():
        raise ValueError('The application executable is missing.')
    binary = path / 'Contents/MacOS' / executable
    with binary.open('rb') as stream:
        header = stream.read(4096)
    cpus = []
    if header[:4] in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe') and len(header) >= 8:
        cpus = [struct.unpack('<I', header[4:8])[0]]
    elif header[:4] in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf') and len(header) >= 8:
        count = min(struct.unpack('>I', header[4:8])[0], 32)
        stride = 32 if header[:4] == b'\xca\xfe\xba\xbf' else 20
        cpus = [struct.unpack('>I', header[8+i*stride:12+i*stride])[0]
                for i in range(count) if 12+i*stride <= len(header)]
    if cpus and not any(cpu in (7, 0x01000007) for cpu in cpus):
        raise ValueError('This app has no Intel executable. Darling on this system cannot run Apple Silicon-only apps.')
    return {'name': str(info.get('CFBundleDisplayName') or info.get('CFBundleName') or path.stem),
            'id': str(info.get('CFBundleIdentifier') or path.stem), 'executable': executable,
            'icon': str(info.get('CFBundleIconFile') or '')}


def launcher(path, info):
    import hashlib
    key = hashlib.sha256(str(path).encode()).hexdigest()[:20]
    destination = DESKTOPS / ('quickintosh-mac-' + key + '.desktop')
    # Desktop Entry values are not shell expressions. Escape their own grammar.
    def quoted(value):
        value = str(value).replace('%', '%%').replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
        return '"' + value + '"'
    name = info['name'].replace('\n', ' ').replace('\r', ' ')
    icon = 'application-x-executable'
    icon_name = info.get('icon', '')
    if icon_name and Path(icon_name).name == icon_name:
        source = path / 'Contents/Resources' / icon_name
        if not source.suffix:
            source = source.with_suffix('.icns')
        if source.is_file():
            try:
                from PIL import Image
                icons = DATA / 'icons'
                icons.mkdir(parents=True, exist_ok=True)
                target = icons / (key + '.png')
                with Image.open(source) as image:
                    image.thumbnail((256, 256))
                    image.save(target, format='PNG')
                icon = str(target)
            except (OSError, ImportError):
                pass
    DESKTOPS.mkdir(parents=True, exist_ok=True)
    destination.write_text('[Desktop Entry]\nType=Application\nName=' + name +
                           '\nComment=macOS application · Darling compatibility\nIcon=' + icon + '\nExec=quickintosh-mac open ' + quoted(path) +
                           '\nTerminal=false\nCategories=Utility;\nStartupNotify=false\n')
    return destination


def install_app(source):
    source = Path(source).resolve()
    info = metadata(source)
    APPLICATIONS.mkdir(parents=True, exist_ok=True)
    destination = APPLICATIONS / source.name
    if destination.exists():
        raise ValueError('This application is already installed. Remove it before replacing it.')
    # Atomic publication; preserve framework symlinks and executable bits.
    with tempfile.TemporaryDirectory(prefix='.install-', dir=APPLICATIONS) as temporary:
        staging = Path(temporary) / source.name
        shutil.copytree(source, staging, symlinks=True)
        staging.rename(destination)
    launcher(destination, info)
    print(destination)
    return destination


def launch(path):
    """Launch the bundle executable: this release's LaunchServices open is a stub."""
    import hashlib
    path = Path(path).resolve()
    info = metadata(path)
    run('/usr/bin/true')
    log_root = Path.home() / '.local/state/quickintosh/mac-apps'
    log_root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(path).encode()).hexdigest()[:20]
    log_path = log_root / (key + ('-experimental' if DARLING_COMMAND == 'darling-experimental' else '') + '.log')
    with log_path.open('wb') as log:
        process = subprocess.Popen([DARLING_COMMAND, 'shell', guest(path / 'Contents/MacOS' / info['executable'])],
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True)
    try:
        status = process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        status = None
    with log_path.open('rb') as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - 8192))
        output = stream.read(8192).decode(errors='replace')
    loader_failed = any(line.startswith(('dyld: Library not loaded:', 'dyld: Symbol not found:',
                                         'abort_with_payload: reason:')) for line in output.splitlines())
    if status or loader_failed:
        raise RuntimeError('The macOS app could not start. Log: ' + str(log_path) + '\n' + output)


def dialog(*args):
    result = subprocess.run(['zenity', '--title=macOS Applications', *args], text=True, stdout=subprocess.PIPE)
    return result.stdout.strip() if result.returncode == 0 else None


def installed_apps():
    result = []
    for root in (APPLICATIONS, PREFIX / 'Applications'):
        for path in sorted(root.glob('*.app')):
            try:
                result.append(dict(metadata(path), path=str(path)))
            except (ValueError, OSError, plistlib.InvalidFileException):
                continue
    return result


def sync():
    for item in installed_apps():
        launcher(Path(item['path']), item)


def install(source, app_choice=None):
    source = Path(source).expanduser().resolve()
    if source.suffix.lower() == '.app':
        return install_app(source)
    if source.suffix.lower() == '.dmg':
        with disk_image(source) as root:
            applications = [p for p in root.rglob('*.app') if p.is_dir() and
                            not any(parent.suffix.lower() == '.app' for parent in p.relative_to(root).parents)]
            if app_choice:
                applications = [p for p in applications if p.name == app_choice]
            if not applications:
                raise ValueError('No compatible .app bundle found in this image. Images containing .pkg installers need the package extracted first.')
            if len(applications) == 1:
                selected = applications[0]
            else:
                selected = dialog('--list', '--column=Application', *[str(p) for p in applications])
                if not selected:
                    return
                selected = Path(selected)
            return install_app(selected)
    if source.suffix.lower() == '.pkg':
        if subprocess.run(['zenity', '--question', '--title=Install macOS package', '--text=Run this package installer inside Darling? Only install packages you trust. Compatibility is experimental.']).returncode != 0:

            return
        run('installer', '-pkg', guest(source), '-target', '/')
        sync()
        return
    raise ValueError('Supported: .app, .dmg and .pkg. ZIP files must be extracted first.')


def main():
    global GUI, DARLING_COMMAND, PREFIX
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='library', choices=['library', 'install', 'open', 'list', 'terminal', 'doctor', 'remove', 'sync', 'eject'])
    parser.add_argument('path', nargs='?')
    parser.add_argument('--app', help='Bundle name to install from a disk image containing several apps')
    parser.add_argument('--runtime', choices=['stable', 'experimental'], default='stable',
                        help='Experimental Swift/Combine runtime uses a separate Darwin prefix')
    args = parser.parse_args()
    DARLING_COMMAND = 'darling-experimental' if args.runtime == 'experimental' else 'darling'
    if args.runtime == 'experimental':
        if not shutil.which(DARLING_COMMAND):
            raise RuntimeError('Experimental runtime is not installed. Build the darling-experimental package first.')
        PREFIX = Path(os.environ.get('DPREFIX', Path.home() / '.local/share/quickintosh/darling-experimental/prefix'))
    GUI = bool(os.environ.get('DISPLAY')) and (args.action == 'library' or
          (args.action in ('open', 'install') and not sys.stdin.isatty()))
    if args.action == 'doctor':
        print('Runtime:', shutil.which(DARLING_COMMAND) or 'NOT INSTALLED')
        print('Darwin prefix:', PREFIX)
        print('DMG reader:', shutil.which('darling-dmg') or 'NOT INSTALLED (7-Zip fallback)')
        print('Host FUSE:', 'available' if os.access('/dev/fuse', os.R_OK | os.W_OK) else 'unavailable (7-Zip fallback)')
        print('Applications:', APPLICATIONS)
        run('/usr/bin/uname', '-s')
    elif args.action == 'terminal':
        os.execvp('kitty', ['kitty', '--title', 'Darling Terminal', DARLING_COMMAND, 'shell'])
    elif args.action == 'list':
        print(json.dumps(installed_apps(), ensure_ascii=False, indent=2))
    elif args.action == 'sync':
        sync()
    elif args.action == 'library':
        choice = dialog('--list', '--column=Action', 'Install application', 'Open application', 'Show applications', 'Darling Terminal', 'Check runtime')
        if choice == 'Install application':
            kind = dialog('--list', '--column=Install', 'Application bundle (.app)', 'Disk image or package')
            if not kind:
                return
            options = ['--file-selection'] + (['--directory'] if kind.startswith('Application') else ['--file-filter=macOS installers | *.dmg *.pkg'])
            path = dialog(*options)
            if path:
                install(path)
        elif choice == 'Open application':
            paths = [Path(item['path']) for item in installed_apps()]
            selected = dialog('--list', '--column=Application', *[str(p) for p in paths]) if paths else None
            if selected:
                launch(selected)
        elif choice == 'Show applications':
            APPLICATIONS.mkdir(parents=True, exist_ok=True)
            subprocess.run(['xdg-open', str(APPLICATIONS)], check=True)
        elif choice == 'Darling Terminal':
            os.execvp('kitty', ['kitty', '--title', 'Darling Terminal', DARLING_COMMAND, 'shell'])
        elif choice == 'Check runtime':
            result = run('/usr/bin/uname', '-s', capture=True)
            dialog('--info', '--text=' + result)
    else:
        if not args.path:
            parser.error('This action requires a path.')
        if args.action == 'install':
            install(args.path, args.app)
        elif args.action == 'open':
            launch(args.path)
        elif args.action == 'remove':
            path = Path(args.path).resolve()
            if path.parent not in (APPLICATIONS.resolve(), (PREFIX / 'Applications').resolve()):
                raise ValueError('Only applications in the Quickintosh library can be removed.')
            metadata(path)
            desktop = launcher(path, metadata(path))
            subprocess.run(['gio', 'trash', str(path)], check=True)
            desktop.unlink(missing_ok=True)
        elif args.action == 'eject':
            eject(args.path)


def eject(path):
    path = Path(path)
    if path.parent != Path('/Volumes') or path.name in ('SystemRoot', 'DarlingEmulatedDrive'):
        raise ValueError('Select a mounted disk image under /Volumes.')
    run('hdiutil', 'detach', str(path))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as error:
        print(str(error), file=sys.stderr)
        if GUI:
            dialog('--error', '--text=' + str(error))
        sys.exit(1)
