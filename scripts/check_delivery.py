#!/usr/bin/env python3
"""Fail-closed release check for huatu render bundles.

This script does not judge aesthetics. It verifies that a claimed release has
fresh rendered artifacts, structurally valid QA, structurally complete PNGs,
and a human-authored visual review marked PASS with no blocking findings.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SLIDE_PATTERN = re.compile(r"^slide-(\d{2})\.png$")
SECTION_PATTERN = re.compile(r"(?m)^([A-Z][A-Z_ ]+):\s*(.*)$")
PNG_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
PNG_ALLOWED_BIT_DEPTHS = {
    0: {1, 2, 4, 8, 16},
    2: {8, 16},
    3: {1, 2, 4, 8},
    4: {8, 16},
    6: {8, 16},
}
ADAM7_PASSES = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(f"Missing {label}: {path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        errors.append(f"Could not read {label}: {path.name}")
        return None
    except UnicodeDecodeError:
        errors.append(f"{label} is not valid UTF-8: {path.name}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid {label} JSON at {path.name}: line {exc.lineno}, column {exc.colno}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object: {path.name}")
        return None
    return value


def safe_source_name(path: Path, spec_path: Path) -> str:
    """Describe checked sources without exposing the caller's absolute path."""
    try:
        return path.relative_to(spec_path.parent).as_posix()
    except ValueError:
        return path.name


def safe_artifact_name(path: Path, output_dir: Path) -> str:
    """Describe release artifacts relative to the output directory."""
    try:
        return f"output/{path.relative_to(output_dir).as_posix()}"
    except ValueError:
        return path.name


def _pass_extent(size: int, start: int, step: int) -> int:
    if size <= start:
        return 0
    return (size - start + step - 1) // step


def _expected_png_scanline_bytes(
    width: int,
    height: int,
    bit_depth: int,
    color_type: int,
    interlace: int,
) -> int:
    channels = PNG_CHANNELS.get(color_type)
    if channels is None or bit_depth not in PNG_ALLOWED_BIT_DEPTHS[color_type]:
        raise ValueError(f"unsupported PNG color type/bit depth: {color_type}/{bit_depth}")
    bits_per_pixel = channels * bit_depth

    def pass_bytes(pass_width: int, pass_height: int) -> int:
        if pass_width == 0 or pass_height == 0:
            return 0
        row_bytes = (pass_width * bits_per_pixel + 7) // 8
        return pass_height * (row_bytes + 1)  # one filter byte per scanline

    if interlace == 0:
        return pass_bytes(width, height)
    return sum(
        pass_bytes(
            _pass_extent(width, x_start, x_step),
            _pass_extent(height, y_start, y_step),
        )
        for x_start, y_start, x_step, y_step in ADAM7_PASSES
    )


def _feed_png_data(
    decoder: zlib.Decompress,
    data: bytes,
    decompressed: int,
    expected: int,
) -> int:
    pending = data
    while pending:
        limit = max(1, expected - decompressed + 1)
        try:
            output = decoder.decompress(pending, limit)
        except zlib.error as exc:
            raise ValueError(f"invalid IDAT zlib stream: {exc}") from exc
        decompressed += len(output)
        if decompressed > expected:
            raise ValueError("IDAT expands beyond the dimensions declared by IHDR")
        next_pending = decoder.unconsumed_tail
        if next_pending == pending:
            raise ValueError("IDAT decompressor made no progress")
        pending = next_pending
    return decompressed


