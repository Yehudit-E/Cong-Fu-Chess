import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Board import Board
from mock_img import MockImg


@pytest.fixture
def board():
    """Return a standard 8x8 board with known pixel and meter sizes."""
    return Board(
        cell_H_pix=60,
        cell_W_pix=60,
        cell_H_m=1,
        cell_W_m=1,
        W_cells=8,
        H_cells=8,
        img=MockImg()
    )


def test_clone_returns_deep_copy(board):
    """Test that clone returns a new Board object with equal but separate data."""
    cloned = board.clone()
    assert isinstance(cloned, Board)
    assert cloned is not board
    assert cloned.img is not board.img 
    
    assert cloned.cell_H_pix == board.cell_H_pix
    assert cloned.cell_W_pix == board.cell_W_pix
    assert cloned.cell_H_m == board.cell_H_m
    assert cloned.cell_W_m == board.cell_W_m
    assert cloned.W_cells == board.W_cells
    assert cloned.H_cells == board.H_cells


def test_cell_to_world_returns_correct_pixel_position(board):
    """Test that cell_to_world returns top-left pixel coordinates of a given cell."""
    x, y = board.cell_to_world((3, 5))  # row=3, col=5
    assert x == 5 * board.cell_W_pix
    assert y == 3 * board.cell_H_pix


def test_cell_to_world_on_zero_cell(board):
    """Test cell_to_world for (0, 0) returns (0, 0)."""
    assert board.cell_to_world((0, 0)) == (0, 0)


def test_world_to_cell_maps_pixel_to_correct_cell(board):
    """Test that world_to_cell converts pixel position to the correct cell indices."""
    row, col = board.world_to_cell((150, 120))
    assert (row, col) == (2, 2)  # y // 60 = 2, x // 60 = 2


def test_world_to_cell_returns_0_0_for_top_left(board):
    """Test world_to_cell at (0, 0) returns (0, 0)."""
    assert board.world_to_cell((0, 0)) == (0, 0)


def test_world_to_cell_handles_floats_and_rounding(board):
    """Test world_to_cell handles floating point positions correctly."""
    assert board.world_to_cell((59.9, 59.9)) == (0, 0)
    assert board.world_to_cell((60.1, 60.1)) == (1, 1)


def test_algebraic_to_cell_standard_cases(board):
    """Test algebraic_to_cell on standard inputs like a1, h8."""
    assert board.algebraic_to_cell("a1") == (7, 0)
    assert board.algebraic_to_cell("h8") == (0, 7)
    assert board.algebraic_to_cell("e4") == (4, 4)


def test_algebraic_to_cell_is_case_insensitive(board):
    """Test algebraic_to_cell works with uppercase input."""
    assert board.algebraic_to_cell("A1") == (7, 0)
    assert board.algebraic_to_cell("H8") == (0, 7)


def test_algebraic_to_cell_invalid_input_raises():
    """Test that invalid algebraic notation raises ValueError or IndexError."""
    b = Board(60, 60, 1, 1, 8, 8, MockImg())
    with pytest.raises(ValueError):
        b.algebraic_to_cell("1a")  # wrong format
    with pytest.raises(ValueError):
        b.algebraic_to_cell("z9")  # invalid rank/file
    with pytest.raises(ValueError):
        b.algebraic_to_cell("a")  # too short
    with pytest.raises(ValueError):
        b.algebraic_to_cell("a9")


def test_cell_to_algebraic_standard_cases(board):
    """Test cell_to_algebraic converts cell to correct notation."""
    assert board.cell_to_algebraic((7, 0)) == "a1"
    assert board.cell_to_algebraic((0, 7)) == "h8"
    assert board.cell_to_algebraic((3, 3)) == "d5"


def test_cell_to_algebraic_min_and_max_bounds(board):
    """Test edge values of cells are converted properly."""
    assert board.cell_to_algebraic((0, 0)) == "a8"
    assert board.cell_to_algebraic((7, 7)) == "h1"


def test_cell_to_algebraic_negative_index(board):
    """Test behavior when negative cell indices are passed (not expected)."""
    result = board.cell_to_algebraic((-1, -1))
    assert result == "`9"  # this is how chr works for col=-1, row=-1


def test_cell_to_world_large_cell_size():
    """Test cell_to_world works for large pixel sizes."""
    b = Board(100, 150, 1, 1, 8, 8, MockImg())
    assert b.cell_to_world((2, 3)) == (3 * 150, 2 * 100)


def test_world_to_cell_with_large_pixels():
    """Test world_to_cell works with large pixel size board."""
    b = Board(100, 150, 1, 1, 8, 8, MockImg())
    assert b.world_to_cell((301, 201)) == (2, 2)  # floor division
