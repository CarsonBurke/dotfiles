#!/usr/bin/env python3
"""Render a self-contained PR evidence report from a validated JSON specification."""

from __future__ import annotations

import argparse
from datetime import datetime
import html
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
from urllib.parse import urlsplit

from embed_local_images import embed_local_images


TEXT_TOKEN_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")
STRUCTURAL_MARKER_PATTERN = re.compile(r"<!-- [A-Z0-9_]+ -->")


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")
    return value


def require_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value


def optional_text(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return require_text(value, path)


def escaped(value: Any, path: str) -> str:
    return html.escape(require_text(value, path), quote=True)


def safe_link(label: str, url: str, path: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{path} must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{path} must not contain URL credentials")
    return f'<a href="{html.escape(url, quote=True)}" rel="noreferrer">{html.escape(label)}</a>'


def render_linked_label(value: Any, path: str) -> str:
    if isinstance(value, str):
        return html.escape(require_text(value, path))
    item = require_object(value, path)
    return safe_link(
        require_text(item.get("label"), f"{path}.label"),
        require_text(item.get("url"), f"{path}.url"),
        f"{path}.url",
    )


def replace_once(document: str, placeholder: str, replacement: str) -> str:
    count = document.count(placeholder)
    if count != 1:
        raise ValueError(f"Expected exactly one {placeholder!r} placeholder, found {count}")
    return document.replace(placeholder, replacement)


def render_coverage(items: list[Any]) -> str:
    if not items:
        raise ValueError("coverage must contain at least one item")
    rows: list[str] = []
    for index, raw_item in enumerate(items):
        path = f"coverage[{index}]"
        item = require_object(raw_item, path)
        status = require_text(item.get("status"), f"{path}.status").lower()
        if status not in {"covered", "gap"}:
            raise ValueError(f"{path}.status must be 'covered' or 'gap'")
        css_class = "covered" if status == "covered" else "coverage-gap"
        rows.append(
            "<tr>"
            f"<td>{escaped(item.get('claim'), f'{path}.claim')}</td>"
            f"<td>{escaped(item.get('evidence'), f'{path}.evidence')}</td>"
            f'<td><span class="status {css_class}">{html.escape(status.title())}</span></td>'
            "</tr>"
        )
    return "\n              ".join(rows)


def render_evidence_header(item: dict[str, Any], path: str, kind: str) -> str:
    return (
        '<header class="evidence-header"><div>'
        f'<p class="eyebrow">{escaped(item.get("area"), f"{path}.area")}</p>'
        f'<h2>{escaped(item.get("title"), f"{path}.title")}</h2>'
        f'<p>{escaped(item.get("summary"), f"{path}.summary")}</p>'
        f'</div><span class="kind">{html.escape(kind)}</span></header>'
    )


def render_screenshot_panel(raw_panel: Any, path: str, side: str) -> str:
    panel = require_object(raw_panel, path)
    image_path = require_text(panel.get("image"), f"{path}.image")
    parsed = urlsplit(image_path)
    if parsed.scheme or parsed.netloc or Path(parsed.path).is_absolute():
        raise ValueError(f"{path}.image must be a relative local path")
    label = side.title()
    return (
        '<figure class="panel">'
        f'<figcaption class="panel-label"><span>{escaped(panel.get("caption"), f"{path}.caption")}</span>'
        f'<span class="tag {side}">{label}</span></figcaption>'
        f'<img src="{html.escape(image_path, quote=True)}" alt="{escaped(panel.get("alt"), f"{path}.alt")}">'
        "</figure>"
    )


def render_code_panel(raw_panel: Any, path: str, side: str) -> str:
    panel = require_object(raw_panel, path)
    label = side.title()
    return (
        f'<section class="panel" aria-label="{label} code">'
        f'<div class="panel-label"><span>{escaped(panel.get("caption"), f"{path}.caption")}</span>'
        f'<span class="tag {side}">{label}</span></div>'
        f'<div class="code-meta">{escaped(panel.get("path_ref"), f"{path}.path_ref")}</div>'
        f'<pre><code>{escaped(panel.get("code"), f"{path}.code")}</code></pre>'
        "</section>"
    )


def render_before_after_panels(
    item: dict[str, Any],
    path: str,
    renderer: Any,
) -> str:
    panels: list[str] = []
    for side in ("before", "after"):
        raw_panel = item.get(side)
        if raw_panel is not None:
            panels.append(renderer(raw_panel, f"{path}.{side}", side))
    if not panels:
        raise ValueError(f"{path} must define before and/or after evidence")
    pair_class = "pair single" if len(panels) == 1 else "pair"
    return f'<div class="{pair_class}">' + "".join(panels) + "</div>"


def render_table_evidence(item: dict[str, Any], path: str) -> str:
    columns = require_list(item.get("columns"), f"{path}.columns")
    if not columns:
        raise ValueError(f"{path}.columns must not be empty")
    column_labels = [require_text(column, f"{path}.columns[{index}]") for index, column in enumerate(columns)]
    rows = require_list(item.get("rows"), f"{path}.rows")
    rendered_rows: list[str] = []
    for row_index, raw_row in enumerate(rows):
        row = require_list(raw_row, f"{path}.rows[{row_index}]")
        if len(row) != len(column_labels):
            raise ValueError(f"{path}.rows[{row_index}] must have {len(column_labels)} cells")
        rendered_rows.append(
            "<tr>"
            + "".join(
                f"<td>{escaped(cell, f'{path}.rows[{row_index}][{cell_index}]')}</td>"
                for cell_index, cell in enumerate(row)
            )
            + "</tr>"
        )
    headings = "".join(f"<th>{html.escape(column)}</th>" for column in column_labels)
    return (
        '<div class="table-wrap evidence-table"><table>'
        f"<thead><tr>{headings}</tr></thead>"
        f"<tbody>{''.join(rendered_rows)}</tbody>"
        "</table></div>"
    )


def render_evidence(items: list[Any]) -> str:
    if not items:
        raise ValueError("evidence must contain at least one item")
    blocks: list[str] = []
    for index, raw_item in enumerate(items):
        path = f"evidence[{index}]"
        item = require_object(raw_item, path)
        evidence_type = require_text(item.get("type"), f"{path}.type").lower()
        if evidence_type == "screenshot":
            body = render_before_after_panels(item, path, render_screenshot_panel)
            kind = "Screenshot"
        elif evidence_type == "code":
            body = render_before_after_panels(item, path, render_code_panel)
            kind = "Code"
        elif evidence_type == "table":
            body = render_table_evidence(item, path)
            kind = "Table"
        else:
            raise ValueError(f"{path}.type must be screenshot, code, or table")

        note = optional_text(item.get("note"), f"{path}.note")
        rendered_note = f'<p class="evidence-note">{html.escape(note)}</p>' if note else ""
        blocks.append(
            '<article class="evidence">'
            + render_evidence_header(item, path, kind)
            + body
            + rendered_note
            + "</article>"
        )
    return "\n          ".join(blocks)


def render_validation(items: list[Any]) -> str:
    if not items:
        raise ValueError("validation must contain at least one item")
    cards: list[str] = []
    for index, raw_item in enumerate(items):
        path = f"validation[{index}]"
        item = require_object(raw_item, path)
        status = require_text(item.get("status"), f"{path}.status").lower()
        if status not in {"pass", "warn", "gap", "fail"}:
            raise ValueError(f"{path}.status must be pass, warn, gap, or fail")
        css_class = {
            "pass": "pass",
            "warn": "warn",
            "gap": "validation-gap",
            "fail": "fail",
        }[status]
        cards.append(
            '<article class="card">'
            f'<span class="status {css_class}">{html.escape(status.title())}</span>'
            f'<h3>{escaped(item.get("name"), f"{path}.name")}</h3>'
            f'<p>{escaped(item.get("evidence"), f"{path}.evidence")}</p>'
            "</article>"
        )
    return "\n          ".join(cards)


def render_risks(items: list[Any]) -> str:
    if not items:
        raise ValueError("risks must contain at least one item, even if it records an evidence limitation")
    rendered: list[str] = []
    for index, raw_item in enumerate(items):
        path = f"risks[{index}]"
        item = require_object(raw_item, path)
        rendered.append(
            f'<p><strong>{escaped(item.get("title"), f"{path}.title")}</strong> '
            f'{escaped(item.get("detail"), f"{path}.detail")}</p>'
        )
    return "".join(rendered)


def render_provenance(value: Any) -> str:
    provenance = require_object(value, "provenance")
    parts = [html.escape(require_text(provenance.get("text"), "provenance.text"))]
    for index, raw_link in enumerate(require_list(provenance.get("links", []), "provenance.links")):
        path = f"provenance.links[{index}]"
        link = require_object(raw_link, path)
        parts.append(
            safe_link(
                require_text(link.get("label"), f"{path}.label"),
                require_text(link.get("url"), f"{path}.url"),
                f"{path}.url",
            )
        )
    return "<p>" + " · ".join(parts) + "</p>"


def render_report(specification: dict[str, Any], template: str) -> str:
    generated = specification.get("generated")
    if generated is None:
        now = datetime.now().astimezone()
        generated_iso = now.isoformat(timespec="seconds")
        generated_display = now.strftime("%B %d, %Y · %H:%M %Z").replace(" 0", " ")
    else:
        generated_object = require_object(generated, "generated")
        generated_iso = require_text(generated_object.get("iso"), "generated.iso")
        generated_display = require_text(generated_object.get("display"), "generated.display")

    outcome = require_object(specification.get("outcome"), "outcome")
    important_note = require_object(specification.get("important_note"), "important_note")
    replacements = {
        "REPORT_TITLE": escaped(specification.get("title"), "title"),
        "EXECUTIVE_SUMMARY": escaped(specification.get("executive_summary"), "executive_summary"),
        "REPOSITORY": render_linked_label(specification.get("repository"), "repository"),
        "PR_LINK_OR_SCOPE": render_linked_label(specification.get("scope"), "scope"),
        "BASE_SHA": escaped(specification.get("base_sha"), "base_sha"),
        "HEAD_SHA": escaped(specification.get("head_sha"), "head_sha"),
        "WORKTREE_STATE": escaped(specification.get("worktree_state"), "worktree_state"),
        "GENERATED_ISO": html.escape(generated_iso, quote=True),
        "GENERATED_DISPLAY": html.escape(generated_display),
        "OUTCOME_TITLE": escaped(outcome.get("title"), "outcome.title"),
        "OUTCOME_SUMMARY": escaped(outcome.get("summary"), "outcome.summary"),
        "IMPORTANT_NOTE_TITLE": escaped(important_note.get("title"), "important_note.title"),
        "IMPORTANT_NOTE": escaped(important_note.get("text"), "important_note.text"),
        "RISK_SUMMARY": escaped(specification.get("risk_summary"), "risk_summary"),
    }

    expected_tokens = {f"{{{{{token}}}}}" for token in replacements}
    template_tokens = set(TEXT_TOKEN_PATTERN.findall(template))
    missing_tokens = expected_tokens - template_tokens
    unknown_tokens = template_tokens - expected_tokens
    if missing_tokens:
        raise ValueError(f"Missing required template tokens: {sorted(missing_tokens)}")
    if unknown_tokens:
        raise ValueError(f"Unknown template tokens: {sorted(unknown_tokens)}")

    document = TEXT_TOKEN_PATTERN.sub(
        lambda match: replacements[match.group(0)[2:-2]],
        template,
    )

    document = replace_once(
        document,
        "<!-- COVERAGE_ROWS -->",
        render_coverage(require_list(specification.get("coverage"), "coverage")),
    )
    document = replace_once(
        document,
        "<!-- EVIDENCE_BLOCKS -->",
        render_evidence(require_list(specification.get("evidence"), "evidence")),
    )
    document = replace_once(
        document,
        "<!-- VALIDATION_CARDS -->",
        render_validation(require_list(specification.get("validation"), "validation")),
    )
    document = replace_once(
        document,
        "<!-- RISK_ITEMS -->",
        render_risks(require_list(specification.get("risks"), "risks")),
    )
    document = replace_once(document, "<!-- PROVENANCE -->", render_provenance(specification.get("provenance")))

    unresolved_markers = STRUCTURAL_MARKER_PATTERN.findall(document)
    if unresolved_markers:
        raise ValueError(f"Unresolved structural markers: {sorted(set(unresolved_markers))}")
    return document


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as temporary_file:
            temporary_file.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def parse_arguments() -> argparse.Namespace:
    script_directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specification", type=Path, help="validated JSON report specification")
    parser.add_argument("output", type=Path, help="destination HTML report")
    parser.add_argument(
        "--template",
        type=Path,
        default=script_directory.parent / "assets" / "report-template.html",
        help="HTML template path",
    )
    parser.add_argument(
        "--asset-root",
        type=Path,
        help="root for screenshot paths (defaults to the specification directory)",
    )
    parser.add_argument(
        "--no-embed-images",
        action="store_true",
        help="leave relative screenshot paths instead of embedding them",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    specification_path = arguments.specification.resolve(strict=True)
    template_path = arguments.template.resolve(strict=True)
    output_path = arguments.output.resolve()
    if output_path == template_path:
        raise ValueError("Output must not overwrite the skill template")
    if output_path == specification_path:
        raise ValueError("Output must not overwrite the report specification")
    if output_path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("Output must use an .html or .htm extension")

    specification = require_object(json.loads(specification_path.read_text(encoding="utf-8")), "root")
    template = template_path.read_text(encoding="utf-8")
    rendered_report = render_report(specification, template)

    embedded_count = 0
    if arguments.no_embed_images:
        write_atomic(output_path, rendered_report)
    else:
        asset_root = (arguments.asset_root or specification_path.parent).resolve(strict=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
        ) as temporary_directory:
            intermediate_path = Path(temporary_directory) / "report.html"
            intermediate_path.write_text(rendered_report, encoding="utf-8")
            embedded_count = embed_local_images(intermediate_path, output_path, asset_root)
    print(f"Rendered {output_path} ({embedded_count} embedded image(s))")


if __name__ == "__main__":
    main()
