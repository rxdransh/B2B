"""Smoke-test every Streamlit navigation view."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class StreamlitPageTests(unittest.TestCase):
    def test_every_page_renders_without_exception(self):
        app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
        app.run(timeout=30)
        self.assertFalse(app.exception, [str(item.value) for item in app.exception])

        pages = ["Leads", "Lead Details", "Sales Pipeline", "Follow-ups", "Analytics", "Add Lead"]
        for page in pages:
            with self.subTest(page=page):
                app.radio[0].set_value(page).run(timeout=30)
                self.assertFalse(app.exception, [str(item.value) for item in app.exception])


if __name__ == "__main__":
    unittest.main()
