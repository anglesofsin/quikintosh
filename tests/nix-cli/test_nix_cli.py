from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock


SOURCE_ROOT = Path(
    os.environ.get(
        "NIX_HELPER_SOURCE",
        str(Path(__file__).resolve().parents[2] / "scripts" / "nix-cli"),
    )
)
SPEC = importlib.util.spec_from_file_location("nix_cli", SOURCE_ROOT / "nix_cli.py")
assert SPEC and SPEC.loader
nix_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nix_cli)


class RunHelperTests(unittest.TestCase):
    def test_timeout_returns_a_bounded_failure(self):
        expired = nix_cli.subprocess.TimeoutExpired(["slow-command"], 4)
        with mock.patch.object(nix_cli.subprocess, "run", side_effect=expired):
            completed = nix_cli.run(["slow-command"], capture=True, timeout=4)

        self.assertEqual(completed.returncode, 124)
        self.assertEqual(completed.stdout, "")
        self.assertIn("timed out after 4s", completed.stderr)


class AttributeValidationTests(unittest.TestCase):
    def test_accepts_dotted_and_hyphenated_attributes(self):
        self.assertEqual(
            nix_cli.validate_attr("javaPackages.compiler.openjdk21"),
            "javaPackages.compiler.openjdk21",
        )
        self.assertEqual(nix_cli.validate_attr("zen-browser"), "zen-browser")

    def test_rejects_expression_injection(self):
        for value in ("", ".hello", "hello.", "hello..world", 'hello"; builtins.abort "x"'):
            with self.subTest(value=value), self.assertRaises(nix_cli.CLIError):
                nix_cli.validate_attr(value)


class ManifestTests(unittest.TestCase):
    def write_manifest(self, root: Path, categories: dict[str, list[str]]) -> Path:
        path = root / "apps.json"
        path.write_text(
            json.dumps({"schemaVersion": 1, "categories": categories}),
            encoding="utf-8",
        )
        return path

    def test_add_remove_and_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), {"development": ["git"], "other": []})
            manifest = nix_cli.Manifest(path)
            manifest.add("ripgrep", "development")
            manifest.add("hello", "other")
            manifest.save()

            loaded = nix_cli.Manifest(path)
            self.assertEqual(loaded.categories["development"], ["git", "ripgrep"])
            self.assertEqual(loaded.category_of("hello"), "other")
            self.assertEqual(loaded.remove("hello"), "other")

    def test_duplicate_packages_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), {"one": ["git"], "two": ["git"]})
            with self.assertRaises(nix_cli.CLIError):
                nix_cli.Manifest(path)

    def test_failed_install_restores_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_manifest(root, {"development": ["git"], "other": []})
            before = path.read_text(encoding="utf-8")
            ui = nix_cli.UI(plain=True)
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(nix_cli, "STATE_ROOT", root / "state"),
                mock.patch.object(
                    nix_cli,
                    "package_metadata",
                    return_value={"version": "1", "license": "mit", "description": "test"},
                ),
                mock.patch.object(nix_cli, "apply_apps", side_effect=nix_cli.CLIError("build failed")),
                self.assertRaises(nix_cli.CLIError),
            ):
                nix_cli.command_install(["hello"], ui)
            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_dry_run_does_not_edit_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_manifest(Path(temporary), {"other": []})
            before = path.read_text(encoding="utf-8")
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(
                    nix_cli,
                    "package_metadata",
                    return_value={"version": "1", "license": "mit", "description": "test"},
                ),
            ):
                nix_cli.command_install(["hello", "--dry-run"], nix_cli.UI(plain=True))
            self.assertEqual(path.read_text(encoding="utf-8"), before)


