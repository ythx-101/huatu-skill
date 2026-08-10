from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_DIR / "scripts" / "render_carousel.py"
SPEC = importlib.util.spec_from_file_location("render_carousel", MODULE_PATH)
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def legacy_spec() -> dict:
    return {
        "title": "Legacy",
        "author": "@test",
        "slides": [
            {
                "title": "Legacy slide",
                "density": "normal",
                "blocks": [{"type": "paragraph", "text": "Still renders."}],
            }
        ],
    }


def interpreted_spec(slide_count: int = 2) -> dict:
    slides = []
    intents = []
    archetypes = ["poster", "diagram", "split", "timeline", "editorial", "custom"]
    for index in range(slide_count):
        intent = f"Page {index + 1} makes relationship {index + 1} visible."
        intents.append(intent)
        composition = {
            "archetype": archetypes[index % len(archetypes)],
            "primitives": ["scale-contrast", "whitespace"] if index % 2 == 0 else ["flow", "annotation"],
            "intent": intent,
        }
        if composition["archetype"] == "custom":
            composition["reason"] = "The content relationship needs a nonstandard reading path."
        slides.append(
            {
                "title": f"Claim {index + 1}",
                "density": "airy" if index == 0 else "normal",
                "composition": composition,
                "blocks": [{"type": "paragraph", "text": f"Evidence {index + 1}."}],
            }
        )
    return {
        "title": "Interpreted",
        "author": "@test",
        "referenceDriven": True,
        "theme": {
            "background": "#F4EFE4",
            "ink": "#171714",
            "muted": "#5F5C55",
            "accent": "#A23F32",
            "highlight": "#F3E58B",
            "card": "#FBF8F0",
        },
        "designManifest": {
            "candidateDirection": "Metaphor-led",
            "visualThesis": "Understanding appears when hidden relationships become visible.",
            "readerEmotion": "Confusion, recognition, then agency.",
            "semanticMetaphor": "A lens bringing a system into focus.",
            "motifs": ["lens", "signal path"],
            "rhythmPlan": "Open quietly, compress the mechanism, then resolve with space.",
            "compositionIntent": intents,
            "contrastPlan": "Use the strongest scale break at the mechanism reveal.",
            "typeStrategy": "Serif display claims with sans-serif explanatory copy.",
            "avoidList": ["uniform stacked cards", "yellow marker on every page"],
            "whyThisVisual": "The topic is about seeing relationships rather than decorating text.",
        },
        "slides": slides,
    }


class ValidationTests(unittest.TestCase):
    def test_legacy_spec_remains_valid(self) -> None:
        self.assertEqual(renderer.validate_spec(legacy_spec()), [])

    def test_reference_driven_spec_requires_manifest(self) -> None:
        spec = legacy_spec()
        spec["referenceDriven"] = True
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("designManifest" in error for error in errors), errors)

    def test_valid_interpreted_spec_passes(self) -> None:
        self.assertEqual(renderer.validate_spec(interpreted_spec()), [])

    def test_reference_driven_slide_requires_composition(self) -> None:
        spec = interpreted_spec()
        del spec["slides"][0]["composition"]
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("slides[0].composition" in error for error in errors), errors)

    def test_manifest_and_slide_intent_must_match(self) -> None:
        spec = interpreted_spec()
        spec["slides"][0]["composition"]["intent"] = "A contradictory intent."
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("must exactly match" in error for error in errors), errors)

    def test_custom_composition_requires_reason(self) -> None:
        spec = interpreted_spec(6)
        del spec["slides"][5]["composition"]["reason"]
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("reason" in error for error in errors), errors)

    def test_more_than_three_emphasis_phrases_fails(self) -> None:
        spec = interpreted_spec()
        spec["slides"][0]["blocks"] = [
            {"type": "paragraph", "text": "one two three four", "emphasis": ["one", "two", "three", "four"]}
        ]
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("three emphasis" in error for error in errors), errors)

    def test_legacy_excessive_emphasis_warns_without_breaking(self) -> None:
        spec = legacy_spec()
        spec["slides"][0]["blocks"] = [
            {"type": "paragraph", "text": "one two three four", "emphasis": ["one", "two", "three", "four"]}
        ]
        self.assertEqual(renderer.validate_spec(spec), [])
        codes = {item["code"] for item in renderer.analyze_spec(spec)}
        self.assertIn("LEGACY_EXCESSIVE_EMPHASIS", codes)

    def test_strict_contrast_rejects_low_muted_contrast(self) -> None:
        spec = interpreted_spec()
        spec["theme"]["muted"] = "#B0ADA5"
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("contrast" in error for error in errors), errors)

    def test_local_image_block_is_valid(self) -> None:
        spec = interpreted_spec()
        spec["designManifest"].update(
            {
                "visualMode": "mixed",
                "materialSystem": ["paper", "pencil"],
                "imageCadence": "Alternate image-led and structural pages.",
            }
        )
        spec["slides"][0]["blocks"] = [
            {
                "type": "image",
                "src": "assets/hero.png",
                "alt": "A thread returns through observation points",
                "role": "hero",
                "fit": "contain",
                "position": "center",
                "treatment": "paper",
                "height": 500,
            }
        ]
        self.assertEqual(renderer.validate_spec(spec), [])

    def test_remote_image_url_is_rejected(self) -> None:
        spec = interpreted_spec()
        spec["slides"][0]["blocks"] = [
            {
                "type": "image",
                "src": "https://example.com/hero.png",
                "alt": "Remote image",
                "role": "hero",
            }
        ]
        errors = renderer.validate_spec(spec)
        self.assertTrue(any("local file path" in error for error in errors), errors)

    def test_image_led_manifest_without_image_warns(self) -> None:
        spec = interpreted_spec(6)
        spec["designManifest"]["visualMode"] = "image-led"
        codes = {item["code"] for item in renderer.analyze_spec(spec)}
        self.assertIn("VISUAL_MODE_UNDELIVERED", codes)

    def test_resolve_local_image_sources_uses_spec_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            asset = Path(temp_name) / "hero.png"
            asset.write_bytes(b"png fixture")
            spec = legacy_spec()
            spec["slides"][0]["blocks"] = [
                {"type": "image", "src": "hero.png", "alt": "Fixture", "role": "hero"}
            ]
            resolved = renderer.resolve_local_image_sources(spec, Path(temp_name))
        self.assertTrue(resolved["slides"][0]["blocks"][0]["src"].startswith("file://"))


