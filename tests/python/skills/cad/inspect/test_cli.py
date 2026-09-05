"""The inspect front door: `cadgen step inspect` (the skill shims are gone).

The command is a SHELL over `cadgen.step.inspect` — argv in, the verb's report
out — so the CLI and a Python caller cannot answer the same question
differently. `ShellsOverTheVerb` pins that: every subcommand goes through the
verb, and the verb takes the argument the subcommand parsed.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


class InspectCliFrontDoorTests(unittest.TestCase):
    def test_incomplete_interference_text_preserves_clashes_and_coverage(self) -> None:
        from cadgen.cli.step_inspect.cli import _format_interfere_text

        result = {
            "ok": False, "complete": False, "conclusive": False,
            "entry": "fixture.step", "tolerance": 1,
            "stats": {"pairs_tested": 2, "pairs_total": 3, "pairs_failed": 1, "pairs_truncated": 1},
            "errors": [{"message": "kernel failed"}],
            "clashes": [{"volume": 50, "a": {"name": "plate", "ref": "o1"},
                         "b": {"name": "shaft", "ref": "o2"}}],
            "intraPartOverlaps": [{"volume": 25, "part": {"name": "servo", "ref": "o3"}}],
        }
        text = _format_interfere_text(result)
        for expected in ("INCOMPLETE", "kernel failed", "plate [o1]", "shaft [o2]", "50.0",
                         "2 tested", "TRUNCATED", "servo [o3]", "intra-part"):
            self.assertIn(expected, text)
        self.assertNotIn("PASS", text)
        result["clashes"] = []
        self.assertNotIn("PASS", _format_interfere_text(result))

    def test_each_incomplete_signal_prevents_a_text_pass(self) -> None:
        from cadgen.cli.step_inspect.cli import _format_interfere_text

        for signal in ({"complete": False}, {"errors": [{"message": "failed"}]},
                       {"stats": {"pairs_failed": 1}}, {"stats": {"pairs_truncated": 1}}):
            with self.subTest(signal=signal):
                text = _format_interfere_text({"ok": False, **signal})
                self.assertIn("INCOMPLETE", text)
                self.assertNotIn("PASS", text)

    def test_incomplete_report_through_public_verb_and_cli_exits_nonzero(self) -> None:
        from cadgen.cli.step_inspect import cli

        report = {"ok": False, "complete": False, "conclusive": False,
                  "errors": [{"code": "pairFailed", "message": "kernel failed"}],
                  "stats": {"pairs_failed": 1}, "clashes": []}
        for flags in ([], ["--json"], ["--format", "text"]):
            with self.subTest(flags=flags):
                args = cli.build_parser().parse_args(["interfere", "fixture.step", *flags])
                output = io.StringIO()
                with mock.patch("cadgen.interference.inspect_interference", return_value=report), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                    self.assertNotEqual(0, args.handler(args))
                if "text" not in flags:
                    emitted = json.loads(output.getvalue())
                    self.assertFalse(emitted["ok"])
                    self.assertFalse(emitted["complete"])
                else:
                    self.assertIn("INCOMPLETE", output.getvalue())
                    self.assertNotIn("PASS", output.getvalue())

    def test_front_door_help_names_the_cadgen_verb(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cadgen.cli", "step", "inspect", "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertIn("usage: cadgen step inspect", result.stdout)

    def test_inspect_help_does_not_import_heavy_cad_modules(self) -> None:
        code = (
            "import sys; "
            "import cadgen.cli.step_inspect.cli; "
            "print('OCP.OCP' in sys.modules); "
            "print('cadgen._internal.step_scene' in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertEqual(["False", "False"], result.stdout.strip().splitlines())

    def test_inspect_rejects_render_subcommand(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cadgen.cli", "step", "inspect", "render", "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid choice", result.stderr)


class ShellsOverTheVerb(unittest.TestCase):
    """Each subcommand reaches `cadgen.step.inspect`, with what it parsed."""

    # (argv, the inspection the verb must be asked for, a call kwarg it must carry)
    CASES = (
        (["refs", "part.step", "#o1.1", "--facts"], "refs", ("facts", True)),
        (["diff", "left.step", "right.step"], "diff", ("against", "right.step")),
        (["frame", "part.step", "#o1.2"], "frame", ("refs", ["#o1.2"])),
        (
            ["measure", "part.step", "--from", "#o1.1", "--to", "#o1.2"],
            "measure",
            ("refs", ["#o1.1", "#o1.2"]),
        ),
        (
            ["align", "part.step", "--moving", "#o1.1", "--target", "#o1.2", "--mode", "center"],
            "align",
            ("align_mode", "center"),
        ),
        (["interfere", "part.step", "--refs", "o1.1,o1.2"], "interfere", ("refs", ["o1.1", "o1.2"])),
        (["validate", "part.step", "--allow-open"], "validate", ("allow_open", True)),
        (["validate", "part.step", "--every-placement"], "validate", ("every_placement", True)),
        (["validate", "part.step", "--out", "v.json"], "validate", ("out", Path("v.json"))),
    )

    def _dispatch(self, argv: list[str]) -> dict:
        from cadgen.cli.step_inspect import cli as inspect_cli

        seen: dict = {}

        def fake_verb(**call):
            seen.update(call)
            return SimpleNamespace(ok=True, command=call.get("inspection"), report={"ok": True})

        args = inspect_cli.build_parser().parse_args(argv)
        with mock.patch.object(inspect_cli, "_inspect_verb", lambda: fake_verb):
            with mock.patch.object(inspect_cli, "_emit_result", lambda *a, **k: None):
                self.assertEqual(0, args.handler(args))
        return seen

    def test_every_subcommand_calls_the_verb(self) -> None:
        for argv, inspection, (name, value) in self.CASES:
            with self.subTest(subcommand=argv[0]):
                call = self._dispatch(argv)
                self.assertEqual(call["inspection"], inspection)
                self.assertEqual(call[name], value)
                self.assertEqual(str(call["target"]), argv[1])

    def test_the_verb_covers_every_subcommand_the_parser_offers(self) -> None:
        """No subcommand may reach an inspection the verb does not name."""
        from cadgen import step
        from cadgen.cli.step_inspect import cli as inspect_cli

        parser = inspect_cli.build_parser()
        subcommands = {
            name
            for action in parser._actions  # noqa: SLF001 - argparse exposes no public view
            if action.nargs == argparse.PARSER
            for name in (action.choices or ())
        }
        self.assertEqual(subcommands, set(step.INSPECTIONS))


if __name__ == "__main__":
    unittest.main()
