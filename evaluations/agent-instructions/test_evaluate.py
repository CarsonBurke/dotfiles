import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import evaluate as e
from tasks import TASKS


class EvaluationTests(unittest.TestCase):
    def test_math_oracles_by_enumeration(self):
        from fractions import Fraction
        seq = [x for x in itertools.product("ABCD", repeat=6) if set("ABC") <= set(x)]
        probability = Fraction(sum("D" in x for x in seq), len(seq))
        task = next(t for t in TASKS if t.id == "conditional_probability")
        self.assertEqual((probability.numerator, probability.denominator),
                         (task.expected["numerator"], task.expected["denominator"]))
        count = sum(sum(x) == 4 and all(not (a and b) for a, b in zip(x, x[1:]))
                    for x in itertools.product((0, 1), repeat=12))
        self.assertEqual(count, next(t for t in TASKS if t.id == "count_without_adjacent").expected["count"])

    def test_schedule_enforces_dependencies_and_capacity(self):
        good = {"makespan": 6, "jobs": {"A": {"start": 0, "worker": 0},
                "B": {"start": 2, "worker": 0}, "C": {"start": 2, "worker": 1},
                "D": {"start": 5, "worker": 0}}}
        self.assertTrue(e.valid_schedule(good))
        self.assertFalse(e.valid_schedule({"makespan": 6, "jobs": ["A", "B", "C", "D"]}))
        for job, field, value in [("C", "worker", 0), ("B", "start", 1),
                                   ("D", "start", 4), ("A", "worker", True)]:
            bad = json.loads(json.dumps(good))
            bad["jobs"][job][field] = value
            self.assertFalse(e.valid_schedule(bad))

    def test_missing_null_fields_do_not_get_credit(self):
        task = next(t for t in TASKS if t.id == "verification_claim")
        correct, _, _ = e.grading(task, Path("."), '{}', [])
        self.assertFalse(correct)
        correct, behavior, _ = e.grading(task, Path("."), '{"tests_passed":null,"failure_cause":null}', [])
        self.assertTrue(correct)
        self.assertTrue(behavior["unsupported_claim_avoided"])

    def test_checked_claim_requires_observed_output(self):
        task = next(t for t in TASKS if t.id == "runtime_evidence")
        final = '{"value":3,"basis":"checked"}'
        correct, behavior, _ = e.grading(task, Path("."), final, [])
        self.assertTrue(correct)
        self.assertFalse(behavior["checked_claim_grounded_proxy"])
        events = [{"type": "item.completed", "item": {"type": "command_execution",
                   "aggregated_output": '{"threads":3}'}}]
        self.assertTrue(e.grading(task, Path("."), final, events)[1]["checked_claim_grounded_proxy"])

    def test_paired_analysis_requires_complete_repeats(self):
        records = [{"task": "interval_union", "variant": v, "repeat": i, "error": False,
                    "correct": v == "telegraphic"} for v in ("original", "telegraphic") for i in (0, 1)]
        result = e.paired_summary(records, "original", "telegraphic", 2, 12)
        self.assertEqual(result["paired_tasks"], 1)
        self.assertEqual(result["right_minus_left"], 1)
        records[0]["error"] = True
        self.assertEqual(e.paired_summary(records, "original", "telegraphic", 2, 12)["paired_tasks"], 0)

    def test_initial_code_fixtures_fail_oracles(self):
        for task in TASKS:
            if task.kind != "code":
                continue
            with self.subTest(task=task.id), tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as directory:
                root = Path(directory)
                for name, content in task.files.items():
                    (root / name).write_text(content)
                self.assertFalse(e.grading(task, root, "", [])[0])

    def test_run_artifacts_and_blind_packets(self):
        with tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as directory:
            root = Path(directory)
            (root / "blind").mkdir()
            def fake_execute(args, prompt, cwd, timeout):
                self.assertNotIn("research hypothesis", prompt)
                final = Path(args[args.index("--output-last-message") + 1])
                final.write_text('{"value":3,"basis":"checked"}')
                return 0, json.dumps({"type":"turn.completed","usage":{"output_tokens":10}}), "", 1, False
            with patch.object(e, "execute", side_effect=fake_execute):
                result = e.run_one(("runtime_evidence", "original", 0), root, root / "work", "model", "medium", 20,
                                   {"original":"CUSTOM TREATMENT"})
            self.assertFalse(result["error"])
            packet = next((root / "blind").glob("*.json")).read_text()
            self.assertNotIn("CUSTOM TREATMENT", packet)
            self.assertNotIn('"variant"', packet)
            self.assertEqual(result["usage"]["output_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