class ProfileAndLockTests(unittest.TestCase):
    def test_normalizes_profile_attributes(self):
        self.assertEqual(
            nix_cli.normalize_profile_attr("legacyPackages.x86_64-linux.kdePackages.okular"),
            "kdePackages.okular",
        )
        self.assertEqual(
            nix_cli.normalize_profile_attr("packages.x86_64-linux.apps"),
            "apps",
        )

    def test_lock_summary_reports_only_changed_nodes(self):
        before = {
            "nodes": {
                "nixpkgs": {"locked": {"rev": "old"}},
                "same": {"locked": {"rev": "stable"}},
            }
        }
        after = {
            "nodes": {
                "nixpkgs": {"locked": {"rev": "new"}},
                "same": {"locked": {"rev": "stable"}},
            }
        }
        self.assertEqual(
            nix_cli.flake_lock_summary(before, after),
            [{"input": "nixpkgs", "before": "old", "after": "new"}],
        )

    def test_buildenv_detection_requires_a_direct_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            buildenv = root / "buildenv"
            (output / "bin").mkdir(parents=True)
            (buildenv / "bin").mkdir(parents=True)
            (output / "bin" / "hello").write_text("hello", encoding="utf-8")
            (buildenv / "bin" / "hello").symlink_to(output / "bin" / "hello")
            self.assertTrue(nix_cli.buildenv_links_output([str(buildenv)], str(output)))
            self.assertFalse(nix_cli.buildenv_links_output([str(buildenv)], str(root / "other")))

    def test_individual_profile_records_keep_source_and_store_paths(self):
        records = nix_cli.individual_profile_records(
            {
                "apps": {"attrPath": "packages.x86_64-linux.apps", "storePaths": ["/nix/store/apps"]},
                "antigravity": {
                    "attrPath": "legacyPackages.x86_64-linux.antigravity",
                    "storePaths": ["/nix/store/hash-antigravity-ide-2.5.5"],
                    "priority": 5,
                    "active": True,
                },
            }
        )
        self.assertNotIn("apps", records)
        self.assertEqual(records["antigravity"]["attribute"], "antigravity")
        self.assertEqual(
            records["antigravity"]["storePaths"],
            ["/nix/store/hash-antigravity-ide-2.5.5"],
        )

    def test_profile_alias_matching_requires_the_exact_output(self):
        records = {
            "antigravity": {
                "attribute": "antigravity",
                "storePaths": ["/nix/store/hash-antigravity-ide-2.5.5"],
            }
        }
        self.assertEqual(
            nix_cli.matching_profile_elements(
                "antigravity-ide",
                "antigravity-ide",
                "/nix/store/hash-antigravity-ide-2.5.5",
                records,
            ),
            ["antigravity"],
        )
        self.assertEqual(
            nix_cli.matching_profile_elements(
                "antigravity-ide-fhs",
                "antigravity-ide-fhs",
                "/nix/store/other-antigravity-ide-2.5.5",
                records,
            ),
            [],
        )


