from __future__ import annotations

import importlib.util
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
SPEC = importlib.util.spec_from_file_location("rice_shell", SOURCE_ROOT / "rice-shell.py")
assert SPEC and SPEC.loader
rice_shell = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rice_shell)


class RiceShellLegacyActionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        state = Path(self.temporary.name)
        self.patches = [
            mock.patch.object(rice_shell, "STATE_DIR", state),
            mock.patch.object(rice_shell, "LOCK_FILE", state / "shell.lock"),
            mock.patch.object(rice_shell, "selected", return_value="noctalia-legacy"),
            mock.patch.object(rice_shell, "is_running", return_value=True),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_legacy_plugin_actions_use_their_native_ipc(self):
        expected = {
            "clipboard": ["noctalia-legacy", "ipc", "call", "plugin:clipboard", "toggle"],
            "keybinds": ["noctalia-legacy", "ipc", "call", "plugin:keybind-cheatsheet", "toggle"],
            "screenshot-region": [
                "noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "choose"
            ],
            "ocr": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "ocr"],
            "lens": ["noctalia-legacy", "ipc", "call", "plugin:screen-toolkit", "lens"],
        }

        for action, command in expected.items():
            with self.subTest(action=action), mock.patch.object(rice_shell, "run") as runner:
                rice_shell.action(action)
                runner.assert_called_once_with(command, check=True, timeout=10)


class SettingsRiceRestorationTests(unittest.TestCase):
    def test_only_owned_settings_are_closed_on_leave(self):
        processes=[(123,'quickshell','qs -p /nix/store/abc-lickintosh-source-1/settings.qml'),(124,'quickshell','qs -p /other/settings.qml')]
        with mock.patch.object(rice_shell, "is_running", return_value=False), mock.patch.object(rice_shell, "shell_pids", return_value=[]), mock.patch.object(rice_shell, "processes", return_value=processes), mock.patch.object(rice_shell, "run"), mock.patch.object(rice_shell, "terminate_pids") as stop:
            rice_shell.stop_shell("lickintosh")
            stop.assert_called_once_with([123])

    def test_settings_restored_before_desktop_profile_on_leave(self):
        with mock.patch.object(rice_shell, "is_running", return_value=False), mock.patch.object(rice_shell, "shell_pids", return_value=[]), mock.patch.object(rice_shell, "processes", return_value=[]), mock.patch.object(rice_shell, "run") as run:
            rice_shell.stop_shell("lickintosh")
            self.assertEqual([call.args[0] for call in run.call_args_list], [["lickintosh", "settings-restore"], ["lickintosh-desktop-profile", "leave"]])


class ShellIsolationTests(unittest.TestCase):
    def test_all_native_actions_dispatch_only_to_the_selected_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(rice_shell, "STATE_DIR", Path(folder)), mock.patch.object(rice_shell, "LOCK_FILE", Path(folder) / "lock"), mock.patch.object(rice_shell, "is_running", return_value=True), mock.patch.object(rice_shell, "ensure_running", side_effect=AssertionError("keybind changed lifecycle")), mock.patch.object(rice_shell, "start_shell", side_effect=AssertionError("keybind started shell")), mock.patch.object(rice_shell, "stop_shell", side_effect=AssertionError("keybind stopped shell")):
                for shell, actions in rice_shell.ACTION_TABLES.items():
                    for name, command in actions.items():
                        with self.subTest(shell=shell, action=name), mock.patch.object(rice_shell, "selected", return_value=shell), mock.patch.object(rice_shell, "run") as runner:
                            rice_shell.action(name)
                            self.assertEqual(runner.call_args.args[0], command)

    def test_unsupported_actions_do_not_start_a_shell(self):
        with mock.patch.object(rice_shell, "selected", return_value="lickintosh"), mock.patch.object(rice_shell, "ensure_running") as ensure, mock.patch.object(rice_shell, "run") as runner:
            with self.assertRaises(rice_shell.RiceError):
                rice_shell.action("nonexistent-action")
            ensure.assert_not_called()
            runner.assert_not_called()

    def test_shortcuts_do_not_restart_a_stopped_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(rice_shell, "STATE_DIR", Path(folder)), mock.patch.object(rice_shell, "LOCK_FILE", Path(folder) / "lock"), mock.patch.object(rice_shell, "selected", return_value="noctalia-legacy"), mock.patch.object(rice_shell, "is_running", return_value=False), mock.patch.object(rice_shell, "run") as runner:
                rice_shell.action("launcher")
                runner.assert_not_called()

    def test_shortcuts_pressed_during_a_switch_are_discarded(self):
        import fcntl
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lock"
            with path.open("a+") as lifecycle_lock:
                fcntl.flock(lifecycle_lock, fcntl.LOCK_EX)
                with mock.patch.object(rice_shell, "STATE_DIR", Path(folder)), mock.patch.object(rice_shell, "LOCK_FILE", path), mock.patch.object(rice_shell, "selected", return_value="lickintosh"), mock.patch.object(rice_shell, "run") as runner:
                    rice_shell.action("launcher")
                    runner.assert_not_called()

    def test_zombie_processes_are_not_running_desktops(self):
        import subprocess
        output = "21001 Z .noctalia-wrapp [noctalia] <defunct>\n21002 Sl .noctalia-wrapp /bin/noctalia --daemon\n"
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, output, "")):
            self.assertEqual(rice_shell.processes(), [(21002, ".noctalia-wrapp", "/bin/noctalia --daemon")])

    def test_failed_stop_restores_the_previously_selected_shell(self):
        with mock.patch.object(rice_shell, "selected", return_value="noctalia-legacy"), mock.patch.object(rice_shell, "stop_all", side_effect=rice_shell.RiceError("stop failed")), mock.patch.object(rice_shell, "set_selected") as select, mock.patch.object(rice_shell, "stop_shell"), mock.patch.object(rice_shell, "start_shell") as start, mock.patch.object(rice_shell, "reload_hyprland"):
            with self.assertRaises(rice_shell.RiceError):
                rice_shell.switch_shell("lickintosh")
            select.assert_called_once_with("noctalia-legacy")
            start.assert_called_once_with("noctalia-legacy")

    def test_concurrent_ipc_clients_are_not_desktop_instances(self):
        import subprocess
        rows = [(21001, ".quickshell-wra", "/bin/quickshell -p /store/lickintosh/shell.qml list -j"),
                (21002, ".quickshell-wra", "/bin/quickshell -p /store/caelestia/shell.qml ipc show"),
                (21003, ".quickshell-wra", "/bin/quickshell -p /store/noctalia-shell/shell.qml log"),
                (21004, ".noctalia-wrapp", "/bin/.noctalia-wrapped msg status")]
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 1, "", "")), mock.patch.object(rice_shell, "processes", return_value=rows):
            for shell in rice_shell.VALID_SHELLS:
                self.assertEqual(rice_shell.shell_pids(shell), [], shell)

    def test_detects_old_and_new_generations_without_counting_settings(self):
        import subprocess
        output = '[{"pid":12,"config_path":"/nix/store/old-lickintosh-source/shell.qml"},{"pid":13,"config_path":"/nix/store/new-lickintosh-source/shell.qml"},{"pid":14,"config_path":"/nix/store/old-lickintosh-source/settings.qml"}]'
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, output, "")) as run:
            self.assertEqual(rice_shell.shell_pids("lickintosh"), [12, 13])
            run.assert_called_once_with(["lickintosh", "list", "--all", "-j"], capture=True, timeout=2)

    def test_legacy_inventory_avoids_wrapper_config_selection_conflict(self):
        import subprocess
        output = '[{"pid":12,"config_path":"/nix/store/noctalia/share/noctalia-shell/shell.qml"}]'
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, output, "")) as run:
            self.assertEqual(rice_shell.shell_pids("noctalia-legacy"), [12])
            run.assert_called_once_with(["lickintosh", "list", "--all", "-j"], capture=True, timeout=2)

    def test_process_listing_filters_other_quickshell_instances(self):
        import subprocess
        output = '[{"pid":12,"config_path":"/nix/store/noctalia/share/noctalia-shell/shell.qml"},{"pid":13,"config_path":"/nix/store/lickintosh-source/shell.qml"},{"pid":14,"config_path":"/nix/store/caelestia-shell/shell.qml"}]'
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, output, "")):
            self.assertEqual(rice_shell.shell_pids("noctalia-legacy"), [12])
            self.assertEqual(rice_shell.shell_pids("lickintosh"), [13])
            self.assertEqual(rice_shell.shell_pids("caelestia"), [14])

