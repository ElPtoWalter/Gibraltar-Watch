import tempfile
import unittest
from pathlib import Path

import install_gibraltar_layout_polish as polish


class LayoutPolishInstallerTests(unittest.TestCase):
    def test_installer_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text("<!doctype html><html><head><title>X</title></head><body></body></html>", encoding="utf-8")
            self.assertTrue(polish.update_html(page))
            first = page.read_text(encoding="utf-8")
            self.assertEqual(first.count("gibraltar-layout-polish.css"), 1)
            self.assertFalse(polish.update_html(page))
            second = page.read_text(encoding="utf-8")
            self.assertEqual(second.count("gibraltar-layout-polish.css"), 1)

    def test_existing_version_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(
                '<html><head><link rel="stylesheet" href="gibraltar-layout-polish.css?v=old"></head><body></body></html>',
                encoding="utf-8",
            )
            self.assertTrue(polish.update_html(page))
            text = page.read_text(encoding="utf-8")
            self.assertIn("v=20260829-1", text)
            self.assertEqual(text.count("gibraltar-layout-polish.css"), 1)


if __name__ == "__main__":
    unittest.main()
