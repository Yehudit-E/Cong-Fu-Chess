import pytest
import time
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from GameMessages import GameMessages
from mock_img import MockImg 

class DummyEvent:
    """Simple dummy Event for testing."""
    def __init__(self, event_type, data=None):
        self.type = event_type
        self.data = data or {}

@pytest.fixture
def gm():
    """Return a fresh GameMessages instance for each test."""
    return GameMessages()

def test_set_messages_updates_texts(gm):
    """Test that set_messages updates start and end messages correctly."""
    gm.set_messages("Start now", "White wins!", "Black wins!", "No winner")
    assert gm.start_message == "Start now"
    assert gm.end_messages["white"] == "White wins!"
    assert gm.end_messages["black"] == "Black wins!"
    assert gm.end_messages["draw"] == "No winner"

def test_handle_game_start_sets_start_message_and_flags(gm):
    """Test handle_game_start sets start message and show_message flag."""
    event = DummyEvent("game_start")
    gm.handle_game_start(event)
    assert gm.show_message is True
    assert gm.current_message == gm.start_message
    assert gm.is_end_message is False
    assert gm.message_start_time is not None

def test_handle_game_end_sets_correct_message_and_image_for_winner(gm):
    """Test handle_game_end sets correct message and image depending on winner."""
    for winner, attr in [("white", "white_win_bg"), ("black", "black_win_bg"), ("draw", "draw_bg")]:
        event = DummyEvent("game_end", {"winner": winner})
        gm.handle_game_end(event)
        assert gm.show_message is True
        assert gm.current_message == gm.end_messages[winner]
        assert gm.current_image is getattr(gm, attr)
        assert gm.is_end_message is True
        assert gm.message_start_time is not None

def test_handle_game_end_defaults_to_draw_for_unknown_winner(gm):
    """Test handle_game_end defaults to draw message if winner is unknown."""
    event = DummyEvent("game_end", {"winner": "unknown"})
    gm.handle_game_end(event)
    assert gm.current_message == gm.end_messages["draw"]
    assert gm.current_image == gm.draw_bg

def test_show_timed_message_sets_correct_state(gm):
    """Test show_timed_message sets current_message, flags, and start time."""
    gm.show_timed_message("Hello", is_end=True)
    assert gm.current_message == "Hello"
    assert gm.show_message is True
    assert gm.is_end_message is True
    assert gm.message_start_time is not None

def test_update_turns_off_message_after_duration(gm):
    """Test update disables message after duration has elapsed."""
    gm.show_timed_message("Hello", is_end=False)
    gm.message_start_time -= (gm.message_duration + 1)
    gm.update()
    assert gm.show_message is False
    assert gm.current_message is None
    assert gm.current_image is None
    assert gm.message_start_time is None
    assert gm.is_end_message is False

def test_update_turns_off_end_message_after_end_duration(gm):
    """Test update disables end message after end_message_duration has elapsed."""
    gm.show_timed_message("Goodbye", is_end=True)
    gm.message_start_time -= (gm.end_message_duration + 1)
    gm.update()
    assert gm.show_message is False
    assert gm.current_message is None

def test_update_does_nothing_if_message_not_shown(gm):
    """Test update does nothing if show_message is False."""
    gm.show_message = False
    prev_msg = gm.current_message
    gm.update()
    assert gm.current_message == prev_msg  # unchanged

@patch("cv2.putText")
@patch("cv2.addWeighted")
@patch("cv2.rectangle")
@patch("cv2.resize")
def test_draw_message_shows_nothing_if_no_message(mock_resize, mock_rectangle, mock_addWeighted, mock_putText, gm):
    """Test draw_message does nothing if show_message is False."""
    gm.show_message = False
    img = MockImg()
    gm.draw_message(img)
    # No drawing calls expected
    assert mock_resize.call_count == 0
    assert mock_rectangle.call_count == 0
    assert mock_addWeighted.call_count == 0
    assert mock_putText.call_count == 0

