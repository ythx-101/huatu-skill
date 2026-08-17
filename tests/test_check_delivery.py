from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
CHECKER = SKILL_DIR / "scripts" / "check_delivery.py"


def write_png_header(path: Path, width: int = 1080, height: int = 1350) -> None:
    """Write the bytes needed by the delivery checker's PNG IHDR probe."""
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


class DeliveryCheckerTests(unittest.TestCase):
    def make_bundle(self, root: Path, *, reference_driven: bool = False) -> tuple[Path, Path, Path]:
        spec = {
            "title": "Release fixture",
            "author": "@test",
            "canvas": {"width": 1080, "height": 1350},
            "slides": [
                {"title": "One", "blocks": [{"type": "paragraph", "text": "First."}]},
                {"title": "Two", "blocks": [{"type": "paragraph", "text": "Second."}]},
            ],
        }
        if reference_driven:
            spec["referenceDriven"] = True
            spec["designManifest"] = {"candidateDirection": "Fixture"}
        spec_path = root / "carousel.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")

        output = root / "rendered"
        output.mkdir()
        (output / "carousel.html").write_text("<!doctype html><title>fixture</title>", encoding="utf-8")
        write_png_header(output / "slide-01.png")
        write_png_header(output / "slide-02.png")
        qa = {
            "valid": True,
            "structurally_valid": True,
            "slideCount": 2,
            "canvas": {"width": 1080, "height": 1350},
            "errors": [],
        }
        (output / "qa.json").write_text(json.dumps(qa), encoding="utf-8")
        if reference_driven:
            (output / "design-manifest.json").write_text(
                json.dumps(spec["designManifest"]), encoding="utf-8"
            )

        # Rendered files must be newer than their sources; human QA must be newer than the render.
        source_time = time.time() - 20
        render_time = time.time() - 10
        os.utime(spec_path, (source_time, source_time))
        for item in output.iterdir():
            os.utime(item, (render_time, render_time))

        qa_summary = root / "qa-summary.md"
        qa_summary.write_text(
            "# QA\n\nVERDICT: PASS\n\nBLOCKING:\n\n- none\n\nEVIDENCE:\n\n- inspected every slide\n",
            encoding="utf-8",
        )
        return spec_path, output, qa_summary

    def run_checker(self, spec: Path, output: Path, qa_summary: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                str(spec),
                "--output-dir",
                str(output),
                "--qa-summary",
                str(qa_summary),
            ],
            capture_output=True,
            text=True,
        )
        return result, json.loads(result.stdout)

    def test_complete_fresh_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name), reference_driven=True)
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(payload["release_ready"])
        self.assertEqual(payload["errors"], [])

    def test_missing_png_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            (output / "slide-02.png").unlink()
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["release_ready"])
        self.assertTrue(any("slide-02.png" in error for error in payload["errors"]), payload)

    def test_report_does_not_disclose_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            (output / "slide-02.png").unlink()
            result, payload = self.run_checker(spec, output, qa_summary)
            self.assertNotIn(temp_name, result.stdout)
        self.assertEqual(payload["evidence"]["sourcesChecked"], ["carousel.json"])
        self.assertTrue(
            all(path.startswith("output/") for path in payload["evidence"]["artifactsChecked"]),
            payload,
        )
        self.assertEqual(payload["evidence"]["qaSummary"], "qa-summary.md")

    def test_malformed_qa_summary_fails_without_path_disclosure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            qa_summary.write_bytes(b"\xff\xfe\x00")
            result, payload = self.run_checker(spec, output, qa_summary)
            self.assertNotIn(temp_name, result.stdout)
            self.assertNotIn(temp_name, result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["release_ready"])
        self.assertTrue(any("not valid UTF-8" in error for error in payload["errors"]), payload)

    def test_blocked_visual_review_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            qa_summary.write_text("VERDICT: BLOCKED\n\nBLOCKING:\n\n- browser unavailable\n", encoding="utf-8")
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("VERDICT: PASS" in error for error in payload["errors"]), payload)

    def test_stale_render_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            future = time.time() + 20
            os.utime(spec, (future, future))
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("stale" in error.lower() for error in payload["errors"]), payload)

    def test_wrong_png_dimensions_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            write_png_header(output / "slide-01.png", 900, 1350)
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("900x1350" in error for error in payload["errors"]), payload)

    def test_visual_review_older_than_render_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            spec, output, qa_summary = self.make_bundle(Path(temp_name))
            older = time.time() - 30
            os.utime(qa_summary, (older, older))
            result, payload = self.run_checker(spec, output, qa_summary)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("visual QA is stale" in error for error in payload["errors"]), payload)


if __name__ == "__main__":
    unittest.main()
