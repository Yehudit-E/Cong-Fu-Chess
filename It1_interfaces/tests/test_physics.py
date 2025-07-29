import pytest
import sys
import os
from unittest.mock import Mock, patch

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Physics import Physics, IdlePhysics, MovePhysics, JumpPhysics, ShortRestPhysics, LongRestPhysics
from Command import Command
from mock_img import MockImg
from Board import Board


@pytest.fixture
def mock_board():
    """יוצר Board mock לבדיקות"""
    return Board(60, 60, 1, 1, 8, 8, MockImg())


@pytest.fixture
def mock_command():
    """יוצר Command mock לבדיקות"""
    return Mock(spec=Command)


# ────────────────────────────── IdlePhysics Tests ──────────────────────────────

class TestIdlePhysics:
    
    def test_WhenIdlePhysicsCreated_ThenInitializesCorrectly(self, mock_board):
        """בדיקה: יצירת IdlePhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        start_cell = (3, 4)
        speed = 2.0
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics = IdlePhysics(start_cell, mock_board, speed)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == start_cell
        assert physics.board == mock_board
        assert physics.speed == speed * 200  # המהירות מוכפלת ב-200
        assert physics.finished == False
    
    def test_WhenReset_ThenUpdatesStateCorrectly(self, mock_board):
        """בדיקה: איפוס IdlePhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((2, 3), mock_board)
        cmd = Mock()
        cmd.params = [(4, 5)]
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.cmd == cmd
        assert physics.start_cell == (4, 5)
        assert physics.start_time == 0
    
    def test_WhenUpdate_ThenReturnsNone(self, mock_board):
        """בדיקה: עדכון IdlePhysics תמיד מחזיר None"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((2, 3), mock_board)
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = physics.update(1000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result is None
    
    def test_WhenCanBeCaptured_ThenReturnsTrue(self, mock_board):
        """בדיקה: IdlePhysics יכול להיתפס"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((2, 3), mock_board)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.can_be_captured() == True
    
    def test_WhenCanCapture_ThenReturnsTrue(self, mock_board):
        """בדיקה: IdlePhysics יכול לתפוס"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((2, 3), mock_board)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.can_capture() == True


# ────────────────────────────── MovePhysics Tests ──────────────────────────────

class TestMovePhysics:
    
    def test_WhenMovePhysicsCreated_ThenInitializesCorrectly(self, mock_board):
        """בדיקה: יצירת MovePhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        start_cell = (2, 3)
        speed = 1.5
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics = MovePhysics(start_cell, mock_board, speed)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == start_cell
        assert physics.speed == speed * 200
        assert physics.finished == False
        assert physics.extra_delay_ms == 300
    
    def test_WhenReset_ThenCalculatesMovement(self, mock_board):
        """בדיקה: איפוס MovePhysics מחשב תנועה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = MovePhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["a1", "b2"]  # תנועה מa1 לb2
        cmd.piece_id = "test_piece_W"  # הוספת piece_id חוקי
        cmd.timestamp = 1000  # הוספת timestamp
        
        # Mock של board.algebraic_to_cell
        mock_board.algebraic_to_cell = Mock(side_effect=[(7, 0), (6, 1)])
        mock_board.cell_to_world = Mock(side_effect=[(0, 420), (60, 360)])
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.cmd == cmd
        assert physics.start_cell == (7, 0)
        assert physics.end_cell == (6, 1)
        assert physics.finished == False
        mock_board.algebraic_to_cell.assert_any_call("a1")
        mock_board.algebraic_to_cell.assert_any_call("b2")
    
    def test_WhenUpdateBeforeStartTime_ThenSetsStartTime(self, mock_board):
        """בדיקה: עדכון ראשון קובע זמן התחלה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = MovePhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["a1", "a2"]
        cmd.piece_id = "test_piece_B"  # הוספת piece_id חוקי
        cmd.timestamp = 1000  # הוספת timestamp
        
        mock_board.algebraic_to_cell = Mock(side_effect=[(7, 0), (6, 0)])
        mock_board.cell_to_world = Mock(side_effect=[(0, 420), (0, 360)])
        
        physics.reset(cmd)
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = physics.update(1000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_time == 1000
        assert result is None  # עדיין בתנועה
    
    def test_WhenMovementFinished_ThenReturnsCommand(self, mock_board):
        """בדיקה: סיום תנועה מחזיר פקודה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = MovePhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["a1", "a2"]
        cmd.piece_id = "test_piece_B"  # הוספת piece_id חוקי
        cmd.timestamp = 1000  # הוספת timestamp
        
        mock_board.algebraic_to_cell = Mock(side_effect=[(7, 0), (6, 0)])
        mock_board.cell_to_world = Mock(side_effect=[(0, 420), (0, 360)])
        
        physics.reset(cmd)
        physics.update(1000)  # קביעת זמן התחלה
        
        # ─── ACT ──────────────────────────────────────────────────────
        # מדמה זמן לאחר סיום התנועה + השהיה
        result = physics.update(1000 + physics.duration_ms + physics.extra_delay_ms + 100)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == cmd
        assert physics.finished == True


# ────────────────────────────── JumpPhysics Tests ──────────────────────────────

class TestJumpPhysics:
    
    def test_WhenJumpPhysicsCreated_ThenInitializesCorrectly(self, mock_board):
        """בדיקה: יצירת JumpPhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        start_cell = (3, 3)
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics = JumpPhysics(start_cell, mock_board)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == start_cell
        assert physics.board == mock_board
        assert physics.finished == False
    
    def test_WhenCanBeCaptured_ThenReturnsFalse(self, mock_board):
        """בדיקה: JumpPhysics לא יכול להיתפס בזמן קפיצה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = JumpPhysics((2, 3), mock_board)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.can_be_captured() == False
    
    def test_WhenCanCapture_ThenReturnsFalse(self, mock_board):
        """בדיקה: JumpPhysics לא יכול לתפוס בזמן קפיצה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = JumpPhysics((2, 3), mock_board)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.can_capture() == False

    def test_WhenJumpReset_ThenCalculatesJumpPath(self, mock_board):
        """בדיקה: reset מחשב נתיב קפיצה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = JumpPhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["e4", "e6"]
        cmd.piece_id = "test_piece_B"
        cmd.timestamp = 1000
        
        mock_board.algebraic_to_cell = Mock(side_effect=[(4, 4), (2, 4)])
        mock_board.cell_to_world = Mock(side_effect=[(320, 320), (320, 160)])
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == (4, 4)
        assert physics.end_cell == (2, 4)
        assert physics.start_pos == (320, 320)
        assert physics.end_pos == (320, 160)
        assert physics.jump_duration == 1500
        assert physics.start_time is None

    def test_WhenJumpUpdate_BeforeStartTime_ThenSetsStartTime(self, mock_board):
        """בדיקה: עדכון ראשון קובע זמן התחלה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = JumpPhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["e4", "e6"]
        cmd.piece_id = "test_piece_B"
        cmd.timestamp = 1000
        
        mock_board.algebraic_to_cell = Mock(side_effect=[(4, 4), (2, 4)])
        mock_board.cell_to_world = Mock(side_effect=[(320, 320), (320, 160)])
        
        physics.reset(cmd)
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = physics.update(1000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_time == 1000
        assert result is None

    def test_WhenJumpFinished_ThenReturnsShortRestCommand(self, mock_board):
        """בדיקה: סיום קפיצה מחזיר פקודת short_rest"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = JumpPhysics((0, 0), mock_board)
        cmd = Mock()
        cmd.params = ["e4", "e6"]
        cmd.piece_id = "test_piece_B"
        cmd.timestamp = 1000
        
        mock_board.algebraic_to_cell = Mock(side_effect=[(4, 4), (2, 4)])
        mock_board.cell_to_world = Mock(side_effect=[(320, 320), (320, 160)])
        
        physics.reset(cmd)
        physics.update(1000)  # התחלת קפיצה
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = physics.update(2500)  # סיום קפיצה (אחרי 1.5 שניות)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result is not None
        assert result.type == "short_rest"
        assert result.params == [(2, 4), (2, 4)]
        assert physics.pos == (320, 160)  # במיקום הסופי


# ────────────────────────────── ShortRestPhysics Tests ──────────────────────────────

class TestShortRestPhysics:
    
    def test_WhenShortRestPhysicsCreated_ThenInitializesCorrectly(self, mock_board):
        """בדיקה: יצירת ShortRestPhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        start_cell = (1, 2)
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics = ShortRestPhysics(start_cell, mock_board)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == start_cell
        # rest_duration נקבע ב-reset, לא ב-__init__
        assert physics.board == mock_board
        assert physics.finished == False
    
    def test_WhenRestFinished_ThenReturnsCommand(self, mock_board):
        """בדיקה: סיום מנוחה קצרה מחזיר פקודה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = ShortRestPhysics((1, 2), mock_board)
        cmd = Mock()
        cmd.params = [(1, 2)]  # מיקום התחלה
        cmd.piece_id = "test_piece"
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        physics.update(1000)  # קביעת זמן התחלה
        result = physics.update(1000 + physics.rest_duration + 100)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result is not None
        assert result.type == "idle"
        assert result.piece_id == "test_piece"


# ────────────────────────────── LongRestPhysics Tests ──────────────────────────────

class TestLongRestPhysics:
    
    def test_WhenLongRestPhysicsCreated_ThenInitializesCorrectly(self, mock_board):
        """בדיקה: יצירת LongRestPhysics"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        start_cell = (5, 6)
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics = LongRestPhysics(start_cell, mock_board)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.start_cell == start_cell
        # rest_duration נקבע ב-reset, לא ב-__init__
        assert physics.board == mock_board
        assert physics.finished == False
    
    def test_WhenRestFinished_ThenReturnsCommand(self, mock_board):
        """בדיקה: סיום מנוחה ארוכה מחזיר פקודה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = LongRestPhysics((5, 6), mock_board)
        cmd = Mock()
        cmd.params = [(5, 6)]  # מיקום התחלה
        cmd.piece_id = "test_piece_long"
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        physics.update(1000)  # קביעת זמן התחלה
        result = physics.update(1000 + physics.rest_duration + 100)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result is not None
        assert result.type == "idle"
        assert result.piece_id == "test_piece_long"


# ────────────────────────────── Base Physics Tests ──────────────────────────────

class TestBasePhysics:
    
    def test_WhenGetPos_ThenReturnsCorrectPosition(self, mock_board):
        """בדיקה: get_pos מחזיר מיקום נכון"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((2, 3), mock_board)
        
        # ─── ACT ──────────────────────────────────────────────────────
        pos = physics.get_pos()
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert isinstance(pos, tuple)
        assert len(pos) == 2
    
    def test_WhenGetPosInCell_ThenReturnsCell(self, mock_board):
        """בדיקה: get_pos_in_cell מחזיר תא נכון"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = IdlePhysics((3, 4), mock_board)
        mock_board.world_to_cell = Mock(return_value=(3, 4))
        
        # ─── ACT ──────────────────────────────────────────────────────
        cell = physics.get_pos_in_cell()
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert cell == (3, 4)
        mock_board.world_to_cell.assert_called_once_with(physics.pos)
    
    @patch('Physics.event_bus')
    def test_WhenPhysicsCreated_ThenEventBusSet(self, mock_event_bus, mock_board):
        """בדיקה: יצירת Physics קובעת event_bus"""
        # ─── ARRANGE & ACT ────────────────────────────────────────────
        physics = IdlePhysics((1, 1), mock_board)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert physics.event_bus == mock_event_bus
    
    def test_WhenIsAtDestination_WithExactPosition_ThenReturnsTrue(self, mock_board):
        """בדיקה: is_at_destination עם מיקום מדויק"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = MovePhysics((0, 0), mock_board)
        physics.pos = (100, 100)
        physics.end_pos = (100, 100)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.is_at_destination(1.0) == True
    
    def test_WhenIsAtDestination_WithDistantPosition_ThenReturnsFalse(self, mock_board):
        """בדיקה: is_at_destination עם מיקום רחוק"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = MovePhysics((0, 0), mock_board)
        physics.pos = (100, 100)
        physics.end_pos = (200, 200)
        
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert physics.is_at_destination(1.0) == False


# ────────────────────────────── Integration Tests ──────────────────────────────

class TestPhysicsIntegration:
    
    def test_WhenPhysicsChain_ThenStateTransitionsWork(self, mock_board):
        """בדיקה: שרשרת מעברי מצב פיזיקה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        idle = IdlePhysics((2, 2), mock_board)
        move = MovePhysics((2, 2), mock_board)
        
        cmd1 = Mock()
        cmd1.params = ["c3", "d4"]
        cmd1.piece_id = "chain_test_piece"  # הוספת piece_id חוקי
        cmd1.timestamp = 1000  # הוספת timestamp
        
        # ─── ACT ──────────────────────────────────────────────────────
        idle.reset(cmd1)
        move.reset(cmd1)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert idle.cmd == cmd1
        assert move.cmd == cmd1
        assert not idle.finished
        assert not move.finished
    
    def test_WhenMultiplePhysicsUpdates_ThenTimingIsCorrect(self, mock_board):
        """בדיקה: עדכונים מרובים עם תזמון נכון"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        physics = ShortRestPhysics((1, 1), mock_board)
        cmd = Mock()
        cmd.params = [(1, 1)]
        cmd.piece_id = "timing_test"
        
        # ─── ACT ──────────────────────────────────────────────────────
        physics.reset(cmd)
        result1 = physics.update(1000)  # התחלה
        result2 = physics.update(1100)  # באמצע
        result3 = physics.update(1000 + physics.rest_duration + 100)  # סיום
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result1 is None
        assert result2 is None  
        assert result3 is not None
        assert result3.type == "idle"
