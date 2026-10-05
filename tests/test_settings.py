import unittest
from pathlib import Path

from config.settings import BASE_DIR, DB_PATH


class TestPortableConfiguration(unittest.TestCase):
    def test_base_dir_is_project_root(self):
        self.assertEqual(BASE_DIR, Path(__file__).resolve().parents[1])

    def test_db_path_is_inside_project(self):
        self.assertTrue(Path(DB_PATH).is_relative_to(BASE_DIR))


if __name__ == "__main__":
    unittest.main()