@patch("cv2.putText")
@patch("cv2.addWeighted")
@patch("cv2.rectangle")
@patch("cv2.resize")
def test_draw_message_draws_end_message_with_blinking_text(mock_resize, mock_rectangle, mock_addWeighted, mock_putText, gm):
    """Test draw_message draws end message background and blinking text."""
    gm.show_message = True
    gm.is_end_message = True
    gm.current_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
    gm.current_message = "Test End"
    img = MockImg()
    img.img = np.zeros((50, 50, 3), dtype=np.uint8)
    mock_resize.return_value = img.img

    with patch.object(gm, "_draw_blinking_text") as mock_blink:
        gm.draw_message(img)
        mock_resize.assert_called_once()
        mock_blink.assert_called_once_with(img, "Test End")

@patch("cv2.putText")
@patch("cv2.addWeighted")
@patch("cv2.rectangle")
def test__draw_start_message_draws_expected(mock_rectangle, mock_addWeighted, mock_putText, gm):
    """Test that _draw_start_message renders a start message with background and text."""
    img = MockImg()
    img.img = np.zeros((100, 200, 3), dtype=np.uint8)
    gm._draw_start_message(img, "Start Message")

    # Expect at least two rectangles (background and border)
    assert mock_rectangle.call_count >= 2
    # Expect at least two putText calls (shadow + main text)
    assert mock_putText.call_count >= 2
    # Expect one addWeighted call for transparency blending
    assert mock_addWeighted.call_count == 1

@patch("cv2.putText")
@patch("cv2.addWeighted")
def test__draw_blinking_text_draws_text_with_alpha(mock_addWeighted, mock_putText, gm):
    """Test that _draw_blinking_text draws text with shadow and blends with alpha."""
    img = MockImg()
    img.img = np.zeros((100, 200, 3), dtype=np.uint8)
    gm.message_start_time = time.time() - 1  # set start time so blinking runs

    gm.current_message = "Blinking!"
    gm._draw_blinking_text(img, "Blinking!")

    # Expect calls to putText twice (shadow and main)
    assert mock_putText.call_count == 2
    # Expect one call to addWeighted to blend text with image
    assert mock_addWeighted.call_count == 1

def test_draw_message_calls_start_message_for_non_end(gm):
    """Test draw_message calls _draw_start_message when is_end_message is False."""
    gm.show_message = True
    gm.is_end_message = False
    gm.current_message = "Opening"
    img = MockImg()

    with patch.object(gm, "_draw_start_message") as mock_start:
        gm.draw_message(img)
        mock_start.assert_called_once_with(img, "Opening")

def test_draw_message_returns_without_message_start_time(gm):
    """Test _draw_blinking_text returns immediately if message_start_time is None."""
    img = MockImg()
    gm.message_start_time = None
    # Should not raise or do anything
    gm._draw_blinking_text(img, "Test")
    # No exception means pass

def test_handle_game_start_prints_and_sets_message(capsys, gm):
    """Test handle_game_start prints message and sets flags."""
    event = DummyEvent("game_start")
    gm.handle_game_start(event)
    captured = capsys.readouterr()
    assert "Game start event received!" in captured.out
    assert gm.show_message is True

def test_handle_game_end_prints_and_sets_message(capsys, gm):
    """Test handle_game_end prints message and sets flags."""
    event = DummyEvent("game_end", {"winner": "white"})
    gm.handle_game_end(event)
    captured = capsys.readouterr()
    assert "🏁 Game end event received!" in captured.out
    assert gm.show_message is True

# Edge case: zero-duration messages
def test_show_timed_message_with_zero_duration(gm):
    """Test message disappears immediately if duration is zero."""
    gm.message_duration = 0
    gm.show_timed_message("Instant")
    time.sleep(0.01)
    gm.update()
    assert gm.show_message is False

def test_show_timed_message_with_zero_end_duration(gm):
    """Test end message disappears immediately if end duration is zero."""
    gm.end_message_duration = 0
    gm.show_timed_message("Instant end", is_end=True)
    time.sleep(0.01)
    gm.update()
    assert gm.show_message is False
