#!/usr/bin/env python3
"""Embed relative local <img src> assets into a standalone HTML report."""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit


IMAGE_SOURCE_PATTERN = re.compile(
    r"(?P<prefix><img\b[^>]*?\bsrc\s*=\s*)(?P<quote>['\"])(?P<src>[^'\"]+)(?P=quote)",
    re.IGNORECASE,
)


def embed_local_images(source: Path, output: Path, asset_root: Path) -> int:
    source = source.resolve(strict=True)
    asset_root = asset_root.resolve(strict=True)
    document = source.read_text(encoding="utf-8")
    embedded_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal embedded_count

        raw_source = html.unescape(match.group("src"))
        parsed = urlsplit(raw_source)
        if parsed.scheme or parsed.netloc or raw_source.startswith(("#", "//")):
            return match.group(0)
        if parsed.query or parsed.fragment:
            raise ValueError(f"Local image URLs may not contain a query or fragment: {raw_source}")

        relative_path = Path(unquote(parsed.path))
        if relative_path.is_absolute():
            raise ValueError(f"Local image paths must be relative: {raw_source}")

        image_path = (asset_root / relative_path).resolve()
        if not image_path.is_relative_to(asset_root):
            raise ValueError(f"Image escapes the asset root: {raw_source}")
        if not image_path.is_file():
            raise ValueError(f"Local image does not exist or is not a file: {raw_source}")

        mime_type, _ = mimetypes.guess_type(image_path.name)
        if mime_type is None or not mime_type.startswith("image/"):
            raise ValueError(f"Unsupported image type: {image_path}")

        payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
        embedded_count += 1
        data_uri = f"data:{mime_type};base64,{payload}"
        return f"{match.group('prefix')}{match.group('quote')}{data_uri}{match.group('quote')}"

    standalone_document = IMAGE_SOURCE_PATTERN.sub(replace, document)
    output.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as temporary_file:
            temporary_file.write(standalone_document)
        os.replace(temporary_name, output)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise

    return embedded_count


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="HTML file containing relative local image sources")
    parser.add_argument("output", type=Path, help="destination for the standalone HTML file")
    parser.add_argument(
        "--asset-root",
        type=Path,
        help="root for local image paths (defaults to the source HTML directory)",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    asset_root = arguments.asset_root or arguments.source.parent
    count = embed_local_images(arguments.source, arguments.output, asset_root)
    print(f"Embedded {count} image(s) into {arguments.output}")


if __name__ == "__main__":
    main()
