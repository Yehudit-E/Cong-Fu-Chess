import pytest
from unittest.mock import MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PhysicsFactory import PhysicsFactory
from Board import Board
from Physics import IdlePhysics, MovePhysics, JumpPhysics, ShortRestPhysics, LongRestPhysics

@pytest.fixture
def mock_board():
    """Fixture to create a mock Board instance."""
    return MagicMock(spec=Board)

@pytest.fixture
def factory(mock_board):
    """Fixture to create a PhysicsFactory with a mock board."""
    return PhysicsFactory(board=mock_board)

@pytest.mark.parametrize("state_class, state_name", [
    (IdlePhysics, "idle"),
    (MovePhysics, "move"),
    (JumpPhysics, "jump"),
    (ShortRestPhysics, "short_rest"),
    (LongRestPhysics, "long_rest")
])
def test_create_physics_valid_states(factory, state_class, state_name):
    """
    Test that PhysicsFactory creates the correct physics object type
    for each valid state.
    """
    cfg = {"physics": {"speed_m_per_sec": 2.5}}
    obj = factory.create(state_name, start_cell=(0, 0), cfg=cfg)
    assert isinstance(obj, state_class)
    assert obj.speed == 2.5 * 200

def test_create_physics_default_speed(factory):
    """
    Test that PhysicsFactory assigns the default speed (1.0 m/s)
    when speed is not provided in the config.
    """
    cfg = {}  # No 'physics' key
    obj = factory.create("idle", start_cell=(1, 1), cfg=cfg)
    assert isinstance(obj, IdlePhysics)
    assert obj.speed == 1.0 * 200

def test_create_physics_missing_speed_key(factory):
    """
    Test that PhysicsFactory assigns default speed when 'physics' is provided
    but 'speed_m_per_sec' is missing.
    """
    cfg = {"physics": {}}  # Empty physics dict
    obj = factory.create("move", start_cell=(2, 2), cfg=cfg)
    assert isinstance(obj, MovePhysics)
    assert obj.speed == 1.0 * 200

def test_create_physics_invalid_state_raises(factory):
    """
    Test that PhysicsFactory raises a ValueError when an invalid state is passed.
    """
    cfg = {"physics": {"speed_m_per_sec": 3.3}}
    with pytest.raises(ValueError) as exc_info:
        factory.create("fly", start_cell=(3, 3), cfg=cfg)
    assert "Unknown state name: fly" in str(exc_info.value)
