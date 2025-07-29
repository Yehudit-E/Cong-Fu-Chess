import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Tuple

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Piece import Piece
from Command import Command
from State import State
from mock_img import MockImg
from Board import Board


@pytest.fixture
def mock_state():
    """יוצר State mock לבדיקות"""
    state = Mock(spec=State)
    state.transitions = {"move": Mock(), "idle": Mock()}
    state._physics = Mock()
    state._physics.start_cell = (2, 3)
    state._physics.board = Mock()
    state._physics.board.algebraic_to_cell = Mock(return_value=(4, 5))
    state._physics.finished = False
    state._physics.get_pos = Mock(return_value=(120, 180))
    state._physics.get_pos_in_cell = Mock(return_value=(2, 3))
    state._graphics = Mock()
    state._graphics.get_img = Mock()
    state._graphics.get_img.return_value.img = None
    state._moves = Mock()
    state._moves.get_moves = Mock(return_value=[(4, 5), (3, 4)])
    state.process_command = Mock(return_value=state)
    state.update = Mock(return_value=state)
    state.reset = Mock()
    state.get_command = Mock(return_value=None)
    return state


@pytest.fixture
def mock_board():
    """יוצר Board mock לבדיקות"""
    board = Mock(spec=Board)
    board.img = Mock()
    board.img.img = Mock()
    board.img.img.shape = [480, 640, 3]  # height, width, channels
    return board


@pytest.fixture
def mock_command():
    """יוצר Command mock לבדיקות"""
    cmd = Mock(spec=Command)
    cmd.type = "move"
    cmd.params = ["a1", "b2"]
    cmd.piece_id = "test_piece"
    return cmd


@pytest.fixture
def piece(mock_state):
    """יוצר Piece לבדיקות"""
    return Piece("test_piece", mock_state, 1000)


# ────────────────────────────── Piece Initialization Tests ──────────────────────────────

