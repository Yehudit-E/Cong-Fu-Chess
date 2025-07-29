import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock, patch
from CommandLog import CommandLog
from Bus.EventBus import Event
import numpy as np

@pytest.fixture
def cmd_log():
    """Create a fresh CommandLog instance for each test."""
    return CommandLog()


def make_event(piece_id="PW", desc="moved to (3,4)", time_val=123456):
    """Helper to create a mock Event."""
    return Event("piece_command", {
        "piece": piece_id,
        "description": desc,
        "time": time_val
    })


def test_handle_white_command_with_time(cmd_log):
    """Test handling a white piece command with a valid time value."""
    event = make_event("KW", "jumped", 90000)  # 90 sec
    cmd_log.handle_command(event)

    assert len(cmd_log.white_moves) == 1
    assert "01:30" in cmd_log.white_moves[0]
    assert "KW - jumped" in cmd_log.white_moves[0]


def test_handle_black_command_with_no_time(cmd_log):
    """Test handling a black piece command with no or invalid time."""
    event = Event("piece_command", {
        "piece": "KB", "description": "moved"
    })
    cmd_log.handle_command(event)

    assert len(cmd_log.black_moves) == 1
    assert "00:00" in cmd_log.black_moves[0]
    assert "KB - moved" in cmd_log.black_moves[0]


def test_white_moves_limit(cmd_log):
    """Test that white move history does not exceed 10 items."""
    for i in range(15):
        event = make_event("PW", f"move {i}", 60000)
        cmd_log.handle_command(event)

    assert len(cmd_log.white_moves) == 10
    assert "move 5" in cmd_log.white_moves[0]  # first 5 removed


def test_black_moves_limit(cmd_log):
    """Test that black move history does not exceed 10 items."""
    for i in range(12):
        event = make_event("PB", f"attack {i}", 61000)
        cmd_log.handle_command(event)

    assert len(cmd_log.black_moves) == 10
    assert "attack 2" in cmd_log.black_moves[0]


def test_handle_invalid_piece_field(cmd_log):
    """Test piece ID with invalid format (e.g., too short). Should go to black_moves."""
    event = make_event("P", "strange format", 3000)
    cmd_log.handle_command(event)

    assert len(cmd_log.black_moves) == 1


@patch("cv2.rectangle")
@patch("cv2.putText")
@patch("cv2.line")
def test_draw_moves_panel_calls_cv2(mock_line, mock_put, mock_rect):
    """Test that draw_moves_panel triggers drawing calls when moves are present."""
    cmd_log = CommandLog()
    img = MagicMock()
    moves = [f"00:0{i} | PW - move {i}" for i in range(3)]

    cmd_log.draw_moves_panel(img, 10, 20, 200, 300, moves, "White Moves")

    assert mock_rect.call_count == 2  # background + border
    assert mock_put.call_count >= 4  # title + at least 3 moves
    mock_line.assert_called_once()


@patch("cv2.rectangle")
@patch("cv2.putText")
@patch("cv2.line")
def test_draw_ui_triggers_panels(mock_line, mock_put, mock_rect):
    """Test draw_ui draws both white and black move panels."""
    cmd_log = CommandLog()
    cmd_log.white_moves = ["00:01 | KW - jump"]
    cmd_log.black_moves = ["00:02 | KB - slide"]

    img = MagicMock()
    img.img.shape = (800, 1000, 3)

    cmd_log.draw_ui(img)

    # 2 panels = 2*2 rectangles, 2*putText titles + 2 moves
    assert mock_rect.call_count >= 4
    assert mock_put.call_count >= 4
    assert mock_line.call_count == 2


@patch("cv2.putText")
def test_draw_moves_panel_skips_if_too_many(mock_put):
    """Test draw_moves_panel skips drawing moves if they exceed height."""
    cmd_log = CommandLog()
    dummy_img = np.zeros((200, 300, 3), dtype = np.uint8)
    class DummyImg:
        def __init__(self):
            self.img = dummy_img

    img = DummyImg()
    moves = [f"00:0{i} | PW - move {i}" for i in range(20)]  # way more than fits

    cmd_log.draw_moves_panel(img, 0, 0, 300, 100, moves, "White Moves")

    # Should still draw only max 8 moves that fit
    assert mock_put.call_count <= 9