class EqshIntegrationTests(unittest.TestCase):
    def test_registry_separates_eqsh_from_other_shells(self):
        import subprocess
        output = '[{"pid":31,"config_path":"/nix/store/old-eqsh-source/shell.qml"},{"pid":32,"config_path":"/nix/store/new-eqsh-source/shell.qml"},{"pid":33,"config_path":"/nix/store/lickintosh-source/shell.qml"}]'
        with mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, output, "")):
            self.assertEqual(rice_shell.shell_pids("eqsh"), [31, 32])
            self.assertEqual(rice_shell.shell_pids("lickintosh"), [33])

    def test_eqsh_uses_its_own_ipc_status(self):
        import subprocess
        with mock.patch.object(rice_shell, "is_running", return_value=True), mock.patch.object(rice_shell, "run", return_value=subprocess.CompletedProcess([], 0, "ready", "")) as run:
            self.assertTrue(rice_shell.is_ready("eqsh"))
            run.assert_called_once_with(["eqsh", "ipc", "call", "rice", "status"], capture=True, timeout=2)

    def test_eqsh_has_no_legacy_profiles_or_lickintosh_switcher(self):
        capabilities = rice_shell.supported_actions("eqsh")
        self.assertTrue({"launchpad", "spotlight", "ai", "notch-active", "notch-info"} <= capabilities)
        self.assertNotIn("profiles", capabilities)
        self.assertNotIn("switcher-next", capabilities)
        for shell in rice_shell.VALID_SHELLS:
            if shell != "eqsh":
                self.assertNotIn("notch-active", rice_shell.supported_actions(shell))

class RiceShellProcessCacheTests(unittest.TestCase):
    def test_live_process_avoids_relaunching_registry_for_each_shortcut(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(rice_shell, 'STATE_DIR', Path(folder)), \
                mock.patch.object(rice_shell, 'lickintosh_process_stamp', return_value='start-1'), \
                mock.patch.object(rice_shell, 'shell_pids', return_value=[123]) as registry:
            self.assertTrue(rice_shell.is_running('lickintosh'))
            self.assertTrue(rice_shell.is_running('lickintosh'))
            registry.assert_called_once_with('lickintosh')

    def test_reused_pid_or_exited_shell_does_not_pass_cached_check(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(rice_shell, 'STATE_DIR', Path(folder)), \
                mock.patch.object(rice_shell, 'lickintosh_process_stamp', return_value='start-2'), \
                mock.patch.object(rice_shell, 'shell_pids', return_value=[]):
            (Path(folder) / 'lickintosh-process.json').write_text('{"pid":123,"start":"start-1"}')
            self.assertFalse(rice_shell.is_running('lickintosh'))


if __name__ == "__main__":
    unittest.main()