class TestPieceInitialization:
    
    def test_WhenPieceCreated_ThenInitializesCorrectly(self, mock_state):
        """בדיקה: יצירת Piece"""
        # ─── ARRANGE & ACT ────────────────────────────────────────────
        piece = Piece("my_piece", mock_state, 500)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert piece._id == "my_piece"
        assert piece._state == mock_state
        assert piece._current_cmd is None
    
    def test_WhenGetId_ThenReturnsCorrectId(self, piece):
        """בדיקה: get_id מחזיר ID נכון"""
        # ─── ACT & ASSERT ─────────────────────────────────────────────
        assert piece.get_id() == "test_piece"
    
    def test_WhenGetCommand_ThenDelegatesToState(self, piece, mock_state):
        """בדיקה: get_command מפנה ל-state"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        expected_cmd = Mock()
        mock_state.get_command.return_value = expected_cmd
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece.get_command()
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == expected_cmd
        mock_state.get_command.assert_called_once()


# ────────────────────────────── Command Processing Tests ──────────────────────────────

class TestPieceCommands:
    
    def test_WhenOnCommand_WithValidCommand_ThenProcessesCommand(self, piece, mock_command, mock_state):
        """בדיקה: on_command עם פקודה חוקית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        pos_to_piece = {}
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.on_command(mock_command, 1000, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert piece._current_cmd == mock_command
        mock_state.process_command.assert_called_once_with(mock_command, 1000)
    
    def test_WhenOnCommand_WithImpossibleCommand_ThenIgnoresCommand(self, piece, mock_state):
        """בדיקה: on_command עם פקודה בלתי אפשרית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        impossible_cmd = Mock()
        impossible_cmd.type = "invalid_move"
        impossible_cmd.params = ["z9", "z8"]  # מיקום לא חוקי
        pos_to_piece = {}
        
        # Mock שמחזיר False עבור פקודה בלתי אפשרית
        with patch.object(piece, 'is_command_possible', return_value=False):
            # ─── ACT ──────────────────────────────────────────────────
            piece.on_command(impossible_cmd, 1000, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert piece._current_cmd is None
        mock_state.process_command.assert_not_called()
    
    def test_WhenIsCommandPossible_WithValidMoveCommand_ThenReturnsTrue(self, piece, mock_state):
        """בדיקה: is_command_possible עם פקודת תנועה חוקית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        cmd = Mock()
        cmd.type = "move"
        cmd.params = ["a1", "b2"]
        pos_to_piece = {}
        
        # הגדרת המיקום הנוכחי והמטרה כחוקיים
        mock_state._physics.start_cell = (2, 3)
        mock_state._physics.board.algebraic_to_cell.return_value = (4, 5)
        mock_state._moves.get_moves.return_value = [(4, 5), (3, 4)]  # המטרה חוקית
        mock_state.transitions = {"move": Mock()}
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece.is_command_possible(cmd, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == True
        mock_state._moves.get_moves.assert_called_once_with(2, 3, pos_to_piece)
    
    def test_WhenIsCommandPossible_WithIllegalMove_ThenReturnsFalse(self, piece, mock_state):
        """בדיקה: is_command_possible עם תנועה לא חוקית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        cmd = Mock()
        cmd.type = "move"
        cmd.params = ["a1", "h8"]
        pos_to_piece = {}
        
        # הגדרת המטרה כלא חוקית
        mock_state._physics.start_cell = (2, 3)
        mock_state._physics.board.algebraic_to_cell.return_value = (7, 7)  # מטרה
        mock_state._moves.get_moves.return_value = [(4, 5), (3, 4)]  # המטרה לא בתוך הרשימה
        mock_state.transitions = {"move": Mock()}
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece.is_command_possible(cmd, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == False
    
    def test_WhenIsCommandPossible_WithNonMoveCommand_ThenChecksTransitions(self, piece, mock_state):
        """בדיקה: is_command_possible עם פקודה שאינה תנועה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        cmd = Mock()
        cmd.type = "idle"
        pos_to_piece = {}
        mock_state.transitions = {"idle": Mock(), "move": Mock()}
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece.is_command_possible(cmd, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == True


# ────────────────────────────── State Management Tests ──────────────────────────────

class TestPieceStateManagement:
    
    def test_WhenReset_WithCurrentCommand_ThenResetsStateWithCommand(self, piece, mock_state):
        """בדיקה: reset עם פקודה נוכחית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        current_cmd = Mock()
        piece._current_cmd = current_cmd
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.reset(2000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        mock_state.reset.assert_called_once_with(current_cmd)
    
    def test_WhenReset_WithoutCurrentCommand_ThenCreatesIdleCommand(self, piece, mock_state):
        """בדיקה: reset ללא פקודה נוכחית"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        piece._current_cmd = None
        mock_state._physics.start_cell = (3, 4)
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.reset(1500)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        # וידוא שנקרא reset עם פקודת idle
        mock_state.reset.assert_called_once()
        call_args = mock_state.reset.call_args[0][0]  # הפרמטר הראשון
        assert call_args.timestamp == 1500
        assert call_args.piece_id == "test_piece"
        assert call_args.type == "idle"
        assert call_args.params == [(3, 4), (3, 4)]
    
    def test_WhenUpdate_WithUnfinishedPhysics_ThenUpdatesState(self, piece, mock_state):
        """בדיקה: update עם פיזיקה לא גמורה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        mock_state._physics.finished = False
        pos_to_piece = {}
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.update(1000, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        mock_state.update.assert_called_once_with(1000)
        # לא אמור לקרוא ל-on_command כי הפיזיקה לא סיימה
    
    def test_WhenUpdate_WithFinishedPhysics_ThenCreatesNextCommand(self, piece, mock_state):
        """בדיקה: update עם פיזיקה שסיימה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        mock_state._physics.finished = True
        mock_state._physics.get_pos_in_cell.return_value = (5, 6)
        mock_state.transitions = {"idle": Mock()}
        pos_to_piece = {}
        
        with patch.object(piece, 'on_command') as mock_on_command:
            # ─── ACT ──────────────────────────────────────────────────
            piece.update(2000, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        mock_state.update.assert_called_once_with(2000)
        mock_on_command.assert_called_once()
        call_args = mock_on_command.call_args[0]  # הפרמטרים
        cmd = call_args[0]
        assert cmd.timestamp == 2000
        assert cmd.piece_id == "test_piece"
        assert cmd.type == "idle"
        assert cmd.params == [(5, 6), (5, 6)]


# ────────────────────────────── Drawing Tests ──────────────────────────────

class TestPieceDrawing:
    
    @patch('cv2.addWeighted')
    def test_WhenDrawOnBoard_WithValidImage_ThenDrawsCorrectly(self, mock_addWeighted, piece, mock_board, mock_state):
        """בדיקה: draw_on_board עם תמונה תקפה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        # הגדרת תמונה מדומה
        import numpy as np
        fake_piece_img = np.zeros((50, 40, 3), dtype=np.uint8)
        mock_state._graphics.get_img.return_value.img = fake_piece_img
        mock_state._physics.get_pos.return_value = (100, 150)
        
        fake_board_img = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_board.img.img = fake_board_img
        
        mock_addWeighted.return_value = fake_piece_img
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.draw_on_board(mock_board, 1000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        mock_state._graphics.get_img.assert_called_once()
        mock_state._physics.get_pos.assert_called_once()
        mock_addWeighted.assert_called_once()
    
    def test_WhenDrawOnBoard_WithNoneImage_ThenSkipsDrawing(self, piece, mock_board, mock_state):
        """בדיקה: draw_on_board עם תמונה None"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        mock_state._graphics.get_img.return_value.img = None
        
        # ─── ACT ──────────────────────────────────────────────────────
        piece.draw_on_board(mock_board, 1000)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        # אמור לקרוא לget_img אבל לא לעשות כלום אחר
        mock_state._graphics.get_img.assert_called_once()
    
    @patch('cv2.cvtColor')
    def test_WhenMatchChannels_WithDifferentChannels_ThenConverts(self, mock_cvtColor, piece):
        """בדיקה: _match_channels ממיר ערוצים"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        import numpy as np
        test_img = np.zeros((10, 10, 4), dtype=np.uint8)  # 4 ערוצים
        expected_result = np.zeros((10, 10, 3), dtype=np.uint8)  # 3 ערוצים
        mock_cvtColor.return_value = expected_result
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece._match_channels(test_img, 3)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        mock_cvtColor.assert_called_once()
        assert result is expected_result
    
    def test_WhenMatchChannels_WithSameChannels_ThenReturnsOriginal(self, piece):
        """בדיקה: _match_channels עם אותו מספר ערוצים"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        import numpy as np
        test_img = np.zeros((10, 10, 3), dtype=np.uint8)
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece._match_channels(test_img, 3)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result is test_img  # אותו אובייקט
    
    @patch('cv2.addWeighted')
    def test_WhenBlend_ThenUsesCorrectAlpha(self, mock_addWeighted, piece):
        """בדיקה: _blend משתמש ב-alpha נכון"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        import numpy as np
        base = np.zeros((10, 10, 3), dtype=np.uint8)
        overlay = np.ones((10, 10, 3), dtype=np.uint8)
        expected_result = np.ones((10, 10, 3), dtype=np.uint8)
        mock_addWeighted.return_value = expected_result
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece._blend(base, overlay)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        # בדיקה שנקרא עם הפרמטרים הנכונים (ללא דיוק floating point מוחלט)
        mock_addWeighted.assert_called_once()
        call_args = mock_addWeighted.call_args[0]
        assert call_args[1] == 0.8  # alpha for overlay
        assert abs(call_args[3] - 0.2) < 0.001  # alpha for base (with tolerance)
        assert call_args[4] == 0  # gamma
        assert result is expected_result


# ────────────────────────────── Clone Tests ──────────────────────────────

class TestPieceCloning:
    
    def test_WhenCloneTo_ThenCreatesNewPieceAtTargetCell(self, piece, mock_state):
        """בדיקה: clone_to יוצר חתיכה חדשה במיקום יעד"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        target_cell = (6, 7)
        mock_physics_factory = Mock()
        
        # Mock של graphics copy
        mock_graphics_copy = Mock()
        mock_state._graphics.copy.return_value = mock_graphics_copy
        
        # Mock של physics creation
        mock_new_physics = Mock()
        mock_physics_factory.create.return_value = mock_new_physics
        
        # Mock של physics attributes
        mock_state._physics.speed = 2.5
        mock_state._physics.__class__.__name__ = "MovePhysics"
        
        with patch('Piece.State') as mock_state_class:
            mock_new_state = Mock()
            mock_state_class.return_value = mock_new_state
            mock_new_state.set_transition = Mock()
            
            # ─── ACT ──────────────────────────────────────────────────
            cloned_piece = piece.clone_to(target_cell, mock_physics_factory)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert cloned_piece._id == "test_piece"  # אותו ID
        mock_state._graphics.copy.assert_called_once()
        mock_physics_factory.create.assert_called_once_with("move", target_cell, {"physics": {"speed_m_per_sec": 2.5}})
        mock_state_class.assert_called_once_with(mock_state._moves, mock_graphics_copy, mock_new_physics)


# ────────────────────────────── Integration Tests ──────────────────────────────

class TestPieceIntegration:
    
    def test_WhenFullPieceLifecycle_ThenAllSystemsWork(self, mock_state):
        """בדיקה: מחזור חיים מלא של חתיכה"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        piece = Piece("lifecycle_test", mock_state, 0)
        cmd = Mock()
        cmd.type = "move"
        cmd.params = ["a1", "b2"]
        pos_to_piece = {}
        
        # הגדרת התנהגות State
        mock_state._physics.start_cell = (0, 0)
        mock_state._physics.board.algebraic_to_cell.return_value = (1, 1)
        mock_state._moves.get_moves.return_value = [(1, 1)]
        mock_state.transitions = {"move": Mock()}
        mock_state._physics.finished = False
        
        # ─── ACT ──────────────────────────────────────────────────────
        # שלב 1: קבלת פקודה
        piece.on_command(cmd, 1000, pos_to_piece)
        
        # שלב 2: עדכון
        piece.update(1100, pos_to_piece)
        
        # שלב 3: איפוס
        piece.reset(1200)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert piece._current_cmd == cmd
        mock_state.process_command.assert_called_once_with(cmd, 1000)
        mock_state.update.assert_called_once_with(1100)
        mock_state.reset.assert_called_once_with(cmd)
    
    def test_WhenMultiplePiecesInteract_ThenPositionMapWorks(self, mock_state):
        """בדיקה: אינטראקציה בין מספר חתיכות"""
        # ─── ARRANGE ──────────────────────────────────────────────────
        piece1 = Piece("piece1", mock_state, 0)
        piece2 = Piece("piece2", mock_state, 0)
        
        pos_to_piece = {
            (2, 3): piece1,
            (4, 5): piece2
        }
        
        cmd = Mock()
        cmd.type = "move"
        cmd.params = ["a1", "b2"]
        
        # הגדרת מיקומים
        mock_state._physics.start_cell = (0, 0)
        mock_state._physics.board.algebraic_to_cell.return_value = (1, 1)
        mock_state._moves.get_moves.return_value = [(1, 1)]
        mock_state.transitions = {"move": Mock()}
        
        # ─── ACT ──────────────────────────────────────────────────────
        result = piece1.is_command_possible(cmd, pos_to_piece)
        
        # ─── ASSERT ───────────────────────────────────────────────────
        assert result == True
        mock_state._moves.get_moves.assert_called_with(0, 0, pos_to_piece)