class ApplicationCommandTests(unittest.TestCase):
    def write_manifest(self, root: Path, packages: list[str] | None = None) -> Path:
        path = root / "apps.json"
        path.write_text(
            json.dumps({"schemaVersion": 1, "categories": {"other": packages or []}}),
            encoding="utf-8",
        )
        return path

    def test_uninstall_removes_an_individual_profile_element(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_manifest(root)
            elements = {
                "antigravity": {
                    "attrPath": "legacyPackages.x86_64-linux.antigravity",
                    "storePaths": ["/nix/store/hash-antigravity-ide-2.5.5"],
                }
            }
            completed = mock.Mock(returncode=0, stdout="", stderr="")
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(nix_cli, "STATE_ROOT", root / "state"),
                mock.patch.object(nix_cli, "profile_elements", side_effect=[elements, {}]),
                mock.patch.object(nix_cli, "run", return_value=completed) as runner,
            ):
                code = nix_cli.command_remove(["antigravity"], nix_cli.UI(plain=True))
            self.assertEqual(code, 0)
            remove_command = runner.call_args_list[0].args[0]
            self.assertEqual(remove_command[-3:], ["profile", "remove", "antigravity"])

    def test_uninstall_dry_run_reports_profile_without_changing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_manifest(root)
            elements = {
                "antigravity": {
                    "attrPath": "legacyPackages.x86_64-linux.antigravity",
                    "storePaths": ["/nix/store/hash-antigravity-ide-2.5.5"],
                }
            }
            output = io.StringIO()
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(nix_cli, "profile_elements", return_value=elements),
                redirect_stdout(output),
            ):
                code = nix_cli.command_remove(["antigravity", "--dry-run"], nix_cli.UI(plain=True))
            self.assertEqual(code, 0)
            self.assertIn("profile:antigravity", output.getvalue())
            self.assertIn("dry-run complete", output.getvalue())

    def test_combined_uninstall_restores_manifest_when_profile_removal_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_manifest(root, ["hello"])
            before = path.read_text(encoding="utf-8")
            elements = {
                "hello": {
                    "attrPath": "legacyPackages.x86_64-linux.hello",
                    "storePaths": ["/nix/store/hash-hello-1"],
                }
            }
            failed = mock.Mock(returncode=1, stdout="", stderr="profile failure")
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(nix_cli, "STATE_ROOT", root / "state"),
                mock.patch.object(nix_cli, "profile_elements", return_value=elements),
                mock.patch.object(nix_cli, "apply_apps") as apply_apps,
                mock.patch.object(nix_cli, "run", return_value=failed),
                redirect_stdout(io.StringIO()),
                self.assertRaisesRegex(nix_cli.CLIError, "profile failure"),
            ):
                nix_cli.command_remove(["hello"], nix_cli.UI(plain=True))
            self.assertEqual(path.read_text(encoding="utf-8"), before)
            self.assertEqual(apply_apps.call_count, 2)

    def test_list_combines_declarative_profile_and_flatpak_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_manifest(root, ["hello"])
            elements = {
                "antigravity": {
                    "attrPath": "legacyPackages.x86_64-linux.antigravity",
                    "storePaths": ["/nix/store/hash-antigravity-ide-2.5.5"],
                }
            }
            output = io.StringIO()
            with (
                mock.patch.object(nix_cli, "MANIFEST_FILE", path),
                mock.patch.object(nix_cli, "profile_elements", return_value=elements),
                mock.patch.object(
                    nix_cli,
                    "flatpak_applications",
                    return_value=[{"application": "org.example.App", "name": "Example"}],
                ),
                redirect_stdout(output),
            ):
                code = nix_cli.command_list([], nix_cli.UI(plain=True))
            self.assertEqual(code, 0)
            listing = output.getvalue()
            self.assertIn("hello", listing)
            self.assertIn("antigravity", listing)
            self.assertIn("org.example.App", listing)


class PlanningAndCleanupTests(unittest.TestCase):
    def test_build_plan_parser_groups_derivations_and_downloads(self):
        text = """
        these 3 derivations will be built:
          /nix/store/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-nix-helper-2.1.0.drv
          /nix/store/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-unit-dbus.service.drv
          /nix/store/cccccccccccccccccccccccccccccccc-noctalia-shell.drv
        these 1 paths will be fetched:
          /nix/store/dddddddddddddddddddddddddddddddd-source
        """
        parsed = nix_cli.parse_build_plan(text)
        self.assertEqual(len(parsed["derivations"]), 3)
        self.assertEqual(len(parsed["downloads"]), 1)
        self.assertEqual(len(parsed["groups"]["core-driver"]), 1)
        self.assertEqual(len(parsed["groups"]["desktop-sources"]), 1)

    def test_rebuild_scopes_and_exclusions(self):
        self.assertEqual(
            nix_cli.rebuild_selection(["all", "test"], [], ["apps"]),
            (["system"], "test"),
        )
        self.assertEqual(
            nix_cli.rebuild_selection([], ["apps"], []),
            (["apps"], "switch"),
        )
        with self.assertRaises(nix_cli.CLIError):
            nix_cli.rebuild_selection(["apps"], [], ["apps"])
        with self.assertRaises(nix_cli.CLIError):
            nix_cli.rebuild_selection(["switch", "test"], [], [])

    def test_cleanup_components_are_strict(self):
        self.assertEqual(
            nix_cli.parse_clean_components(["store,logs", "caches"]),
            {"store", "logs", "caches"},
        )
        with self.assertRaises(nix_cli.CLIError):
            nix_cli.parse_clean_components(["home"])

    def test_cleanup_candidates_preserve_last_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / "old.log"
            protected = root / "protected.log"
            old.write_text("old", encoding="utf-8")
            protected.write_text("protected", encoding="utf-8")
            os.utime(old, (1, 1))
            os.utime(protected, (1, 1))
            self.assertEqual(
                nix_cli.cleanup_candidates(root, 1, preserve={protected}),
                [old],
            )


