#!/usr/bin/env python3
"""Validate and render a Xiaohongshu carousel JSON spec to PNGs.

The default canvas is the classic 1080x1350 (4:5) poster. A spec may request a
different size with an optional top-level ``canvas`` field, e.g.
``{"width": 1080, "height": 1440}`` for a 3:4 cover.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


WIDTH = 1080
HEIGHT = 1350
MIN_CANVAS = 720
MAX_CANVAS = 2160
ALLOWED_BLOCKS = {
    "heading",
    "paragraph",
    "metrics",
    "bullets",
    "quote",
    "compare",
    "table",
    "steps",
    "callout",
    "chips",
    "image",
}
ALLOWED_DENSITIES = {"airy", "normal", "compact"}
ALLOWED_ARCHETYPES = {"editorial", "poster", "split", "diagram", "timeline", "custom"}
ALLOWED_PRIMITIVES = {
    "scale-contrast",
    "framing",
    "alignment-break",
    "annotation",
    "flow",
    "whitespace",
    "repetition",
}
ALLOWED_QUOTE_VARIANTS = {"light", "dark"}
ALLOWED_CALLOUT_VARIANTS = {"plain", "warn", "accent", "dark"}
ALLOWED_IMAGE_FITS = {"cover", "contain"}
ALLOWED_IMAGE_POSITIONS = {"center", "top", "bottom", "left", "right"}
ALLOWED_IMAGE_TREATMENTS = {"plain", "paper", "bleed", "cutout", "monochrome"}
ALLOWED_IMAGE_ROLES = {"hero", "evidence", "atmosphere", "texture", "motif", "transition"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
ALLOWED_VISUAL_MODES = {"editorial", "mixed", "image-led", "photo-diary", "object-study", "poetic-poster"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_THEME = {
    # Kami 默认主题（v2.0）：暖纸 + 墨蓝 + 暖灰 + 象牙卡，替换旧「纸红/黄荧光」默认
    "background": "#F5F4ED",  # --parchment 暖纸画布
    "ink": "#141413",         # --near-black 近黑正文（暖橄榄 undertone）
    "muted": "#6B6A64",       # --stone 三级文字 / metadata
    "accent": "#1B365D",      # --brand 墨蓝（唯一强调色，≤5% 版面）
    "highlight": "#EEF2F7",   # --brand-tint 墨蓝×暖纸固色 tint（文字标记）
    "card": "#FAF9F5",        # --ivory 抬升容器
}


def canvas_dimensions(spec: dict[str, Any]) -> tuple[int, int]:
    """Resolve the output canvas from an optional top-level ``canvas`` field."""
    canvas = spec.get("canvas")
    if isinstance(canvas, dict):
        width = canvas.get("width")
        height = canvas.get("height")
        if isinstance(width, int) and not isinstance(width, bool) and isinstance(height, int) and not isinstance(height, bool):
            return width, height
    return WIDTH, HEIGHT
MANIFEST_TEXT_FIELDS = (
    "candidateDirection",
    "visualThesis",
    "readerEmotion",
    "semanticMetaphor",
    "rhythmPlan",
    "contrastPlan",
    "typeStrategy",
    "whyThisVisual",
)

# 理解证据探针：reference-driven 的 manifest 出现占位/空壳文字 = 「没理解就填表」，直接报 spec 错误。
PLACEHOLDER_PATTERN = re.compile(
    r"(?i)\b(t\.?b\.?d\.?|todo|placeholder|lorem ipsum|to be (?:determined|filled)|fill (?:me )?in)\b|"
    r"(待定|占位|待补充|待补写|待完善)"
)
DEGENERATE_TEXT_PATTERN = re.compile(r"^[\s.\-_…]{1,8}$|^x{2,}$", re.IGNORECASE)


def is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def expect_text(errors: list[str], value: Any, path: str) -> None:
    if not is_text(value):
        errors.append(f"{path} must be a non-empty string")


def has_placeholder_text(value: Any) -> bool:
    """True when the field is empty, a placeholder token, or a degenerate filler."""
    if not is_text(value):
        return True
    return bool(PLACEHOLDER_PATTERN.search(value) or DEGENERATE_TEXT_PATTERN.match(value))


def expect_text_list(errors: list[str], value: Any, path: str, minimum: int = 1) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        errors.append(f"{path} must be a list with at least {minimum} item(s)")
        return
    for index, item in enumerate(value):
        expect_text(errors, item, f"{path}[{index}]")


def validate_rich_text(errors: list[str], block: dict[str, Any], path: str) -> None:
    text = block.get("text")
    expect_text(errors, text, f"{path}.text")
    emphasis = block.get("emphasis", [])
    if not isinstance(emphasis, list) or any(not is_text(value) for value in emphasis):
        errors.append(f"{path}.emphasis must be a list of non-empty strings")
    elif isinstance(text, str):
        for index, phrase in enumerate(emphasis):
            if phrase not in text:
                errors.append(f"{path}.emphasis[{index}] must occur literally in {path}.text")


def validate_block(errors: list[str], block: Any, path: str) -> None:
    if not isinstance(block, dict):
        errors.append(f"{path} must be an object")
        return

    block_type = block.get("type")
    if block_type not in ALLOWED_BLOCKS:
        errors.append(f"{path}.type must be one of {sorted(ALLOWED_BLOCKS)}")
        return

    if block_type == "heading":
        expect_text(errors, block.get("text"), f"{path}.text")
        return

    if block_type == "paragraph":
        validate_rich_text(errors, block, path)
        return

    if block_type == "metrics":
        items = block.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 6:
            errors.append(f"{path}.items must contain 1–6 metric objects")
        else:
            for index, item in enumerate(items):
                item_path = f"{path}.items[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_path} must be an object")
                    continue
                expect_text(errors, item.get("value"), f"{item_path}.value")
                expect_text(errors, item.get("label"), f"{item_path}.label")
                if item.get("source") is not None:
                    expect_text(errors, item.get("source"), f"{item_path}.source")
        columns = block.get("columns", min(3, len(items) if isinstance(items, list) else 1))
        if not isinstance(columns, int) or not 1 <= columns <= 4:
            errors.append(f"{path}.columns must be an integer from 1 to 4")
        return

    if block_type == "bullets":
        items = block.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 8:
            errors.append(f"{path}.items must contain 1–8 bullet items")
        else:
            for index, item in enumerate(items):
                item_path = f"{path}.items[{index}]"
                if isinstance(item, str):
                    expect_text(errors, item, item_path)
                elif isinstance(item, dict):
                    validate_rich_text(errors, item, item_path)
                else:
                    errors.append(f"{item_path} must be a string or rich-text object")
        return

    if block_type == "quote":
        validate_rich_text(errors, block, path)
        if block.get("source") is not None:
            expect_text(errors, block.get("source"), f"{path}.source")
        if block.get("variant", "light") not in ALLOWED_QUOTE_VARIANTS:
            errors.append(f"{path}.variant must be one of {sorted(ALLOWED_QUOTE_VARIANTS)}")
        return

    if block_type == "compare":
        items = block.get("items")
        if not isinstance(items, list) or not 2 <= len(items) <= 3:
            errors.append(f"{path}.items must contain 2–3 comparison objects")
        else:
            for index, item in enumerate(items):
                item_path = f"{path}.items[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_path} must be an object")
                    continue
                expect_text(errors, item.get("title"), f"{item_path}.title")
                if item.get("subtitle") is not None:
                    expect_text(errors, item.get("subtitle"), f"{item_path}.subtitle")
                expect_text_list(errors, item.get("items", []), f"{item_path}.items")
        return

    if block_type == "table":
        headers = block.get("headers")
        rows = block.get("rows")
        expect_text_list(errors, headers, f"{path}.headers", minimum=2)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{path}.rows must be a non-empty list")
        elif isinstance(headers, list):
            for index, row in enumerate(rows):
                row_path = f"{path}.rows[{index}]"
                if not isinstance(row, list) or len(row) != len(headers):
                    errors.append(f"{row_path} must contain exactly {len(headers)} cells")
                    continue
                for cell_index, cell in enumerate(row):
                    expect_text(errors, cell, f"{row_path}[{cell_index}]")
        return

    if block_type == "steps":
        items = block.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 5:
            errors.append(f"{path}.items must contain 1–5 step objects")
        else:
            for index, item in enumerate(items):
                item_path = f"{path}.items[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_path} must be an object")
                    continue
                if item.get("label") is not None:
                    expect_text(errors, item.get("label"), f"{item_path}.label")
                expect_text(errors, item.get("title"), f"{item_path}.title")
                if item.get("text") is not None:
                    expect_text(errors, item.get("text"), f"{item_path}.text")
        return

    if block_type == "callout":
        validate_rich_text(errors, block, path)
        if block.get("title") is not None:
            expect_text(errors, block.get("title"), f"{path}.title")
        if block.get("variant", "plain") not in ALLOWED_CALLOUT_VARIANTS:
            errors.append(f"{path}.variant must be one of {sorted(ALLOWED_CALLOUT_VARIANTS)}")
        return

    if block_type == "chips":
        expect_text_list(errors, block.get("items"), f"{path}.items")
        return

    if block_type == "image":
        src = block.get("src")
        expect_text(errors, src, f"{path}.src")
        if isinstance(src, str):
            if "://" in src or src.lower().startswith(("javascript:", "data:")):
                errors.append(f"{path}.src must be a local file path, not a URL or data payload")
            elif Path(src).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                errors.append(f"{path}.src must use one of {sorted(ALLOWED_IMAGE_EXTENSIONS)}")
        expect_text(errors, block.get("alt"), f"{path}.alt")
        if block.get("caption") is not None:
            expect_text(errors, block.get("caption"), f"{path}.caption")
        if block.get("role") not in ALLOWED_IMAGE_ROLES:
            errors.append(f"{path}.role must be one of {sorted(ALLOWED_IMAGE_ROLES)}")
        if block.get("fit", "cover") not in ALLOWED_IMAGE_FITS:
            errors.append(f"{path}.fit must be one of {sorted(ALLOWED_IMAGE_FITS)}")
        if block.get("position", "center") not in ALLOWED_IMAGE_POSITIONS:
            errors.append(f"{path}.position must be one of {sorted(ALLOWED_IMAGE_POSITIONS)}")
        if block.get("treatment", "plain") not in ALLOWED_IMAGE_TREATMENTS:
            errors.append(f"{path}.treatment must be one of {sorted(ALLOWED_IMAGE_TREATMENTS)}")
        height = block.get("height", 480)
        if not isinstance(height, int) or not 240 <= height <= 700:
            errors.append(f"{path}.height must be an integer from 240 to 700")


def relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def validate_manifest(errors: list[str], manifest: Any, slide_count: int) -> None:
    if not isinstance(manifest, dict):
        errors.append("designManifest must be an object for reference-driven work")
        return
    for key in MANIFEST_TEXT_FIELDS:
        value = manifest.get(key)
        expect_text(errors, value, f"designManifest.{key}")
        if is_text(value) and has_placeholder_text(value):
            errors.append(f"designManifest.{key} is placeholder text; record the actual visual reasoning (理解证据) instead")
    motifs = manifest.get("motifs")
    if not isinstance(motifs, list) or not 1 <= len(motifs) <= 2:
        errors.append("designManifest.motifs must contain one or two meaningful motifs")
    else:
        for index, value in enumerate(motifs):
            expect_text(errors, value, f"designManifest.motifs[{index}]")
            if is_text(value) and has_placeholder_text(value):
                errors.append(f"designManifest.motifs[{index}] is placeholder text; name the actual motif")
    avoid_list = manifest.get("avoidList")
    if not isinstance(avoid_list, list) or not avoid_list:
        errors.append("designManifest.avoidList must be a list with at least 1 item(s)")
    else:
        for index, value in enumerate(avoid_list):
            expect_text(errors, value, f"designManifest.avoidList[{index}]")
            if is_text(value) and has_placeholder_text(value):
                errors.append(f"designManifest.avoidList[{index}] is placeholder text; name the actual habit to avoid")
    intents = manifest.get("compositionIntent")
    if not isinstance(intents, list) or len(intents) != slide_count:
        errors.append(f"designManifest.compositionIntent must contain exactly {slide_count} slide intents")
    else:
        for index, value in enumerate(intents):
            expect_text(errors, value, f"designManifest.compositionIntent[{index}]")
            if is_text(value) and has_placeholder_text(value):
                errors.append(f"designManifest.compositionIntent[{index}] is placeholder text; state what the page makes visible")
    visual_mode = manifest.get("visualMode")
    if visual_mode is not None and visual_mode not in ALLOWED_VISUAL_MODES:
        errors.append(f"designManifest.visualMode must be one of {sorted(ALLOWED_VISUAL_MODES)}")
    material_system = manifest.get("materialSystem")
    if material_system is not None:
        if not isinstance(material_system, list) or not 1 <= len(material_system) <= 3:
            errors.append("designManifest.materialSystem must contain one to three material treatments")
        else:
            for index, value in enumerate(material_system):
                expect_text(errors, value, f"designManifest.materialSystem[{index}]")
                if is_text(value) and has_placeholder_text(value):
                    errors.append(f"designManifest.materialSystem[{index}] is placeholder text; name the actual material treatment")
    if manifest.get("imageCadence") is not None:
        expect_text(errors, manifest.get("imageCadence"), "designManifest.imageCadence")
        if is_text(manifest.get("imageCadence")) and has_placeholder_text(manifest.get("imageCadence")):
            errors.append("designManifest.imageCadence is placeholder text; describe the actual image rhythm")


def validate_composition(errors: list[str], composition: Any, path: str) -> None:
    if not isinstance(composition, dict):
        errors.append(f"{path} must be an object")
        return
    archetype = composition.get("archetype")
    if archetype not in ALLOWED_ARCHETYPES:
        errors.append(f"{path}.archetype must be one of {sorted(ALLOWED_ARCHETYPES)}")
    primitives = composition.get("primitives")
    if not isinstance(primitives, list) or not primitives:
        errors.append(f"{path}.primitives must contain at least one composition primitive")
    else:
        for index, value in enumerate(primitives):
            if value not in ALLOWED_PRIMITIVES:
                errors.append(f"{path}.primitives[{index}] must be one of {sorted(ALLOWED_PRIMITIVES)}")
    expect_text(errors, composition.get("intent"), f"{path}.intent")
    if archetype == "custom":
        expect_text(errors, composition.get("reason"), f"{path}.reason")


def block_emphasis_count(block: Any) -> int:
    if not isinstance(block, dict):
        return 0
    count = len(block.get("emphasis", [])) if isinstance(block.get("emphasis"), list) else 0
    if block.get("type") == "bullets" and isinstance(block.get("items"), list):
        count += sum(
            len(item.get("emphasis", []))
            for item in block["items"]
            if isinstance(item, dict) and isinstance(item.get("emphasis"), list)
        )
    return count


def validate_spec(spec: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["The top-level JSON value must be an object"]

    if spec.get("title") is not None:
        expect_text(errors, spec.get("title"), "title")
    if spec.get("author") is not None:
        expect_text(errors, spec.get("author"), "author")

    reference_driven = spec.get("referenceDriven", False)
    if not isinstance(reference_driven, bool):
        errors.append("referenceDriven must be a boolean")
        reference_driven = False

    theme = spec.get("theme", {})
    if not isinstance(theme, dict):
        errors.append("theme must be an object")
    else:
        for key in ("background", "ink", "muted", "accent", "highlight", "card"):
            if key in theme and (not isinstance(theme[key], str) or not HEX_COLOR.fullmatch(theme[key])):
                errors.append(f"theme.{key} must be a six-digit hex color")

    canvas = spec.get("canvas")
    if canvas is not None:
        if not isinstance(canvas, dict):
            errors.append("canvas must be an object with width and height")
        else:
            for axis in ("width", "height"):
                value = canvas.get(axis)
                if not isinstance(value, int) or isinstance(value, bool) or not MIN_CANVAS <= value <= MAX_CANVAS:
                    errors.append(f"canvas.{axis} must be an integer between {MIN_CANVAS} and {MAX_CANVAS}")

    slides = spec.get("slides")
    if not isinstance(slides, list) or not 1 <= len(slides) <= 12:
        errors.append("slides must be a list containing 1–12 slides")
        return errors

    if reference_driven:
        validate_manifest(errors, spec.get("designManifest"), len(slides))

    merged_theme = {**DEFAULT_THEME, **theme} if isinstance(theme, dict) else DEFAULT_THEME
    if reference_driven and all(HEX_COLOR.fullmatch(str(merged_theme[key])) for key in DEFAULT_THEME):
        for role, minimum in (("ink", 4.5), ("muted", 4.5), ("accent", 3.0)):
            ratio = contrast_ratio(merged_theme[role], merged_theme["background"])
            if ratio < minimum:
                errors.append(
                    f"theme.{role} contrast against theme.background is {ratio:.2f}:1; reference-driven work requires {minimum:.1f}:1"
                )

    for index, slide in enumerate(slides):
        path = f"slides[{index}]"
        if not isinstance(slide, dict):
            errors.append(f"{path} must be an object")
            continue
        expect_text(errors, slide.get("title"), f"{path}.title")
        if slide.get("eyebrow") is not None and slide.get("eyebrow") != "":
            expect_text(errors, slide.get("eyebrow"), f"{path}.eyebrow")
        if slide.get("footer") is not None:
            expect_text(errors, slide.get("footer"), f"{path}.footer")
        header_inset = slide.get("headerInset")
        if header_inset is not None and (
            not isinstance(header_inset, int) or isinstance(header_inset, bool) or not 0 <= header_inset <= 400
        ):
            errors.append(f"{path}.headerInset must be an integer from 0 to 400")
        display_scale = slide.get("displayScale")
        if display_scale is not None and (
            not isinstance(display_scale, (int, float))
            or isinstance(display_scale, bool)
            or not 1.0 <= display_scale <= 2.0
        ):
            errors.append(f"{path}.displayScale must be a number from 1.0 to 2.0")
        if slide.get("hidePageNumber") is not None and not isinstance(slide.get("hidePageNumber"), bool):
            errors.append(f"{path}.hidePageNumber must be a boolean")
        if slide.get("density", "normal") not in ALLOWED_DENSITIES:
            errors.append(f"{path}.density must be one of {sorted(ALLOWED_DENSITIES)}")
        composition = slide.get("composition")
        if reference_driven and composition is None:
            errors.append(f"{path}.composition is required for reference-driven work")
        elif composition is not None:
            validate_composition(errors, composition, f"{path}.composition")
            manifest = spec.get("designManifest")
            manifest_intents = manifest.get("compositionIntent") if isinstance(manifest, dict) else None
            if (
                reference_driven
                and isinstance(manifest_intents, list)
                and index < len(manifest_intents)
                and is_text(manifest_intents[index])
                and composition.get("intent") != manifest_intents[index]
            ):
                errors.append(
                    f"{path}.composition.intent must exactly match designManifest.compositionIntent[{index}]"
                )
        blocks = slide.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            errors.append(f"{path}.blocks must be a non-empty list")
            continue
        for block_index, block in enumerate(blocks):
            validate_block(errors, block, f"{path}.blocks[{block_index}]")
        emphasis_count = sum(block_emphasis_count(block) for block in blocks)
        if emphasis_count > 3 and reference_driven:
            errors.append(f"{path} uses {emphasis_count} emphasis phrases; no more than three emphasis phrases are allowed")

    return errors


def warning(code: str, message: str, slide: int | None = None, evidence: Any = None) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message}
    if slide is not None:
        result["slide"] = slide
    if evidence is not None:
        result["evidence"] = evidence
    return result


def block_signature(slide: dict[str, Any]) -> str:
    return "+".join(str(block.get("type", "unknown")) for block in slide.get("blocks", []) if isinstance(block, dict))


def analyze_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    slides = spec.get("slides", [])
    if not isinstance(slides, list):
        return warnings
    if len(slides) >= 6:
        families = {
            slide.get("composition", {}).get("archetype", "editorial")
            for slide in slides
            if isinstance(slide, dict)
        }
        if len(families) < 2:
            warnings.append(
                warning(
                    "LOW_COMPOSITION_DIVERSITY",
                    "Six-plus-slide decks should use at least two meaningful composition families.",
                    evidence={"families": sorted(families)},
                )
            )
    signatures = [block_signature(slide) for slide in slides if isinstance(slide, dict)]
    if signatures:
        most_common = max(signatures.count(value) for value in set(signatures))
        ratio = most_common / len(signatures)
        if len(signatures) >= 4 and ratio > 0.5:
            warnings.append(
                warning(
                    "REPEATED_BLOCK_SIGNATURE",
                    "More than half of the deck repeats the same component sequence.",
                    evidence={"ratio": round(ratio, 3)},
                )
            )
    manifest = spec.get("designManifest", {}) if isinstance(spec.get("designManifest"), dict) else {}
    visual_mode = manifest.get("visualMode", "editorial")
    if visual_mode != "editorial":
        image_slides = [
            index + 1
            for index, slide in enumerate(slides)
            if isinstance(slide, dict)
            and any(isinstance(block, dict) and block.get("type") == "image" for block in slide.get("blocks", []))
        ]
        if not image_slides:
            warnings.append(
                warning(
                    "VISUAL_MODE_UNDELIVERED",
                    "The manifest promises a non-editorial visual mode, but the render spec contains no image block.",
                    evidence={"visualMode": visual_mode},
                )
            )
        elif visual_mode in {"image-led", "photo-diary", "object-study", "poetic-poster"} and len(image_slides) < max(2, len(slides) // 3):
            warnings.append(
                warning(
                    "WEAK_IMAGE_CADENCE",
                    "The image-led mode has too few image-bearing pages to establish the promised perceptual rhythm.",
                    evidence={"visualMode": visual_mode, "imageSlides": image_slides},
                )
            )
    if not spec.get("referenceDriven"):
        for index, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            emphasis_count = sum(block_emphasis_count(block) for block in slide.get("blocks", []))
            if emphasis_count > 3:
                warnings.append(
                    warning(
                        "LEGACY_EXCESSIVE_EMPHASIS",
                        "This legacy slide exceeds the interpreted emphasis budget; rendering remains allowed for compatibility.",
                        slide=index + 1,
                        evidence={"emphasisCount": emphasis_count, "recommendedMaximum": 3},
                    )
                )
        theme = {**DEFAULT_THEME, **spec.get("theme", {})} if isinstance(spec.get("theme", {}), dict) else DEFAULT_THEME
        muted_ratio = contrast_ratio(theme["muted"], theme["background"])
        if muted_ratio < 4.5:
            warnings.append(
                warning(
                    "LEGACY_MUTED_CONTRAST",
                    "Muted/source text is below the 4.5:1 reference-driven floor; legacy rendering remains allowed.",
                    evidence={"ratio": round(muted_ratio, 2)},
                )
            )
    return warnings


def normalized_ngrams(value: Any, size: int = 3) -> set[str]:
    text = re.sub(r"\s+", "", str(value).lower())
    if not text:
        return set()
    if len(text) <= size:
        return {text}
    return {text[index : index + size] for index in range(len(text) - size + 1)}


def jaccard(first: set[str], second: set[str]) -> float:
    if not first and not second:
        return 1.0
    union = first | second
    return len(first & second) / len(union) if union else 0.0


def manifest_concept_text(manifest: dict[str, Any]) -> str:
    fields = [manifest.get(key, "") for key in MANIFEST_TEXT_FIELDS if key != "candidateDirection"]
    fields.extend(manifest.get("motifs", []) if isinstance(manifest.get("motifs"), list) else [])
    return " ".join(str(value) for value in fields)


def compare_candidate_manifests(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    distinct = True
    for first_index in range(len(manifests)):
        for second_index in range(first_index + 1, len(manifests)):
            similarity = jaccard(
                normalized_ngrams(manifest_concept_text(manifests[first_index])),
                normalized_ngrams(manifest_concept_text(manifests[second_index])),
            )
            if similarity >= 0.72:
                distinct = False
            pairs.append(
                {
                    "first": first_index + 1,
                    "second": second_index + 1,
                    "similarity": round(similarity, 3),
                    "distinct": similarity < 0.72,
                }
            )
    return {"distinct": distinct and len(manifests) >= 2, "pairs": pairs}


def composition_similarity(first: dict[str, Any], second: dict[str, Any]) -> float:
    first_fingerprint = build_design_fingerprint(first)
    second_fingerprint = build_design_fingerprint(second)
    archetypes = sequence_similarity(
        first_fingerprint.get("archetypeSequence", []), second_fingerprint.get("archetypeSequence", [])
    )
    primitives = jaccard(
        set(first_fingerprint.get("primitiveSet", [])), set(second_fingerprint.get("primitiveSet", []))
    )
    components = sequence_similarity(
        first_fingerprint.get("componentSignatures", []), second_fingerprint.get("componentSignatures", [])
    )
    return round(0.45 * archetypes + 0.25 * primitives + 0.30 * components, 3)


def compare_candidate_specs(specs: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_result = compare_candidate_manifests(
        [spec.get("designManifest", {}) for spec in specs if isinstance(spec.get("designManifest"), dict)]
    )
    pairs = []
    distinct = manifest_result["distinct"] and len(specs) >= 2
    manifest_pairs = {(item["first"], item["second"]): item for item in manifest_result["pairs"]}
    for first_index in range(len(specs)):
        for second_index in range(first_index + 1, len(specs)):
            comp_similarity = composition_similarity(specs[first_index], specs[second_index])
            manifest_pair = manifest_pairs.get((first_index + 1, second_index + 1), {})
            concept_similarity = manifest_pair.get("similarity", 1.0)
            pair_distinct = concept_similarity < 0.72 and comp_similarity < 0.82
            if not pair_distinct:
                distinct = False
            pairs.append(
                {
                    "first": first_index + 1,
                    "second": second_index + 1,
                    "conceptSimilarity": concept_similarity,
                    "compositionSimilarity": comp_similarity,
                    "distinct": pair_distinct,
                }
            )
    return {"distinct": distinct, "pairs": pairs}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_design_fingerprint(spec: dict[str, Any]) -> dict[str, Any]:
    manifest = spec.get("designManifest", {}) if isinstance(spec.get("designManifest"), dict) else {}
    slides = spec.get("slides", []) if isinstance(spec.get("slides"), list) else []
    archetypes = []
    primitives: set[str] = set()
    signatures = []
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        composition = slide.get("composition", {}) if isinstance(slide.get("composition"), dict) else {}
        archetypes.append(composition.get("archetype", "editorial"))
        primitives.update(value for value in composition.get("primitives", []) if isinstance(value, str))
        signatures.append(block_signature(slide))
    theme = {**DEFAULT_THEME, **spec.get("theme", {})} if isinstance(spec.get("theme", {}), dict) else DEFAULT_THEME
    return {
        "version": 1,
        "conceptHash": stable_hash(manifest_concept_text(manifest)),
        "motifHash": stable_hash(manifest.get("motifs", [])),
        "typeStrategyHash": stable_hash(manifest.get("typeStrategy", "")),
        "archetypeSequence": archetypes,
        "primitiveSet": sorted(primitives),
        "componentSignatures": signatures,
        "palette": {key: theme[key] for key in sorted(DEFAULT_THEME)},
    }


def sequence_similarity(first: list[Any], second: list[Any]) -> float:
    if not first and not second:
        return 1.0
    length = max(len(first), len(second))
    if length == 0:
        return 0.0
    matches = sum(1 for index in range(min(len(first), len(second))) if first[index] == second[index])
    return matches / length


def fingerprint_similarity(first: dict[str, Any], second: dict[str, Any]) -> float:
    primitive_similarity = jaccard(set(first.get("primitiveSet", [])), set(second.get("primitiveSet", [])))
    score = (
        0.25 * (first.get("conceptHash") == second.get("conceptHash"))
        + 0.10 * (first.get("motifHash") == second.get("motifHash"))
        + 0.10 * (first.get("typeStrategyHash") == second.get("typeStrategyHash"))
        + 0.20 * sequence_similarity(first.get("archetypeSequence", []), second.get("archetypeSequence", []))
        + 0.10 * primitive_similarity
        + 0.15 * sequence_similarity(first.get("componentSignatures", []), second.get("componentSignatures", []))
        + 0.10 * (first.get("palette") == second.get("palette"))
    )
    return round(score, 3)


def compare_with_history(fingerprint: dict[str, Any], history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for offset, previous in enumerate(history[-5:]):
        similarity = fingerprint_similarity(fingerprint, previous)
        if similarity >= 0.78:
            matches.append({"recentIndex": offset - min(5, len(history)) + 1, "similarity": similarity})
    if not matches:
        return []
    return [
        warning(
            "RECENT_DESIGN_SIMILARITY",
            "This direction closely repeats a recent local design fingerprint; keep it only with a content-specific reason.",
            evidence={"matches": matches},
        )
    ]


def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    results = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            results.append(value)
    return results


def append_history(path: Path, fingerprint: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(fingerprint, ensure_ascii=False, sort_keys=True) + "\n")


def load_history_safely(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        return load_history(path), []
    except OSError as exc:
        return [], [
            warning(
                "DESIGN_HISTORY_READ_FAILED",
                "Design history could not be read; rendering continues without recent-design comparison.",
                evidence={"error": str(exc)},
            )
        ]


def append_history_safely(path: Path, fingerprint: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        append_history(path, fingerprint)
        return []
    except OSError as exc:
        return [
            warning(
                "DESIGN_HISTORY_WRITE_FAILED",
                "Rendered output is valid, but its design fingerprint could not be appended to local history.",
                evidence={"error": str(exc)},
            )
        ]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def resolve_local_image_sources(spec: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Return a render-only copy whose validated local image paths are file URIs."""
    resolved = copy.deepcopy(spec)
    for slide_index, slide in enumerate(resolved.get("slides", [])):
        if not isinstance(slide, dict):
            continue
        for block_index, block in enumerate(slide.get("blocks", [])):
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            src = block.get("src")
            if not isinstance(src, str):
                continue
            path = Path(src).expanduser()
            if not path.is_absolute():
                path = base_dir / path
            path = path.resolve()
            if path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"slides[{slide_index}].blocks[{block_index}].src has an unsupported image extension"
                )
            if not path.is_file():
                raise ValueError(f"Image asset does not exist: {path}")
            block["src"] = path.as_uri()
    return resolved


