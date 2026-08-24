#!/usr/bin/env python3
"""Fail-closed validation for self-contained Huatu ELI5 HTML explainers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VIEWPORTS = (
    ("mobile", 390, 844, "preview-mobile.png"),
    ("desktop", 1365, 768, "preview-desktop.png"),
)
MIN_VISIBLE_TEXT_PX = 12.0
LOADING_ATTRIBUTES = {
    "img": {"src", "srcset"},
    "audio": {"src"},
    "video": {"src", "poster"},
    "source": {"src", "srcset"},
    "track": {"src"},
    "iframe": {"src", "srcdoc"},
    "embed": {"src"},
    "object": {"data"},
    "input": {"src"},
}
FORBIDDEN_ELEMENTS = {"script", "iframe", "frame", "frameset", "object", "embed", "link", "base", "form"}
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
ACTIVE_URL_ATTRIBUTES = {"href", "xlink:href", "action", "formaction", "ping"}
SECRET_PATTERNS = (
    ("private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("JWT-like token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("API/token credential", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]\s*[\"']?[^\s<\"']{8,}")),
    ("bot-style token", re.compile(r"\b\d{8,}:[A-Za-z0-9_-]{20,}\b")),
    ("private identifier", re.compile(r"(?i)\b(?:user|account|chat|device|session)[_-]?id\s*[:=]\s*[A-Za-z0-9_-]{4,}")),
    ("UUID/private identifier", re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b")),
    ("host-local absolute path", re.compile(r"(?:file://|/(?:Users|home|root)/)[^\s<\"']+")),
    ("private network address", re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b")),
    ("QR code", re.compile(r"(?i)\bQR\s*(?:code)?\b|二维码")),
)


class ExplainerParser(HTMLParser):
    """Collect only the structure needed for deterministic static policy checks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype = False
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.stack: list[str] = []
        self.html_lang: str | None = None
        self.viewport_values: list[str] = []
        self.main_count = 0
        self.h1_count = 0
        self.scene_depths: list[int] = []
        self.scenes: list[dict[str, Any]] = []
        self.sources_depths: list[int] = []
        self.source_sections: list[dict[str, Any]] = []
        self.simplification_depths: list[int] = []
        self.simplification_sections: list[dict[str, Any]] = []
        self.style_chunks: list[str] = []
        self._in_style = 0

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value for name, value in attrs}
        self.tags.append((tag, attr_map))
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)
        depth = len(self.stack)
        if tag == "html":
            self.html_lang = attr_map.get("lang")
        elif tag == "meta" and (attr_map.get("name") or "").lower() == "viewport":
            self.viewport_values.append(attr_map.get("content") or "")
        elif tag == "main":
            self.main_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "style":
            self._in_style += 1

        classes = set((attr_map.get("class") or "").split())
        is_scene = tag == "section" and ("scene" in classes or "data-scene" in attr_map)
        if is_scene:
            self.scene_depths.append(depth)
            self.scenes.append({"headings": 0, "visuals": 0, "text": []})
        if self.scene_depths:
            scene = self.scenes[-1]
            if tag in {"h2", "h3"}:
                scene["headings"] += 1
            if tag in {"svg", "figure"}:
                scene["visuals"] += 1

        is_sources = tag in {"section", "footer", "aside"} and (
            "data-sources" in attr_map or attr_map.get("id", "").lower() == "sources"
        )
        if is_sources:
            self.sources_depths.append(depth)
            self.source_sections.append({"text": []})
        is_simplification = tag in {"section", "aside"} and (
            "data-simplification" in attr_map or attr_map.get("id", "").lower() == "simplification"
        )
        if is_simplification:
            self.simplification_depths.append(depth)
            self.simplification_sections.append({"text": []})

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        depth = len(self.stack)
        if tag == "style" and self._in_style:
            self._in_style -= 1
        if self.scene_depths and depth == self.scene_depths[-1]:
            self.scene_depths.pop()
        if self.sources_depths and depth == self.sources_depths[-1]:
            self.sources_depths.pop()
        if self.simplification_depths and depth == self.simplification_depths[-1]:
            self.simplification_depths.pop()
        if tag in self.stack:
            while self.stack:
                opened = self.stack.pop()
                if opened == tag:
                    break

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.style_chunks.append(data)
        normalized = " ".join(data.split())
        if not normalized:
            return
        if self.scene_depths:
            self.scenes[-1]["text"].append(normalized)
        if self.sources_depths:
            self.source_sections[-1]["text"].append(normalized)
        if self.simplification_depths:
            self.simplification_sections[-1]["text"].append(normalized)