class GenerationManagementTests(unittest.TestCase):
    @staticmethod
    def row(number: int, created: float, *, current: bool = False, boot: bool = False):
        return {
            "generation": number,
            "current": current,
            "boot": boot,
            "storePath": f"/nix/store/hash-{number}-nixos-system",
            "created": "2026-01-01T00:00:00",
            "createdTimestamp": created,
            "ageDays": 1.0,
            "nixosVersion": "26.11",
            "kernel": "6.18",
            "rebuild": None,
        }

    def test_retention_policy_combines_count_age_and_explicit_protection(self):
        now = 2_000_000.0
        old = now - 30 * 86400
        recent = now - 86400
        rows = [
            self.row(1, old),
            self.row(2, old),
            self.row(3, recent),
            self.row(4, old),
            self.row(5, old, boot=True),
            self.row(6, old, current=True),
        ]
        plan = nix_cli.generation_retention_plan(
            rows,
            keep=2,
            older_than="14d",
            protected={4},
            now=now,
        )
        self.assertEqual([row["generation"] for row in plan["candidates"]], [1, 2])
        self.assertIn("recent", plan["keepReasons"][3])
        self.assertIn("explicit", plan["keepReasons"][4])
        self.assertIn("boot", plan["keepReasons"][5])
        self.assertIn("current", plan["keepReasons"][6])

    def test_deletion_estimate_counts_only_paths_unused_by_retained_generations(self):
        analysis = {
            "closures": {
                1: {"/nix/store/shared", "/nix/store/old-a", "/nix/store/old-b"},
                2: {"/nix/store/shared", "/nix/store/new"},
            },
            "pathSizes": {
                "/nix/store/shared": 100,
                "/nix/store/old-a": 20,
                "/nix/store/old-b": 30,
                "/nix/store/new": 40,
            },
        }
        estimate = nix_cli.deletion_space_estimate(analysis, {1})
        self.assertEqual(estimate["paths"], 2)
        self.assertEqual(estimate["size"], 50)

        adjusted = nix_cli.deletion_space_estimate(
            analysis,
            {1},
            {"/nix/store/old-b"},
        )
        self.assertEqual(adjusted["paths"], 1)
        self.assertEqual(adjusted["size"], 20)
        self.assertEqual(adjusted["retainedByOtherManagedScopeSize"], 30)

    def test_delete_refuses_current_or_boot_generation_before_mutation(self):
        rows = [self.row(8, 1.0, current=True, boot=True)]
        with (
            mock.patch.object(nix_cli, "generation_records", return_value=rows),
            mock.patch.object(nix_cli, "delete_system_generations") as deleter,
            self.assertRaises(nix_cli.CLIError),
        ):
            nix_cli.command_generations_delete(["8", "--apply"], nix_cli.UI(plain=True, assume_yes=True))
        deleter.assert_not_called()

    def test_delete_is_preview_only_without_apply(self):
        rows = [self.row(7, 1.0), self.row(8, 2.0, current=True, boot=True)]
        estimate = {"paths": 2, "size": 50, "topPaths": []}
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "generation_records", return_value=rows),
            mock.patch.object(nix_cli, "generation_deletion_analysis", return_value=({}, estimate)),
            mock.patch.object(nix_cli, "delete_system_generations") as deleter,
            redirect_stdout(output),
        ):
            code = nix_cli.command_generations_delete(["7"], nix_cli.UI(plain=True))
        self.assertEqual(code, 0)
        deleter.assert_not_called()
        self.assertIn("preview only", output.getvalue())

    def test_exact_deletion_targets_only_requested_system_generations(self):
        with mock.patch.object(nix_cli, "run_streamed", return_value=0) as runner:
            code = nix_cli.delete_system_generations([3, 5], Path("/tmp/generation-test.log"))
        self.assertEqual(code, 0)
        command = runner.call_args.args[0]
        self.assertEqual(command[-3:], ["--delete-generations", "3", "5"])

    def test_profile_generation_inventory_reads_manifest_and_current_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            one = root / "store-one-profile"
            two = root / "store-two-profile"
            one.mkdir()
            two.mkdir()
            (one / "manifest.json").write_text(
                json.dumps({"elements": {"old": {"active": True, "storePaths": ["/nix/store/old"]}}}),
                encoding="utf-8",
            )
            (two / "manifest.json").write_text(
                json.dumps({"elements": {"apps": {"active": True, "storePaths": ["/nix/store/apps"]}}}),
                encoding="utf-8",
            )
            (root / "profile-1-link").symlink_to(one)
            (root / "profile-2-link").symlink_to(two)
            (root / "profile").symlink_to(root / "profile-2-link")
            with mock.patch.object(nix_cli, "PROFILE_PATH", str(root / "profile")):
                rows = nix_cli.profile_generation_records()
            self.assertEqual([row["generation"] for row in rows], [1, 2])
            self.assertFalse(rows[0]["current"])
            self.assertTrue(rows[1]["current"])
            self.assertEqual(rows[1]["elements"], ["apps"])

    def test_profile_element_diff_detects_content_change(self):
        previous = {"elementPaths": {"apps": ["/nix/store/apps-v1"], "old": ["/nix/store/old"]}}
        current = {"elementPaths": {"apps": ["/nix/store/apps-v2"], "new": ["/nix/store/new"]}}
        self.assertEqual(
            nix_cli.profile_element_changes(current, previous),
            {"added": ["new"], "removed": ["old"], "changed": ["apps"]},
        )

    def test_exact_profile_deletion_does_not_use_sudo(self):
        with (
            mock.patch.object(nix_cli, "PROFILE_PATH", "/tmp/test-profile"),
            mock.patch.object(nix_cli, "run_streamed", return_value=0) as runner,
        ):
            code = nix_cli.delete_profile_generations([121, 122], Path("/tmp/profile-generation-test.log"))
        self.assertEqual(code, 0)
        command = runner.call_args.args[0]
        self.assertNotIn("sudo", command)
        self.assertEqual(command[-3:], ["--delete-generations", "121", "122"])

    def test_store_root_summary_separates_histories_and_named_roots(self):
        summary = nix_cli.summarize_store_roots(
            [
                "/nix/var/nix/profiles/system-439-link -> /nix/store/system",
                "/home/pg/.local/state/nix/profiles/profile-154-link -> /nix/store/profile",
                "/home/pg/.local/state/nix-helper/previews/apps -> /nix/store/apps",
                "{censored} -> /nix/store/runtime",
            ]
        )
        self.assertEqual(summary["systemGenerations"], [439])
        self.assertEqual(summary["profileGenerations"], [154])
        self.assertEqual(summary["runtimeRoots"], 1)
        self.assertEqual(len(summary["otherRoots"]), 1)

    def test_combined_root_estimate_subtracts_every_retained_history(self):
        metadata = {
            "/nix/store/old": {"narSize": 20},
            "/nix/store/shared": {"narSize": 30},
        }
        with (
            mock.patch.object(
                nix_cli,
                "store_requisites",
                side_effect=[{"/nix/store/old", "/nix/store/shared"}, {"/nix/store/shared"}],
            ),
            mock.patch.object(nix_cli, "recursive_store_metadata", return_value=metadata),
        ):
            estimate = nix_cli.root_set_deletion_estimate(["candidate"], ["retained"])
        self.assertEqual(estimate["paths"], 1)
        self.assertEqual(estimate["size"], 20)


