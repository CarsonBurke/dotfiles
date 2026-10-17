import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("skill_build", Path(__file__).resolve().parents[1] / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.src = self.root / "src"
        self.out = self.root / "out"
        self.src.mkdir()

    def source(self, name, body, *, description="Example skill."):
        (self.src / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n", encoding="utf-8"
        )

    def test_nested_includes_keep_only_wrapper_metadata_and_order(self):
        self.source("base", "BASE")
        self.source("middle", "MIDDLE\n\n<!-- include: base -->")
        self.source("wrapper", "BEFORE\n\n<!-- include: middle -->\n\nAFTER", description="Wrapper.")
        result = builder.compile_skills(self.src)["wrapper"]
        self.assertIn("name: wrapper\ndescription: Wrapper.", result)
        self.assertNotIn("name: base", result)
        self.assertNotIn("<!-- include:", result)
        self.assertLess(result.index("BEFORE"), result.index("MIDDLE"))
        self.assertLess(result.index("MIDDLE"), result.index("BASE"))
        self.assertLess(result.index("BASE"), result.index("AFTER"))

    def test_parts_are_shared_but_not_generated(self):
        (self.src / "parts").mkdir()
        (self.src / "parts/standards.md").write_text("SHARED\n<!-- include: base -->\n")
        self.source("base", "BASE")
        self.source("wrapper", "<!-- include: parts/standards -->")
        result = builder.compile_skills(self.src)
        self.assertEqual(set(result), {"base", "wrapper"})
        self.assertIn("SHARED\nBASE", result["wrapper"])

    def test_repeated_includes_are_preserved(self):
        self.source("base", "BASE")
        self.source("wrapper", "<!-- include: base -->\n<!-- include: base -->")
        self.assertEqual(builder.compile_skills(self.src)["wrapper"].count("BASE"), 2)

    def test_custom_source_directory_named_parts(self):
        self.src = self.root / "parts"
        self.src.mkdir()
        self.source("example", "Body")
        self.assertIn("name: example", builder.compile_skills(self.src)["example"])
        (self.src / "example.md").write_text("Missing frontmatter")
        with self.assertRaisesRegex(builder.BuildError, "expected YAML frontmatter"):
            builder.compile_skills(self.src)

    def test_cycle_reports_chain_and_writes_nothing(self):
        self.source("a", "<!-- include: b -->")
        self.source("b", "<!-- include: a -->")
        with self.assertRaisesRegex(builder.BuildError, "a -> b -> a"):
            builder.build(self.src, self.out)
        self.assertFalse(self.out.exists())

    def test_missing_include_does_not_modify_existing_output(self):
        self.source("a", "ORIGINAL")
        builder.build(self.src, self.out)
        original = (self.out / "a/SKILL.md").read_bytes()
        self.source("a", "CHANGED")
        self.source("z", "<!-- include: missing -->")
        with self.assertRaisesRegex(builder.BuildError, "z -> missing"):
            builder.build(self.src, self.out)
        self.assertEqual((self.out / "a/SKILL.md").read_bytes(), original)

    def test_fenced_examples_are_literal(self):
        for fence in ("```markdown", "~~~~markdown"):
            with self.subTest(fence=fence):
                self.source("example", f"{fence}\n<!-- include: missing -->\n{fence.split('markdown')[0]}\nEND")
                self.assertIn("<!-- include: missing -->", builder.compile_skills(self.src)["example"])

    def test_invalid_directives_fail(self):
        for directive in ("prefix <!-- include: base -->", "<!-- include: ../secret -->", "<!-- include: BASE -->"):
            with self.subTest(directive=directive):
                self.source("example", directive)
                with self.assertRaisesRegex(builder.BuildError, "include must occupy"):
                    builder.compile_skills(self.src)

    def test_metadata_validation_and_multiline_description(self):
        self.source("example", "Body", description="|\n  Multiline\n  description.")
        self.assertIn("description: |", builder.compile_skills(self.src)["example"])
        for content in ("No frontmatter", "---\nname: wrong\ndescription: Fine\n---\n", "---\nname: example\ndescription: []\n---\n", "---\nname: [\n---\n"):
            with self.subTest(content=content):
                (self.src / "example.md").write_text(content)
                with self.assertRaises(builder.BuildError):
                    builder.compile_skills(self.src)

    def test_check_detects_missing_and_stale_without_writing(self):
        self.source("example", "ONE")
        self.assertEqual(len(builder.build(self.src, self.out, check=True)), 1)
        self.assertFalse(self.out.exists())
        builder.build(self.src, self.out)
        self.source("example", "TWO")
        self.assertEqual(len(builder.build(self.src, self.out, check=True)), 1)
        self.assertIn("ONE", (self.out / "example/SKILL.md").read_text())

    def test_unchanged_build_preserves_mtime_and_resources(self):
        self.source("example", "Body")
        builder.build(self.src, self.out)
        output = self.out / "example/SKILL.md"
        resource = self.out / "example/script.py"
        resource.write_text("resource")
        mtime = output.stat().st_mtime_ns
        self.assertEqual(builder.build(self.src, self.out), [])
        self.assertEqual(output.stat().st_mtime_ns, mtime)
        self.assertEqual(resource.read_text(), "resource")

    def test_skills_without_sources_are_untouched(self):
        self.source("old", "OLD")
        builder.build(self.src, self.out)
        (self.src / "old.md").unlink()
        self.source("new", "NEW")
        builder.build(self.src, self.out)
        self.assertIn("OLD", (self.out / "old/SKILL.md").read_text())

    def test_cli_check_exit_codes_from_other_directory(self):
        self.source("example", "Body")
        command = [sys.executable, str(builder.ROOT / "build.py"), "--source-dir", str(self.src), "--output-dir", str(self.out)]
        stale = subprocess.run([*command, "--check"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(stale.returncode, 1)
        self.assertFalse(self.out.exists())
        self.assertEqual(subprocess.run(command, cwd=self.root, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([*command, "--check"], cwd=self.root, capture_output=True).returncode, 0)

    def test_repository_merge_workflow_is_self_contained(self):
        result = builder.compile_skills(builder.ROOT / "src")["merge-steward-pr"]
        for instruction in ("Get Merge Ready", "Commits", "--force-with-lease", "30 minutes", "Merge after stewardship", "current head SHA"):
            self.assertIn(instruction, result)
        self.assertNotIn("<!-- include:", result)
        self.assertNotIn("Apply `get-merge-ready`", result)
        self.assertNotIn("Follow `commits`", result)


if __name__ == "__main__":
    unittest.main()
