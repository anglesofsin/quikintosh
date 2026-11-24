from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SOURCE_ROOT = Path(
    os.environ.get(
        "RICE_MANAGER_SOURCE",
        str(Path(__file__).resolve().parents[2] / "modules" / "rice"),
    )
)
SPEC = importlib.util.spec_from_file_location("rice_manager", SOURCE_ROOT / "rice-manager.py")
assert SPEC and SPEC.loader
rice_manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rice_manager)


class RiceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.home = root / "home"
        self.config = self.home / ".config"
        self.state = self.home / ".local/state/nixos-rice"
        self.wallpapers = self.home / "Pictures/Wallpapers"
        self.wallpapers.mkdir(parents=True)
        self.shell_file = self.state / "active-shell"
        self.shell_file.parent.mkdir(parents=True)
        self.shell_file.write_text("caelestia\n", encoding="utf-8")
        self.patches = [
            mock.patch.object(rice_manager, "HOME", self.home),
            mock.patch.object(rice_manager, "CONFIG_HOME", self.config),
            mock.patch.object(rice_manager, "STATE_DIR", self.state),
            mock.patch.object(rice_manager, "WALLPAPER_DIR", self.wallpapers),
            mock.patch.object(rice_manager, "SHELL_STATE_FILE", self.shell_file),
            mock.patch.object(rice_manager, "ACTIVE_FILE", self.state / "active-rices.json"),
            mock.patch.object(rice_manager, "HISTORY_FILE", self.state / "rice-history.json"),
            mock.patch.object(rice_manager, "SNAPSHOT_DIR", self.state / "rice-snapshots"),
            mock.patch.object(rice_manager, "LOCK_FILE", self.state / "rice.lock"),
            mock.patch.object(rice_manager, "USER_CATALOG_DIR", self.config / "nixos-rice/rices"),
            mock.patch.object(rice_manager, "CATALOG_FILE", SOURCE_ROOT / "catalog.json"),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def profile(self, identifier="midnight-amethyst"):
        return rice_manager.load_catalog()[identifier]

    def test_list_filters_profiles_for_active_shell(self):
        value = rice_manager.list_value("caelestia")
        identifiers = {item["id"] for item in value["rices"]}
        self.assertIn("caelestia-glass", identifiers)
        self.assertNotIn("noctalia-eclipse", identifiers)
        all_value = rice_manager.list_value("caelestia", include_all=True)
        self.assertIn("noctalia-eclipse", {item["id"] for item in all_value["rices"]})

    def test_plan_is_read_only_and_reports_protected_targets(self):
        wallpaper = self.wallpapers / self.profile()["wallpaper"]
        wallpaper.write_bytes(b"wallpaper")
        value = rice_manager.plan_value("midnight-amethyst", "caelestia")
        self.assertEqual(value["shell"], "caelestia")
        self.assertIn("kitty", value["apps"])
        self.assertGreater(len(value["targets"]), 10)
        self.assertFalse((self.state / "rice-snapshots").exists())

    def test_common_app_edits_are_idempotent(self):
        (self.config / "kitty").mkdir(parents=True)
        (self.config / "kitty/kitty.conf").write_text("font_size 12\n", encoding="utf-8")
        (self.config / "fuzzel").mkdir(parents=True)
        (self.config / "fuzzel/fuzzel.ini").write_text(
            "font=Mono\n\n[colors]\nbackground=000000ff\n\n[border]\nradius=4\n\n[colors]\ntext=ffffffff\n",
            encoding="utf-8",
        )
        profile = self.profile()
        rice_manager.apply_common(profile)
        rice_manager.apply_common(profile)
        kitty = (self.config / "kitty/kitty.conf").read_text(encoding="utf-8")
        fuzzel = (self.config / "fuzzel/fuzzel.ini").read_text(encoding="utf-8")
        gtk = (self.config / "gtk-3.0/gtk.css").read_text(encoding="utf-8")
        self.assertEqual(kitty.count(rice_manager.BEGIN), 1)
        self.assertEqual(fuzzel.casefold().count("[colors]"), 1)
        self.assertEqual(gtk.count("BEGIN NIXOS RICE"), 1)

    def test_qt_palette_has_every_qpalette_role_once(self):
        rendered = rice_manager.render_qt(self.profile()["palette"])
        active = next(line for line in rendered.splitlines() if line.startswith("active_colors="))
        self.assertEqual(len(active.split("=", 1)[1].split(",")), 22)

    def test_snapshot_restores_changed_and_new_files(self):
        original = self.config / "existing.conf"
        generated = self.config / "new.conf"
        original.parent.mkdir(parents=True)
        original.write_text("before\n", encoding="utf-8")
        _snapshot_id, root = rice_manager.snapshot("test-rice", "caelestia", [original, generated])
        original.write_text("after\n", encoding="utf-8")
        generated.write_text("new\n", encoding="utf-8")
        rice_manager.restore_snapshot(root)
        self.assertEqual(original.read_text(encoding="utf-8"), "before\n")
        self.assertFalse(generated.exists())

    def test_failed_apply_automatically_restores_configuration(self):
        wallpaper = self.wallpapers / self.profile()["wallpaper"]
        wallpaper.write_bytes(b"wallpaper")
        config = self.config / "kitty/kitty.conf"
        config.parent.mkdir(parents=True)
        config.write_text("original\n", encoding="utf-8")

        def fail_after_change(*_args):
            config.write_text("broken\n", encoding="utf-8")
            raise rice_manager.RiceError("simulated shell failure")

        with (
            mock.patch.object(rice_manager, "apply_shell", side_effect=fail_after_change),
            mock.patch.object(rice_manager, "reload_after_restore"),
            self.assertRaisesRegex(rice_manager.RiceError, "previous configuration restored"),
        ):
            rice_manager.apply_profile("midnight-amethyst", "caelestia")
        self.assertEqual(config.read_text(encoding="utf-8"), "original\n")

    def test_personal_catalog_can_override_a_builtin(self):
        personal = self.config / "nixos-rice/rices/custom.json"
        personal.parent.mkdir(parents=True)
        profile = dict(self.profile())
        profile.pop("id", None)
        profile.pop("source", None)
        profile["label"] = "My Midnight"
        personal.write_text(json.dumps({"midnight-amethyst": profile}), encoding="utf-8")
        self.assertEqual(rice_manager.load_catalog()["midnight-amethyst"]["label"], "My Midnight")

    def test_catalog_rejects_invalid_shell_variants(self):
        profile = dict(self.profile())
        profile.pop("id", None)
        profile.pop("source", None)
        profile["shellOptions"] = dict(profile["shellOptions"])
        profile["shellOptions"]["noctalia"] = {"wallpaperScheme": "not-a-real-scheme"}
        with self.assertRaisesRegex(rice_manager.RiceError, "invalid Noctalia wallpaper scheme"):
            rice_manager.validate_profile("invalid-rice", profile, Path("invalid.json"))

    def test_noctalia_apply_uses_supported_ipc_and_disables_rotation(self):
        config = self.config / "noctalia/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text(
            '[theme]\nmode = "dark"\nsource = "wallpaper"\nwallpaper_scheme = "muted"\n\n[wallpaper.automation]\nenabled = true\n',
            encoding="utf-8",
        )
        wallpaper = self.wallpapers / "wallpaper.png"
        wallpaper.write_bytes(b"wallpaper")
        success = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(rice_manager.subprocess, "run", return_value=success) as runner:
            rice_manager.apply_shell(self.profile("aurora-forest"), "noctalia", wallpaper)
        updated = config.read_text(encoding="utf-8")
        self.assertIn('wallpaper_scheme = "faithful"', updated)
        self.assertIn("enabled = false", updated)
        self.assertIn(
            mock.call(
                ["noctalia", "msg", "color-scheme-set", "wallpaper", "faithful"],
                text=True,
                stdout=mock.ANY,
                stderr=mock.ANY,
                check=False,
            ),
            runner.call_args_list,
        )

    def test_legacy_apply_updates_settings_then_restarts(self):
        settings = self.config / "noctalia-legacy/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text("{}\n", encoding="utf-8")
        wallpaper = self.wallpapers / "wallpaper.png"
        wallpaper.write_bytes(b"wallpaper")
        success = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(rice_manager.subprocess, "run", return_value=success) as runner:
            rice_manager.apply_shell(self.profile("noctalia-eclipse"), "noctalia-legacy", wallpaper)
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["colorSchemes"]["generationMethod"], "monochrome")
        self.assertFalse(data["wallpaper"]["automationEnabled"])
        commands = [call.args[0] for call in runner.call_args_list]
        self.assertEqual(commands[0], [rice_manager.SHELL_BIN, "restart"])
        self.assertEqual(commands[1], ["noctalia-legacy", "ipc", "call", "wallpaper", "set", str(wallpaper), "all"])

    def test_caelestia_apply_validates_installed_flavour(self):
        wallpaper = self.wallpapers / "wallpaper.png"
        wallpaper.write_bytes(b"wallpaper")
        scheme_list = mock.Mock(returncode=0, stdout=json.dumps({"everforest": {"hard": {}}}), stderr="")
        success = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(rice_manager.subprocess, "run", side_effect=[scheme_list, success, success]) as runner:
            rice_manager.apply_shell(self.profile("aurora-forest"), "caelestia", wallpaper)
        commands = [call.args[0] for call in runner.call_args_list]
        self.assertEqual(
            commands[1],
            ["caelestia", "scheme", "set", "-n", "everforest", "-m", "dark", "-v", "fidelity", "-f", "hard"],
        )
        self.assertEqual(commands[2], ["caelestia", "wallpaper", "-f", str(wallpaper), "-N"])


if __name__ == "__main__":
    unittest.main()