class SearchTests(unittest.TestCase):
    def test_exact_name_ranks_above_description_match(self):
        exact = {
            "attribute": "ripgrep",
            "pname": "ripgrep",
            "description": "fast search",
            "declared": False,
        }
        description = {
            "attribute": "unrelated",
            "pname": "unrelated",
            "description": "uses ripgrep internally",
            "declared": False,
        }
        self.assertGreater(
            nix_cli.search_relevance("ripgrep", exact),
            nix_cli.search_relevance("ripgrep", description),
        )

    def test_multiword_search_requires_every_term_by_default(self):
        data = {
            "legacyPackages.x86_64-linux.alpha": {
                "pname": "alpha",
                "version": "1",
                "description": "visual code editor",
            },
            "legacyPackages.x86_64-linux.beta": {
                "pname": "beta",
                "version": "1",
                "description": "visual utility",
            },
        }
        with (
            mock.patch.object(nix_cli, "search_results", return_value=data),
            mock.patch.object(nix_cli, "profile_elements", return_value={}),
            mock.patch.object(nix_cli, "store_requisites", return_value=set()),
            mock.patch.object(nix_cli, "Manifest") as manifest_class,
            mock.patch("builtins.print") as printer,
        ):
            manifest_class.return_value.all_packages.return_value = []
            manifest_class.return_value.category_of.return_value = None
            code = nix_cli.command_search(["visual", "editor"], nix_cli.UI(plain=True))
        self.assertEqual(code, 0)
        output = "\n".join(" ".join(map(str, call.args)) for call in printer.call_args_list)
        self.assertIn("alpha", output)
        self.assertNotIn("beta", output)

    def test_search_profile_alias_uses_exact_output_path(self):
        records = {
            "antigravity": {
                "attribute": "antigravity",
                "storePaths": ["/nix/store/installed-antigravity-ide-2.5.5"],
            }
        }
        with mock.patch.object(
            nix_cli,
            "package_out_path",
            return_value="/nix/store/installed-antigravity-ide-2.5.5",
        ):
            profile, system = nix_cli.search_installation_sources(
                "antigravity-ide",
                "antigravity-ide",
                "2.5.5",
                records,
                set(),
            )
        self.assertEqual(profile, ["antigravity"])
        self.assertFalse(system)

        with mock.patch.object(
            nix_cli,
            "package_out_path",
            return_value="/nix/store/different-antigravity-ide-2.5.5",
        ):
            profile, system = nix_cli.search_installation_sources(
                "antigravity-ide-fhs",
                "antigravity-ide",
                "2.5.5",
                records,
                set(),
            )
        self.assertEqual(profile, [])
        self.assertFalse(system)


