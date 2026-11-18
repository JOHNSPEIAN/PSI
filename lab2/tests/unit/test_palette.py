"""Палитры светлой и тёмной темы: полнота токенов и читаемость (WCAG 2.1 AA)."""
import re
import unittest

from ticket_generator.ui.theme import (DARK, LIGHT, PALETTES, blend, color_tokens, contrast_ratio,
                                       header_pill_color)

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Пары «текст — фон», которые реально встречаются в интерфейсе.
TEXT_PAIRS = [
    ("text", "bg"), ("text", "surface"), ("text", "surface_alt"),
    ("text_muted", "bg"), ("text_muted", "surface"), ("text_muted", "surface_alt"),
    ("on_primary", "primary"), ("on_primary", "primary_hover"), ("on_primary", "primary_pressed"),
    ("on_primary_soft", "primary_soft"),
    ("on_success_soft", "success_soft"), ("on_warning_soft", "warning_soft"),
    ("on_danger_soft", "danger_soft"),
    ("on_header", "header_from"), ("on_header", "header_to"),
    ("on_header_muted", "header_from"), ("on_header_muted", "header_to"),
]
AA = 4.5


class PaletteTest(unittest.TestCase):
    def test_registry(self):
        self.assertEqual(set(PALETTES), {"light", "dark"})
        self.assertFalse(LIGHT.is_dark)
        self.assertTrue(DARK.is_dark)

    def test_all_tokens_are_hex_colors(self):
        for palette in PALETTES.values():
            for token, value in color_tokens(palette).items():
                with self.subTest(theme=palette.name, token=token):
                    self.assertRegex(value, HEX)

    def test_text_contrast_meets_wcag_aa(self):
        for palette in PALETTES.values():
            for fg, bg in TEXT_PAIRS:
                with self.subTest(theme=palette.name, pair=f"{fg} / {bg}"):
                    ratio = contrast_ratio(getattr(palette, fg), getattr(palette, bg))
                    self.assertGreaterEqual(ratio, AA, f"{ratio:.2f}")

    def test_header_pill_is_readable(self):
        for palette in PALETTES.values():
            with self.subTest(theme=palette.name):
                self.assertGreaterEqual(contrast_ratio(palette.on_header, header_pill_color(palette)), AA)

    def test_dark_theme_is_actually_dark(self):
        self.assertLess(contrast_ratio(DARK.bg, "#000000"), contrast_ratio(LIGHT.bg, "#000000"))


class ColorMathTest(unittest.TestCase):
    def test_contrast_extremes(self):
        self.assertAlmostEqual(contrast_ratio("#FFFFFF", "#000000"), 21.0, places=1)
        self.assertAlmostEqual(contrast_ratio("#777777", "#777777"), 1.0)

    def test_contrast_is_symmetric(self):
        self.assertAlmostEqual(contrast_ratio("#4F46E5", "#FFFFFF"),
                               contrast_ratio("#FFFFFF", "#4F46E5"))

    def test_blend_endpoints_and_middle(self):
        self.assertEqual(blend("#000000", "#FFFFFF", 0), "#000000")
        self.assertEqual(blend("#000000", "#FFFFFF", 1), "#FFFFFF")
        self.assertEqual(blend("#000000", "#FFFFFF", 0.5), "#808080")


if __name__ == "__main__":
    unittest.main()
