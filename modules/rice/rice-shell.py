#!/usr/bin/env python3
"""Runtime selector and action router for the installed desktop shells."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import time
from typing import Any, Sequence


MANIFEST = Path(os.environ.get("RICE_SHELL_MANIFEST", "/etc/nixos-rice/shells.json"))
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "nixos-rice"
STATE_FILE = STATE_DIR / "active-shell"
LOCK_FILE = STATE_DIR / "shell.lock"
LOG_FILE = STATE_DIR / "shell.log"
RECORD_PID_FILE = STATE_DIR / "wf-recorder.pid"
VALID_SHELLS = ("noctalia", "noctalia-legacy", "caelestia", "lickintosh", "eqsh")


class RiceError(RuntimeError):
    pass


def run(
    command: Sequence[str],
    *,
    capture: bool = False,
    check: bool = False,
    input_text: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            input=input_text,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        completed = subprocess.CompletedProcess(
            list(command),
            124,
            stdout="",
            stderr=f"command timed out after {timeout:g}s",
        )
    if check and completed.returncode:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RiceError(detail or f"command failed ({completed.returncode}): {' '.join(command)}")
    return completed


def manifest() -> dict[str, Any]:
    try:
        value = json.loads(MANIFEST.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RiceError(f"cannot read shell manifest {MANIFEST}: {exc}") from exc
    if not isinstance(value.get("shells"), dict):
        raise RiceError(f"invalid shell manifest: {MANIFEST}")
    return value


def selected() -> str:
    default = str(manifest().get("default", "noctalia"))
    try:
        value = STATE_FILE.read_text().strip().lower()
    except OSError:
        value = default
    return value if value in VALID_SHELLS else default


def set_selected(name: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(name + "\n")
    temporary.replace(STATE_FILE)


def processes() -> list[tuple[int, str, str]]:
    completed = run(["ps", "-eo", "pid=,stat=,comm=,args="], capture=True, check=True, timeout=2)
    rows: list[tuple[int, str, str]] = []
    for line in completed.stdout.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) < 4 or fields[1].startswith(("Z", "X")):
            continue
        try:
            rows.append((int(fields[0]), fields[2], fields[3]))
        except ValueError:
            continue
    return rows


def shell_pids(name: str) -> list[int]:
    quickshell_command = {
        "caelestia": "caelestia-shell",
        # Legacy sets QS_CONFIG_PATH, which conflicts with list --all.
        # Lickintosh exposes the shared Quickshell instance registry unfiltered.
        "noctalia-legacy": "lickintosh",
        "lickintosh": "lickintosh",
        "eqsh": "eqsh",
    }.get(name)
    if quickshell_command:
        completed = run([quickshell_command, "list", "--all", "-j"], capture=True, timeout=2)
        output = completed.stdout.strip()
        if "No running instances" in output + (completed.stderr or ""):
            return []
        if completed.returncode == 0 and output.startswith("["):
            try:
                return [int(item["pid"]) for item in json.loads(output)
                        if item.get("pid") and item.get("config_path", "").endswith("/shell.qml") and (
                            (name == "noctalia-legacy" and "/share/noctalia-shell/" in item.get("config_path", ""))
                            or (name == "caelestia" and "caelestia" in item.get("config_path", ""))
                            or (name == "lickintosh" and "lickintosh" in item.get("config_path", ""))
                            or (name == "eqsh" and "eqsh-source" in item.get("config_path", ""))
                        )]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass
    current = {os.getpid(), os.getppid()}
    found: list[int] = []
    for pid, command, args in processes():
        if pid in current:
            continue
        # Concurrent IPC/status clients use the same executable as the shell.
        # They are never desktop instances and must not be counted or killed.
        try:
            arguments = set(shlex.split(args)[1:])
        except ValueError:
            arguments = set(args.split()[1:])
        client_verbs = {"list", "ipc", "log", "kill", "msg", "plugins", "completions", "config", "theme", "dmenu", "firefox-theme"}
        if arguments & client_verbs:
            continue
        if name == "noctalia":
            # Linux truncates /proc/<pid>/stat's command name to 15 bytes, so
            # the wrapped binary normally appears as `.noctalia-wrapp`.
            match = (
                command == "noctalia"
                or command.startswith(".noctalia-wrap")
                or "/.noctalia-wrapped" in args
                or args.endswith("/bin/noctalia")
            )
        elif name == "caelestia":
            match = command == "caelestia-shell" or (
                command in {"qs", "quickshell", ".quickshell-wrapped"} and "caelestia" in args
            )
        elif name in {"lickintosh", "eqsh"}:
            match = command in {"qs", "quickshell", ".quickshell-wrapped", ".quickshell-wra"} and name in args
        else:
            match = command == "noctalia-legacy" or (
                command in {"qs", "quickshell", ".quickshell-wrapped", ".quickshell-wra"}
                and "noctalia-shell" in args
                and "caelestia-shell" not in args
            )
        if match:
            found.append(pid)
    return found


def lickintosh_process_stamp(pid: int) -> str:
    """Validate an exact shell process, including protection against PID reuse."""
    process = Path('/proc') / str(int(pid))
    command = (process / 'cmdline').read_bytes().split(b'\0')
    if not any(b'-lickintosh-source-' in arg for arg in command) or any(arg.endswith(b'/settings.qml') for arg in command):
        raise ValueError('not the Lickintosh shell')
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    if fields[0] in {'Z', 'X'}:
        raise ValueError('shell exited')
    return fields[19]  # Linux /proc stat field 22, process start time.


def is_running(name: str) -> bool:
    if name != 'lickintosh':
        return bool(shell_pids(name))
    cache = STATE_DIR / 'lickintosh-process.json'
    try:
        record = json.loads(cache.read_text())
        if lickintosh_process_stamp(record['pid']) == record['start']:
            return True
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        pass
    pids = shell_pids(name)
    for pid in pids:
        try:
            record = {'pid': pid, 'start': lickintosh_process_stamp(pid)}
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            temporary = cache.with_suffix(f'.{os.getpid()}.tmp')
            temporary.write_text(json.dumps(record))
            temporary.chmod(0o600)
            temporary.replace(cache)
            break
        except (OSError, ValueError, IndexError):
            continue
    return bool(pids)


def is_ready(name: str) -> bool:
    if not is_running(name):
        return False
    if name == "noctalia":
        command = ["noctalia", "msg", "status"]
    elif name == "noctalia-legacy":
        command = ["noctalia-legacy", "ipc", "show"]
    elif name in {"lickintosh", "eqsh"}:
        command = [name, "ipc", "call", "rice", "status"]
    else:
        command = ["caelestia", "shell", "drawers", "list"]
    return run(command, capture=True, timeout=2).returncode == 0


def wait_until_ready(name: str, timeout: float = 15) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_ready(name):
            return True
        time.sleep(0.2)
    return False


def terminate_pids(pids: list[int]) -> None:
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        alive = []
        for pid in pids:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except ProcessLookupError:
                pass
        if not alive:
            return
        time.sleep(0.1)
    for pid in alive:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    # SIGKILL is asynchronous. Do not report a switch failure while the kernel
    # is still completing exit, and never treat a zombie as a running desktop.
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        live = {pid for pid, _command, _args in processes()}
        if not live.intersection(alive):
            return
        time.sleep(0.05)


def stop_shell(name: str) -> None:
    if name == "caelestia" and is_running(name):
        run(["caelestia", "shell", "-k"], capture=True)
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline and is_running(name):
            time.sleep(0.1)
    elif name in {"noctalia-legacy", "lickintosh", "eqsh"} and is_running(name):
        if name == "lickintosh":
            run([name, "ipc", "call", "rice", "prepareStop"], capture=True, timeout=2)
            time.sleep(0.2)
        run([name, "kill"], capture=True, timeout=3)
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline and is_running(name):
            time.sleep(0.1)
    remaining = shell_pids(name)
    if remaining:
        terminate_pids(remaining)
    if is_running(name):
        raise RiceError(f"could not stop {name}")
    if name == "lickintosh":
        # Standalone Settings must not keep writing preferences after rice exit.
        settings = [pid for pid, _command, args in processes()
                    if any(arg.endswith('/settings.qml') and '-lickintosh-source-' in arg for arg in args.split())]
        if settings:
            terminate_pids(settings)
        run(["lickintosh", "settings-restore"], check=True, timeout=15)
        run(["lickintosh-desktop-profile", "leave"], check=True)


def stop_all() -> None:
    for name in VALID_SHELLS:
        stop_shell(name)


def start_shell(name: str) -> None:
    if name not in VALID_SHELLS:
        raise RiceError(f"unknown shell: {name}")
    if is_ready(name):
        return
    if is_running(name):
        if wait_until_ready(name):
            return
        stop_shell(name)
    run(["lickintosh-desktop-profile", "enter" if name == "lickintosh" else "leave"], check=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    commands = {
        "noctalia": ["noctalia", "--daemon"],
        "noctalia-legacy": ["noctalia-legacy", "--no-duplicate", "--daemonize"],
        "caelestia": ["caelestia", "shell", "-d"],
        # Popen below already detaches. Keep the native preview and GUI in one
        # directly managed process instead of forking the Qt application twice.
        "lickintosh": ["lickintosh", "--no-duplicate"],
        "eqsh": ["eqsh", "--no-duplicate", "--daemonize"],
    }
    command = commands[name]
    with LOG_FILE.open("a") as log:
        log.write(f"\n[{time.strftime('%Y-%m-%dT%H:%M:%S')}] starting {name}\n")
        log.flush()
        subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
    if wait_until_ready(name):
        return
    raise RiceError(f"{name} did not start; inspect {LOG_FILE}")


def reload_hyprland() -> None:
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        run(["hyprctl", "reload"], capture=True)


def switch_shell(name: str) -> None:
    if name not in VALID_SHELLS:
        raise RiceError(f"unknown shell: {name}; choose {', '.join(VALID_SHELLS)}")
    previous = selected()
    if name == previous and is_running(name) and not any(is_running(other) for other in VALID_SHELLS if other != name):
        return
    try:
        stop_all()
        set_selected(name)
        start_shell(name)
    except Exception:
        set_selected(previous)
        try:
            if name != previous:
                stop_shell(name)
            start_shell(previous)
        except Exception as rollback_error:
            raise RiceError(f"switch failed and rollback failed: {rollback_error}")
        reload_hyprland()
        raise
    reload_hyprland()


def ensure_running() -> str:
    name = selected()
    for other in VALID_SHELLS:
        if other != name and is_running(other):
            stop_shell(other)
    start_shell(name)
    return name


NOCTALIA_ACTIONS: dict[str, list[str]] = {
    "launcher": ["noctalia", "msg", "panel-toggle", "launcher"],
    "emoji": ["noctalia", "msg", "panel-toggle", "launcher", "/emo"],
    "command-runner": ["noctalia", "msg", "panel-toggle", "launcher"],
    "clipboard": ["noctalia", "msg", "panel-toggle", "clipboard"],
    "control-center": ["noctalia", "msg", "panel-toggle", "control-center"],
    "bar-toggle": ["noctalia", "msg", "bar-toggle"],
    "settings": ["noctalia", "msg", "settings-open"],
    "session": ["noctalia", "msg", "panel-toggle", "session"],
    "lock": ["noctalia", "msg", "session", "lock"],
    "wallpaper-picker": ["noctalia", "msg", "panel-toggle", "wallpaper"],
    "wallpaper-random": ["noctalia", "msg", "wallpaper-random"],
    "theme-mode": ["noctalia", "msg", "theme-mode-toggle"],
    "nightlight": ["noctalia", "msg", "nightlight-toggle"],
    "dpms-off": ["noctalia", "msg", "dpms-off"],
    "desktop-widgets": ["noctalia", "msg", "desktop-widgets-toggle-edit"],
    "screenshot-region": ["noctalia", "msg", "screenshot-region"],
    "dnd": ["noctalia", "msg", "notification-dnd-toggle"],
    "volume-up": ["noctalia", "msg", "volume-up"],
    "volume-down": ["noctalia", "msg", "volume-down"],
    "volume-mute": ["noctalia", "msg", "volume-mute"],
    "brightness-up": ["noctalia", "msg", "brightness-up"],
    "brightness-down": ["noctalia", "msg", "brightness-down"],
    "notifications": ["noctalia", "msg", "panel-toggle", "control-center", "notifications"],
}


NOCTALIA_LEGACY_ACTIONS: dict[str, list[str]] = {
    "launcher": ["noctalia-legacy", "ipc", "call", "launcher", "toggle"],
    "emoji": ["noctalia-legacy", "ipc", "call", "launcher", "emoji"],
    "command-runner": ["noctalia-legacy", "ipc", "call", "launcher", "command"],
    "clipboard": ["noctalia-legacy", "ipc", "call", "plugin:clipboard", "toggle"],
    "control-center": ["noctalia-legacy", "ipc", "call", "controlCenter", "toggle"],
    "bar-toggle": ["noctalia-legacy", "ipc", "call", "bar", "toggle"],
    "settings": ["noctalia-legacy", "ipc", "call", "settings", "open"],
    "session": ["noctalia-legacy", "ipc", "call", "sessionMenu", "toggle"],
    "lock": ["noctalia-legacy", "ipc", "call", "lockScreen", "lock"],
    "keybinds": ["noctalia-legacy", "ipc", "call", "plugin:keybind-cheatsheet", "toggle"],
    "wallpaper-picker": ["noctalia-legacy", "ipc", "call", "wallpaper", "toggle"],
    "wallpaper-random": ["noctalia-legacy", "ipc", "call", "wallpaper", "random", "all"],
    "theme-mode": ["noctalia-legacy", "ipc", "call", "darkMode", "toggle"],
    "nightlight": ["noctalia-legacy", "ipc", "call", "nightLight", "toggle"],
    "dpms-off": ["noctalia-legacy", "ipc", "call", "monitors", "off"],
    "desktop-widgets": ["noctalia-legacy", "ipc", "call", "desktopWidgets", "edit"],
    "screenshot-region": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "choose"],
    "ocr": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "ocr"],
    "lens": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "lens"],
    "dnd": ["noctalia-legacy", "ipc", "call", "notifications", "toggleDND"],
    "volume-up": ["noctalia-legacy", "ipc", "call", "volume", "increase"],
    "volume-down": ["noctalia-legacy", "ipc", "call", "volume", "decrease"],
    "volume-mute": ["noctalia-legacy", "ipc", "call", "volume", "muteOutput"],
    "brightness-up": ["noctalia-legacy", "ipc", "call", "brightness", "increase"],
    "brightness-down": ["noctalia-legacy", "ipc", "call", "brightness", "decrease"],
    "notifications": ["noctalia-legacy", "ipc", "call", "notifications", "toggleHistory"],
}


CAELESTIA_ACTIONS: dict[str, list[str]] = {
    "keep-awake": ["caelestia", "shell", "idleInhibitor", "toggle"],
    "launcher": ["caelestia", "shell", "drawers", "toggle", "launcher"],
    "emoji": ["caelestia", "emoji", "-p"],
    "command-runner": ["caelestia", "shell", "drawers", "toggle", "launcher"],
    "clipboard": ["caelestia", "clipboard"],
    "control-center": ["caelestia", "shell", "drawers", "toggle", "dashboard"],
    "bar-toggle": ["caelestia", "shell", "drawers", "toggle", "bar"],
    "settings": ["caelestia", "shell", "nexus", "open"],
    "session": ["caelestia", "shell", "drawers", "toggle", "session"],
    "lock": ["caelestia", "shell", "lock", "lock"],
    "wallpaper-random": ["caelestia", "wallpaper", "-r", str(Path.home() / "Pictures/Wallpapers")],
    "screenshot-region": ["caelestia", "screenshot", "--region"],
    "dnd": ["caelestia", "shell", "notifs", "toggleDnd"],
    "volume-up": ["wpctl", "set-volume", "--limit", "1.5", "@DEFAULT_AUDIO_SINK@", "5%+"],
    "volume-down": ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"],
    "volume-mute": ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
    "brightness-up": ["caelestia", "shell", "brightness", "set", "+5%"],
    "brightness-down": ["caelestia", "shell", "brightness", "set", "5%-"],
    "notifications": ["caelestia", "shell", "drawers", "toggle", "sidebar"],
    "dpms-off": ["hyprctl", "dispatch", "dpms", "off"],
}


NOCTALIA_ACTIONS.update({
    "dock-toggle": ["noctalia", "msg", "dock-toggle"],
    "keep-awake": ["noctalia", "msg", "caffeine-toggle"],
    "annotate-fullscreen": ["noctalia", "msg", "annotate"],
})
NOCTALIA_LEGACY_ACTIONS.update({
    "profiles": ["noctalia-legacy", "ipc", "call", "plugin:shell-profiles", "toggleProfiles"],
    "keep-awake": ["noctalia-legacy", "ipc", "call", "idleInhibitor", "toggle"],
    "dock-toggle": ["noctalia-legacy", "ipc", "call", "dock", "toggle"],
    "screen-toolkit": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "toggle"],
    "annotate-fullscreen": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "annotateFullscreen"],
})
LICKINTOSH_ACTIONS = {
    action: ["lickintosh", "ipc", "call", "rice", method]
    for action, method in {
        "launcher": "launcher", "launchpad": "launchpad", "spotlight": "spotlight", "command-runner": "command", "emoji": "emoji",
        "control-center": "controlCenter", "bar-toggle": "bar", "dock-toggle": "dock",
        "settings": "settings", "session": "session", "notifications": "notifications",
        "wallpaper-picker": "wallpaper", "theme-mode": "theme", "nightlight": "nightlight",
        "desktop-widgets": "widgets", "dnd": "dnd", "ai": "ai", "game-mode": "gameMode",
        "keep-awake": "keepAwake",
    }.items()
}
LICKINTOSH_ACTIONS.update({
    "switcher-next": ["lickintosh", "ipc", "call", "switcher", "next"],
    "switcher-prev": ["lickintosh", "ipc", "call", "switcher", "prev"],
    "lock": ["lickintosh", "ipc", "call", "lock", "lock"],
    "clipboard": ["lickintosh", "ipc", "call", "rice", "clipboard"],
    "volume-up": CAELESTIA_ACTIONS["volume-up"],
    "volume-down": CAELESTIA_ACTIONS["volume-down"],
    "volume-mute": CAELESTIA_ACTIONS["volume-mute"],
    "brightness-up": ["lickintosh", "brightness", "change", "5"],
    "brightness-down": ["lickintosh", "brightness", "change", "-5"],
    "dpms-off": ["hyprctl", "dispatch", "dpms", "off"],
    "screenshot-region": ["lickintosh", "ipc", "call", "capture", "region"],
    "screenshot-fullscreen": ["lickintosh", "ipc", "call", "capture", "fullscreen"],
    "screen-toolkit": ["lickintosh", "ipc", "call", "capture", "hub"],
    "annotate-fullscreen": ["lickintosh", "ipc", "call", "capture", "annotate"],
    "ocr": ["lickintosh", "ipc", "call", "capture", "ocr"],
    "color-picker": ["lickintosh", "ipc", "call", "capture", "colorPicker"],
    "palette": ["lickintosh", "ipc", "call", "capture", "palette"],
    "qr": ["lickintosh", "ipc", "call", "capture", "qr"],
    "lens": ["lickintosh", "ipc", "call", "capture", "lens"],
    "measure": ["lickintosh", "ipc", "call", "capture", "measure"],
    "screen-record": ["lickintosh", "ipc", "call", "capture", "record"],
    "screen-record-audio": ["lickintosh", "ipc", "call", "capture", "recordAudio"],
})
EQSH_ACTIONS = {
    action: ["eqsh", "ipc", "call", *args]
    for action, args in {
        "launcher": ["rice", "launchpad"], "launchpad": ["rice", "launchpad"],
        "spotlight": ["rice", "spotlight"], "command-runner": ["rice", "command"],
        "clipboard": ["rice", "clipboard"], "control-center": ["rice", "controlCenter"],
        "settings": ["settings", "toggle"], "ai": ["ai", "toggle"],
        "notifications": ["notificationCenter", "toggle"], "dnd": ["doNotDisturb", "toggle"],
        "bar-toggle": ["rice", "bar"], "dock-toggle": ["rice", "dock"],
        "theme-mode": ["rice", "theme"], "wallpaper-picker": ["rice", "wallpaper"],
        "desktop-widgets": ["widgets", "toggleEditMode"], "session": ["rice", "session"],
        "lock": ["lock", "lock"], "screen-toolkit": ["screenshot", "open"],
        "screenshot-region": ["screenshot", "region"],
        "notch-active": ["notch", "activateInstance"], "notch-info": ["notch", "informInstance"],
    }.items()
}
EQSH_ACTIONS.update({name: LICKINTOSH_ACTIONS[name] for name in (
    "volume-up", "volume-down", "volume-mute", "brightness-up", "brightness-down", "dpms-off")})

ACTION_TABLES = {"noctalia": NOCTALIA_ACTIONS, "noctalia-legacy": NOCTALIA_LEGACY_ACTIONS,
                 "caelestia": CAELESTIA_ACTIONS, "lickintosh": LICKINTOSH_ACTIONS, "eqsh": EQSH_ACTIONS}


def supported_actions(shell: str) -> set[str]:
    actions = set(ACTION_TABLES[shell]) | {"screen-record", "screen-record-audio", "keybinds"}
    if shell == "caelestia":
        actions |= {"wallpaper-picker", "theme-mode", "nightlight"}
    return actions


def choose_with_fuzzel(lines: list[str], prompt: str) -> str:
    completed = run(["fuzzel", "--dmenu", "--prompt", prompt], capture=True, input_text="\n".join(lines) + "\n")
    return completed.stdout.strip() if completed.returncode == 0 else ""


def show_keybinds() -> None:
    completed = run(["hyprctl", "binds", "-j"], capture=True, check=True)
    try:
        bindings = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RiceError(f"could not parse Hyprland keybinds: {exc}") from exc
    rows = []
    for bind in bindings:
        description = str(bind.get("description") or "").strip()
        if not description:
            continue
        try:
            mask = int(bind.get("modmask") or 0)
        except (TypeError, ValueError):
            mask = 0
        modifier_bits = ((64, "SUPER"), (4, "CTRL"), (8, "ALT"), (1, "SHIFT"))
        mods = "+".join(label for bit, label in modifier_bits if mask & bit)
        key = str(bind.get("key") or bind.get("keycode") or "")
        shortcut = "+".join(value for value in (mods, key) if value)
        rows.append(f"{shortcut:<30} {description}")
    choose_with_fuzzel(sorted(set(rows), key=str.casefold), "Keybinds: ")


def wallpaper_picker() -> None:
    completed = run(["caelestia", "shell", "wallpaper", "list"], capture=True, check=True)
    paths = [line for line in completed.stdout.splitlines() if line.strip()]
    choice = choose_with_fuzzel(paths, "Wallpaper: ")
    if choice:
        run(["caelestia", "wallpaper", "-f", choice], check=True)


def toggle_caelestia_theme() -> None:
    completed = run(["caelestia", "scheme", "get", "-m"], capture=True, check=True)
    current = completed.stdout.strip().casefold()
    target = "light" if current == "dark" else "dark"
    run(["caelestia", "scheme", "set", "-m", target], check=True)


def toggle_nightlight() -> None:
    pids = [pid for pid, command, _args in processes() if command == "hyprsunset"]
    if pids:
        terminate_pids(pids)
        return
    subprocess.Popen(
        ["hyprsunset", "--temperature", "4000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def record_screen(with_audio: bool) -> None:
    try:
        pid = int(RECORD_PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGINT)
        RECORD_PID_FILE.unlink(missing_ok=True)
        return
    except (OSError, ValueError, ProcessLookupError):
        RECORD_PID_FILE.unlink(missing_ok=True)
    geometry = run(["slurp"], capture=True).stdout.strip()
    if not geometry:
        return
    videos = Path.home() / "Videos"
    videos.mkdir(parents=True, exist_ok=True)
    output = videos / f"recording-{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    command = ["wf-recorder", "-g", geometry, "-f", str(output)]
    if with_audio:
        command.append("--audio")
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    RECORD_PID_FILE.write_text(str(process.pid) + "\n")


def action(name: str) -> None:
    # Keybinds must NEVER start, stop or switch a desktop shell. Only explicit
    # lifecycle commands may do that. Holding the lifecycle lock during IPC
    # also prevents a queued shortcut from reaching the shell after a switch.
    active = selected()
    if name not in supported_actions(active):
        raise RiceError(f"action not supported by {active}: {name}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # discard keys pressed while switching instead of replaying them
        if selected() != active or not is_running(active):
            return
        if name in ACTION_TABLES[active] and (active, name) not in {("caelestia", "screenshot-region"), ("caelestia", "clipboard"), ("caelestia", "emoji")}:
            run(ACTION_TABLES[active][name], check=True, timeout=10)
            return
    # Interactive helpers do not retain the lifecycle lock.
    if name in {"screen-record", "screen-record-audio"}:
        # Keep recording shell-independent and silent: the upstream Caelestia
        # recorder always invokes notify-send, which this setup intentionally
        # does not use.
        record_screen(name.endswith("audio"))
        return
    if active in {"lickintosh", "noctalia", "eqsh"} and name == "keybinds":
        show_keybinds()
        return
    if active == "lickintosh":
        if name == "keybinds":
            show_keybinds()
            return
        command = LICKINTOSH_ACTIONS.get(name)
    elif active == "caelestia":
        if name == "keybinds":
            show_keybinds()
            return
        if name == "wallpaper-picker":
            wallpaper_picker()
            return
        if name == "theme-mode":
            toggle_caelestia_theme()
            return
        if name == "nightlight":
            toggle_nightlight()
            return
        command = CAELESTIA_ACTIONS.get(name)
    elif active == "eqsh":
        command = EQSH_ACTIONS.get(name)
    elif active == "noctalia-legacy":
        command = NOCTALIA_LEGACY_ACTIONS.get(name)
    else:
        command = NOCTALIA_ACTIONS.get(name)
    if not command:
        raise RiceError(f"action not supported by {active}: {name}")
    run(command, check=True)


def status() -> dict[str, Any]:
    data = manifest()
    active = selected()
    shells = []
    for name in VALID_SHELLS:
        metadata = data["shells"].get(name, {})
        shells.append(
            {
                "name": "quickintosh" if name == "lickintosh" else name,
                "label": metadata.get("label", name.title()),
                "version": metadata.get("version", "unknown"),
                "selected": name == active,
                "running": is_running(name),
            }
        )
    return {"active": active, "shells": shells, "stateFile": str(STATE_FILE), "logFile": str(LOG_FILE)}


def print_status(*, json_mode: bool = False) -> None:
    value = status()
    if json_mode:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
        return
    for item in value["shells"]:
        marks = []
        if item["selected"]:
            marks.append("selected")
        if item["running"]:
            marks.append("running")
        suffix = f"  [{', '.join(marks)}]" if marks else ""
        print(f"{item['name']:<18} {item['version']:<28} {item['label']}{suffix}")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="rice-shell", description="Select and control the active desktop shell")
    sub = value.add_subparsers(dest="command", required=True)
    for name in ("list", "status"):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true")
    switch = sub.add_parser("switch")
    switch.add_argument("name", choices=(*VALID_SHELLS, "quickintosh"))
    switch.add_argument("--json", action="store_true")
    capabilities = sub.add_parser("capabilities")
    capabilities.add_argument("--lua", action="store_true")
    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("restart")
    sub.add_parser("toggle")
    action_parser = sub.add_parser("action")
    action_parser.add_argument("name")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if getattr(args, "name", None) == "quickintosh" and args.command == "switch":
        args.name = "lickintosh"  # Preserve existing state, IPC and private settings paths.
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == "capabilities":
        actions = sorted(supported_actions(selected()))
        print("return {" + ",".join('["' + a + '"]=true' for a in actions) + "}" if args.lua else json.dumps(actions))
        return 0

    # Read-only inspection must never wait behind a launcher, screenshot
    # selector or another interactive desktop action.
    if args.command in {"list", "status"}:
        print_status(json_mode=args.json)
        return 0

    # action() acquires the lock only for its short lifecycle check and then
    # releases it before dispatching IPC or waiting for user interaction.
    if args.command == "action":
        action(args.name)
        return 0

    with LOCK_FILE.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.command == "switch":
            switch_shell(args.name)
            if args.json:
                print(json.dumps(status(), ensure_ascii=False, indent=2, sort_keys=True))
            else:
                item = manifest()["shells"][args.name]
                print(f"active shell: {item['label']} {item['version']}")
        elif args.command == "start":
            ensure_running()
        elif args.command == "stop":
            stop_all()
        elif args.command == "restart":
            name = selected()
            stop_all()
            start_shell(name)
        elif args.command == "toggle":
            name = selected()
            stop_shell(name) if is_running(name) else start_shell(name)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RiceError as exc:
        print(f"rice-shell: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        raise SystemExit(130)
