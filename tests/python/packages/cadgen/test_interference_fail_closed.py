"""Regression checks for incomplete and failed interference measurements."""

import json
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from build123d import Box, Pos, Shape
from OCP.TopoDS import TopoDS_Shape

from cadgen.interference import Occurrence, _intersection, _shape_bbox, find_clashes, inspect_interference


class InterferenceFailClosedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.a = self.occurrence("o1", Box(10, 10, 10))
        self.b = self.occurrence("o2", Pos(5, 0, 0) * Box(10, 10, 10))
        self.far = self.occurrence("o3", Pos(30, 0, 0) * Box(10, 10, 10))

    @staticmethod
    def occurrence(ref: str, shape: Shape) -> Occurrence:
        return Occurrence(ref, ref, shape.wrapped, _shape_bbox(shape.wrapped))

    def inspect(self, occurrences: list[Occurrence], **kwargs: Any) -> dict:
        target = SimpleNamespace(source_path=None, step_path=Path("fixture.step"), cad_path="fixture.step")
        with (
            patch("cadgen.step_targets.resolve_step_target", return_value=target),
            patch("cadgen.step_export_target._resolve_spec_and_scene", return_value=(None, object())),
            patch("cadgen.interference.occurrences_from_scene", return_value=occurrences),
            patch("cadgen.interference.scene_label_rows", return_value=[]),
        ):
            result = inspect_interference("fixture.step", **kwargs)
        json.dumps(result, allow_nan=False)
        return result

    def assert_incomplete(self, result: dict) -> None:
        self.assertFalse(result["ok"])
        self.assertFalse(result["complete"])
        self.assertTrue(result["errors"])

    def test_boolean_failure_and_null_result_fail_closed(self) -> None:
        for common in (None, TopoDS_Shape()):
            with self.subTest(common=common), patch("cadgen.interference._intersection", return_value=common):
                result = self.inspect([self.a, self.b])
                self.assert_incomplete(result)
                self.assertEqual(result["stats"]["pairs_failed"], 1)
                self.assertEqual(result["stats"]["pairs_tested"], 1)
                self.assertEqual(result["errors"][0]["a"]["ref"], "o1")
                self.assertEqual(result["errors"][0]["b"]["ref"], "o2")

    def test_boolean_volume_and_bounds_exceptions_fail_closed(self) -> None:
        for helper in ("_intersection", "_solid_volume", "_shape_bbox"):
            with self.subTest(helper=helper), patch(
                "cadgen.interference." + helper, side_effect=RuntimeError("kernel failure")
            ):
                result = self.inspect([self.a, self.b])
                self.assert_incomplete(result)
                self.assertEqual(result["stats"]["pairs_failed"], 1)
                self.assertIn("kernel failure", result["errors"][0]["message"])

    def test_nonfinite_volumes_fail_closed(self) -> None:
        for volume in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(volume=volume), patch("cadgen.interference._solid_volume", return_value=volume):
                result = self.inspect([self.a, self.b])
                self.assert_incomplete(result)
                self.assertEqual(result["clashes"], [])

    def test_nonfinite_intersection_bounds_fail_closed(self) -> None:
        with patch("cadgen.interference._shape_bbox", return_value=(float("nan"), 0, 0, 1, 1, 1)):
            result = self.inspect([self.a, self.b])
        self.assert_incomplete(result)

    def test_nonfinite_occurrence_bounds_cannot_silently_skip_pair(self) -> None:
        invalid = replace(self.a, bbox=(float("nan"), 0, 0, 1, 1, 1))
        self.assert_incomplete(self.inspect([invalid, self.b]))

    def test_invalid_options_fail_closed_even_without_pairs(self) -> None:
        for tolerance in (float("nan"), float("inf"), float("-inf"), -1.0):
            with self.subTest(tolerance=tolerance):
                self.assert_incomplete(self.inspect([], tolerance=tolerance))
                with self.assertRaises(ValueError):
                    find_clashes([], tolerance=tolerance)
        for limit in (-1, float("nan"), float("inf"), 0.5):
            with self.subTest(max_pairs=limit):
                self.assert_incomplete(self.inspect([], max_pairs=limit))

    def test_truncation_without_clashes_is_not_a_pass(self) -> None:
        result = self.inspect([self.a, self.b], max_pairs=0)
        self.assert_incomplete(result)
        self.assertEqual(result["clashCount"], 0)
        self.assertEqual(result["stats"]["pairs_truncated"], 1)

    def test_empty_selection_is_incomplete_but_single_part_is_complete(self) -> None:
        self.assert_incomplete(self.inspect([]))
        result = self.inspect([self.a])
        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["stats"]["pairs_total"], 0)

    def test_exact_budget_and_bbox_rejections_are_complete(self) -> None:
        result = self.inspect([self.a, self.b, self.far], max_pairs=1, tolerance=1000.0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["stats"]["pairs_tested"], 1)
        self.assertEqual(result["stats"]["pairs_skipped_bbox"], 2)
        self.assertEqual(result["errors"], [])

    def test_successful_empty_intersection_is_not_a_boolean_failure(self) -> None:
        common = _intersection(self.a.shape, self.far.shape)
        self.assertIsNotNone(common)
        self.assertFalse(common.IsNull())
        # Force a conservative broad-phase candidate while using real disjoint solids.
        candidate = replace(self.far, bbox=self.a.bbox)
        result = self.inspect([self.a, candidate])
        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["stats"]["pairs_tested"], 1)
        self.assertEqual(result["clashes"], [])
        self.assertEqual(result["errors"], [])

    def test_real_clash_is_complete_but_not_ok(self) -> None:
        result = self.inspect([self.a, self.b])
        self.assertFalse(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["clashCount"], 1)
        self.assertAlmostEqual(result["clashes"][0]["volume"], 500.0)
        self.assertEqual(result["errors"], [])

    def test_failure_does_not_discard_other_clashes_or_exceed_budget(self) -> None:
        third = self.occurrence("o3", Pos(2, 0, 0) * Box(10, 10, 10))
        original = _intersection
        calls = 0

        def fail_first(a: Any, b: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 1:
                return None
            return original(a, b)

        with patch("cadgen.interference._intersection", side_effect=fail_first):
            result = self.inspect([self.a, self.b, third], max_pairs=2)
        self.assert_incomplete(result)
        self.assertEqual(result["clashCount"], 1)
        self.assertEqual(result["stats"]["pairs_tested"], 2)
        self.assertEqual(result["stats"]["pairs_failed"], 1)
        self.assertEqual(result["stats"]["pairs_truncated"], 1)


if __name__ == "__main__":
    unittest.main()