def _is_unsafe_url(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    lowered = re.sub(r"[\x00-\x20]+", "", value).lower()
    if lowered.startswith(("javascript:", "vbscript:", "data:", "file:")):
        return True
    parsed = urlparse(value)
    return bool(parsed.scheme or parsed.netloc or value.startswith("//"))


def validate_html_text(text: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    parser = ExplainerParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        return [f"HTML parsing failed: {exc}"], {}

    if not parser.doctype:
        errors.append("Missing <!doctype html> declaration")
    if not parser.html_lang or not parser.html_lang.strip():
        errors.append("The html element must declare a non-empty lang attribute")
    if not any("width=device-width" in value.replace(" ", "").lower() for value in parser.viewport_values):
        errors.append("Missing responsive viewport meta with width=device-width")
    if parser.main_count != 1:
        errors.append(f"Expected exactly one main element; found {parser.main_count}")
    if parser.h1_count != 1:
        errors.append(f"Expected exactly one h1; found {parser.h1_count}")
    if not 3 <= len(parser.scenes) <= 7:
        errors.append(f"Expected 3–7 scene sections; found {len(parser.scenes)}")
    for index, scene in enumerate(parser.scenes, start=1):
        if scene["headings"] != 1:
            errors.append(f"Scene {index} must contain exactly one h2 or h3 heading")
        if scene["visuals"] == 0:
            errors.append(f"Scene {index} is missing a visual teaching element (figure or svg)")
        if not " ".join(scene["text"]).strip():
            errors.append(f"Scene {index} has no explanatory text")
    if len(parser.source_sections) != 1 or not " ".join(
        parser.source_sections[0]["text"] if parser.source_sections else []
    ).strip():
        errors.append("Expected one non-empty sources section marked data-sources or id=sources")
    if len(parser.simplification_sections) != 1 or not " ".join(
        parser.simplification_sections[0]["text"] if parser.simplification_sections else []
    ).strip():
        errors.append(
            "Expected one non-empty simplification boundary marked data-simplification or id=simplification"
        )

    for tag, attrs in parser.tags:
        if tag in FORBIDDEN_ELEMENTS:
            errors.append(f"Forbidden active/external element: <{tag}>")
        if tag == "meta" and (attrs.get("http-equiv") or "").lower() == "refresh":
            errors.append("Meta refresh is forbidden")
        for name, raw_value in attrs.items():
            value = raw_value or ""
            if name.startswith("on"):
                errors.append(f"Inline event handler is forbidden: {name}")
            if name == "style" and re.search(r"(?i)@import|url\s*\(", value):
                errors.append("Inline style contains an external-capable @import or url()")
            if name in LOADING_ATTRIBUTES.get(tag, set()):
                errors.append(f"External-capable resource attribute is forbidden: <{tag} {name}>")
            if name in ACTIVE_URL_ATTRIBUTES and value and not value.lstrip().startswith("#"):
                errors.append(f"Non-fragment navigation/resource URL is forbidden: <{tag} {name}>")
            if _is_unsafe_url(value):
                errors.append(f"Unsafe URL scheme or remote reference in <{tag} {name}>")
        if tag == "svg":
            role = (attrs.get("role") or "").lower()
            if role != "img" or not (attrs.get("aria-label") or attrs.get("aria-labelledby")):
                errors.append("Every svg must use role=img and an accessible name")

    css = "\n".join(parser.style_chunks)
    if re.search(r"(?i)@import|url\s*\(", css):
        errors.append("Inline CSS must not contain @import or url()")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"Potentially unsafe private content detected: {label}")

    # Stable ordering without repeated noise from the same malformed attribute.
    errors = list(dict.fromkeys(errors))
    facts = {
        "lang": parser.html_lang,
        "sceneCount": len(parser.scenes),
        "mainCount": parser.main_count,
        "h1Count": parser.h1_count,
        "sourcesPresent": len(parser.source_sections) == 1,
        "simplificationBoundaryPresent": len(parser.simplification_sections) == 1,
        "inlineStyleBlockCount": sum(1 for tag, _ in parser.tags if tag == "style"),
        "inlineSvgCount": sum(1 for tag, _ in parser.tags if tag == "svg"),
    }
    return errors, facts


def validate_html_file(path: Path) -> tuple[list[str], dict[str, Any]]:
    if not path.is_file():
        return [f"HTML file does not exist: {path.name}"], {}
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"HTML is not valid UTF-8: {path.name}"], {}
    except OSError:
        return [f"Could not read HTML: {path.name}"], {}
    return validate_html_text(text)


