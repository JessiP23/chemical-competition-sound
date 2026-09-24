import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class DashboardTests(unittest.TestCase):
    def test_start_and_stop(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=15)
        self.assertFalse(app.exception)
        app.button[0].click().run(timeout=15)
        self.assertFalse(app.exception)
        app.button[1].click().run(timeout=15)
        self.assertFalse(app.exception)

if __name__=='__main__': unittest.main()
