from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
CHECKER_PATH = SKILL_DIR / "scripts" / "check_explainer.py"
SPEC = importlib.util.spec_from_file_location("check_explainer", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def valid_html() -> str:
    scenes = "".join(
        f"""
        <section class="scene" data-scene="{index}">
          <h2>概念 {index}</h2>
          <figure>
            <svg role="img" aria-label="概念 {index} 的流程图" viewBox="0 0 100 40">
              <rect x="1" y="1" width="98" height="38" rx="8"></rect>
              <text x="50" y="24">{index}</text>
            </svg>
            <figcaption>一张图只解释一个概念。</figcaption>
          </figure>
        </section>
        """
        for index in range(1, 4)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>测试解释器</title>
  <style>* {{ box-sizing: border-box; }} body {{ margin: 0; font-size: 16px; }}</style>
</head>
<body>
  <header><h1>它是怎么工作的？</h1></header>
  <main>{scenes}</main>
  <aside id="simplification" data-simplification><h2>简化边界</h2><p>箭头只表示概念流向，不代表具体协议。</p></aside>
  <footer id="sources" data-sources><h2>来源</h2><ul><li>测试事实说明，2026。</li></ul></footer>
</body>
</html>"""


class StaticValidationTests(unittest.TestCase):
    def test_valid_self_contained_explainer_passes(self) -> None:
        errors, facts = checker.validate_html_text(valid_html())
        self.assertEqual(errors, [])
        self.assertEqual(facts["sceneCount"], 3)
        self.assertTrue(facts["sourcesPresent"])
        self.assertTrue(facts["simplificationBoundaryPresent"])

    def test_shipped_starter_and_examples_pass_static_validation(self) -> None:
        shipped_files = {
            "assets/eli5-explainer-starter.html": 3,
            "examples/eli5-moshi-hook.html": 5,
            "examples/eli5-moshi-browser-preview.html": 5,
        }
        for relative_path, expected_scenes in shipped_files.items():
            with self.subTest(path=relative_path):
                errors, facts = checker.validate_html_file(SKILL_DIR / relative_path)
                self.assertEqual(errors, [])
                self.assertEqual(facts["sceneCount"], expected_scenes)

    def test_remote_resource_is_rejected(self) -> None:
        html = valid_html().replace("</figure>", '<img src="https://example.com/a.png"></figure>', 1)
        errors, _ = checker.validate_html_text(html)
        self.assertTrue(any("resource attribute" in error for error in errors), errors)
        self.assertTrue(any("remote reference" in error for error in errors), errors)

    def test_script_and_inline_handler_are_rejected(self) -> None:
        html = valid_html().replace(
            "<main>", '<main onclick="alert(1)"><script>document.body.dataset.bad = 1</script>', 1
        )
        errors, _ = checker.validate_html_text(html)
        self.assertTrue(any("<script>" in error for error in errors), errors)
        self.assertTrue(any("event handler" in error for error in errors), errors)

    def test_source_less_media_elements_are_rejected(self) -> None:
        snippets = {
            "audio": "<audio></audio>",
            "video": "<video></video>",
            "img": "<img>",
            "picture": "<picture></picture>",
            "source": "<source>",
            "track": "<track>",
        }
        for tag, snippet in snippets.items():
            with self.subTest(tag=tag):
                html = valid_html().replace("<figure>", f"<figure>{snippet}", 1)
                errors, _ = checker.validate_html_text(html)
                self.assertIn(f"Forbidden media element: <{tag}>", errors)

    def test_svg_namespace_declarations_are_not_remote_resources(self) -> None:
        html = valid_html().replace(
            '<svg role="img"',
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" role="img"',
            1,
        )
        errors, _ = checker.validate_html_text(html)
        self.assertEqual(errors, [])

    def test_self_closing_void_tag_does_not_end_scene_tracking(self) -> None:
        html = valid_html().replace("<h2>概念 1</h2>", "<br/><h2>概念 1</h2>", 1)
        errors, facts = checker.validate_html_text(html)
        self.assertEqual(errors, [])
        self.assertEqual(facts["sceneCount"], 3)

    def test_missing_semantic_sections_fail_closed(self) -> None:
        mutations = {
            "lang": valid_html().replace(' lang="zh-CN"', ""),
            "viewport": valid_html().replace('name="viewport"', 'name="not-viewport"'),
            "main": valid_html().replace("<main>", "<div>").replace("</main>", "</div>"),
            "sources": valid_html().replace(' id="sources" data-sources', ""),
            "boundary": valid_html().replace(' id="simplification" data-simplification', ""),
        }
        expected = {
            "lang": "lang attribute",
            "viewport": "viewport meta",
            "main": "main element",
            "sources": "sources section",
            "boundary": "simplification boundary",
        }
        for name, html in mutations.items():
            with self.subTest(name=name):
                errors, _ = checker.validate_html_text(html)
                self.assertTrue(any(expected[name] in error for error in errors), errors)

    def test_every_scene_needs_heading_and_visual(self) -> None:
        html = valid_html().replace("<h2>概念 1</h2>", "", 1).replace("<figure>", "<div>", 1).replace(
            "</figure>", "</div>", 1
        ).replace('<svg role="img" aria-label="概念 1 的流程图" viewBox="0 0 100 40">', "", 1).replace(
            "</svg>", "", 1
        )
        errors, _ = checker.validate_html_text(html)
        self.assertTrue(any("Scene 1 must contain exactly one" in error for error in errors), errors)
        self.assertTrue(any("Scene 1 is missing" in error for error in errors), errors)

    def test_private_credentials_and_qr_codes_are_rejected(self) -> None:
        html = valid_html().replace("测试事实说明，2026。", "api_key=abcdefghijklmnop；另附二维码。")
        errors, _ = checker.validate_html_text(html)
        self.assertTrue(any("API/token credential" in error for error in errors), errors)
        self.assertTrue(any("QR code" in error for error in errors), errors)

    def test_check_only_cli_is_browser_independent_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            html_path = Path(temp_name) / "valid.html"
            html_path.write_text(valid_html(), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECKER_PATH), str(html_path), "--check-only"],
                capture_output=True,
                text=True,
                env={"PATH": "", "CHROME_BIN": "/definitely/missing/chrome"},
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertTrue(payload["check_only"])
        self.assertNotIn("browser_valid", payload)

    def test_invalid_preflight_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            html_path = Path(temp_name) / "invalid.html"
            html_path.write_text(valid_html().replace("<main>", "<div>").replace("</main>", "</div>"), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECKER_PATH), str(html_path), "--check-only"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["valid"])


class BrowserMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from playwright.sync_api import sync_playwright

            cls.playwright = sync_playwright().start()
            executable = checker.choose_browser(cls.playwright, None)
            if executable is None:
                raise unittest.SkipTest("No Chromium browser available for rendered SVG text test")
            cls.browser = cls.playwright.chromium.launch(
                executable_path=str(executable), headless=True
            )
        except unittest.SkipTest:
            if hasattr(cls, "playwright"):
                cls.playwright.stop()
            raise
        except Exception as exc:
            if hasattr(cls, "playwright"):
                cls.playwright.stop()
            raise unittest.SkipTest(f"Chromium unavailable for rendered SVG text test: {exc}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()

    def test_svg_text_uses_effective_size_after_viewbox_scaling(self) -> None:
        page = self.browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(
                '<!doctype html><body><svg width="200" viewBox="0 0 400 100">'
                '<text x="0" y="40" font-size="20">scaled label</text></svg></body>'
            )
            metrics = checker._viewport_metrics(page)
        finally:
            page.close()
        self.assertEqual(len(metrics["smallText"]), 1)
        self.assertEqual(metrics["smallText"][0]["fontSize"], 20)
        self.assertEqual(metrics["smallText"][0]["effectiveFontSize"], 10)


if __name__ == "__main__":
    unittest.main()
