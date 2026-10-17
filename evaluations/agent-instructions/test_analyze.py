import json
from pathlib import Path
import tempfile
import unittest

from analyze import export, VARIANTS


class ExportTests(unittest.TestCase):
    def fixture(self, root):
        run = root / "run"
        (run / "audit").mkdir(parents=True)
        manifest = {"model": "fixture", "effort": "medium", "repeats": 1, "seed": 1,
                    "task_snapshot": [{"id": "interval_union"}],
                    "jobs": [["interval_union", v, 0] for v in VARIANTS],
                    "harness_sha256": "fixture", "tasks_sha256": "fixture",
                    "variants": {v: {"sha256": "fixture", "utf8_bytes": 0} for v in VARIANTS}}
        (run / "manifest.json").write_text(json.dumps(manifest))
        (run / "audit/isolation.json").write_text(json.dumps({"passed": True, "host_hashes_unchanged_after_run": True}))
        for v in VARIANTS:
            p = run / "episodes" / v
            p.mkdir(parents=True)
            record = {"task": "interval_union", "kind": "code", "variant": v, "repeat": 0,
                      "correct": True, "error": False, "seconds": 1, "final_chars": 1,
                      "commands": 1, "behaviors": {}, "usage": {"output_tokens": 1}}
            (p / "result.json").write_text(json.dumps(record))
        return run

    def test_recomputes_stale_summary(self):
        with tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as directory:
            root = Path(directory)
            run = self.fixture(root)
            (run / "summary.json").write_text('{"recorded_episodes":1}')
            export(run, root / "out")
            artifact = json.loads((root / "out/pilot-results.json").read_text())
            self.assertEqual(artifact["summary"]["recorded_episodes"], 4)
            self.assertEqual(artifact["by_kind"]["original"]["code"], {"correct": 1, "episodes": 1})

    def test_rejects_incomplete_and_invalidated_runs(self):
        with tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as directory:
            root = Path(directory)
            run = self.fixture(root)
            (run / "episodes/none/result.json").unlink()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                export(run, root / "out")
            (run / "INVALID.json").write_text('{}')
            with self.assertRaisesRegex(ValueError, "Invalidated"):
                export(run, root / "out")


if __name__ == "__main__":
    unittest.main()
