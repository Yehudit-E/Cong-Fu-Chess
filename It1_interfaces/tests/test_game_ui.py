import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import MagicMock, patch
from GameUI import GameUI


@pytest.fixture
def mock_dependencies():
    """Patch and return all GameUI dependencies as mocks."""
    with patch("GameUI.CommandLog") as MockCommandLog, \
         patch("GameUI.ScoreBoard") as MockScoreBoard, \
         patch("GameUI.GameMessages") as MockGameMessages, \
         patch("GameUI.GameSounds") as MockGameSounds, \
         patch("GameUI.event_bus") as mock_event_bus:

        yield {
            "CommandLog": MockCommandLog,
            "ScoreBoard": MockScoreBoard,
            "GameMessages": MockGameMessages,
            "GameSounds": MockGameSounds,
            "event_bus": mock_event_bus
        }


def test_game_ui_initialization(mock_dependencies):
    """Test GameUI initializes all components and subscribes to events."""
    GameUI()

    # Assert components were created
    mock_dependencies["CommandLog"].assert_called_once()
    mock_dependencies["ScoreBoard"].assert_called_once()
    mock_dependencies["GameMessages"].assert_called_once()
    mock_dependencies["GameSounds"].assert_called_once()

    # Assert event subscriptions
    subscribe = mock_dependencies["event_bus"].subscribe
    assert subscribe.call_count == 4
    subscribe.assert_any_call("game_start", mock_dependencies["GameMessages"]().handle_game_start)
    subscribe.assert_any_call("game_end", mock_dependencies["GameMessages"]().handle_game_end)
    subscribe.assert_any_call("piece_captured", mock_dependencies["ScoreBoard"]().handle_capture)
    subscribe.assert_any_call("piece_command", mock_dependencies["CommandLog"]().handle_command)


def test_draw_all_ui_calls_all_components(mock_dependencies):
    """Test draw_all_ui triggers all relevant draw methods with correct parameters."""
    # Arrange
    game_ui = GameUI()
    mock_frame = MagicMock()
    mock_frame.img.shape = (800, 600, 3)

    # Act
    game_ui.draw_all_ui(mock_frame)

    # Assert draw methods were called
    game_ui.command_log.draw_ui.assert_called_once_with(mock_frame)
    game_ui.scoreboard.draw_black_score_panel.assert_called_once()
    game_ui.scoreboard.draw_white_score_panel.assert_called_once()
    game_ui.game_messages.draw_message.assert_called_once_with(mock_frame)
    game_ui.game_messages.update.assert_called_once()


def test_draw_all_ui_without_scoreboard(mock_dependencies):
    """Test draw_all_ui works if scoreboard is manually set to None (edge case)."""
    game_ui = GameUI()
    game_ui.scoreboard = None
    mock_frame = MagicMock()
    mock_frame.img.shape = (800, 600, 3)

    game_ui.draw_all_ui(mock_frame)

    game_ui.command_log.draw_ui.assert_called_once()
    game_ui.game_messages.draw_message.assert_called_once()
    game_ui.game_messages.update.assert_called_once()


def test_draw_all_ui_without_command_log(mock_dependencies):
    """Test draw_all_ui works if command_log is manually set to None (edge case)."""
    game_ui = GameUI()
    game_ui.command_log = None
    mock_frame = MagicMock()
    mock_frame.img.shape = (800, 600, 3)

    game_ui.draw_all_ui(mock_frame)

    game_ui.game_messages.draw_message.assert_called_once()
    game_ui.game_messages.update.assert_called_once()
    game_ui.scoreboard.draw_black_score_panel.assert_called_once()
    game_ui.scoreboard.draw_white_score_panel.assert_called_once()


def test_cleanup_calls_game_sounds_cleanup(mock_dependencies):
    """Test cleanup method calls game_sounds.cleanup()."""
    game_ui = GameUI()
    game_ui.cleanup()
    game_ui.game_sounds.cleanup.assert_called_once()


def test_cleanup_handles_missing_game_sounds_gracefully(mock_dependencies):
    """Test cleanup method does nothing if game_sounds attribute is missing."""
    game_ui = GameUI()
    delattr(game_ui, "game_sounds")

    # Should not raise an exception
    game_ui.cleanup()
