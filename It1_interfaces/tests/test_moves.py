import tempfile
import pathlib
import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Moves import Moves
from unittest.mock import Mock

@pytest.fixture
def valid_rules_file():
    """Fixture for a valid rules file with directional moves (like rook/queen)."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("1,0\n0,1\n-1,0\n0,-1\n")  # Up, right, down, left
        f.flush()
        yield pathlib.Path(f.name)

@pytest.fixture
def invalid_rules_file():
    """Fixture for an invalid rules file (bad formatting)."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("bad_line\n")
        f.flush()
        yield pathlib.Path(f.name)

@pytest.fixture
def piece_factory():
    """Helper to create mock pieces with specified id like 'PW' (white pawn)."""
    def create(piece_id):
        piece = Mock()
        piece.get_id.return_value = piece_id
        return piece
    return create

def test_load_valid_rules(valid_rules_file):
    """Test loading a valid rules file results in correct rule list."""
    moves = Moves(valid_rules_file, (8, 8))
    assert moves.rules == [(1, 0), (0, 1), (-1, 0), (0, -1)]

def test_load_invalid_rules_raises(invalid_rules_file):
    """Test loading an invalid rules file raises a ValueError."""
    with pytest.raises(ValueError):
        Moves(invalid_rules_file, (8, 8))

def test_white_pawn_one_step(piece_factory, valid_rules_file):
    """Test white pawn moves one step forward if the square is empty."""
    moves = Moves(valid_rules_file, (8, 8))
    pos = {(6, 4): piece_factory("PW")}  # White pawn at starting row
    result = moves.get_moves(6, 4, pos)
    assert (5, 4) in result
    assert (4, 4) in result

def test_white_pawn_blocked(piece_factory, valid_rules_file):
    """Test white pawn cannot move forward if the square is occupied."""
    moves = Moves(valid_rules_file, (8, 8))
    pos = {
        (6, 4): piece_factory("PW"),
        (5, 4): piece_factory("PB")
    }
    result = moves.get_moves(6, 4, pos)
    assert (5, 4) not in result
    assert (4, 4) not in result

def test_black_pawn_double_step(piece_factory, valid_rules_file):
    """Test black pawn can move two steps from starting row."""
    moves = Moves(valid_rules_file, (8, 8))
    pos = {(1, 4): piece_factory("PB")}
    result = moves.get_moves(1, 4, pos)
    assert (2, 4) in result
    assert (3, 4) in result

def test_pawn_diagonal_capture(piece_factory, valid_rules_file):
    """Test pawn captures diagonally only if enemy is present."""
    moves = Moves(valid_rules_file, (8, 8))
    pos = {
        (6, 4): piece_factory("PW"),
        (5, 3): piece_factory("PB"),
        (5, 5): piece_factory("PW")  # friendly piece – should not be captured
    }
    result = moves.get_moves(6, 4, pos)
    assert (5, 3) in result
    assert (5, 5) not in result

def test_non_pawn_moves_valid(valid_rules_file, piece_factory):
    """Test non-pawn pieces follow rules and stop on enemy or block on friendly."""
    rules_path = valid_rules_file
    moves = Moves(rules_path, (8, 8))
    pos = {
        (4, 4): piece_factory("QW"),  # queen or any non-pawn white piece
        (3, 4): piece_factory("PB"),  # enemy
        (4, 5): piece_factory("PW")   # friendly
    }
    result = moves.get_moves(4, 4, pos)
    assert (3, 4) in result      # Can capture enemy
    assert (4, 5) not in result  # Can't move onto friendly
    assert (5, 4) in result      # Can move forward (not blocked)
    assert (4, 3) in result      # Can move left

def test_blocked_direction_stops_after_first_piece(valid_rules_file, piece_factory):
    """Test move logic blocks further steps in a direction after a piece is hit."""
    rules_path = valid_rules_file
    moves = Moves(rules_path, (8, 8))
    pos = {
        (4, 4): piece_factory("QW"),
        (3, 4): piece_factory("PB"),
        (2, 4): piece_factory("PB")  # should not be reachable due to blocking
    }
    result = moves.get_moves(4, 4, pos)
    assert (3, 4) in result
    assert (2, 4) not in result

def test_out_of_bounds_moves_are_filtered(valid_rules_file, piece_factory):
    """Test moves that go out of bounds are ignored."""
    rules_path = valid_rules_file
    moves = Moves(rules_path, (8, 8))
    pos = {(0, 0): piece_factory("QW")}
    result = moves.get_moves(0, 0, pos)
    assert all(0 <= r < 8 and 0 <= c < 8 for r, c in result)

def test_get_moves_empty_cell(valid_rules_file):
    """Test get_moves returns empty list for an empty cell (no piece)."""
    moves = Moves(valid_rules_file, (8, 8))
    pos = {}
    result = moves.get_moves(4, 4, pos)
    assert result == []

def test_empty_rules_file_allows_only_pawn_logic(tmp_path, piece_factory):
    """Test fallback to pawn logic when rules file is empty."""
    rules_path = tmp_path / "empty.txt"
    rules_path.write_text("")  # No rules
    moves = Moves(rules_path, (8, 8))
    pos = {(6, 4): piece_factory("PW")}
    result = moves.get_moves(6, 4, pos)
    assert (5, 4) in result
