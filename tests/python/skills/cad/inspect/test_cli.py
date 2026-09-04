from __future__ import annotations

import subprocess
import sys
import unittest

from tests.python.support.paths import repo_path


class InspectCliWrapperTests(unittest.TestCase):
    def test_incomplete_interference_text_preserves_clashes_and_coverage(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("inspect_cli_format_test", repo_path("skills/cad/scripts/inspect/inspect_refs/cli.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = {"ok": False, "complete": False, "entry": "fixture.step", "tolerance": 1,
                  "stats": {"pairs_tested": 2, "pairs_total": 3, "pairs_failed": 1, "pairs_truncated": 1},
                  "errors": [{"message": "kernel failed"}],
                  "clashes": [{"volume": 50, "a": {"name": "plate", "ref": "o1"}, "b": {"name": "shaft", "ref": "o2"}}]}
        text = module._format_interfere_text(result)
        for expected in ("INCOMPLETE", "kernel failed", "plate [o1]", "shaft [o2]", "50.0", "2 tested", "TRUNCATED"):
            self.assertIn(expected, text)
        self.assertNotIn("PASS", text)
        result["clashes"] = []
        self.assertNotIn("PASS", module._format_interfere_text(result))

    def test_inspect_directory_invokes_cli(self) -> None:
        skill_root = repo_path("skills/cad")
        result = subprocess.run(
            [sys.executable, "scripts/inspect", "--help"],
            cwd=skill_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertIn("usage: scripts/inspect", result.stdout)

    def test_inspect_help_does_not_import_heavy_cad_modules(self) -> None:
        skill_root = repo_path("skills/cad")
        code = (
            "import sys; "
            "sys.path.insert(0, 'scripts/inspect'); "
            "import inspect_refs.cli; "
            "print('OCP.OCP' in sys.modules); "
            "print('cadgen._internal.step_scene' in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=skill_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertEqual(["False", "False"], result.stdout.strip().splitlines())

    def test_scripts_inspect_rejects_render_subcommand(self) -> None:
        skill_root = repo_path("skills/cad")
        result = subprocess.run(
            [sys.executable, "scripts/inspect", "render", "--help"],
            cwd=skill_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid choice", result.stderr)

    def test_scripts_inspect_worker_reads_jsonl(self) -> None:
        skill_root = repo_path("skills/cad")
        result = subprocess.run(
            [sys.executable, "scripts/inspect", "worker"],
            cwd=skill_root,
            input='{"id":"bad","argv":["refs"]}\n',
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertIn('"id":"bad"', result.stdout)
        self.assertIn('"exitCode":2', result.stdout)


if __name__ == "__main__":
    unittest.main()
