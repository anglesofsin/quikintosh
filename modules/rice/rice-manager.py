#!/usr/bin/env python3
"""Transactional rice profiles for the selected desktop shell."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Sequence


HOME = Path(os.environ.get("RICE_HOME", str(Path.home()))).expanduser().resolve()
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", str(HOME / ".config"))).expanduser().resolve()
STATE_DIR = Path(
    os.environ.get("RICE_STATE_DIR", os.environ.get("XDG_STATE_HOME", str(HOME / ".local/state")) + "/nixos-rice")
).expanduser().resolve()
CATALOG_FILE = Path(os.environ.get("RICE_CATALOG", "/etc/nixos-rice/rices.json"))
USER_CATALOG_DIR = Path(os.environ.get("RICE_USER_CATALOG", str(CONFIG_HOME / "nixos-rice/rices")))
WALLPAPER_DIR = Path(os.environ.get("RICE_WALLPAPER_DIR", str(HOME / "Pictures/Wallpapers"))).expanduser().resolve()
SHELL_STATE_FILE = Path(os.environ.get("RICE_ACTIVE_SHELL_FILE", str(STATE_DIR / "active-shell")))
SHELL_BIN = os.environ.get("RICE_SHELL_BIN", "/run/current-system/sw/bin/rice-shell")
ACTIVE_FILE = STATE_DIR / "active-rices.json"
HISTORY_FILE = STATE_DIR / "rice-history.json"
SNAPSHOT_DIR = STATE_DIR / "rice-snapshots"
LOCK_FILE = STATE_DIR / "rice.lock"
VALID_SHELLS = ("noctalia", "noctalia-legacy", "caelestia", "lickintosh")
PROFILE_SHELLS = VALID_SHELLS[:-1]
SUPPORTED_APPS = {"kitty", "fuzzel", "btop", "cava", "gtk", "qt"}
PALETTE_KEYS = {
    "background",
    "surface",
    "surfaceAlt",
    "foreground",
    "muted",
    "primary",
    "secondary",
    "accent",
    "success",
    "warning",
    "error",
    "terminal",
}
NOCTALIA_SCHEMES = {
    "m3-tonal-spot", "m3-content", "m3-fruit-salad", "m3-rainbow", "m3-monochrome",
    "vibrant", "faithful", "dysfunctional", "muted",
}
LEGACY_SCHEMES = {
    "tonal-spot", "content", "fruit-salad", "rainbow", "monochrome",
    "vibrant", "faithful", "dysfunctional", "muted",
}
CAELESTIA_VARIANTS = {"tonalspot", "vibrant", "expressive", "fidelity", "fruitsalad", "monochrome", "neutral", "rainbow", "content"}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SCHEME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
BEGIN = "# BEGIN NIXOS RICE (managed)"
END = "# END NIXOS RICE (managed)"


class RiceError(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, json.JSONDecodeError) as exc:
        raise RiceError(f"cannot read {path}: {exc}") from exc


def atomic_write(path: Path, content: str, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode if mode is not None else (previous_mode or 0o600))
        temporary.replace(path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def validate_profile(identifier: str, value: Any, source: Path) -> dict[str, Any]:
    if not ID_RE.fullmatch(identifier):
        raise RiceError(f"invalid rice id {identifier!r} in {source}")
    if not isinstance(value, dict):
        raise RiceError(f"rice {identifier!r} in {source} is not an object")
    missing = {"label", "description", "shells", "wallpaper", "mode", "apps", "palette"} - set(value)
    if missing:
        raise RiceError(f"rice {identifier!r} is missing: {', '.join(sorted(missing))}")
    shells = value["shells"]
    if not isinstance(shells, list) or not shells or len(shells) != len(set(shells)) or any(item not in PROFILE_SHELLS for item in shells):
        raise RiceError(f"rice {identifier!r} has invalid shells")
    if not isinstance(value["label"], str) or not value["label"].strip() or not isinstance(value["description"], str):
        raise RiceError(f"rice {identifier!r} has invalid metadata")
    if not isinstance(value["wallpaper"], str) or not value["wallpaper"].strip():
        raise RiceError(f"rice {identifier!r} has invalid wallpaper")
    apps = value["apps"]
    if not isinstance(apps, list) or not apps or len(apps) != len(set(apps)) or any(app not in SUPPORTED_APPS for app in apps):
        raise RiceError(f"rice {identifier!r} has invalid app integrations")
    if value["mode"] not in {"dark", "light"}:
        raise RiceError(f"rice {identifier!r} has invalid mode")
    palette = value["palette"]
    if not isinstance(palette, dict) or PALETTE_KEYS - set(palette):
        raise RiceError(f"rice {identifier!r} has an incomplete palette")
    for key in PALETTE_KEYS - {"terminal"}:
        if not isinstance(palette[key], str) or not HEX_RE.fullmatch(palette[key]):
            raise RiceError(f"rice {identifier!r} has an invalid {key} colour")
    terminal = palette["terminal"]
    if not isinstance(terminal, list) or len(terminal) != 16 or any(not isinstance(c, str) or not HEX_RE.fullmatch(c) for c in terminal):
        raise RiceError(f"rice {identifier!r} must define 16 terminal colours")
    options = value.get("shellOptions", {})
    if not isinstance(options, dict):
        raise RiceError(f"rice {identifier!r} has invalid shell options")
    for shell_name, shell_options in options.items():
        if shell_name not in VALID_SHELLS or not isinstance(shell_options, dict):
            raise RiceError(f"rice {identifier!r} has invalid options for {shell_name}")
    if "noctalia" in shells:
        scheme = options.get("noctalia", {}).get("wallpaperScheme", "muted")
        if scheme not in NOCTALIA_SCHEMES:
            raise RiceError(f"rice {identifier!r} has invalid Noctalia wallpaper scheme: {scheme}")
    if "noctalia-legacy" in shells:
        scheme = options.get("noctalia-legacy", {}).get("generationMethod", "tonal-spot")
        if scheme not in LEGACY_SCHEMES:
            raise RiceError(f"rice {identifier!r} has invalid Noctalia legacy generation method: {scheme}")
    if "caelestia" in shells:
        caelestia = options.get("caelestia", {})
        name = caelestia.get("name", "dynamic")
        flavour = caelestia.get("flavour", "default")
        variant = caelestia.get("variant", "tonalspot")
        if not isinstance(name, str) or not SCHEME_RE.fullmatch(name) or not isinstance(flavour, str) or not SCHEME_RE.fullmatch(flavour):
            raise RiceError(f"rice {identifier!r} has malformed Caelestia scheme/flavour: {name}/{flavour}")
        if variant not in CAELESTIA_VARIANTS:
            raise RiceError(f"rice {identifier!r} has invalid Caelestia variant: {variant}")
    result = dict(value)
    result["id"] = identifier
    result["source"] = str(source)
    return result


def load_catalog() -> dict[str, dict[str, Any]]:
    document = read_json(CATALOG_FILE)
    if not isinstance(document, dict) or document.get("schemaVersion") != 1 or not isinstance(document.get("rices"), dict):
        raise RiceError(f"invalid rice catalog: {CATALOG_FILE}")
    values = {
        identifier: validate_profile(identifier, profile, CATALOG_FILE)
        for identifier, profile in document["rices"].items()
    }
    if USER_CATALOG_DIR.exists():
        for path in sorted(USER_CATALOG_DIR.glob("*.json")):
            user_document = read_json(path)
            entries = user_document.get("rices") if isinstance(user_document, dict) and "rices" in user_document else user_document
            if not isinstance(entries, dict):
                raise RiceError(f"personal rice file must contain an object: {path}")
            for identifier, profile in entries.items():
                values[identifier] = validate_profile(identifier, profile, path)
    return values


def selected_shell(explicit: str | None = None) -> str:
    if explicit:
        if explicit not in VALID_SHELLS:
            raise RiceError(f"unknown shell: {explicit}")
        return explicit
    try:
        name = SHELL_STATE_FILE.read_text(encoding="utf-8").strip().casefold()
    except OSError:
        name = "noctalia"
    return name if name in VALID_SHELLS else "noctalia"


def wallpaper_path(profile: dict[str, Any]) -> Path:
    value = Path(str(profile["wallpaper"])).expanduser()
    path = value if value.is_absolute() else WALLPAPER_DIR / value
    resolved = path.resolve()
    if not resolved.is_file():
        raise RiceError(f"wallpaper not found: {resolved}")
    return resolved


def active_map() -> dict[str, Any]:
    value = read_json(ACTIVE_FILE, {"schemaVersion": 1, "shells": {}})
    if not isinstance(value, dict) or not isinstance(value.get("shells"), dict):
        return {"schemaVersion": 1, "shells": {}}
    return value


def targets_for(shell: str) -> list[Path]:
    common = [
        CONFIG_HOME / "kitty/kitty.conf",
        CONFIG_HOME / "kitty/themes/nixos-rice.conf",
        CONFIG_HOME / "fuzzel/fuzzel.ini",
        CONFIG_HOME / "btop/btop.conf",
        CONFIG_HOME / "btop/themes/nixos-rice.theme",
        CONFIG_HOME / "cava/config",
        CONFIG_HOME / "gtk-3.0/gtk.css",
        CONFIG_HOME / "gtk-3.0/nixos-rice.css",
        CONFIG_HOME / "gtk-4.0/gtk.css",
        CONFIG_HOME / "gtk-4.0/nixos-rice.css",
        CONFIG_HOME / "qt6ct/qt6ct.conf",
        CONFIG_HOME / "qt6ct/colors/nixos-rice.conf",
        ACTIVE_FILE,
    ]
    shell_targets = {
        "noctalia": [
            CONFIG_HOME / "noctalia/config.toml",
            HOME / ".local/state/noctalia/settings.toml",
            CONFIG_HOME / "kitty/themes/noctalia.conf",
            CONFIG_HOME / "gtk-3.0/noctalia.css",
            CONFIG_HOME / "gtk-4.0/noctalia.css",
            CONFIG_HOME / "qt6ct/colors/noctalia.conf",
            CONFIG_HOME / "hypr/noctalia/noctalia-colors.lua",
            CONFIG_HOME / "hypr/borders.conf",
            CONFIG_HOME / "nvim/lua/matugen.lua",
            CONFIG_HOME / "spicetify/Themes/Comfy/color.ini",
        ],
        "noctalia-legacy": [
            CONFIG_HOME / "noctalia-legacy/settings.json",
            CONFIG_HOME / "noctalia-legacy/colors.json",
            HOME / ".cache/noctalia-legacy/wallpapers.json",
        ],
        "caelestia": [
            HOME / ".local/state/caelestia/scheme.json",
            HOME / ".local/state/caelestia/wallpaper/path.txt",
            CONFIG_HOME / "caelestia/shell.json",
        ],
    }
    return common + shell_targets.get(shell, [])


def profile_summary(profile: dict[str, Any], shell: str, active: dict[str, Any]) -> dict[str, Any]:
    current = active.get("shells", {}).get(shell, {})
    return {
        "id": profile["id"],
        "label": profile["label"],
        "description": profile["description"],
        "shells": profile["shells"],
        "compatible": shell in profile["shells"],
        "active": current.get("rice") == profile["id"],
        "mode": profile["mode"],
        "wallpaper": str((WALLPAPER_DIR / profile["wallpaper"]).resolve()) if not Path(profile["wallpaper"]).is_absolute() else profile["wallpaper"],
        "apps": profile["apps"],
        "source": profile["source"],
    }


def list_value(shell: str, *, include_all: bool = False) -> dict[str, Any]:
    catalog = load_catalog()
    active = active_map()
    profiles = [profile_summary(profile, shell, active) for profile in catalog.values()]
    if not include_all:
        profiles = [profile for profile in profiles if profile["compatible"]]
    profiles.sort(key=lambda profile: (not profile["active"], profile["label"].casefold()))
    return {"shell": shell, "active": active.get("shells", {}).get(shell), "rices": profiles}


def show_value(identifier: str, shell: str) -> dict[str, Any]:
    catalog = load_catalog()
    if identifier not in catalog:
        raise RiceError(f"unknown rice: {identifier}")
    profile = catalog[identifier]
    value = profile_summary(profile, shell, active_map())
    value["palette"] = profile["palette"]
    value["shellOptions"] = profile.get("shellOptions", {})
    return value


def plan_value(identifier: str, shell: str) -> dict[str, Any]:
    catalog = load_catalog()
    if identifier not in catalog:
        raise RiceError(f"unknown rice: {identifier}")
    profile = catalog[identifier]
    if shell not in profile["shells"]:
        raise RiceError(f"rice {identifier!r} is not compatible with {shell}")
    wallpaper = wallpaper_path(profile)
    return {
        "action": "apply",
        "rice": identifier,
        "label": profile["label"],
        "shell": shell,
        "mode": profile["mode"],
        "wallpaper": str(wallpaper),
        "apps": profile["apps"],
        "targets": [str(path) for path in targets_for(shell)],
        "backup": str(SNAPSHOT_DIR),
        "restart": shell == "noctalia-legacy",
    }


def snapshot(identifier: str, shell: str, targets: Sequence[Path]) -> tuple[str, Path]:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    snapshot_id = f"{stamp}-{shell}-{identifier}"
    root = SNAPSHOT_DIR / snapshot_id
    files = root / "files"
    files.mkdir(parents=True, exist_ok=False)
    entries = []
    for index, path in enumerate(dict.fromkeys(targets)):
        entry: dict[str, Any] = {"path": str(path), "existed": path.exists() or path.is_symlink()}
        if entry["existed"]:
            if path.is_symlink():
                entry["symlink"] = os.readlink(path)
            elif path.is_file():
                backup_name = f"{index:03d}-{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
                shutil.copy2(path, files / backup_name)
                entry["backup"] = backup_name
            else:
                raise RiceError(f"refusing to snapshot non-file target: {path}")
        entries.append(entry)
    write_json(
        root / "snapshot.json",
        {"schemaVersion": 1, "id": snapshot_id, "createdAt": now(), "rice": identifier, "shell": shell, "entries": entries},
    )
    return snapshot_id, root


def assert_home_path(path: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(HOME)
    except ValueError as exc:
        raise RiceError(f"refusing to restore path outside home: {path}") from exc


def restore_snapshot(root: Path) -> dict[str, Any]:
    document = read_json(root / "snapshot.json")
    if not isinstance(document, dict) or not isinstance(document.get("entries"), list):
        raise RiceError(f"invalid snapshot: {root}")
    for entry in reversed(document["entries"]):
        path = Path(entry["path"])
        assert_home_path(path)
        if entry.get("existed"):
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() or path.is_symlink():
                path.unlink()
            if "symlink" in entry:
                path.symlink_to(entry["symlink"])
            else:
                shutil.copy2(root / "files" / entry["backup"], path)
        elif path.exists() or path.is_symlink():
            if path.is_dir() and not path.is_symlink():
                raise RiceError(f"refusing to remove directory during rollback: {path}")
            path.unlink()
    return document


def managed_block(content: str, body: str, *, comment: str = "#") -> str:
    begin = BEGIN.replace("#", comment, 1)
    end = END.replace("#", comment, 1)
    pattern = re.compile(rf"\n?{re.escape(begin)}\n.*?\n{re.escape(end)}\n?", re.DOTALL)
    clean = pattern.sub("\n", content).rstrip()
    return f"{clean}\n\n{begin}\n{body.rstrip()}\n{end}\n" if clean else f"{begin}\n{body.rstrip()}\n{end}\n"


def managed_css_block(content: str, body: str) -> str:
    begin = "/* BEGIN NIXOS RICE (managed) */"
    end = "/* END NIXOS RICE (managed) */"
    pattern = re.compile(rf"\n?{re.escape(begin)}\n.*?\n{re.escape(end)}\n?", re.DOTALL)
    clean = pattern.sub("\n", content).rstrip()
    return f"{clean}\n\n{begin}\n{body.rstrip()}\n{end}\n" if clean else f"{begin}\n{body.rstrip()}\n{end}\n"


def replace_ini_section(content: str, section: str, body: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    skipping = False
    header = f"[{section}]".casefold()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if stripped.casefold() == header:
                skipping = True
                continue
            skipping = False
        if not skipping:
            result.append(line)
    clean = "\n".join(result).rstrip()
    return f"{clean}\n\n[{section}]\n{body.rstrip()}\n"


def replace_key(content: str, key: str, value: str, *, section: str | None = None) -> str:
    lines = content.splitlines()
    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    in_section = section is None
    section_found = section is None
    replaced = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section is not None and in_section and not replaced:
                output.append(f"{key}={value}")
                replaced = True
            in_section = stripped.casefold() == f"[{section}]".casefold() if section else True
            section_found = section_found or in_section
        if in_section and key_re.match(line):
            if not replaced:
                output.append(f"{key}={value}")
                replaced = True
            continue
        output.append(line)
    if section is not None and in_section and not replaced:
        output.append(f"{key}={value}")
        replaced = True
    if not section_found:
        output.extend(["", f"[{section}]", f"{key}={value}"])
    elif not replaced:
        output.append(f"{key}={value}")
    return "\n".join(output).rstrip() + "\n"


def replace_toml_key(content: str, section: str, key: str, value: str) -> str:
    lines = content.splitlines()
    section_header = f"[{section}]"
    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    in_section = False
    found_section = False
    replaced = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section and not replaced:
                output.append(f"{key} = {value}")
                replaced = True
            in_section = stripped == section_header
            found_section = found_section or in_section
        if in_section and key_re.match(line):
            if not replaced:
                output.append(f"{key} = {value}")
                replaced = True
            continue
        output.append(line)
    if in_section and not replaced:
        output.append(f"{key} = {value}")
        replaced = True
    if not found_section:
        output.extend(["", section_header, f"{key} = {value}"])
    return "\n".join(output).rstrip() + "\n"


def render_kitty(palette: dict[str, Any]) -> str:
    lines = [
        f"foreground {palette['foreground']}",
        f"background {palette['background']}",
        f"selection_foreground {palette['background']}",
        f"selection_background {palette['primary']}",
        f"cursor {palette['primary']}",
        f"cursor_text_color {palette['background']}",
        f"active_border_color {palette['primary']}",
        f"inactive_border_color {palette['surfaceAlt']}",
        f"url_color {palette['secondary']}",
    ]
    lines.extend(f"color{index} {colour}" for index, colour in enumerate(palette["terminal"]))
    return "\n".join(lines) + "\n"


def render_fuzzel(palette: dict[str, Any]) -> str:
    raw = lambda name, alpha="ff": palette[name].lstrip("#") + alpha
    return "\n".join(
        [
            f"background={raw('background', 'ee')}",
            f"text={raw('foreground')}",
            f"prompt={raw('primary')}",
            f"placeholder={raw('muted')}",
            f"input={raw('foreground')}",
            f"match={raw('accent')}",
            f"selection={raw('surfaceAlt', 'ee')}",
            f"selection-text={raw('foreground')}",
            f"selection-match={raw('accent')}",
            f"counter={raw('muted')}",
            f"border={raw('primary')}",
        ]
    )


def render_btop(palette: dict[str, Any]) -> str:
    values = {
        "main_bg": palette["background"], "main_fg": palette["foreground"], "title": palette["foreground"],
        "hi_fg": palette["primary"], "selected_bg": palette["surfaceAlt"], "selected_fg": palette["foreground"],
        "inactive_fg": palette["muted"], "graph_text": palette["accent"], "meter_bg": palette["surfaceAlt"],
        "proc_misc": palette["secondary"], "cpu_box": palette["primary"], "mem_box": palette["secondary"],
        "net_box": palette["accent"], "proc_box": palette["success"], "div_line": palette["surfaceAlt"],
        "temp_start": palette["secondary"], "temp_mid": palette["warning"], "temp_end": palette["error"],
        "cpu_start": palette["secondary"], "cpu_mid": palette["primary"], "cpu_end": palette["accent"],
        "free_start": palette["primary"], "free_mid": palette["secondary"], "free_end": palette["accent"],
        "cached_start": palette["secondary"], "cached_mid": palette["primary"], "cached_end": palette["accent"],
        "available_start": palette["success"], "available_mid": palette["secondary"], "available_end": palette["primary"],
        "used_start": palette["warning"], "used_mid": palette["accent"], "used_end": palette["error"],
        "download_start": palette["secondary"], "download_mid": palette["primary"], "download_end": palette["accent"],
        "upload_start": palette["success"], "upload_mid": palette["secondary"], "upload_end": palette["primary"],
        "process_start": palette["secondary"], "process_mid": palette["primary"], "process_end": palette["accent"],
    }
    return "# Generated by nix rice; edit the rice profile instead.\n" + "\n".join(f"theme[{key}]={value}" for key, value in values.items()) + "\n"


def render_cava(palette: dict[str, Any]) -> str:
    colours = [palette["secondary"], palette["primary"], palette["accent"], palette["warning"], palette["error"]]
    return "\n".join(
        [f"background = '{palette['background']}'", f"foreground = '{palette['primary']}'", "gradient = 1"]
        + [f"gradient_color_{index} = '{colour}'" for index, colour in enumerate(colours, 1)]
    )


def render_gtk(palette: dict[str, Any]) -> str:
    return "\n".join(
        [
            "/* Generated by nix rice. */",
            f"@define-color theme_bg_color {palette['background']};",
            f"@define-color theme_fg_color {palette['foreground']};",
            f"@define-color theme_base_color {palette['surface']};",
            f"@define-color theme_text_color {palette['foreground']};",
            f"@define-color theme_selected_bg_color {palette['primary']};",
            f"@define-color theme_selected_fg_color {palette['background']};",
            f"@define-color accent_bg_color {palette['primary']};",
            f"@define-color accent_fg_color {palette['background']};",
            f"@define-color window_bg_color {palette['background']};",
            f"@define-color window_fg_color {palette['foreground']};",
            f"@define-color view_bg_color {palette['surface']};",
            f"@define-color view_fg_color {palette['foreground']};",
            f"@define-color headerbar_bg_color {palette['surface']};",
            f"@define-color headerbar_fg_color {palette['foreground']};",
        ]
    ) + "\n"


def render_qt(palette: dict[str, Any]) -> str:
    colours = [
        palette["foreground"], palette["surface"], "#ffffff", palette["surfaceAlt"], palette["muted"],
        palette["surfaceAlt"], palette["foreground"], "#ffffff", palette["foreground"], palette["background"],
        palette["surface"], "#000000", palette["primary"], palette["background"],
        palette["secondary"], palette["surfaceAlt"], palette["surface"], palette["surfaceAlt"],
        palette["foreground"], palette["foreground"], palette["muted"], palette["primary"],
    ]
    joined = ", ".join(colours)
    return f"[ColorScheme]\nactive_colors={joined}\ndisabled_colors={joined}\ninactive_colors={joined}\n"


def apply_common(profile: dict[str, Any]) -> None:
    palette = profile["palette"]
    if "kitty" in profile["apps"]:
        theme = CONFIG_HOME / "kitty/themes/nixos-rice.conf"
        atomic_write(theme, render_kitty(palette))
        config = CONFIG_HOME / "kitty/kitty.conf"
        atomic_write(config, managed_block(config.read_text(encoding="utf-8") if config.exists() else "", f"include {theme}"))
    if "fuzzel" in profile["apps"]:
        path = CONFIG_HOME / "fuzzel/fuzzel.ini"
        atomic_write(path, replace_ini_section(path.read_text(encoding="utf-8") if path.exists() else "", "colors", render_fuzzel(palette)))
    if "btop" in profile["apps"]:
        theme = CONFIG_HOME / "btop/themes/nixos-rice.theme"
        atomic_write(theme, render_btop(palette))
        config = CONFIG_HOME / "btop/btop.conf"
        atomic_write(config, replace_key(config.read_text(encoding="utf-8") if config.exists() else "", "color_theme", '"nixos-rice"'))
    if "cava" in profile["apps"]:
        path = CONFIG_HOME / "cava/config"
        atomic_write(path, replace_ini_section(path.read_text(encoding="utf-8") if path.exists() else "", "color", render_cava(palette)))
    if "gtk" in profile["apps"]:
        for version in ("gtk-3.0", "gtk-4.0"):
            theme = CONFIG_HOME / version / "nixos-rice.css"
            atomic_write(theme, render_gtk(palette))
            config = CONFIG_HOME / version / "gtk.css"
            body = '@import url("nixos-rice.css");'
            atomic_write(config, managed_css_block(config.read_text(encoding="utf-8") if config.exists() else "", body))
    if "qt" in profile["apps"]:
        scheme = CONFIG_HOME / "qt6ct/colors/nixos-rice.conf"
        atomic_write(scheme, render_qt(palette))
        config = CONFIG_HOME / "qt6ct/qt6ct.conf"
        atomic_write(config, replace_key(config.read_text(encoding="utf-8") if config.exists() else "", "color_scheme_path", str(scheme), section="Appearance"))


def run_checked(command: Sequence[str]) -> None:
    completed = subprocess.run(list(command), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RiceError(detail or f"command failed ({completed.returncode}): {' '.join(command)}")


def run_best_effort(command: Sequence[str]) -> None:
    with contextlib.suppress(OSError):
        subprocess.run(list(command), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def validate_caelestia_scheme(name: str, flavour: str) -> None:
    completed = subprocess.run(
        ["caelestia", "scheme", "list"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RiceError(detail or "could not inspect Caelestia schemes")
    try:
        schemes = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RiceError(f"invalid Caelestia scheme catalog: {exc}") from exc
    flavours = schemes.get(name) if isinstance(schemes, dict) else None
    if not isinstance(flavours, dict) or flavour not in flavours:
        available = ", ".join(sorted(flavours)) if isinstance(flavours, dict) else "none"
        raise RiceError(f"Caelestia scheme {name!r} does not provide flavour {flavour!r} (available: {available})")


def update_legacy_settings(profile: dict[str, Any]) -> None:
    path = CONFIG_HOME / "noctalia-legacy/settings.json"
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise RiceError(f"invalid Noctalia legacy settings: {path}")
    colours = data.setdefault("colorSchemes", {})
    colours["darkMode"] = profile["mode"] == "dark"
    colours["useWallpaperColors"] = True
    colours["generationMethod"] = profile.get("shellOptions", {}).get("noctalia-legacy", {}).get("generationMethod", "tonal-spot")
    wallpaper = data.setdefault("wallpaper", {})
    wallpaper["enabled"] = True
    wallpaper["automationEnabled"] = False
    write_json(path, data)


def update_noctalia_config(profile: dict[str, Any]) -> None:
    mode = json.dumps(profile["mode"])
    scheme = profile.get("shellOptions", {}).get("noctalia", {}).get("wallpaperScheme", "muted")
    for path in (CONFIG_HOME / "noctalia/config.toml", HOME / ".local/state/noctalia/settings.toml"):
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        content = replace_toml_key(content, "theme", "mode", mode)
        content = replace_toml_key(content, "theme", "source", '"wallpaper"')
        content = replace_toml_key(content, "theme", "wallpaper_scheme", json.dumps(scheme))
        content = replace_toml_key(content, "wallpaper.automation", "enabled", "false")
        atomic_write(path, content)


def apply_shell(profile: dict[str, Any], shell: str, wallpaper: Path) -> None:
    options = profile.get("shellOptions", {}).get(shell, {})
    if shell == "noctalia":
        update_noctalia_config(profile)
        run_checked(["noctalia", "msg", "config-reload"])
        run_checked(["noctalia", "msg", "theme-mode-set", profile["mode"]])
        run_checked(["noctalia", "msg", "color-scheme-set", "wallpaper", options.get("wallpaperScheme", "muted")])
        run_checked(["noctalia", "msg", "wallpaper-set", str(wallpaper)])
    elif shell == "noctalia-legacy":
        update_legacy_settings(profile)
        run_checked([SHELL_BIN, "restart"])
        run_checked(["noctalia-legacy", "ipc", "call", "wallpaper", "set", str(wallpaper), "all"])
    elif shell == "caelestia":
        name = options.get("name", "dynamic")
        flavour = options.get("flavour")
        resolved_flavour = flavour or "default"
        validate_caelestia_scheme(name, resolved_flavour)
        command = ["caelestia", "scheme", "set", "-n", name, "-m", profile["mode"], "-v", options.get("variant", "tonalspot")]
        if flavour and flavour != "default":
            command.extend(["-f", flavour])
        run_checked(command)
        run_checked(["caelestia", "wallpaper", "-f", str(wallpaper), "-N"])
    else:
        raise RiceError(f"rice profiles are not supported by {shell}; use its settings")


def reload_after_restore(shell: str) -> None:
    run_best_effort([SHELL_BIN, "restart"])
    theme = CONFIG_HOME / "kitty/themes/nixos-rice.conf"
    if theme.exists():
        run_best_effort(["kitty", "@", "set-colors", "--all", str(theme)])


def record_history(event: dict[str, Any]) -> None:
    history = read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    history.append(event)
    write_json(HISTORY_FILE, history[-100:])


def prune_snapshots(keep: int = 12) -> None:
    if not SNAPSHOT_DIR.exists():
        return
    roots = sorted(
        (
            path
            for path in SNAPSHOT_DIR.iterdir()
            if path.is_dir() and not path.is_symlink() and (path / "snapshot.json").is_file()
        ),
        reverse=True,
    )
    for root in roots[keep:]:
        shutil.rmtree(root)


def apply_profile(identifier: str, shell: str) -> dict[str, Any]:
    catalog = load_catalog()
    if identifier not in catalog:
        raise RiceError(f"unknown rice: {identifier}")
    profile = catalog[identifier]
    if shell not in profile["shells"]:
        raise RiceError(f"rice {identifier!r} is not compatible with {shell}")
    wallpaper = wallpaper_path(profile)
    snapshot_id, root = snapshot(identifier, shell, targets_for(shell))
    try:
        apply_shell(profile, shell, wallpaper)
        apply_common(profile)
        mapping = active_map()
        mapping["shells"][shell] = {"rice": identifier, "appliedAt": now(), "snapshot": snapshot_id}
        write_json(ACTIVE_FILE, mapping)
        run_best_effort(["kitty", "@", "set-colors", "--all", str(CONFIG_HOME / "kitty/themes/nixos-rice.conf")])
        event = {"action": "apply", "status": "ok", "at": now(), "rice": identifier, "shell": shell, "snapshot": snapshot_id}
        record_history(event)
        prune_snapshots()
        return {**event, "label": profile["label"], "wallpaper": str(wallpaper), "apps": profile["apps"]}
    except Exception as exc:
        restore_snapshot(root)
        reload_after_restore(shell)
        event = {"action": "apply", "status": "failed", "at": now(), "rice": identifier, "shell": shell, "snapshot": snapshot_id, "error": str(exc)}
        record_history(event)
        raise RiceError(f"apply failed; previous configuration restored: {exc}") from exc


def rollback(snapshot_id: str | None, shell: str) -> dict[str, Any]:
    if not SNAPSHOT_DIR.exists():
        raise RiceError("no rice snapshots are available")
    if snapshot_id:
        root = SNAPSHOT_DIR / snapshot_id
    else:
        roots = sorted((path for path in SNAPSHOT_DIR.iterdir() if path.is_dir()), reverse=True)
        root = next((path for path in roots if read_json(path / "snapshot.json", {}).get("shell") == shell), None)
        if root is None:
            raise RiceError(f"no rice snapshot is available for {shell}")
    try:
        root.resolve().relative_to(SNAPSHOT_DIR.resolve())
    except ValueError as exc:
        raise RiceError("invalid snapshot id") from exc
    if not root.is_dir():
        raise RiceError(f"snapshot not found: {root.name}")
    document = restore_snapshot(root)
    reload_after_restore(shell)
    event = {"action": "rollback", "status": "ok", "at": now(), "shell": shell, "snapshot": document["id"], "rice": document.get("rice")}
    record_history(event)
    return event


def status_value(shell: str) -> dict[str, Any]:
    active = active_map()
    current = active.get("shells", {}).get(shell)
    snapshots = []
    if SNAPSHOT_DIR.exists():
        for root in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
            metadata = read_json(root / "snapshot.json", {}) if root.is_dir() else {}
            if metadata.get("shell") == shell:
                snapshots.append({key: metadata.get(key) for key in ("id", "createdAt", "rice", "shell")})
    return {
        "shell": shell,
        "active": current,
        "snapshots": snapshots,
        "personalCatalog": str(USER_CATALOG_DIR),
        "stateDirectory": str(STATE_DIR),
    }


def history_value(shell: str | None = None) -> dict[str, Any]:
    events = read_json(HISTORY_FILE, [])
    if not isinstance(events, list):
        events = []
    if shell:
        events = [event for event in events if event.get("shell") == shell]
    return {"events": list(reversed(events))}


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="rice-manager", description="Transactional visual profiles for the active desktop shell")
    sub = value.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("--shell", choices=VALID_SHELLS)
    listing.add_argument("--all", action="store_true")
    listing.add_argument("--json", action="store_true")
    status = sub.add_parser("status")
    status.add_argument("--shell", choices=VALID_SHELLS)
    status.add_argument("--json", action="store_true")
    for name in ("show", "plan", "apply"):
        command = sub.add_parser(name)
        command.add_argument("rice")
        command.add_argument("--shell", choices=VALID_SHELLS)
        command.add_argument("--json", action="store_true")
    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("snapshot", nargs="?")
    rollback_parser.add_argument("--shell", choices=VALID_SHELLS)
    rollback_parser.add_argument("--json", action="store_true")
    history = sub.add_parser("history")
    history.add_argument("--shell", choices=VALID_SHELLS)
    history.add_argument("--json", action="store_true")
    restore = sub.add_parser("restore")
    restore.add_argument("--shell", choices=VALID_SHELLS, required=True)
    restore.add_argument("--json", action="store_true")
    return value


def emit(value: Any, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    shell = selected_shell(getattr(args, "shell", None))
    if args.command == "list":
        emit(list_value(shell, include_all=args.all), args.json)
        return 0
    if args.command == "status":
        emit(status_value(shell), args.json)
        return 0
    if args.command == "show":
        emit(show_value(args.rice, shell), args.json)
        return 0
    if args.command == "plan":
        emit(plan_value(args.rice, shell), args.json)
        return 0
    if args.command == "history":
        emit(history_value(shell), args.json)
        return 0
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.command == "apply":
            emit(apply_profile(args.rice, shell), args.json)
        elif args.command == "rollback":
            emit(rollback(args.snapshot, shell), args.json)
        elif args.command == "restore":
            current = active_map().get("shells", {}).get(shell)
            if not current:
                emit({"shell": shell, "restored": False, "reason": "no rice selected"}, args.json)
            else:
                result = apply_profile(current["rice"], shell)
                result["restored"] = True
                emit(result, args.json)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RiceError as exc:
        print(f"rice-manager: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        raise SystemExit(130)