def build_html(template_path: Path, spec: dict[str, Any]) -> str:
    try:
        template = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"Template does not exist: {template_path}") from exc
    canvas_w, canvas_h = canvas_dimensions(spec)
    template = (
        template.replace("width: 1080px;", f"width: {canvas_w}px;")
        .replace("height: 1350px;", f"height: {canvas_h}px;")
    )
    token = "__CAROUSEL_SPEC__"
    if template.count(token) != 1:
        raise ValueError(f"Template must contain exactly one {token} token")
    payload = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return template.replace(token, payload)


def browser_candidates(playwright: Any, explicit: str | None) -> list[Path | None]:
    if explicit:
        return [Path(explicit).expanduser()]
    candidates: list[Path | None] = []
    env_browser = os.environ.get("CHROME_BIN")
    if env_browser:
        candidates.append(Path(env_browser).expanduser())
    managed = Path(playwright.chromium.executable_path)
    candidates.append(managed)
    candidates.extend(
        [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/chromium"),
            Path("/usr/bin/chromium-browser"),
        ]
    )
    return candidates


def choose_browser(playwright: Any, explicit: str | None) -> Path | None:
    for candidate in browser_candidates(playwright, explicit):
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def run_render(spec: dict[str, Any], html_path: Path, output_dir: Path, browser_path: str | None) -> dict[str, Any]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Python Playwright is unavailable. Install it in the active Python environment before rendering."
        ) from exc

    canvas_w, canvas_h = canvas_dimensions(spec)
    qa: dict[str, Any] = {
        "valid": True,
        "structurally_valid": True,
        "veg_review_required": True,
        "visually_approved": False,
        "canvas": {"width": canvas_w, "height": canvas_h},
        "slideCount": len(spec["slides"]),
        "slides": [],
        "errors": [],
        "warnings": analyze_spec(spec),
        "designManifestPresent": spec.get("referenceDriven") is True and isinstance(spec.get("designManifest"), dict),
    }

    try:
        with sync_playwright() as playwright:
            executable = choose_browser(playwright, browser_path)
            if executable is None:
                raise RuntimeError(
                    "No Chromium browser was found. Set CHROME_BIN or pass --browser with an executable path."
                )
            browser = playwright.chromium.launch(
                executable_path=str(executable),
                headless=True,
                args=["--allow-file-access-from-files"],
            )
            context = browser.new_context(
                viewport={"width": canvas_w, "height": canvas_h},
                device_scale_factor=1,
            )
            page = context.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="load")
            page.wait_for_function("window.__renderReady === true")
            page.evaluate("() => document.fonts.ready")
            page.wait_for_function(
                "Array.from(document.images).every(image => image.complete && image.naturalWidth > 0)"
            )

            slide_qa = page.evaluate(
                """
                () => Array.from(document.querySelectorAll('.slide')).map((slide, index) => {
                  const slideRect = slide.getBoundingClientRect();
                  const header = slide.querySelector('.slide-header');
                  const content = slide.querySelector('.slide-content');
                  const footer = slide.querySelector('.slide-footer');
                  const headerRect = header.getBoundingClientRect();
                  const contentRect = content.getBoundingClientRect();
                  const footerRect = footer.getBoundingClientRect();
                  const watched = Array.from(slide.querySelectorAll(
                    '.slide-title, .eyebrow, .page-number, .slide-content, .slide-content *, .slide-footer, .slide-footer *'
                  ));
                  const overflowElements = watched.map((element) => {
                    const rect = element.getBoundingClientRect();
                    const horizontalScroll = element.scrollWidth > element.clientWidth + 4;
                    const isContentZone = element === content;
                    const isFooterZone = element === footer;
                    const verticalScroll = (isContentZone || isFooterZone) &&
                      element.scrollHeight > element.clientHeight + 4;
                    const outsideSlide = rect.left < slideRect.left - 1 ||
                      rect.right > slideRect.right + 1 ||
                      rect.top < slideRect.top - 1 ||
                      rect.bottom > slideRect.bottom + 1;
                    const insideContent = element !== content && element.closest('.slide-content') === content;
                    const insideFooter = element !== footer && element.closest('.slide-footer') === footer;
                    const outsideZone = (insideContent && (
                      rect.left < contentRect.left - 1 || rect.right > contentRect.right + 1 ||
                      rect.top < contentRect.top - 1 || rect.bottom > contentRect.bottom + 1
                    )) || (insideFooter && (
                      rect.left < footerRect.left - 1 || rect.right > footerRect.right + 1 ||
                      rect.top < footerRect.top - 1 || rect.bottom > footerRect.bottom + 1
                    ));
                    const elementOverflow = horizontalScroll || verticalScroll || outsideSlide || outsideZone;
                    return elementOverflow ? {
                      element: element.className || element.tagName.toLowerCase(),
                      horizontalScroll,
                      verticalScroll,
                      outsideSlide,
                      outsideZone,
                      left: Math.round(rect.left - slideRect.left),
                      right: Math.round(rect.right - slideRect.left),
                      top: Math.round(rect.top - slideRect.top),
                      bottom: Math.round(rect.bottom - slideRect.top)
                    } : null;
                  }).filter(Boolean);
                  const zoneOverlap = headerRect.bottom > contentRect.top + 1 ||
                    contentRect.bottom > footerRect.top + 1;
                  const overflow = content.scrollHeight > content.clientHeight + 1 ||
                    overflowElements.length > 0 || zoneOverlap;
                  const contentChildren = Array.from(content.children);
                  const occupiedTop = contentChildren.length
                    ? Math.min(...contentChildren.map(element => element.getBoundingClientRect().top))
                    : contentRect.top;
                  const occupiedBottom = contentChildren.length
                    ? Math.max(...contentChildren.map(element => element.getBoundingClientRect().bottom))
                    : contentRect.top;
                  const contentOccupiedHeight = Math.max(0, occupiedBottom - occupiedTop);
                  const titleStyle = getComputedStyle(header.querySelector('.slide-title'));
                  const titleLineHeight = parseFloat(titleStyle.lineHeight) || parseFloat(titleStyle.fontSize);
                  const titleLineCount = Math.max(1, Math.round(
                    header.querySelector('.slide-title').getBoundingClientRect().height / titleLineHeight
                  ));
                  const highlightArea = Array.from(content.querySelectorAll('mark')).reduce((sum, element) => {
                    const rect = element.getBoundingClientRect();
                    return sum + rect.width * rect.height;
                  }, 0);
                  return {
                    slide: index + 1,
                    width: Math.round(slideRect.width),
                    height: Math.round(slideRect.height),
                    contentHeight: Math.round(content.clientHeight),
                    contentScrollHeight: Math.round(content.scrollHeight),
                    contentOccupiedHeight: Math.round(contentOccupiedHeight),
                    contentUtilization: Number((contentOccupiedHeight / Math.max(1, contentRect.height)).toFixed(3)),
                    titleLineCount,
                    blockCount: contentChildren.length,
                    highlightCount: content.querySelectorAll('mark').length,
                    highlightAreaRatio: Number((highlightArea / Math.max(1, contentRect.width * contentRect.height)).toFixed(4)),
                    overflow,
                    zoneOverlap,
                    overflowElements
                  };
                })
                """
            )

            slides = page.locator(".slide")
            count = slides.count()
            if count != len(spec["slides"]):
                raise RuntimeError(f"Rendered {count} slides but expected {len(spec['slides'])}")
            for index in range(count):
                output_path = output_dir / f"slide-{index + 1:02d}.png"
                slides.nth(index).screenshot(path=str(output_path))

            qa["slides"] = slide_qa
            for result in slide_qa:
                if result["width"] != canvas_w or result["height"] != canvas_h:
                    qa["errors"].append(
                        f"Slide {result['slide']} rendered at {result['width']}x{result['height']} instead of {canvas_w}x{canvas_h}"
                    )
                if result["overflow"]:
                    qa["errors"].append(f"Slide {result['slide']} elements exceed the safe slide regions")
                slide_spec = spec["slides"][result["slide"] - 1]
                composition = slide_spec.get("composition", {})
                result["compositionIntent"] = (
                    composition.get("intent") if isinstance(composition, dict) else None
                )
                density = slide_spec.get("density", "normal")
                lower, upper = (0.30, 0.88) if density == "airy" else (0.48, 0.94)
                utilization = result["contentUtilization"]
                if utilization < lower:
                    qa["warnings"].append(
                        warning(
                            "LOW_CONTENT_UTILIZATION",
                            f"Occupied content uses {utilization:.0%} of the content region; review balance or intentional whitespace.",
                            slide=result["slide"],
                            evidence={"utilization": utilization, "expectedMinimum": lower},
                        )
                    )
                elif utilization > upper:
                    qa["warnings"].append(
                        warning(
                            "HIGH_CONTENT_UTILIZATION",
                            f"Occupied content uses {utilization:.0%} of the content region; review density and breathing room.",
                            slide=result["slide"],
                            evidence={"utilization": utilization, "expectedMaximum": upper},
                        )
                    )
            qa["valid"] = not qa["errors"]
            qa["structurally_valid"] = qa["valid"]
            qa["veg_review_required"] = True
            context.close()
            browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(f"Browser rendering failed: {exc}") from exc

    return qa