def png_dimensions(path: Path) -> tuple[int, int]:
    """Validate a complete PNG stream and return its declared dimensions."""
    with path.open("rb") as handle:
        if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            raise ValueError("invalid PNG signature")

        width = height = expected_scanline_bytes = None
        decoder: zlib.Decompress | None = None
        decompressed = 0
        seen_ihdr = False
        seen_idat = False
        seen_iend = False
        idat_finished = False

        while not seen_iend:
            length_bytes = handle.read(4)
            if len(length_bytes) != 4:
                raise ValueError("truncated PNG before IEND")
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = handle.read(4)
            if len(chunk_type) != 4:
                raise ValueError("truncated PNG chunk type")
            data = handle.read(length)
            crc_bytes = handle.read(4)
            if len(data) != length or len(crc_bytes) != 4:
                raise ValueError(f"truncated {chunk_type.decode('ascii', 'replace')} chunk")

            actual_crc = struct.unpack(">I", crc_bytes)[0]
            expected_crc = zlib.crc32(chunk_type)
            expected_crc = zlib.crc32(data, expected_crc) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                raise ValueError(f"CRC mismatch in {chunk_type.decode('ascii', 'replace')} chunk")

            if not seen_ihdr and chunk_type != b"IHDR":
                raise ValueError("IHDR must be the first PNG chunk")

            if chunk_type == b"IHDR":
                if seen_ihdr or length != 13:
                    raise ValueError("PNG must contain exactly one 13-byte IHDR chunk")
                (
                    width,
                    height,
                    bit_depth,
                    color_type,
                    compression_method,
                    filter_method,
                    interlace,
                ) = struct.unpack(">IIBBBBB", data)
                if width == 0 or height == 0:
                    raise ValueError("IHDR width and height must be positive")
                if compression_method != 0 or filter_method != 0 or interlace not in {0, 1}:
                    raise ValueError("unsupported PNG compression, filter, or interlace method")
                expected_scanline_bytes = _expected_png_scanline_bytes(
                    width,
                    height,
                    bit_depth,
                    color_type,
                    interlace,
                )
                seen_ihdr = True
                continue

            if chunk_type == b"IDAT":
                if idat_finished:
                    raise ValueError("IDAT chunks must be consecutive")
                if decoder is None:
                    decoder = zlib.decompressobj()
                seen_idat = True
                assert expected_scanline_bytes is not None
                decompressed = _feed_png_data(
                    decoder,
                    data,
                    decompressed,
                    expected_scanline_bytes,
                )
                continue

            if seen_idat:
                idat_finished = True

            if chunk_type == b"IEND":
                if length != 0:
                    raise ValueError("IEND must be empty")
                if not seen_idat or decoder is None or expected_scanline_bytes is None:
                    raise ValueError("PNG has no IDAT image data")
                try:
                    decompressed += len(decoder.flush())
                except zlib.error as exc:
                    raise ValueError(f"invalid IDAT zlib stream: {exc}") from exc
                if decompressed > expected_scanline_bytes:
                    raise ValueError("IDAT expands beyond the dimensions declared by IHDR")
                if not decoder.eof:
                    raise ValueError("truncated IDAT zlib stream")
                if decoder.unused_data:
                    raise ValueError("IDAT contains trailing compressed data")
                if decompressed != expected_scanline_bytes:
                    raise ValueError(
                        "IDAT scanline byte count does not match the dimensions declared by IHDR"
                    )
                seen_iend = True
                if handle.read(1):
                    raise ValueError("unexpected data after IEND")
                continue

            # Unknown critical chunks are not valid in a baseline PNG stream.
            if chunk_type[0] & 0x20 == 0 and chunk_type not in {b"PLTE"}:
                raise ValueError(f"unknown critical PNG chunk: {chunk_type.decode('ascii', 'replace')}")

    assert width is not None and height is not None
    return width, height


def canvas_dimensions(spec: dict[str, Any]) -> tuple[int, int]:
    canvas = spec.get("canvas")
    if isinstance(canvas, dict):
        width = canvas.get("width")
        height = canvas.get("height")
        if isinstance(width, int) and height is not None and isinstance(height, int):
            return width, height
    return 1080, 1350


def source_paths(spec: dict[str, Any], spec_path: Path, errors: list[str]) -> list[Path]:
    sources = [spec_path]
    slides = spec.get("slides")
    if not isinstance(slides, list):
        return sources
    for slide_index, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        blocks = slide.get("blocks", [])
        if not isinstance(blocks, list):
            continue
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            src = block.get("src")
            location = f"slides[{slide_index}].blocks[{block_index}].src"
            if not isinstance(src, str) or not src.strip():
                errors.append(f"Missing local source asset path at {location}")
                continue
            if "://" in src:
                errors.append(f"Remote source asset is not allowed at {location}")
                continue
            candidate = Path(src).expanduser()
            if not candidate.is_absolute():
                candidate = spec_path.parent / candidate
            candidate = candidate.resolve()
            if not candidate.is_file():
                errors.append(f"Missing local source asset: {safe_source_name(candidate, spec_path)}")
                continue
            if candidate not in sources:
                sources.append(candidate)
    return sources


def section_value(text: str, name: str) -> str | None:
    matches = list(SECTION_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1).strip() != name:
            continue
        inline = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        return "\n".join(part for part in (inline, body) if part).strip()
    return None


def blocking_is_none(value: str | None) -> bool:
    if value is None:
        return False
    normalized = re.sub(r"(?m)^\s*[-*]\s*", "", value).strip().lower()
    return normalized in {"none", "无", "没有"}


