import unittest
from contextlib import redirect_stdout
from io import StringIO

from src.materials_app.main import PROJECT_TITLE, main


class MainTestCase(unittest.TestCase):
    def test_main_prints_project_title(self):
        output = StringIO()
        with redirect_stdout(output):
            result = main()

        self.assertEqual(result.splitlines()[0], PROJECT_TITLE)
        self.assertIn("успешно", output.getvalue())


if __name__ == "__main__":
    unittest.main()