class FlatpakTests(unittest.TestCase):
    def application(self, **updates: str) -> dict[str, str]:
        result = {
            "application": "org.example.App",
            "name": "Example App",
            "version": "1.2.3",
            "branch": "stable",
            "origin": "flathub",
            "installation": "system",
        }
        result.update(updates)
        return result

    def test_flatpak_inventory_parses_provenance(self):
        completed = mock.Mock(
            returncode=0,
            stdout="org.example.App\tExample App\t1.2.3\tstable\tflathub\tsystem\n",
            stderr="",
        )
        with (
            mock.patch.object(nix_cli.shutil, "which", return_value="/bin/flatpak"),
            mock.patch.object(nix_cli, "run", return_value=completed) as runner,
        ):
            applications = nix_cli.flatpak_applications(["--system"])
        self.assertEqual(applications, [self.application()])
        self.assertIn("--columns=application,name,version,branch,origin,installation", runner.call_args.args[0])

    def test_flatpak_inventory_without_scope_checks_system_and_user(self):
        system = mock.Mock(
            returncode=0,
            stdout="org.example.App\tExample App\t1.2.3\tstable\tflathub\tsystem\n",
            stderr="",
        )
        user = mock.Mock(
            returncode=0,
            stdout="org.example.UserApp\tUser App\t2.0\tstable\tflathub\tuser\n",
            stderr="",
        )
        with (
            mock.patch.object(nix_cli.shutil, "which", return_value="/bin/flatpak"),
            mock.patch.object(nix_cli, "run", side_effect=[system, user]) as runner,
        ):
            applications = nix_cli.flatpak_applications()
        self.assertEqual(runner.call_count, 2)
        self.assertEqual({app["installation"] for app in applications}, {"system", "user"})

    def test_flatpak_search_marks_installed_apps(self):
        remote = {
            "application": "org.example.App",
            "name": "Example App",
            "description": "An example",
            "version": "1.3.0",
            "branch": "stable",
            "remotes": "flathub",
        }
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "flatpak_applications", return_value=[self.application()]),
            mock.patch.object(nix_cli, "flatpak_search_results", return_value=[remote]),
            redirect_stdout(output),
        ):
            code = nix_cli.command_flatpak_search(["Example"], nix_cli.UI(plain=True))
        self.assertEqual(code, 0)
        self.assertIn("installed · flatpak/system", output.getvalue())
        self.assertIn("org.example.App", output.getvalue())

    def test_flatpak_install_dry_run_never_mutates_state(self):
        remote = {
            "application": "org.example.App",
            "name": "Example App",
            "description": "An example",
            "version": "1.3.0",
            "branch": "stable",
            "remotes": "flathub",
        }
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "flatpak_applications", return_value=[]),
            mock.patch.object(nix_cli, "resolve_flatpak_remote_application", return_value=remote),
            mock.patch.object(nix_cli, "flatpak_binary", return_value="/bin/flatpak"),
            mock.patch.object(nix_cli, "run") as runner,
            redirect_stdout(output),
        ):
            code = nix_cli.command_flatpak_install(
                ["org.example.App", "--dry-run"],
                nix_cli.UI(plain=True),
            )
        self.assertEqual(code, 0)
        runner.assert_not_called()
        self.assertIn("no Flatpak was installed", output.getvalue())

    def test_flatpak_uninstall_detects_scope_and_preserves_data(self):
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "flatpak_applications", return_value=[self.application()]),
            mock.patch.object(nix_cli, "flatpak_binary", return_value="/bin/flatpak"),
            mock.patch.object(nix_cli, "run") as runner,
            redirect_stdout(output),
        ):
            code = nix_cli.command_flatpak_uninstall(
                ["org.example.App", "--dry-run"],
                nix_cli.UI(plain=True),
            )
        self.assertEqual(code, 0)
        runner.assert_not_called()
        self.assertIn("flatpak/system", output.getvalue())
        self.assertIn("no Flatpak was removed", output.getvalue())

    def test_flatpak_scopes_are_explicit(self):
        self.assertEqual(nix_cli.flatpak_scope_options(default_system=True), ["--system"])
        self.assertEqual(nix_cli.flatpak_scope_options(user=True), ["--user"])
        self.assertEqual(
            nix_cli.flatpak_scope_options(installation="work"),
            ["--installation=work"],
        )

    def test_flatpak_update_preview_uses_cached_remote_metadata(self):
        completed = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "name": "Example App",
                        "application_id": "org.example.App",
                        "version": "1.3.0",
                        "branch": "stable",
                        "origin": "flathub",
                    }
                ]
            ),
            stderr="",
        )
        with (
            mock.patch.object(nix_cli, "flatpak_binary", return_value="/bin/flatpak"),
            mock.patch.object(nix_cli, "run", return_value=completed) as runner,
        ):
            updates = nix_cli.flatpak_update_candidates([self.application()], ["--system"])
        self.assertEqual(updates[0]["installedVersion"], "1.2.3")
        self.assertEqual(updates[0]["availableVersion"], "1.3.0")
        self.assertIn("--cached", runner.call_args.args[0])


