
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
import numpy as np
from ScoreBoard import ScoreBoard
from types import SimpleNamespace
class MockImg:
    """אובייקט מזויף עם תמונה ריקה בגודל 200x400"""
    def __init__(self):
        self.img = np.zeros((200, 400, 3), dtype=np.uint8)

class TestScoreBoard(unittest.TestCase):
    def setUp(self):
        self.board = ScoreBoard()
        self.img = MockImg()

    def test_initial_scores_zero(self):
        self.assertEqual(self.board.scoreB, 0)
        self.assertEqual(self.board.scoreW, 0)

    def test_handle_capture_black_gets_white_piece(self):
        event = SimpleNamespace(data={"piece": "PW"})  # לוכד כלי לבן
        self.board.handle_capture(event)
        self.assertEqual(self.board.scoreB, 1)
        self.assertEqual(self.board.scoreW, 0)

    def test_handle_capture_white_gets_black_piece(self):
        event = SimpleNamespace(data={"piece": "RB"})  # לוכד כלי שחור
        self.board.handle_capture(event)
        self.assertEqual(self.board.scoreW, 5)
        self.assertEqual(self.board.scoreB, 0)

    def test_handle_unknown_piece_type(self):
        event = SimpleNamespace(data={"piece": "ZW"})  # כלי לא מוכר
        self.board.handle_capture(event)
        self.assertEqual(self.board.scoreB, 0)
        self.assertEqual(self.board.scoreW, 0)

    def test_multiple_captures_accumulate_score(self):
        events = [
            SimpleNamespace(data={"piece": "PW"}),
            SimpleNamespace(data={"piece": "NW"}),
            SimpleNamespace(data={"piece": "QB"}),
            SimpleNamespace(data={"piece": "BB"}),
        ]
        for e in events:
            self.board.handle_capture(e)
        self.assertEqual(self.board.scoreB, 1 + 3)
        self.assertEqual(self.board.scoreW, 9 + 3)

    def test_draw_black_score_panel_runs(self):
        try:
            self.board.draw_black_score_panel(self.img, x=0, y=0, width=400, height=50)
        except Exception as e:
            self.fail(f"draw_black_score_panel raised an exception: {e}")

    def test_draw_white_score_panel_runs(self):
        try:
            self.board.draw_white_score_panel(self.img, x=0, y=150, width=400, height=50)
        except Exception as e:
            self.fail(f"draw_white_score_panel raised an exception: {e}")

    def test_draw_black_score_panel_text_centered(self):
        self.board.scoreB = 5
        self.board.draw_black_score_panel(self.img, x=0, y=0, width=400, height=50)
        # אין בדיקה מדויקת של פיקסלים, אבל נוודא שהתמונה השתנתה
        self.assertFalse(np.all(self.img.img == 0), "Image should not be completely black after drawing")

    def test_draw_white_score_panel_text_centered(self):
        self.board.scoreW = 8
        self.board.draw_white_score_panel(self.img, x=0, y=150, width=400, height=50)
        self.assertFalse(np.all(self.img.img == 0), "Image should not be completely black after drawing")

if __name__ == "__main__":
    unittest.main()