def check_delivery(spec_path: Path, output_dir: Path, qa_summary_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, Any] = {}

    spec = load_json(spec_path, "carousel spec", errors)
    qa = load_json(output_dir / "qa.json", "render QA", errors)
    if spec is None:
        return {"release_ready": False, "errors": errors, "warnings": warnings, "evidence": evidence}

    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("carousel spec must contain a non-empty slides array")
        slide_count = 0
    else:
        slide_count = len(slides)
    width, height = canvas_dimensions(spec)
    evidence.update({"slideCount": slide_count, "canvas": {"width": width, "height": height}})

    required = [output_dir / "carousel.html", output_dir / "qa.json"]
    if spec.get("referenceDriven") is True:
        required.append(output_dir / "design-manifest.json")
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty release artifact: {path.name}")

    expected_slides = [output_dir / f"slide-{index:02d}.png" for index in range(1, slide_count + 1)]
    actual_slides = sorted(
        path for path in output_dir.glob("slide-*.png") if SLIDE_PATTERN.fullmatch(path.name)
    )
    expected_names = {path.name for path in expected_slides}
    actual_names = {path.name for path in actual_slides}
    for name in sorted(expected_names - actual_names):
        errors.append(f"Missing rendered slide: {name}")
    for name in sorted(actual_names - expected_names):
        errors.append(f"Unexpected rendered slide: {name}")

    for path in actual_slides:
        try:
            actual_width, actual_height = png_dimensions(path)
        except OSError:
            errors.append(f"Could not read rendered PNG: {path.name}")
            continue
        except ValueError as exc:
            errors.append(f"Invalid rendered PNG {path.name}: {exc}")
            continue
        if (actual_width, actual_height) != (width, height):
            errors.append(
                f"Rendered PNG {path.name} is {actual_width}x{actual_height}; expected {width}x{height}"
            )

    if qa is not None:
        if qa.get("valid") is not True or qa.get("structurally_valid") is not True:
            errors.append("qa.json must report valid=true and structurally_valid=true")
        qa_errors = qa.get("errors")
        if not isinstance(qa_errors, list) or qa_errors:
            errors.append("qa.json errors must be an empty list")
        if qa.get("slideCount") != slide_count:
            errors.append(f"qa.json slideCount does not match the spec ({qa.get('slideCount')} != {slide_count})")
        qa_canvas = qa.get("canvas")
        if qa_canvas != {"width": width, "height": height}:
            errors.append("qa.json canvas does not match the spec canvas")

    if not qa_summary_path.is_file():
        errors.append(f"Missing human visual QA summary: {qa_summary_path.name}")
    else:
        try:
            review_text = qa_summary_path.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"Could not read human visual QA summary: {qa_summary_path.name}")
        except UnicodeDecodeError:
            errors.append(f"Human visual QA summary is not valid UTF-8: {qa_summary_path.name}")
        else:
            verdict = section_value(review_text, "VERDICT")
            blocking = section_value(review_text, "BLOCKING")
            if verdict is None or verdict.splitlines()[0].strip().upper() != "PASS":
                errors.append("Human visual QA must contain `VERDICT: PASS`")
            if not blocking_is_none(blocking):
                errors.append("Human visual QA must contain `BLOCKING: none` (or a section whose only item is none)")

    sources = source_paths(spec, spec_path, errors)
    newest_source = max((path.stat().st_mtime for path in sources), default=0)
    render_artifacts = [path for path in required + expected_slides if path.is_file()]
    stale_artifacts = [path.name for path in render_artifacts if path.stat().st_mtime + 1e-6 < newest_source]
    if stale_artifacts:
        errors.append("Rendered release is stale relative to its spec/assets: " + ", ".join(sorted(stale_artifacts)))

    if qa_summary_path.is_file() and render_artifacts:
        newest_render = max(path.stat().st_mtime for path in render_artifacts)
        if qa_summary_path.stat().st_mtime + 1e-6 < newest_render:
            errors.append("Human visual QA is stale; inspect the latest render and rewrite qa-summary.md")

    evidence["sourcesChecked"] = [safe_source_name(path, spec_path) for path in sources]
    evidence["artifactsChecked"] = [safe_artifact_name(path, output_dir) for path in render_artifacts]
    evidence["qaSummary"] = qa_summary_path.name
    return {
        "release_ready": not errors,
        "errors": errors,
        "warnings": warnings,
        "evidence": evidence,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail-closed release check for a rendered huatu carousel")
    parser.add_argument("spec", help="Path to carousel.json")
    parser.add_argument("--output-dir", required=True, help="Directory containing carousel.html, qa.json and PNGs")
    parser.add_argument(
        "--qa-summary",
        help="Human visual QA Markdown; defaults to qa-summary.md beside the spec",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec_path = Path(args.spec).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    qa_summary = (
        Path(args.qa_summary).expanduser().resolve()
        if args.qa_summary
        else spec_path.parent / "qa-summary.md"
    )
    report = check_delivery(spec_path, output_dir, qa_summary)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["release_ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
