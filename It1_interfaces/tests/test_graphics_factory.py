import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import patch, MagicMock
from GraphicsFactory import GraphicsFactory
from Board import Board
import pathlib

class TestGraphicsFactory(unittest.TestCase):
    def setUp(self):
        self.mock_board = MagicMock(spec=Board)
        self.factory = GraphicsFactory(self.mock_board)
        self.mock_sprites_dir = pathlib.Path("/fake/sprites")

    @patch("GraphicsFactory.Graphics")
    def test_load_with_full_config(self, mock_graphics_class):
        config = {
            "graphics": {
                "frames_per_sec": 10.5,
                "is_loop": False
            }
        }

        instance = self.factory.load(self.mock_sprites_dir, config, cell_size=(64, 64))

        mock_graphics_class.assert_called_once_with(
            sprites_folder=self.mock_sprites_dir,
            board=self.mock_board,
            loop=False,
            fps=10.5
        )

    @patch("GraphicsFactory.Graphics")
    def test_load_with_missing_graphics_config(self, mock_graphics_class):
        config = {}  # no "graphics" key
        instance = self.factory.load(self.mock_sprites_dir, config, cell_size=(64, 64))

        mock_graphics_class.assert_called_once_with(
            sprites_folder=self.mock_sprites_dir,
            board=self.mock_board,
            loop=True,          # default
            fps=6.0             # default
        )

    @patch("GraphicsFactory.Graphics")
    def test_load_with_partial_graphics_config(self, mock_graphics_class):
        config = {
            "graphics": {
                "frames_per_sec": 15.0
                # "is_loop" missing
            }
        }
        instance = self.factory.load(self.mock_sprites_dir, config, cell_size=(64, 64))

        mock_graphics_class.assert_called_once_with(
            sprites_folder=self.mock_sprites_dir,
            board=self.mock_board,
            loop=True,          # default
            fps=15.0
        )

    def test_constructor_stores_board(self):
        self.assertEqual(self.factory.board, self.mock_board)

if __name__ == '__main__':
    unittest.main()