def sync_rendered_output(staging_dir: Path, output_dir: Path) -> None:
    """Replace only renderer-owned output files after a completed render."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slide_pattern = re.compile(r"^slide-\d{2}\.png$")
    for existing in output_dir.iterdir():
        if existing.is_file() and (
            slide_pattern.fullmatch(existing.name)
            or existing.name in {"carousel.html", "qa.json", "design-manifest.json"}
        ):
            existing.unlink()
    for generated in staging_dir.iterdir():
        if generated.is_file() and (
            slide_pattern.fullmatch(generated.name)
            or generated.name in {"carousel.html", "qa.json", "design-manifest.json"}
        ):
            shutil.move(str(generated), str(output_dir / generated.name))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and render a Xiaohongshu carousel JSON spec to 1080x1350 PNGs."
    )
    parser.add_argument("spec", help="Path to the UTF-8 carousel JSON spec")
    parser.add_argument("--output-dir", default="xiaohongshu-output", help="Directory for HTML, PNG, and QA output")
    parser.add_argument("--template", help="Optional HTML template override")
    parser.add_argument("--browser", help="Optional Chromium or Chrome executable path")
    parser.add_argument("--check-only", action="store_true", help="Validate JSON without launching a browser")
    parser.add_argument(
        "--history",
        help="Optional design-history.jsonl path; defaults beside the spec for interpreted decks",
    )
    parser.add_argument("--no-history", action="store_true", help="Do not compare or append local design history")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    spec_path = Path(args.spec).expanduser().resolve()
    template_path = (
        Path(args.template).expanduser().resolve()
        if args.template
        else skill_dir / "assets" / "carousel-template.html"
    )
    output_dir = Path(args.output_dir).expanduser().resolve()

    try:
        spec = load_json(spec_path)
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1

    errors = validate_spec(spec)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    static_warnings = analyze_spec(spec)
    if args.check_only:
        print(
            json.dumps(
                {
                    "valid": True,
                    "schema_valid": True,
                    "structurally_valid": None,
                    "veg_review_required": True,
                    "visually_approved": False,
                    "slideCount": len(spec["slides"]),
                    "warnings": static_warnings,
                    "message": "Schema validation passed; render to determine structural validity and perform visual review",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    try:
        render_spec = resolve_local_image_sources(spec, spec_path.parent)
        html = build_html(template_path, render_spec)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".xiaohongshu-layout-", dir=output_dir.parent) as temp_name:
            staging_dir = Path(temp_name)
            html_path = staging_dir / "carousel.html"
            html_path.write_text(html, encoding="utf-8")
            qa = run_render(render_spec, html_path, staging_dir, args.browser)
            fingerprint = None
            history_path = None
            if spec.get("referenceDriven") is True and isinstance(spec.get("designManifest"), dict):
                manifest_path = staging_dir / "design-manifest.json"
                manifest_path.write_text(
                    json.dumps(spec["designManifest"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                fingerprint = build_design_fingerprint(spec)
                if not args.no_history:
                    history_path = (
                        Path(args.history).expanduser().resolve()
                        if args.history
                        else spec_path.parent / "design-history.jsonl"
                    )
                    history, history_warnings = load_history_safely(history_path)
                    qa["warnings"].extend(history_warnings)
                    qa["warnings"].extend(compare_with_history(fingerprint, history))
            qa["veg_review_required"] = True
            qa_path = staging_dir / "qa.json"
            qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            sync_rendered_output(staging_dir, output_dir)
            if fingerprint is not None and history_path is not None and qa["valid"]:
                history_write_warnings = append_history_safely(history_path, fingerprint)
                if history_write_warnings:
                    qa["warnings"].extend(history_write_warnings)
                    (output_dir / "qa.json").write_text(
                        json.dumps(qa, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 3

    print(json.dumps(qa, ensure_ascii=False, indent=2))
    return 0 if qa["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
