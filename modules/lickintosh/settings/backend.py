"""Linux capabilities behind Lickintosh Settings. No arbitrary command execution."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import configparser
import base64
import datetime
import fcntl
import json
import os
import platform
import pwd
import re
import shutil
import subprocess
import tempfile
import sys
import threading
from urllib.parse import urlsplit

HOME = Path.home()
STATE = Path(os.environ.get('XDG_STATE_HOME', HOME / '.local/state')) / 'lickintosh/settings'
PREFERENCES = HOME / '.config/lickintosh/core/settings-preferences.json'
OUTPUT = threading.Lock()
INPUTS = {
    'input:sensitivity': ('number', -1, 1),
    'input:accel_profile': ('choice', ['flat', 'adaptive']),
    'input:natural_scroll': ('bool',),
    'input:scroll_factor': ('number', .1, 3),
    'input:repeat_rate': ('int', 10, 100),
    'input:repeat_delay': ('int', 100, 1000),
    'input:kb_layout': ('text',), 'input:kb_variant': ('text',),
    'input:touchpad:natural_scroll': ('bool',),
    'input:touchpad:tap-to-click': ('bool',),
    'input:touchpad:disable_while_typing': ('bool',),
    'input:touchpad:clickfinger_behavior': ('bool',),
    'input:touchpad:scroll_factor': ('number', .1, 3),
    'cursor:inactive_timeout': ('number', 0, 120),
}


def run(args, timeout=8, check=True):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout, env=dict(os.environ, LC_ALL='C.UTF-8'))
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout or 'The service is unavailable.').strip()[:800])
    return result.stdout.strip()


def read(path, default=''):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return default


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {} if default is None else default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f'.{os.getpid()}.{threading.get_ident()}.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=True))
    temporary.chmod(0o600)
    temporary.replace(path)


def remember_file(path):
    """Keep rice-specific changes to user services reversible on rice exit."""
    path = Path(path)
    if not path.is_relative_to(HOME):
        raise ValueError('Settings may only override user configuration files.')
    record = read_json(STATE/'files.json')
    key = str(path)
    if key not in record:
        record[key] = {'link': os.readlink(path)} if path.is_symlink() else {'data': base64.b64encode(path.read_bytes()).decode(), 'mode':path.stat().st_mode & 0o777} if path.exists() else None
        write_json(STATE/'files.json', record)


def file_snapshot(path):
    return {'link': os.readlink(path)} if path.is_symlink() else {'data': base64.b64encode(path.read_bytes()).decode(), 'mode':path.stat().st_mode & 0o777} if path.exists() else None


def put_snapshot(path, saved):
    path.unlink(missing_ok=True)
    if saved is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if 'link' in saved:
        path.symlink_to(saved['link'])
    else:
        path.write_bytes(base64.b64decode(saved['data']))
        path.chmod(saved.get('mode', 0o600))


def restore_files():
    previous = read_json(STATE/'files.json')
    if not previous:
        return
    desired = read_json(STATE/'file-preferences.json')
    for name, saved in previous.items():
        path = Path(name)
        if not path.is_relative_to(HOME):
            continue
        desired[name] = file_snapshot(path)
        put_snapshot(path, saved)
    write_json(STATE/'file-preferences.json', desired)
    (STATE/'files.json').unlink(missing_ok=True)


def activate_files():
    active = read_json(STATE/'files.json')
    for name, saved in read_json(STATE/'file-preferences.json').items():
        path = Path(name)
        if not path.is_relative_to(HOME) or name in active:
            continue
        remember_file(path)
        put_snapshot(path, saved)


def split_nm(line):
    fields, current, escaped = [], '', False
    for char in line:
        if escaped:
            current += char
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            fields.append(current)
            current = ''
        else:
            current += char
    return fields + [current]


def system_info():
    release = {}
    for line in read('/etc/os-release').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            release[key] = value.strip('"')
    cpu = next((line.split(':', 1)[1].strip() for line in read('/proc/cpuinfo').splitlines() if line.startswith('model name')), platform.machine())
    mem = next((int(line.split()[1]) * 1024 for line in read('/proc/meminfo').splitlines() if line.startswith('MemTotal:')), 0)
    me = pwd.getpwuid(os.getuid())
    return dict(hostname=platform.node(), os=release.get('PRETTY_NAME', 'Linux'), kernel=platform.release(),
                cpu=cpu, memory=mem, architecture=platform.machine(),
                model=read('/sys/devices/virtual/dmi/id/product_name'),
                vendor=read('/sys/devices/virtual/dmi/id/sys_vendor'),
                user=me.pw_name, fullName=me.pw_gecos.split(',')[0] or me.pw_name,
                home=me.pw_dir, uid=me.pw_uid,
                avatar=str(HOME / '.face') if (HOME / '.face').is_file() else '',
                generation=str(Path('/run/current-system').resolve()),
                capabilities={key: bool(shutil.which(command)) for key, command in {'steam':'steam', 'passwords': 'seahorse', 'backups': 'pika-backup', 'networkEditor': 'nm-connection-editor', 'scanner': 'simple-scan'}.items()},
                uptime=float(read('/proc/uptime', '0').split()[0]))


def storage_info(details=False):
    total, used, free = shutil.disk_usage(HOME)
    result = dict(total=total, used=used, free=free, location=str(HOME), folders=[])
    if details:
        for name in ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Movies', 'Videos', 'Music', '.cache']:
            folder = HOME / name
            if not folder.is_dir():
                continue
            try:
                size = int(run(['du', '-sx', '--block-size=1', '--', str(folder)], timeout=12).split()[0])
            except (RuntimeError, subprocess.TimeoutExpired):
                size = None
            result['folders'].append(dict(name='Caches' if name == '.cache' else name, path=str(folder), size=size))
    return result


def network_info():
    devices = []
    for line in run(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION', 'device']).splitlines():
        fields = split_nm(line)
        if len(fields) == 4:
            devices.append(dict(zip(['device', 'type', 'state', 'connection'], fields)))
    profiles = []
    for line in run(['nmcli', '-t', '-f', 'UUID,NAME,TYPE,DEVICE', 'connection', 'show']).splitlines():
        fields = split_nm(line)
        if len(fields) == 4:
            profiles.append(dict(zip(['uuid', 'name', 'type', 'device'], fields)))
    return dict(devices=devices, profiles=profiles, hostname=platform.node())


def input_values(keys):
    # One IPC round trip per chunk. Unknown options emit plain text; successful
    # results are compact JSON objects with their own option names.
    values = {}
    keys = sorted(set(keys) & INPUTS.keys())
    for start in range(0, len(keys), 48):
        commands = ' ; '.join('getoption ' + key for key in keys[start:start + 48])
        try:
            response = run(['hyprctl', '-j', '--batch', commands])
        except RuntimeError:
            continue
        for line in response.splitlines():
            if not line.lstrip().startswith('{'):
                continue
            try:
                data = json.loads(line)
                key = data.get('option')
                if key not in INPUTS:
                    continue
                value = next((data[n] for n in ('bool', 'int', 'float', 'str', 'css') if n in data), None)
                if value == '[[EMPTY]]':
                    value = ''
                values[key] = bool(value) if INPUTS[key][0] == 'bool' and value is not None else value
            except ValueError:
                continue
    return values


def input_info():
    return dict(values=input_values(key for key in INPUTS if key.startswith(('input:', 'cursor:'))), devices=json.loads(run(['hyprctl', 'devices', '-j'])))


def applications():
    from gi.repository import Gio
    apps = [dict(id=a.get_id(), name=a.get_display_name(), icon=a.get_icon().to_string() if a.get_icon() else '')
            for a in Gio.AppInfo.get_all() if a.should_show() and a.get_id()]
    types = ['x-scheme-handler/http', 'x-scheme-handler/mailto', 'text/plain', 'application/pdf', 'image/png', 'video/mp4', 'audio/mpeg']
    defaults = {}
    for mime in types:
        app = Gio.AppInfo.get_default_for_type(mime, False)
        defaults[mime] = app.get_id() if app else ''
    return dict(apps=sorted(apps, key=lambda a: a['name'].casefold()), defaults=defaults)


def audio_info():
    nodes = json.loads(run(['pw-dump']))
    outputs, inputs = [], []
    for node in nodes:
        props = node.get('info', {}).get('props', {})
        media = props.get('media.class', '')
        if media in {'Audio/Sink', 'Audio/Source'}:
            (outputs if media == 'Audio/Sink' else inputs).append(dict(id=node['id'], name=props.get('node.description', props.get('node.name', 'Audio device'))))
    defaults = {}
    for kind, token in [('output', '@DEFAULT_AUDIO_SINK@'), ('input', '@DEFAULT_AUDIO_SOURCE@')]:
        text = run(['wpctl', 'get-volume', token], check=False)
        value = re.search(r'Volume:\s*([0-9.]+)', text)
        info = run(['wpctl', 'inspect', token], check=False)
        identity = re.search(r'^id (\d+)', info)
        defaults[kind] = dict(id=int(identity[1]) if identity else 0, volume=float(value[1]) if value else 0,
                              muted='MUTED' in text, available=value is not None)
    return dict(outputs=outputs, inputs=inputs, **defaults)


SHORTCUT_MODIFIERS = [(64, 'Super'), (4, 'Ctrl'), (8, 'Alt'), (1, 'Shift')]


def shortcut_path():
    return Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config')) / 'lickintosh/core/shortcuts.tsv'


def shortcut_overrides():
    return dict(line.split('\t', 1) for line in read(shortcut_path()).splitlines() if '\t' in line)


EDITABLE_LUA_SHORTCUTS = {
    'Spotlight', 'Launchpad', 'Clipboard history', 'Emoji picker', 'Command runner',
    'Control center', 'Toggle bar', 'Toggle dock', 'Open shell settings', 'Session menu',
    'Lock screen', 'Shell AI assistant', 'Toggle shell game mode', 'Toggle keep awake',
    'Shell profiles', 'Activate notch item', 'Notch information', 'Wallpaper panel',
    'Toggle dark mode', 'Toggle night light', 'Turn off monitors', 'Edit desktop widgets',
    'Screenshot menu (freeze, select: Copy/Save/Editor/OCR/Lens)', 'Capture / Quickshot',
    'OCR (region selector)', 'Fullscreen markup/annotation',
    'Capture display under pointer (save + clipboard)', 'Toggle do not disturb',
    'Volume up', 'Volume down', 'Mute audio', 'Brightness up', 'Brightness down',
    'Notification center',
}


def editable_shortcut(bind):
    return (bind.get('dispatcher') in {'HL.Dispatcher(global)', 'HL.Dispatcher(exec_cmd)'}
            and bind.get('description') in EDITABLE_LUA_SHORTCUTS and not bind.get('submap'))


def shortcuts_info():
    binds = json.loads(run(['hyprctl', 'binds', '-j']))
    rows = []
    for bind in binds:
        if not bind.get('description'):
            continue
        mask = int(bind.get('modmask', 0))
        mods = [name for bit, name in SHORTCUT_MODIFIERS if mask & bit]
        key = bind.get('key') or f"code:{bind.get('keycode', 0)}"
        rows.append(dict(name=bind['description'], key='+'.join(mods + [str(key)]),
                         editable=editable_shortcut(bind)))
    return dict(items=sorted(rows, key=lambda row: (not row['editable'], row['name'].casefold())),
                customized=bool(shortcut_overrides()))


def save_shortcut(args):
    path = shortcut_path()
    previous = shortcut_overrides()
    desired = dict(previous)
    if args.get('reset'):
        desired.clear()
    else:
        label = args['label']
        binds = json.loads(run(['hyprctl', 'binds', '-j']))
        if not any(b.get('description') == label and editable_shortcut(b) for b in binds):
            raise ValueError('This shortcut is managed by the Hyprland configuration.')
        parts = [part.strip() for part in str(args['value']).split('+')]
        key = parts.pop()
        aliases = {name.casefold(): (bit, name.upper()) for bit, name in SHORTCUT_MODIFIERS}
        if not re.fullmatch(r'(?:[a-zA-Z0-9_]{1,48}|code:[1-9][0-9]{0,2})', key) or any(
                part.casefold() not in aliases for part in parts):
            raise ValueError('Use a shortcut such as Super+Shift+S.')
        mods = {aliases[part.casefold()] for part in parts}
        mask = sum(bit for bit, _ in mods)
        for bind in binds:
            existing = bind.get('key') or f"code:{bind.get('keycode', 0)}"
            if (bind.get('modmask') == mask and existing.casefold() == key.casefold()
                    and bind.get('description') != label):
                raise ValueError('Already used by ' + (bind.get('description') or 'another shortcut') + '.')
        desired[label] = ' + '.join([name for _, name in sorted(mods, reverse=True)] + [key])

    def write(entries):
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as target:
            for label, key in sorted(entries.items()):
                target.write(f'{label}\t{key}\n')
            temporary = target.name
        os.replace(temporary, path)

    write(desired)
    try:
        if run(['hyprctl', 'reload']).strip() != 'ok':
            raise RuntimeError('Hyprland did not reload the shortcuts.')
    except Exception:
        write(previous)
        run(['hyprctl', 'reload'], check=False)
        raise
    return shortcuts_info()


def login_items():
    result = []
    system = Path('/etc/xdg/autostart')
    personal = HOME / '.config/autostart'
    paths = {p.name: p for d in [system, personal] if d.exists() for p in d.glob('*.desktop')}
    for name, path in paths.items():
        conf = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            conf.read(path)
            entry = conf['Desktop Entry']
            result.append(dict(id=name, name=entry.get('Name', name), icon=entry.get('Icon', ''),
                               enabled=entry.get('Hidden', 'false').lower() != 'true' and entry.get('X-GNOME-Autostart-enabled', 'true').lower() != 'false',
                               description=entry.get('Comment', ''), system=path.parent == system))
        except (configparser.Error, KeyError):
            continue
    return dict(items=sorted(result, key=lambda a: a['name'].casefold()))


def privacy_info():
    nodes = json.loads(run(['pw-dump']))
    streams = []
    for node in nodes:
        props = node.get('info', {}).get('props', {})
        media = props.get('media.class', '')
        if media.startswith('Stream/'):
            streams.append(dict(name=props.get('application.name', props.get('node.name', 'Application')),
                                media=media, id=node.get('id')))
    flatpaks = []
    if shutil.which('flatpak'):
        for line in run(['flatpak', 'list', '--app', '--columns=application,name'], check=False).splitlines():
            parts = line.split('\t')
            if len(parts) >= 2:
                flatpaks.append(dict(id=parts[0], name=parts[1]))
    return dict(streams=streams, cameras=[p.name for p in Path('/dev').glob('video*')], flatpaks=flatpaks,
                secretManager=bool(shutil.which('seahorse')), backupManager=bool(shutil.which('pika-backup')))


def printer_info():
    output = run(['lpstat', '-p', '-d'], check=False) if shutil.which('lpstat') else ''
    printers = []
    default = ''
    for line in output.splitlines():
        if line.startswith('printer '):
            parts = line.split(' ', 2)
            printers.append(dict(name=parts[1], status=parts[2] if len(parts) > 2 else ''))
        elif 'destination:' in line:
            default = line.split(':', 1)[1].strip()
    jobs = run(['lpstat', '-o'], check=False).splitlines() if shutil.which('lpstat') else []
    return dict(printers=printers, default=default, jobs=jobs,
                available=run(['systemctl', 'is-active', 'cups.service'], check=False) == 'active')


def users_info():
    # NSS enumeration can be incomplete even when direct UID lookup succeeds.
    current_uid = os.getuid()
    accounts = {u.pw_uid: u for u in pwd.getpwall()
                if 1000 <= u.pw_uid < 65534 and Path(u.pw_shell).name not in {'nologin', 'false'}}
    current = pwd.getpwuid(current_uid)
    accounts[current_uid] = current
    return dict(users=[dict(name=u.pw_name, fullName=u.pw_gecos.split(',')[0], uid=u.pw_uid, home=u.pw_dir,
                           current=u.pw_uid == current_uid) for u in sorted(accounts.values(), key=lambda u: u.pw_uid)],
                declarative=Path('/etc/passwd').is_symlink())


def datetime_info():
    values = {}
    for line in run(['timedatectl', 'show', '--property=Timezone', '--property=NTP', '--property=NTPSynchronized'], check=False).splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            values[key] = value
    values['date'] = datetime.datetime.now().isoformat(timespec='seconds')
    values['locale'] = os.environ.get('LANG', '')
    return values


def updates_info():
    generations = []
    for p in sorted(Path('/nix/var/nix/profiles').glob('system-*-link'), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        generations.append(dict(name=p.name, path=str(p.resolve()), date=datetime.datetime.fromtimestamp(p.lstat().st_mtime).isoformat(timespec='minutes')))
    return dict(current=str(Path('/run/current-system').resolve()), generations=generations,
                config=str(HOME/'nixos-config'), system=system_info()['os'], check=read_json(STATE/'updates.json'))


def check_updates():
    if os.environ.get('QUICKINTOSH_PLATFORM') == 'arch':
        result = dict(changes=run(['/usr/bin/pacman','-Qu'],check=False).splitlines(),checkedAt=datetime.datetime.now().isoformat(timespec='minutes'))
        write_json(STATE/'updates.json',result)
        return result
    changes = json.loads(run(['/run/current-system/sw/bin/nix', '--json', 'update', '--all', '--dry-run'], timeout=180))
    result = dict(changes=changes, checkedAt=datetime.datetime.now().isoformat(timespec='minutes'))
    write_json(STATE/'updates.json', result)
    return result


def permissions(app):
    allowed = {a['id'] for a in privacy_info()['flatpaks']}
    if app not in allowed:
        raise ValueError('Application is not installed.')
    conf = configparser.ConfigParser(interpolation=None, strict=False)
    conf.read_string(run(['flatpak', 'info', '--show-permissions', app]))
    context = dict(conf['Context']) if conf.has_section('Context') else {}
    override = configparser.ConfigParser(interpolation=None, strict=False)
    text = run(['flatpak', 'override', '--user', '--show', app], check=False)
    if text:
        override.read_string(text)
        if override.has_section('Context'):
            for key, tokens in override['Context'].items():
                original=context.get(key, '').split(';')
                changes=tokens.split(';')
                names={token.lstrip('!').split(':',1)[0] for token in changes if token}
                context[key]=';'.join([token for token in original if token and token.lstrip('!').split(':',1)[0] not in names]+[token for token in changes if token])
    def granted(key, wanted, broader=()):
        tokens = context.get(key, '').split(';')
        def named(token):return token.split(':', 1)[0]
        positives = {named(token) for token in tokens if token and not token.startswith('!')}
        negatives = {named(token[1:]) for token in tokens if token.startswith('!')}
        return wanted not in negatives and bool(({wanted} | set(broader)) & positives)
    return dict(app=app, context=context, grants=dict(network=granted('shared','network'),
                home=granted('filesystems','home',('host',)),
                downloads=granted('filesystems','xdg-download',('home','host'))))


def validate_input(key, value):
    if key not in INPUTS:
        raise ValueError('Unsupported input setting.')
    spec = INPUTS[key]
    if spec[0] == 'bool':
        if not isinstance(value, bool):
            raise ValueError('A boolean value is required.')
    elif spec[0] in {'int', 'number'}:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not spec[1] <= value <= spec[2]:
            raise ValueError('Value is outside the supported range.')
        if spec[0] == 'int' and int(value) != value:
            raise ValueError('A whole number is required.')
    elif spec[0] == 'choice' and value not in spec[1]:
        raise ValueError('Unsupported choice.')
    elif spec[0] == 'text' and (not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_,:()+-]{0,120}', value)):
        raise ValueError('Unsupported keyboard layout or variant.')
    return value


def lua(value):
    if isinstance(value, dict):
        return '{' + ','.join('['+json.dumps(k)+']='+lua(v) for k, v in value.items()) + '}'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return json.dumps(value, ensure_ascii=False)


def apply_options(values):
    tree = {}
    for key, value in values.items():
        validate_input(key, value)
        parts = key.replace('tap-to-click', 'tap_to_click').split(':')
        branch = tree
        for part in parts[:-1]:
            branch = branch.setdefault(part, {})
        branch[parts[-1]] = value
    if tree:
        result = run(['hyprctl', 'eval', 'hl.config('+lua(tree)+')'])
        if 'error' in result.lower():
            raise RuntimeError(result)


def runtime(values=None, restore=False):
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE/'runtime.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = STATE/'runtime.json'
        instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '')
        record = read_json(path)
        if record.get('instance') != instance:
            record = dict(instance=instance, original={}, applied={})
        if restore:
            apply_options(record['original'])
            path.unlink(missing_ok=True)
            restore_files()
            return
        activate_files()
        values = values or {}
        if not values and not record['applied']:
            return
        for key, value in values.items():
            validate_input(key, value)
        current = input_values(set(values) | set(record['applied']))
        for key in values:
            if key not in current or current[key] is None:
                raise ValueError('This setting is unavailable on your compositor: '+key)
            if key not in record['original']:
                record['original'][key] = current[key]
        removed = {k: record['original'][k] for k in record['applied'] if k not in values}
        write_json(path, record)  # Save restoration data before changing anything.
        try:
            apply_options(dict(removed, **values))
            record['applied'] = values
            write_json(path, record)
        except Exception:
            apply_options({k: current[k] for k in values if k in current})
            raise


def usage_tick(app, seconds):
    if not isinstance(app, str) or len(app) > 200 or not 0 < seconds <= 120:
        raise ValueError('Invalid usage sample.')
    path = STATE/'usage.json'
    data = read_json(path)
    day = datetime.date.today().isoformat()
    values = data.setdefault(day, {})
    values[app] = round(values.get(app, 0)+seconds, 1)
    for old in sorted(data)[:-30]:
        del data[old]
    write_json(path, data)
    return data


def query(page, args=None):
    handlers = dict(system=system_info, storage=storage_info, network=network_info, input=input_info,
                    apps=applications, login=login_items, privacy=privacy_info, printers=printer_info,
                    users=users_info, datetime=datetime_info, updates=updates_info, audio=audio_info, shortcuts=shortcuts_info,
                    **{'update-check': check_updates},
                    usage=lambda: read_json(STATE/'usage.json'))
    if page == 'main':
        return json.loads(run([os.environ.get('LICKINTOSH_CLI','lickintosh'), 'ipc', 'call', 'rice', 'state']))
    if page == 'storage-details':
        return storage_info(True)
    if page == 'permissions':
        return permissions(args['app'])
    if page not in handlers:
        raise ValueError('Unknown settings page.')
    return handlers[page]()


def action(name, args):
    active = read(Path(os.environ.get('RICE_SHELL_STATE_DIR',str(Path(os.environ.get('XDG_STATE_HOME', HOME/'.local/state'))/'nixos-rice')))/'active-shell')
    if name != 'runtime-restore' and active != 'lickintosh':
        raise RuntimeError('Select Lickintosh before applying these settings. Other desktop profiles are unchanged.')
    if name == 'game-mode':
        enabled = args.get('enabled')
        if not isinstance(enabled, bool):
            raise ValueError('Game Mode must be on or off.')
        cli = os.environ.get('LICKINTOSH_CLI', 'lickintosh')
        current = json.loads(run([cli, 'ipc', 'call', 'rice', 'state']))
        if bool(current.get('gameMode')) != enabled:
            run([cli, 'ipc', 'call', 'rice', 'gameMode'])
        return json.loads(run([cli, 'ipc', 'call', 'rice', 'state']))
    if name == 'shortcut-save':
        return save_shortcut(args)
    if name == 'runtime':
        runtime(args.get('values', {}))
    elif name == 'runtime-restore':
        runtime(restore=True)
    elif name == 'usage-tick':
        return usage_tick(args['app'], float(args['seconds']))
    elif name == 'usage-clear':
        (STATE/'usage.json').unlink(missing_ok=True)
    elif name == 'default-app':
        from gi.repository import Gio
        allowed = applications()
        if args['mime'] not in allowed['defaults'] or args['app'] not in {a['id'] for a in allowed['apps']}:
            raise ValueError('Invalid application association.')
        app = Gio.DesktopAppInfo.new(args['app'])
        app.set_as_default_for_type(args['mime'])
        if args['mime'] == 'x-scheme-handler/http':
            app.set_as_default_for_type('x-scheme-handler/https')
        return dict(mime=args['mime'],app=args['app'])
    elif name in {'audio-volume', 'audio-mute', 'audio-default'}:
        audio = audio_info()
        if name == 'audio-default':
            if args['id'] not in {n['id'] for n in audio['outputs']+audio['inputs']}:
                raise ValueError('Unknown audio device.')
            command=['wpctl', 'set-default', str(args['id'])]
        else:
            if args['target'] not in {'input', 'output'}:
                raise ValueError('Unknown audio target.')
            token = '@DEFAULT_AUDIO_SINK@' if args['target'] == 'output' else '@DEFAULT_AUDIO_SOURCE@'
            if name == 'audio-volume':
                value = args['value']
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not 0 <= value <= 1.5:
                    raise ValueError('Volume is outside the supported range.')
                command=['wpctl', 'set-volume', token, str(value)]
            else:
                if not isinstance(args['value'], bool):
                    raise ValueError('Invalid mute state.')
                command=['wpctl', 'set-mute', token, '1' if args['value'] else '0']
        run([os.environ.get('LICKINTOSH_CLI','lickintosh'),'ipc','call','audioFeedback','manual'],check=False)
        run(command)
    elif name in {'network-up', 'network-down'}:
        if args['uuid'] not in {p['uuid'] for p in network_info()['profiles']}:
            raise ValueError('Unknown network profile.')
        run(['nmcli', 'connection', 'up' if name.endswith('-up') else 'down', 'uuid', args['uuid']], timeout=45)
    elif name == 'login-toggle':
        item = next((i for i in login_items()['items'] if i['id'] == args['id']), None)
        if not item:
            raise ValueError('Unknown login item.')
        target = HOME/'.config/autostart'/item['id']
        remember_file(target)
        source = target if target.exists() else Path('/etc/xdg/autostart')/item['id']
        conf = configparser.ConfigParser(interpolation=None, strict=False)
        conf.optionxform = str
        conf.read(source)
        conf['Desktop Entry']['Hidden'] = 'false' if args['enabled'] else 'true'
        conf['Desktop Entry']['X-GNOME-Autostart-enabled'] = 'true' if args['enabled'] else 'false'
        import io
        buffer = io.StringIO()
        conf.write(buffer)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        target.write_text(buffer.getvalue())
    elif name == 'printer-default':
        if args['name'] not in {p['name'] for p in printer_info()['printers']}:
            raise ValueError('Unknown printer.')
        remember_file(HOME/'.cups/lpoptions')
        run(['lpoptions', '-d', args['name']])
    elif name == 'flatpak-permission':
        permissions(args['app'])
        choices = {'network': ('--share=network', '--unshare=network'),
                   'home': ('--filesystem=home', '--nofilesystem=home'),
                   'downloads': ('--filesystem=xdg-download', '--nofilesystem=xdg-download')}
        if args['permission'] not in choices or not isinstance(args['enabled'], bool):
            raise ValueError('Unsupported permission.')
        remember_file(HOME/'.local/share/flatpak/overrides'/args['app'])
        flags=[choices[args['permission']][0 if args['enabled'] else 1]]
        if args['permission']=='home' and not args['enabled']:
            flags.append('--nofilesystem=host')
        run(['flatpak', 'override', '--user', *flags, args['app']])
    elif name == 'open-server':
        url = str(args['url'])
        parsed = urlsplit(url)
        if parsed.scheme not in {'sftp', 'smb', 'dav', 'davs', 'ftp'} or not parsed.hostname or parsed.password:
            raise ValueError('Use a server address without an embedded password.')
        subprocess.Popen(['lickintosh-finder', url], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    else:
        raise ValueError('Unknown settings action.')
    return {}


def emit(value):
    with OUTPUT:
        print(json.dumps(value, ensure_ascii=True), flush=True)


def worker():
    pool = ThreadPoolExecutor(max_workers=3)
    changes = ThreadPoolExecutor(max_workers=1)
    def handle(request):
        try:
            kind = request['kind']
            result = query(request['name'], request.get('args', {})) if kind == 'query' else action(request['name'], request.get('args', {}))
            if kind == 'action' and request['name']=='runtime':write_json(STATE/'runtime-status.json',dict(error=''))
            emit(dict(type='result', token=request.get('token', 0), name=request['name'], kind=kind, data=result))
        except Exception as error:
            if request.get('name')=='runtime':write_json(STATE/'runtime-status.json',dict(error=str(error)))
            emit(dict(type='error', token=request.get('token', 0), name=request.get('name', ''), message=str(error)))
    emit(dict(type='ready', ownerPid=os.getppid()))
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request.get('kind') not in {'query', 'action'}:
                raise ValueError('Invalid request.')
            (pool if request['kind'] == 'query' else changes).submit(handle, request)
        except Exception as error:
            emit(dict(type='error', message=str(error)))
    pool.shutdown(wait=False, cancel_futures=True)
    changes.shutdown(wait=False, cancel_futures=True)


if __name__ == '__main__':
    if '--restore' in sys.argv:
        runtime(restore=True)
    elif '--worker' in sys.argv:
        worker()
    else:
        print(json.dumps(query(sys.argv[1]), ensure_ascii=True))
