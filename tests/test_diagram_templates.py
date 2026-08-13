from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = SKILL_DIR / "assets" / "diagrams"
ALLOWED_WIDTHS = {128, 144, 160}
ALLOWED_COLORS = {
    "#f5f4ed",
    "#faf9f5",
    "#141413",
    "#504e49",
    "#6b6a64",
    "#1b365d",
    "#eef2f7",
    "#e8e6dc",
    "#e5e3d8",
}
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b")


class DiagramTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.templates = sorted(DIAGRAM_DIR.glob("*.svg"))
        self.assertTrue(self.templates, "expected diagram SVG templates")

    def test_templates_are_parseable_xml(self) -> None:
        for template in self.templates:
            with self.subTest(template=template.name):
                ET.parse(template)

    def test_rect_geometry_uses_budgeted_grid(self) -> None:
        for template in self.templates:
            root = ET.parse(template).getroot()
            for index, rect in enumerate(root.findall(".//{*}rect")):
                with self.subTest(template=template.name, rect=index):
                    geometry = {name: int(rect.attrib[name]) for name in ("x", "y", "width", "height")}
                    for name, value in geometry.items():
                        self.assertEqual(value % 4, 0, f"{name}={value} is not divisible by 4")
                    self.assertIn(geometry["width"], ALLOWED_WIDTHS)

    def test_hex_colors_use_diagram_tokens(self) -> None:
        for template in self.templates:
            source = template.read_text(encoding="utf-8")
            colors = {color.lower() for color in HEX_COLOR.findall(source)}
            with self.subTest(template=template.name):
                self.assertTrue(colors, "expected at least one hex color")
                self.assertEqual(colors - ALLOWED_COLORS, set())

    def test_templates_mark_editable_data_region(self) -> None:
        for template in self.templates:
            source = template.read_text(encoding="utf-8")
            with self.subTest(template=template.name):
                self.assertIn("<!-- DATA START -->", source)
                self.assertIn("<!-- DATA END -->", source)
                self.assertLess(source.index("<!-- DATA START -->"), source.index("<!-- DATA END -->"))


if __name__ == "__main__":
    unittest.main()