def browser_candidates(playwright: Any, explicit: str | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    elif os.environ.get("CHROME_BIN"):
        candidates.append(Path(os.environ["CHROME_BIN"]).expanduser())
    candidates.extend(
        [
            Path(playwright.chromium.executable_path),
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/chromium"),
            Path("/usr/bin/chromium-browser"),
        ]
    )
    return candidates


def choose_browser(playwright: Any, explicit: str | None) -> Path | None:
    return next((path for path in browser_candidates(playwright, explicit) if path.is_file()), None)


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("invalid PNG signature")
        length = struct.unpack(">I", handle.read(4))[0]
        if handle.read(4) != b"IHDR" or length != 13:
            raise ValueError("missing PNG IHDR")
        return struct.unpack(">II", handle.read(8))


def _safe_request_label(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme or 'unknown'}://{host}{port}"


def _viewport_metrics(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """
        (minimumTextSize) => {
          const root = document.documentElement;
          const body = document.body;
          const viewportWidth = root.clientWidth;
          const documentWidth = Math.max(root.scrollWidth, body ? body.scrollWidth : 0);
          const overflowElements = Array.from(document.querySelectorAll('body *')).flatMap((element) => {
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0 ||
                rect.width === 0 || rect.height === 0) return [];
            if (rect.left < -1 || rect.right > viewportWidth + 1 || element.scrollWidth > element.clientWidth + 1) {
              return [{
                element: element.id ? `#${element.id}` : element.classList.length
                  ? `${element.tagName.toLowerCase()}.${Array.from(element.classList).slice(0, 2).join('.')}`
                  : element.tagName.toLowerCase(),
                left: Math.round(rect.left),
                right: Math.round(rect.right),
                clientWidth: element.clientWidth,
                scrollWidth: element.scrollWidth
              }];
            }
            return [];
          }).slice(0, 20);

          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          const smallText = [];
          while (walker.nextNode()) {
            const node = walker.currentNode;
            const text = node.textContent.replace(/\\s+/g, ' ').trim();
            if (!text) continue;
            const parent = node.parentElement;
            const style = getComputedStyle(parent);
            if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) continue;
            const range = document.createRange();
            range.selectNodeContents(node);
            if (!Array.from(range.getClientRects()).some(rect => rect.width > 0 && rect.height > 0)) continue;
            const fontSize = parseFloat(style.fontSize);
            if (fontSize < minimumTextSize) {
              smallText.push({fontSize: Number(fontSize.toFixed(2)), text: text.slice(0, 80)});
              if (smallText.length >= 20) break;
            }
          }
          return {
            documentWidth,
            viewportWidth,
            documentHeight: Math.max(root.scrollHeight, body ? body.scrollHeight : 0),
            horizontalOverflow: documentWidth > viewportWidth + 1,
            overflowElements,
            minimumVisibleTextPx: minimumTextSize,
            smallText
          };
        }
        """,
        MIN_VISIBLE_TEXT_PX,
    )


def run_browser_validation(
    html_path: Path,
    output_dir: Path,
    browser_path: str | None,
    static_facts: dict[str, Any],
) -> dict[str, Any]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Python Playwright is unavailable. Install it in the active Python environment."
        ) from exc

    report: dict[str, Any] = {
        "valid": False,
        "structurally_valid": True,
        "browser_valid": False,
        "visual_review_required": True,
        "visually_approved": False,
        "source": html_path.name,
        "static": static_facts,
        "viewports": [],
        "unsafeRequestAttempts": [],
        "browserErrors": [],
        "errors": [],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            executable = choose_browser(playwright, browser_path)
            if executable is None:
                raise RuntimeError(
                    "No Chromium browser was found. Set CHROME_BIN or pass --browser with an executable path."
                )
            report["browser"] = executable.name
            browser = playwright.chromium.launch(executable_path=str(executable), headless=True)
            for name, width, height, screenshot_name in VIEWPORTS:
                context = browser.new_context(
                    viewport={"width": width, "height": height}, device_scale_factor=1
                )
                unsafe_requests: list[str] = []
                browser_errors: list[str] = []

                def route_request(route: Any) -> None:
                    parsed = urlparse(route.request.url)
                    if parsed.scheme not in {"file", "about"}:
                        unsafe_requests.append(_safe_request_label(route.request.url))
                        route.abort()
                    else:
                        route.continue_()

                context.route("**/*", route_request)
                page = context.new_page()
                page.on("pageerror", lambda error: browser_errors.append(str(error)))
                page.on("crash", lambda: browser_errors.append("Page crashed"))
                page.on(
                    "websocket",
                    lambda socket: unsafe_requests.append(
                        f"websocket:{_safe_request_label(socket.url)}"
                    ),
                )
                page.goto(html_path.resolve().as_uri(), wait_until="load", timeout=30_000)
                page.evaluate("() => document.fonts.ready")
                metrics = _viewport_metrics(page)
                screenshot_path = output_dir / screenshot_name
                page.screenshot(path=str(screenshot_path), full_page=True, animations="disabled")
                if not screenshot_path.is_file() or screenshot_path.stat().st_size < 1024:
                    report["errors"].append(f"{name}: screenshot is missing or unexpectedly empty")
                    screenshot_meta: dict[str, Any] = {"file": screenshot_name, "bytes": 0}
                else:
                    png_width, png_height = _png_dimensions(screenshot_path)
                    screenshot_meta = {
                        "file": screenshot_name,
                        "bytes": screenshot_path.stat().st_size,
                        "width": png_width,
                        "height": png_height,
                        "sha256": hashlib.sha256(screenshot_path.read_bytes()).hexdigest(),
                    }
                result = {
                    "name": name,
                    "viewport": {"width": width, "height": height},
                    **metrics,
                    "unsafeRequestAttempts": unsafe_requests,
                    "browserErrors": browser_errors,
                    "screenshot": screenshot_meta,
                }
                report["viewports"].append(result)
                report["unsafeRequestAttempts"].extend(unsafe_requests)
                report["browserErrors"].extend(browser_errors)
                if metrics["horizontalOverflow"] or metrics["overflowElements"]:
                    report["errors"].append(f"{name}: horizontal overflow detected")
                if metrics["smallText"]:
                    report["errors"].append(
                        f"{name}: visible text below {MIN_VISIBLE_TEXT_PX:g}px detected"
                    )
                if unsafe_requests:
                    report["errors"].append(f"{name}: unsafe external request attempt detected")
                if browser_errors:
                    report["errors"].append(f"{name}: browser error detected")
                context.close()
            browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(f"Browser validation failed: {exc}") from exc

    report["errors"] = list(dict.fromkeys(report["errors"]))
    report["browser_valid"] = not report["errors"]
    report["valid"] = report["browser_valid"]
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a self-contained Huatu ELI5 explainer HTML file"
    )
    parser.add_argument("html", help="Path to the explainer HTML file")
    parser.add_argument(
        "--output-dir", default="explainer-qa", help="Directory for qa.json and preview PNGs"
    )
    parser.add_argument("--browser", help="Optional Chromium/Chrome executable path")
    parser.add_argument(
        "--check-only", action="store_true", help="Run static preflight without launching a browser"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    html_path = Path(args.html).expanduser().resolve()
    errors, facts = validate_html_file(html_path)
    preflight = {
        "valid": not errors,
        "structurally_valid": not errors,
        "check_only": bool(args.check_only),
        "source": html_path.name,
        "static": facts,
        "errors": errors,
    }
    if errors or args.check_only:
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return 0 if not errors else 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for owned_name in ("qa.json", "preview-mobile.png", "preview-desktop.png"):
        owned_path = output_dir / owned_name
        if owned_path.is_file():
            owned_path.unlink()
    try:
        report = run_browser_validation(html_path, output_dir, args.browser, facts)
    except (RuntimeError, OSError, ValueError) as exc:
        failure = {**preflight, "valid": False, "browser_valid": False, "errors": [str(exc)]}
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "qa.json").write_text(
            json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(failure, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    (output_dir / "qa.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