class DiagnosticsTests(unittest.TestCase):
    def test_repetitive_six_slide_deck_warns(self) -> None:
        spec = interpreted_spec(6)
        for slide in spec["slides"]:
            slide["composition"]["archetype"] = "editorial"
            slide["blocks"] = [{"type": "paragraph", "text": "Same structure."}]
        warnings = renderer.analyze_spec(spec)
        codes = {warning["code"] for warning in warnings}
        self.assertIn("LOW_COMPOSITION_DIVERSITY", codes)
        self.assertIn("REPEATED_BLOCK_SIGNATURE", codes)

    def test_fake_candidate_diversity_is_detected(self) -> None:
        first = interpreted_spec()["designManifest"]
        second = copy.deepcopy(first)
        second["candidateDirection"] = "Different name"
        result = renderer.compare_candidate_manifests([first, second])
        self.assertFalse(result["distinct"])
        self.assertGreaterEqual(result["pairs"][0]["similarity"], 0.8)

    def test_meaningfully_different_candidates_pass(self) -> None:
        first = interpreted_spec()["designManifest"]
        second = copy.deepcopy(first)
        second.update(
            {
                "candidateDirection": "Diagram-spatial",
                "visualThesis": "The workflow is a relay of decisions and evidence.",
                "semanticMetaphor": "A relay circuit with human-controlled gates.",
                "motifs": ["gate", "handoff"],
                "rhythmPlan": "Alternate system maps with decisive checkpoints.",
                "contrastPlan": "Use spatial compression before each human gate.",
                "typeStrategy": "Neutral sans-serif with monospaced operational labels.",
                "whyThisVisual": "The material describes a process, so spatial flow carries meaning.",
            }
        )
        result = renderer.compare_candidate_manifests([first, second])
        self.assertTrue(result["distinct"], result)

    def test_different_manifest_but_same_composition_is_not_enough(self) -> None:
        first = interpreted_spec()
        second = copy.deepcopy(first)
        second["designManifest"].update(
            {
                "candidateDirection": "Different story",
                "visualThesis": "A relay makes the process legible.",
                "semanticMetaphor": "A relay circuit.",
                "motifs": ["gate", "handoff"],
                "rhythmPlan": "Pulse through checkpoints.",
                "contrastPlan": "Compress before each gate.",
                "typeStrategy": "Monospaced labels with neutral sans text.",
                "whyThisVisual": "The topic describes a process.",
            }
        )
        result = renderer.compare_candidate_specs([first, second])
        self.assertFalse(result["distinct"], result)
        self.assertGreaterEqual(result["pairs"][0]["compositionSimilarity"], 0.82)

    def test_history_similarity_warns_but_does_not_fail(self) -> None:
        spec = interpreted_spec()
        fingerprint = renderer.build_design_fingerprint(spec)
        warnings = renderer.compare_with_history(fingerprint, [fingerprint])
        self.assertTrue(any(item["code"] == "RECENT_DESIGN_SIMILARITY" for item in warnings))

    def test_history_fingerprint_contains_no_raw_manifest_text(self) -> None:
        spec = interpreted_spec()
        fingerprint_text = json.dumps(renderer.build_design_fingerprint(spec), ensure_ascii=False)
        manifest = spec["designManifest"]
        self.assertNotIn(manifest["visualThesis"], fingerprint_text)
        self.assertNotIn(manifest["semanticMetaphor"], fingerprint_text)
        self.assertNotIn(manifest["motifs"][0], fingerprint_text)

    def test_history_write_failure_becomes_warning(self) -> None:
        fingerprint = renderer.build_design_fingerprint(interpreted_spec())
        with mock.patch.object(renderer, "append_history", side_effect=OSError("read-only filesystem")):
            warnings = renderer.append_history_safely(Path("/not-written/history.jsonl"), fingerprint)
        self.assertEqual(warnings[0]["code"], "DESIGN_HISTORY_WRITE_FAILED")

    def test_check_only_does_not_claim_structural_validity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec_path = Path(temp_name) / "spec.json"
            spec_path.write_text(json.dumps(legacy_spec()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(spec_path), "--check-only"],
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["schema_valid"])
        self.assertIsNone(payload["structurally_valid"])
        self.assertTrue(payload["veg_review_required"])
        self.assertFalse(payload["visually_approved"])

    def test_legacy_manifest_metadata_does_not_enable_interpreted_mode(self) -> None:
        spec = legacy_spec()
        spec["designManifest"] = {"unrelated": "metadata"}
        self.assertEqual(renderer.validate_spec(spec), [])

    def test_build_html_escapes_script_breakout(self) -> None:
        spec = legacy_spec()
        spec["slides"][0]["blocks"][0]["text"] = "</script><script>alert(1)</script>"
        html = renderer.build_html(SKILL_DIR / "assets" / "carousel-template.html", spec)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("\\u003c/script>", html)


if __name__ == "__main__":
    unittest.main()