class InterfaceTests(unittest.TestCase):
    @staticmethod
    def rice_status(active: str = "noctalia") -> dict:
        return {
            "active": active,
            "shells": [
                {
                    "name": "noctalia",
                    "label": "Noctalia C++",
                    "version": "5.0.0",
                    "selected": active == "noctalia",
                    "running": active == "noctalia",
                },
                {
                    "name": "caelestia",
                    "label": "Caelestia Shell",
                    "version": "1.0.0",
                    "selected": active == "caelestia",
                    "running": active == "caelestia",
                },
                {
                    "name": "noctalia-legacy",
                    "label": "Noctalia Stable (Legacy/Quickshell)",
                    "version": "4.7.7+legacy.a08ff361",
                    "selected": active == "noctalia-legacy",
                    "running": active == "noctalia-legacy",
                },
            ],
        }

    def test_global_options_are_removed_before_dispatch(self):
        remaining, json_mode, plain, assume_yes = nix_cli.parse_global_options(
            ["--json", "--plain", "--yes", "doctor"]
        )
        self.assertEqual(remaining, ["doctor"])
        self.assertTrue(json_mode)
        self.assertTrue(plain)
        self.assertTrue(assume_yes)

    def test_native_config_is_not_claimed_as_custom_top_level(self):
        self.assertNotIn("config", nix_cli.CUSTOM_COMMANDS)
        self.assertIn("cfg", nix_cli.CUSTOM_COMMANDS)
        self.assertIn("flatpak", nix_cli.CUSTOM_COMMANDS)
        self.assertIn("shell", nix_cli.CUSTOM_COMMANDS)
        self.assertIn("rice", nix_cli.CUSTOM_COMMANDS)

    def test_shell_list_shows_versions_and_state(self):
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "rice_shell_status", return_value=self.rice_status()),
            redirect_stdout(output),
        ):
            result = nix_cli.command_shell(["list"], nix_cli.UI(plain=True))
        self.assertEqual(result, 0)
        self.assertIn("Noctalia C++", output.getvalue())
        self.assertIn("5.0.0", output.getvalue())
        self.assertIn("selected", output.getvalue())
        self.assertIn("Caelestia Shell", output.getvalue())
        self.assertIn("1.0.0", output.getvalue())
        self.assertIn("Noctalia Stable (Legacy/Quickshell)", output.getvalue())
        self.assertIn("4.7.7+legacy.a08ff361", output.getvalue())

    def test_shell_switch_routes_to_manager_and_restores_its_rice(self):
        result_status = self.rice_status("noctalia-legacy")
        completed = mock.Mock(returncode=0, stdout=json.dumps(result_status), stderr="")
        with (
            mock.patch.object(nix_cli, "rice_shell_status", return_value=self.rice_status()),
            mock.patch.object(nix_cli, "rice_manager_value", return_value={"restored": False}) as rice_manager,
            mock.patch.object(nix_cli, "run", return_value=completed) as runner,
        ):
            result = nix_cli.command_shell(["switch", "noctalia-legacy"], nix_cli.UI(plain=True))
        self.assertEqual(result, 0)
        runner.assert_called_once_with(
            [nix_cli.RICE_SHELL_BIN, "switch", "noctalia-legacy", "--json"],
            capture=True,
        )
        rice_manager.assert_called_once_with(["restore", "--shell", "noctalia-legacy"], required=False)

    def test_rice_list_renders_only_manager_results(self):
        value = {
            "shell": "caelestia",
            "active": None,
            "rices": [
                {
                    "id": "caelestia-glass",
                    "label": "Caelestia Glass",
                    "description": "Glass theme",
                    "compatible": True,
                    "active": False,
                }
            ],
        }
        output = io.StringIO()
        with (
            mock.patch.object(nix_cli, "rice_manager_value", return_value=value) as manager,
            redirect_stdout(output),
        ):
            result = nix_cli.command_rice(["list"], nix_cli.UI(plain=True))
        self.assertEqual(result, 0)
        manager.assert_called_once_with(["list"])
        self.assertIn("Caelestia Glass", output.getvalue())

    def test_rice_apply_plans_confirms_and_applies(self):
        plan = {
            "rice": "midnight-amethyst",
            "label": "Midnight Amethyst",
            "shell": "noctalia",
            "mode": "dark",
            "wallpaper": "/wallpaper.png",
            "apps": ["kitty"],
            "targets": ["/config"],
            "restart": False,
        }
        result_value = {"label": "Midnight Amethyst", "snapshot": "snapshot-1"}
        with mock.patch.object(nix_cli, "rice_manager_value", side_effect=[plan, result_value]) as manager:
            result = nix_cli.command_rice(["apply", "midnight-amethyst"], nix_cli.UI(plain=True, assume_yes=True))
        self.assertEqual(result, 0)
        self.assertEqual(manager.call_args_list, [mock.call(["plan", "midnight-amethyst"]), mock.call(["apply", "midnight-amethyst"])])

    def test_old_rice_shell_namespace_has_clear_migration_error(self):
        with self.assertRaisesRegex(nix_cli.CLIError, "moved to `nix shell`"):
            nix_cli.command_rice(["shell", "list"], nix_cli.UI(plain=True))


if __name__ == "__main__":
    unittest.main()
