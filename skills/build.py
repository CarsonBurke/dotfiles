#!/usr/bin/env python3
"""Compile personal Markdown skills, expanding explicit body includes."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
INCLUDE = re.compile(r"<!-- include: ([a-z0-9/-]+) -->")


class BuildError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    frontmatter: str
    body: str


def read_source(path: Path, *, is_part: bool = False) -> Source:
    content = path.read_text(encoding="utf-8")
    if is_part:
        if content.startswith("---\n"):
            raise BuildError(f"{path}: parts must not have frontmatter")
        return Source("", content)
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", content, re.DOTALL)
    if not match:
        raise BuildError(f"{path}: expected YAML frontmatter")
    try:
        metadata = yaml.safe_load(match[1])
    except yaml.YAMLError as error:
        raise BuildError(f"{path}: invalid YAML: {error}") from error
    if not isinstance(metadata, dict) or metadata.get("name") != path.stem:
        raise BuildError(f"{path}: frontmatter name must match filename")
    if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        raise BuildError(f"{path}: description must be a nonempty string")
    return Source(match[0].rstrip() + "\n", content[match.end():])


def load_sources(source_dir: Path) -> dict[str, Source]:
    paths = sorted(source_dir.glob("*.md")) + sorted((source_dir / "parts").glob("*.md"))
    if not paths:
        raise BuildError(f"{source_dir}: no Markdown sources found")
    sources = {}
    for path in paths:
        if not NAME.fullmatch(path.stem):
            raise BuildError(f"{path}: expected a lowercase kebab-case filename")
        is_part = path.parent == source_dir / "parts"
        key = f"parts/{path.stem}" if is_part else path.stem
        sources[key] = read_source(path, is_part=is_part)
    return sources


def expand(key: str, sources: dict[str, Source], stack: tuple[str, ...] = ()) -> str:
    if key in stack:
        raise BuildError("Include cycle: " + " -> ".join((*stack, key)))
    if key not in sources:
        raise BuildError("Missing include: " + " -> ".join((*stack, key)))
    lines = []
    fence = None
    for line in sources[key].body.splitlines(keepends=True):
        # Examples in fenced code blocks are literal, not build directives.
        fence_match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence_match:
            marker, suffix = fence_match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not suffix.strip():
                fence = None
            lines.append(line)
            continue
        match = INCLUDE.fullmatch(line.strip()) if fence is None else None
        if match:
            lines.append(expand(match[1], sources, (*stack, key)).strip() + "\n")
        elif fence is None and "<!-- include:" in line:
            raise BuildError(f"{key}: include must occupy its own line: {line.strip()}")
        else:
            lines.append(line)
    return "".join(lines)


def compile_skills(source_dir: Path) -> dict[str, str]:
    sources = load_sources(source_dir)
    # Validate even unused parts before writing any output.
    bodies = {key: expand(key, sources) for key in sources}
    return {
        key: source.frontmatter + "\n" + bodies[key].strip() + "\n"
        for key, source in sources.items() if not key.startswith("parts/")
    }


def build(source_dir: Path, output_dir: Path, *, check: bool = False) -> list[Path]:
    outputs = compile_skills(source_dir)
    changed = []
    for name, content in outputs.items():
        path = output_dir / name / "SKILL.md"
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        changed.append(path)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    stream.write(content)
                    stream.flush()
                    temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report stale or missing outputs without writing")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "src")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        changed = build(args.source_dir, args.output_dir, check=args.check)
    except (BuildError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for path in changed:
        print(f"{'stale' if args.check else 'built'}: {path}")
    if not changed:
        print("Skills are up to date.")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    sys.exit(main())
