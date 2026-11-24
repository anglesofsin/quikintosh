#!/usr/bin/env python3
"""Quickintosh macOS application library (Darling compatibility runtime)."""
import argparse
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


def guest(path):
    return '/Volumes/SystemRoot' + str(Path(path).resolve())


def run(*args, capture=False):
    # Distinguish guest command failure from runtime/transport initialization.
    import uuid
    marker = '__QUICKINTOSH_STATUS_' + uuid.uuid4().hex + '__'
    command = ' '.join(shlex.quote(str(arg)) for arg in args)
    script = command + '; result=$?; printf "\\n' + marker + '%s\\n" "$result"; exit "$result"'
    process = subprocess.Popen(['darling', 'shell', '/bin/sh', '-c', script], text=True, stdout=subprocess.PIPE)
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
    log_path = log_root / (key + '.log')
    with log_path.open('wb') as log:
        process = subprocess.Popen(['darling', 'shell', guest(path / 'Contents/MacOS' / info['executable'])],
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True)
    try:
        status = process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        return
    if status:
        raise RuntimeError('The macOS app could not start. Log: ' + str(log_path) + '\n' + log_path.read_text(errors='replace')[-3000:])


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
        # The release's FUSE hdiutil does not mount reliably in user namespaces.
        # Extract read-only in a private directory, without loop devices or sudo.
        DATA.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.image-', dir=DATA) as temporary:
            root = Path(temporary)
            def extract(image, destination):
                destination.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(['7zz', 'x', '-y', '-bd', '-bb0', '-o' + str(destination), '--', str(image)],
                                        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
                if result.returncode > 1:
                    raise RuntimeError('Cannot read this disk image.\n' + result.stdout[-2500:])
            extract(source, root / 'image')
            applications = [p for p in (root / 'image').rglob('*.app') if p.is_dir() and
                            not any(parent.suffix.lower() == '.app' for parent in p.relative_to(root).parents)]
            if not applications:
                # Some UDIF images expose an inner filesystem image first.
                images = [p for p in (root / 'image').rglob('*') if p.is_file() and p.suffix.lower() in ('.hfs', '.hfsx', '.apfs')]
                for index, image in enumerate(images):
                    inner = root / ('filesystem-' + str(index))
                    extract(image, inner)
                    applications.extend(p for p in inner.rglob('*.app') if p.is_dir() and
                                        not any(parent.suffix.lower() == '.app' for parent in p.relative_to(inner).parents))
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
    global GUI
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='library', choices=['library', 'install', 'open', 'list', 'terminal', 'doctor', 'remove', 'sync', 'eject'])
    parser.add_argument('path', nargs='?')
    parser.add_argument('--app', help='Bundle name to install from a disk image containing several apps')
    args = parser.parse_args()
    GUI = bool(os.environ.get('DISPLAY')) and (args.action == 'library' or
          (args.action in ('open', 'install') and not sys.stdin.isatty()))
    if args.action == 'doctor':
        print('Runtime:', shutil.which('darling') or 'NOT INSTALLED')
        print('Applications:', APPLICATIONS)
        run('/usr/bin/uname', '-s')
    elif args.action == 'terminal':
        os.execvp('kitty', ['kitty', '--title', 'Darling Terminal', 'darling', 'shell'])
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
            os.execvp('kitty', ['kitty', '--title', 'Darling Terminal', 'darling', 'shell'])
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
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, plistlib.InvalidFileException) as error:
        print(str(error), file=sys.stderr)
        if GUI:
            dialog('--error', '--text=' + str(error))
        sys.exit(1)
