"""Применение темы к ttk.Style, шрифты и масштаб."""
import unittest

from tests.gui_support import requires_display


@requires_display
class ThemeTest(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()

    def test_styles_use_palette_colors_in_both_themes(self):
        from tkinter import ttk

        from ticket_generator.ui.theme import PALETTES, Theme
        style = ttk.Style(self.root)
        for palette in PALETTES.values():
            with self.subTest(theme=palette.name):
                Theme(self.root, palette).apply()
                self.assertEqual(style.lookup("Primary.TButton", "background"), palette.primary)
                self.assertEqual(style.lookup("Card.TFrame", "background"), palette.surface)
                self.assertEqual(style.lookup("Hint.TLabel", "foreground"), palette.text_muted)
                self.assertEqual(style.lookup("Primary.TButton", "background", ["disabled"]),
                                 palette.disabled_bg)
                self.assertEqual(str(self.root.cget("background")), palette.bg)

    def test_combobox_dropdown_colors_come_from_palette(self):
        from tkinter import ttk

        from ticket_generator.ui.theme import DARK, Theme
        Theme(self.root, DARK).apply()
        combo = ttk.Combobox(self.root, values=["IA-2301"])
        popdown = self.root.tk.call("ttk::combobox::PopdownWindow", combo)
        listbox = f"{popdown}.f.l"
        self.assertEqual(str(self.root.tk.call(listbox, "cget", "-background")), DARK.surface)
        self.assertEqual(str(self.root.tk.call(listbox, "cget", "-selectbackground")), DARK.primary)

    def test_scale_and_px(self):
        from ticket_generator.ui.theme import LIGHT, Theme
        theme = Theme(self.root, LIGHT)
        self.assertGreaterEqual(theme.scale, 1.0)
        self.assertEqual(theme.px(0), 0)
        self.assertGreaterEqual(theme.px(10), 10)

    def test_font_family_is_installed(self):
        import tkinter.font as tkfont

        from ticket_generator.ui.theme import Fonts
        fonts = Fonts.resolve(self.root)
        families = set(tkfont.families(self.root)) | {tkfont.nametofont("TkDefaultFont").actual("family")}
        self.assertIn(fonts.family, families)
        self.assertIn(fonts.heading_family, families)


@requires_display
class PlatformTest(unittest.TestCase):
    def test_icon_is_square_image(self):
        import tkinter as tk

        from ticket_generator.ui.platform import make_icon
        from ticket_generator.ui.theme import LIGHT
        root = tk.Tk()
        try:
            icon = make_icon(root, LIGHT, size=16)
            self.assertEqual((icon.width(), icon.height()), (16, 16))
            self.assertTrue(icon.transparency_get(0, 0))  # скруглённый угол прозрачен
            self.assertFalse(icon.transparency_get(8, 8))
        finally:
            root.destroy()

    def test_system_theme_is_known_value(self):
        from ticket_generator.ui.platform import system_theme
        self.assertIn(system_theme(), ("light", "dark"))


if __name__ == "__main__":
    unittest.main()
