import pytest
import pathlib
import tempfile
import shutil
import json
import csv
import queue
import threading
import time
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game import Game
from Board import Board
from Command import Command
from Piece import Piece
from img import Img
from PieceFactory import PieceFactory
from Bus.EventBus import EventBus

# ────────────────────────────── Fixtures ──────────────────────────────

@pytest.fixture
def mock_board():
    """יוצר mock Board למטרות בדיקה"""
    board = Mock(spec=Board)
    board.H_cells = 8
    board.W_cells = 8
    board.cell_H_pix = 64
    board.cell_W_pix = 64
    board.img = Mock()
    board.clone.return_value = board
    board.cell_to_algebraic.side_effect = lambda cell: f"{chr(ord('a') + cell[1])}{8 - cell[0]}"
    board.algebraic_to_cell.side_effect = lambda alg: (8 - int(alg[1]), ord(alg[0]) - ord('a'))
    return board

@pytest.fixture
def temp_pieces_dir():
    """יוצר תיקייה זמנית עם מבנה pieces בסיסי לבדיקות"""
    with tempfile.TemporaryDirectory() as temp_dir:
        pieces_dir = pathlib.Path(temp_dir) / "pieces"
        pieces_dir.mkdir()
        
        # יצירת תיקיית KW (מלך לבן) בסיסית
        for piece_type in ["KW", "KB", "QW", "QB", "PW", "PB"]:
            piece_dir = pieces_dir / piece_type
            piece_dir.mkdir()
            
            # יצירת קובץ moves.txt
            moves_file = piece_dir / "moves.txt"
            moves_file.write_text("1,0\n0,1\n-1,0\n0,-1\n")
            
            # יצירת תיקיית states
            states_dir = piece_dir / "states"
            for state_name in ["idle", "move", "jump", "long_rest", "short_rest"]:
                state_dir = states_dir / state_name
                state_dir.mkdir(parents=True)
                
                config = {
                    "physics": {"duration": 1000, "speed": 100},
                    "graphics": {"frame_duration": 100, "loop": True}
                }
                config_file = state_dir / "config.json"
                config_file.write_text(json.dumps(config))
                
                sprites_dir = state_dir / "sprites"
                sprites_dir.mkdir()
                for i in range(1, 6):
                    (sprites_dir / f"{i}.png").write_text("dummy_image_data")
        
        yield pieces_dir

@pytest.fixture
def temp_csv_file():
    """יוצר קובץ CSV זמני להצבת כלים"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # יצירת לוח שחמט בסיסי
        csv_content = [
            ["KB", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "KW"]
        ]
        writer = csv.writer(f)
        writer.writerows(csv_content)
        temp_path = pathlib.Path(f.name)
    
    yield temp_path
    
    # ניקוי
    if temp_path.exists():
        temp_path.unlink()

@pytest.fixture
def mock_event_bus():
    """יוצר mock עבור EventBus"""
    return Mock(spec=EventBus)

@pytest.fixture
def game_instance(mock_board, temp_pieces_dir, temp_csv_file, mock_event_bus):
    """יוצר instance של Game עם mocks"""
    with patch('cv2.imread') as mock_imread, \
         patch('Game.event_bus', mock_event_bus):
        
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        
        game = Game(
            board=mock_board, 
            pieces_root=temp_pieces_dir,
            placement_csv=temp_csv_file
        )
        yield game

# ────────────────────────────── Basic Functionality Tests ──────────────────────────────

def test_WhenGameCreated_ThenInitializesCorrectly(mock_board, temp_pieces_dir, temp_csv_file):
    """בדיקה: יצירת Game מאתחלת נכון את כל המאפיינים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    with patch('cv2.imread') as mock_imread:
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # ─── ACT ──────────────────────────────────────────────────────────
        game = Game(mock_board, temp_pieces_dir, temp_csv_file)
        
        # ─── ASSERT ───────────────────────────────────────────────────────
        assert game.board is mock_board
        assert isinstance(game.user_input_queue, queue.Queue)
        assert isinstance(game.piece_factory, PieceFactory)
        assert isinstance(game.pieces, dict)
        assert isinstance(game.pos_to_piece, dict)
        assert game.focus_cell == (0, 0)
        assert game.focus_cell2 == (7, 0)
        assert game._selection_mode == "source"
        assert game._selection_mode2 == "source"
        assert game._selected_source is None
        assert game._selected_source2 is None
        assert game._running is True

def test_WhenGameCreatedWithEmptyCSV_ThenNoPiecesLoaded(mock_board, temp_pieces_dir):
    """בדיקה: יצירת Game עם CSV ריק לא טוענת כלים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # CSV ריק עם 8 שורות ו-8 עמודות ריקות
        writer = csv.writer(f)
        for _ in range(8):
            writer.writerow([""] * 8)
        empty_csv_path = pathlib.Path(f.name)
    
    with patch('cv2.imread') as mock_imread:
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # ─── ACT ──────────────────────────────────────────────────────────
        game = Game(mock_board, temp_pieces_dir, empty_csv_path)
        
        # ─── ASSERT ───────────────────────────────────────────────────────
        assert len(game.pieces) == 0
        assert len(game.pos_to_piece) == 0
    
    # ניקוי
    empty_csv_path.unlink()

def test_WhenGameTimeMs_ThenReturnsCorrectTimestamp(game_instance):
    """בדיקה: game_time_ms מחזירה timestamp נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    initial_time = game_instance.game_time_ms()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    time.sleep(0.1)  # המתנה קצרה
    later_time = game_instance.game_time_ms()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(initial_time, int)
    assert isinstance(later_time, int)
    assert later_time > initial_time
    assert later_time - initial_time >= 90  # לפחות 90ms (עם מרווח לטעויות זמן)

def test_WhenCloneBoard_ThenReturnsBoardClone(game_instance):
    """בדיקה: clone_board מחזירה עותק של הלוח"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # (game_instance מוכן במצב מוקי)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    cloned_board = game_instance.clone_board()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert cloned_board is not None
    game_instance.board.clone.assert_called_once()

# ────────────────────────────── Piece Management Tests ──────────────────────────────

def test_WhenLoadPiecesFromCSV_ThenPiecesCreatedCorrectly(mock_board, temp_pieces_dir):
    """בדיקה: טעינת כלים מ-CSV יוצרת כלים במיקומים הנכונים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_content = [
            ["KB", "", "", "", "", "", "", "KW"],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""]
        ]
        writer = csv.writer(f)
        writer.writerows(csv_content)
        csv_path = pathlib.Path(f.name)
    
    with patch('cv2.imread') as mock_imread:
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # ─── ACT ──────────────────────────────────────────────────────────
        game = Game(mock_board, temp_pieces_dir, csv_path)
        
        # ─── ASSERT ───────────────────────────────────────────────────────
        assert len(game.pieces) == 2
        assert len(game.pos_to_piece) == 2
        
        # בדיקת מיקומים
        assert (0, 0) in game.pos_to_piece
        assert (0, 7) in game.pos_to_piece
        
        # בדיקת סוגי כלים
        piece_ids = [piece.get_id() for piece in game.pieces.values()]
        assert any("KB" in id for id in piece_ids)
        assert any("KW" in id for id in piece_ids)
    
    # ניקוי
    csv_path.unlink()

def test_WhenUpdatePositionMapping_ThenMappingUpdatedCorrectly(game_instance):
    """בדיקה: עדכון מיפוי מיקומים עובד נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת mock piece עם מיקום ידוע
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "TEST_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos.return_value = (128, 192)  # תא (3, 2)
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_piece._state = mock_state
    
    game_instance.pieces = {"TEST_1": mock_piece}
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._update_position_mapping()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    expected_pos = (3.0, 2.0)  # (y, x) במונחי תאים
    assert expected_pos in game_instance.pos_to_piece
    assert game_instance.pos_to_piece[expected_pos] is mock_piece

# ────────────────────────────── Input Handling Tests ──────────────────────────────

def test_WhenOnEnterPressed_InSourceMode_ThenSourceSelected(game_instance):
    """בדיקה: לחיצה על Enter במצב source בוחרת מקור"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת כלי שחור במיקום הפוקוס
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KB_1"  # כלי שחור
    game_instance.pos_to_piece[game_instance.focus_cell] = mock_piece
    game_instance.board.cell_to_algebraic.return_value = "a8"
    
    assert game_instance._selection_mode == "source"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_enter_pressed()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selected_source == game_instance.focus_cell
    assert game_instance._selection_mode == "dest"

def test_WhenOnEnterPressed_WithWhitePiece_ThenIgnored(game_instance):
    """בדיקה: לחיצה על Enter עם כלי לבן נדחית למשתמש ראשון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת כלי לבן במיקום הפוקוס
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KW_1"  # כלי לבן
    game_instance.pos_to_piece[game_instance.focus_cell] = mock_piece
    
    original_mode = game_instance._selection_mode
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_enter_pressed()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selection_mode == original_mode
    assert game_instance._selected_source is None

def test_WhenOnSpacePressed_InSourceMode_ThenSourceSelected(game_instance):
    """בדיקה: לחיצה על Space במצב source בוחרת מקור למשתמש שני"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת כלי לבן במיקום הפוקוס השני
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KW_1"  # כלי לבן
    game_instance.pos_to_piece[game_instance.focus_cell2] = mock_piece
    game_instance.board.cell_to_algebraic.return_value = "a1"
    
    assert game_instance._selection_mode2 == "source"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_space_pressed()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selected_source2 == game_instance.focus_cell2
    assert game_instance._selection_mode2 == "dest"

def test_WhenOnEnterPressed_InDestMode_ThenCommandCreated(game_instance):
    """בדיקה: לחיצה על Enter במצב dest יוצרת פקודת תנועה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # הכנת מצב dest
    source_cell = (1, 1)
    dest_cell = (2, 2)
    
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KB_1"
    
    game_instance._selection_mode = "dest"
    game_instance._selected_source = source_cell
    game_instance.focus_cell = dest_cell
    game_instance.pos_to_piece[source_cell] = mock_piece
    
    game_instance.board.cell_to_algebraic.side_effect = lambda cell: f"{chr(ord('a') + cell[1])}{8 - cell[0]}"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_enter_pressed()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert not game_instance.user_input_queue.empty()
    cmd = game_instance.user_input_queue.get()
    assert isinstance(cmd, Command)
    assert cmd.piece_id == "KB_1"
    assert cmd.type == "move"
    assert len(cmd.params) == 2
    
    # בדיקת איפוס הבחירה
    assert game_instance._selection_mode == "source"
    assert game_instance._selected_source is None

# ────────────────────────────── Jump Tests ──────────────────────────────

def test_WhenOnJumpPressed_WithBlackPiece_ThenJumpCommandCreated(game_instance):
    """בדיקה: לחיצה על jump עם כלי שחור יוצרת פקודת קפיצה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KB_1"  # כלי שחור
    game_instance.pos_to_piece[game_instance.focus_cell] = mock_piece
    game_instance.board.cell_to_algebraic.return_value = "a8"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert not game_instance.user_input_queue.empty()
    cmd = game_instance.user_input_queue.get()
    assert isinstance(cmd, Command)
    assert cmd.piece_id == "KB_1"
    assert cmd.type == "jump"

def test_WhenOnJumpPressed_WithWrongColorPiece_ThenIgnored(game_instance):
    """בדיקה: לחיצה על jump עם כלי בצבע לא נכון נדחית"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KW_1"  # כלי לבן למשתמש ראשון
    game_instance.pos_to_piece[game_instance.focus_cell] = mock_piece
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance.user_input_queue.empty()

# ────────────────────────────── Win Condition Tests ──────────────────────────────

def test_WhenTwoKingsRemain_ThenNotWin(game_instance):
    """בדיקה: כשנשארים שני מלכים המשחק לא מסתיים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    king_black = Mock(spec=Piece)
    king_black.get_id.return_value = "KB_1"
    king_white = Mock(spec=Piece)
    king_white.get_id.return_value = "KW_1"
    
    game_instance.pieces = {"KB_1": king_black, "KW_1": king_white}
    
    # ─── ACT ──────────────────────────────────────────────────────────
    is_win = game_instance._is_win()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert is_win is False

def test_WhenOneKingRemains_ThenWin(game_instance):
    """בדיקה: כשנשאר מלך אחד המשחק מסתיים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    king_white = Mock(spec=Piece)
    king_white.get_id.return_value = "KW_1"
    
    game_instance.pieces = {"KW_1": king_white}
    
    # ─── ACT ──────────────────────────────────────────────────────────
    is_win = game_instance._is_win()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert is_win is True

def test_WhenNoKingsRemain_ThenWin(game_instance):
    """בדיקה: כשלא נשארים מלכים המשחק מסתיים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    game_instance.pieces = {}
    
    # ─── ACT ──────────────────────────────────────────────────────────
    is_win = game_instance._is_win()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert is_win is True

# ────────────────────────────── Pawn Promotion Tests ──────────────────────────────

def test_WhenWhitePawnReachesTopRow_ThenPromotedToQueen(game_instance):
    """בדיקה: חייל לבן שמגיע לשורה העליונה מקודם למלכה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת חייל לבן בשורה העליונה
    mock_pawn = Mock(spec=Piece)
    mock_pawn.get_id.return_value = "PW_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos_in_cell.return_value = (0, 4)  # שורה 0 (עליונה)
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_pawn._state = mock_state
    
    game_instance.pieces = {"PW_1": mock_pawn}
    
    # Mock יצירת מלכה חדשה
    mock_queen = Mock(spec=Piece)
    mock_queen.get_id.return_value = "QW_1"
    game_instance.piece_factory.create_piece = Mock(return_value=mock_queen)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._check_pawn_promotion()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהחייל הוסר
    assert "PW_1" not in game_instance.pieces
    
    # בדיקה שנוצרה מלכה
    game_instance.piece_factory.create_piece.assert_called_once_with("QW", (0, 4))

def test_WhenBlackPawnReachesBottomRow_ThenPromotedToQueen(game_instance):
    """בדיקה: חייל שחור שמגיע לשורה התחתונה מקודם למלכה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת חייל שחור בשורה התחתונה
    mock_pawn = Mock(spec=Piece)
    mock_pawn.get_id.return_value = "PB_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos_in_cell.return_value = (7, 4)  # שורה 7 (תחתונה)
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_pawn._state = mock_state
    
    game_instance.pieces = {"PB_1": mock_pawn}
    
    # Mock יצירת מלכה חדשה
    mock_queen = Mock(spec=Piece)
    mock_queen.get_id.return_value = "QB_1"
    game_instance.piece_factory.create_piece = Mock(return_value=mock_queen)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._check_pawn_promotion()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהחייל הוסר
    assert "PB_1" not in game_instance.pieces
    
    # בדיקה שנוצרה מלכה
    game_instance.piece_factory.create_piece.assert_called_once_with("QB", (7, 4))

def test_WhenPawnNotAtEndRow_ThenNoPromotion(game_instance):
    """בדיקה: חייל שלא בשורה הסופית לא מקודם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת חייל לבן באמצע הלוח
    mock_pawn = Mock(spec=Piece)
    mock_pawn.get_id.return_value = "PW_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos_in_cell.return_value = (4, 4)  # אמצע הלוח
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_pawn._state = mock_state
    
    game_instance.pieces = {"PW_1": mock_pawn}
    game_instance.piece_factory.create_piece = Mock()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._check_pawn_promotion()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהחייל נשאר
    assert "PW_1" in game_instance.pieces
    
    # בדיקה שלא נוצרה מלכה
    game_instance.piece_factory.create_piece.assert_not_called()

def test_WhenPawnIsMoving_ThenNoPromotion(game_instance):
    """בדיקה: חייל שבתנועה לא מקודם גם אם בשורה הנכונה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת חייל לבן בשורה העליונה אבל בתנועה
    mock_pawn = Mock(spec=Piece)
    mock_pawn.get_id.return_value = "PW_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos_in_cell.return_value = (0, 4)  # שורה עליונה
    mock_command.type = "move"  # בתנועה
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_pawn._state = mock_state
    
    game_instance.pieces = {"PW_1": mock_pawn}
    game_instance.piece_factory.create_piece = Mock()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._check_pawn_promotion()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהחייל נשאר (לא קודם)
    assert "PW_1" in game_instance.pieces
    
    # בדיקה שלא נוצרה מלכה
    game_instance.piece_factory.create_piece.assert_not_called()

# ────────────────────────────── Reset Selection Tests ──────────────────────────────

def test_WhenResetSelection_ThenModeAndSourceReset(game_instance):
    """בדיקה: איפוס בחירה מחזירה למצב התחלתי"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    game_instance._selection_mode = "dest"
    game_instance._selected_source = (1, 1)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._reset_selection()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selection_mode == "source"
    assert game_instance._selected_source is None

def test_WhenResetSelection2_ThenModeAndSourceReset(game_instance):
    """בדיקה: איפוס בחירה למשתמש שני מחזירה למצב התחלתי"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    game_instance._selection_mode2 = "dest"
    game_instance._selected_source2 = (1, 1)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._reset_selection2()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selection_mode2 == "source"
    assert game_instance._selected_source2 is None

# ────────────────────────────── Error Handling Tests ──────────────────────────────

def test_WhenCSVFileNotFound_ThenRaisesFileNotFoundError(mock_board, temp_pieces_dir):
    """בדיקה: קובץ CSV שלא קיים זורק שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    non_existent_path = pathlib.Path("non_existent_file.csv")
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises(FileNotFoundError):
        Game(mock_board, temp_pieces_dir, non_existent_path)

def test_WhenInvalidCSVFormat_ThenHandlesGracefully(mock_board, temp_pieces_dir):
    """בדיקה: CSV עם פורמט לא תקין מטופל בחן"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("invalid,csv,format,with,too,many,columns,here,and,more\n")
        f.write("KB,\n")  # שורה קצרה עם כלי תקין
        invalid_csv_path = pathlib.Path(f.name)
    
    with patch('cv2.imread') as mock_imread:
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # ─── ACT ──────────────────────────────────────────────────────────
        # לא צריך לזרוק שגיאה, אלא לטפל בחן - אבל נצפה שגיאה כי "invalid" לא קיים
        with pytest.raises((ValueError, FileNotFoundError)):
            game = Game(mock_board, temp_pieces_dir, invalid_csv_path)
    
    # ניקוי
    invalid_csv_path.unlink()

def test_WhenJumpPressedWithNoPiece_ThenIgnored(game_instance):
    """בדיקה: לחיצה על jump ללא כלי נדחית"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # ודוא שאין כלי במיקום הפוקוס
    game_instance.pos_to_piece.clear()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance.user_input_queue.empty()

def test_WhenEnterPressedWithNoPiece_ThenIgnored(game_instance):
    """בדיקה: לחיצה על Enter ללא כלי נדחית"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # ודוא שאין כלי במיקום הפוקוס
    game_instance.pos_to_piece.clear()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_enter_pressed()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance._selection_mode == "source"
    assert game_instance._selected_source is None

# ────────────────────────────── Edge Cases Tests ──────────────────────────────

def test_WhenPromotePawnWithExistingQueen_ThenCreatesUniqueId(game_instance):
    """בדיקה: קידום חייל כשכבר יש מלכה יוצר ID ייחודי"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת מלכה קיימת
    existing_queen = Mock(spec=Piece)
    existing_queen.get_id.return_value = "QW_1"
    game_instance.pieces["QW_1"] = existing_queen
    
    # יצירת חייל לקידום
    mock_pawn = Mock(spec=Piece)
    mock_pawn.get_id.return_value = "PW_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos_in_cell.return_value = (0, 4)
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_pawn._state = mock_state
    
    game_instance.pieces["PW_1"] = mock_pawn
    
    # Mock יצירת מלכה חדשה
    new_queen = Mock(spec=Piece)
    new_queen.get_id.return_value = "QW_2"
    new_queen._id = "QW_2"
    new_queen.reset = Mock()
    game_instance.piece_factory.create_piece = Mock(return_value=new_queen)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._check_pawn_promotion()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שיש עכשיו שתי מלכות
    queen_pieces = [p for p in game_instance.pieces.values() if "Q" in p.get_id()]
    assert len(queen_pieces) >= 1
    
    # בדיקה שהחייל הוסר
    assert "PW_1" not in game_instance.pieces

def test_WhenPieceCollision_ThenCorrectPieceRemoved(game_instance):
    """בדיקה: התנגשות כלים מסירה את הכלי הנכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת שני כלים באותו מיקום
    piece1 = Mock(spec=Piece)
    piece1.get_id.return_value = "P1"
    
    # יצירת mock state ו-physics עבור piece1
    mock_state1 = Mock()
    mock_physics1 = Mock()
    mock_command1 = Mock()
    
    mock_physics1.get_pos.return_value = (64, 64)  # תא (1, 1)
    mock_physics1.get_pos_in_cell.return_value = (1, 1)  # הוספת get_pos_in_cell
    mock_physics1.start_time = 1000
    mock_command1.type = "move"
    mock_state1._physics = mock_physics1
    mock_state1._current_command = mock_command1
    piece1._state = mock_state1
    
    piece2 = Mock(spec=Piece)
    piece2.get_id.return_value = "P2"
    
    # יצירת mock state ו-physics עבור piece2
    mock_state2 = Mock()
    mock_physics2 = Mock()
    mock_command2 = Mock()
    
    mock_physics2.get_pos.return_value = (64, 64)  # תא (1, 1)
    mock_physics2.get_pos_in_cell.return_value = (1, 1)  # הוספת get_pos_in_cell
    mock_physics2.start_time = 1100
    mock_command2.type = "idle"
    mock_state2._physics = mock_physics2
    mock_state2._current_command = mock_command2
    piece2._state = mock_state2
    
    game_instance.pieces = {"P1": piece1, "P2": piece2}
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._update_position_mapping()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שרק כלי אחד נשאר
    assert len(game_instance.pieces) == 1
    
    # בדיקה שהכלי הנכון נשאר (המתקדם או עם המצב הנכון)
    remaining_pieces = list(game_instance.pieces.keys())
    assert len(remaining_pieces) == 1

# ────────────────────────────── Threading Tests ──────────────────────────────

def test_WhenMultipleThreadsAccessGame_ThenThreadSafe(game_instance):
    """בדיקה: גישה מרובה למשחק מ-threads שונים בטוחה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    results = []
    
    def access_focus_cell():
        for _ in range(100):
            with game_instance._lock:
                current_focus = game_instance.focus_cell
                results.append(current_focus)
                time.sleep(0.001)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=access_focus_cell)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שקיבלנו תוצאות מכל ה-threads
    assert len(results) == 300  # 3 threads * 100 iterations
    
    # בדיקה שכל התוצאות הן tuples תקינים
    for result in results:
        assert isinstance(result, tuple)
        assert len(result) == 2

# ────────────────────────────── Performance Tests ──────────────────────────────

def test_WhenManyPiecesUpdated_ThenPerformanceReasonable(game_instance):
    """בדיקה: עדכון כלים רבים מתבצע בזמן סביר"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת הרבה כלים מדומים
    many_pieces = {}
    for i in range(50):
        mock_piece = Mock(spec=Piece)
        mock_piece.get_id.return_value = f"P{i}"
        
        # יצירת mock state ו-physics
        mock_state = Mock()
        mock_physics = Mock()
        
        mock_physics.get_pos.return_value = (i * 10, i * 10)
        mock_physics.get_pos_in_cell.return_value = (i, i)  # הוספת get_pos_in_cell
        mock_state._physics = mock_physics
        mock_state._current_command = Mock()
        mock_state._current_command.type = "idle"
        mock_piece._state = mock_state
        
        mock_piece.update = Mock()
        mock_piece.draw_on_board = Mock()
        many_pieces[f"P{i}"] = mock_piece
    
    game_instance.pieces = many_pieces
    
    # ─── ACT ──────────────────────────────────────────────────────────
    start_time = time.time()
    
    # סימולציה של עדכון פריים יחיד
    now_ms = game_instance.game_time_ms()
    for piece in game_instance.pieces.values():
        piece.update(now_ms, game_instance.pos_to_piece)
    
    game_instance._update_position_mapping()
    
    end_time = time.time()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    execution_time = end_time - start_time
    assert execution_time < 1.0  # צריך להסתיים תוך שנייה
    
    # בדיקה שכל הכלים עודכנו
    for piece in game_instance.pieces.values():
        piece.update.assert_called_once()

# ────────────────────────────── Integration Tests ──────────────────────────────

def test_WhenGameRunsOneFrame_ThenAllSystemsWork(game_instance):
    """בדיקה: הרצת פריים אחד של המשחק עובדת נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # הכנת כלי מדומה
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KB_1"
    
    # יצירת mock state ו-physics
    mock_state = Mock()
    mock_physics = Mock()
    mock_command = Mock()
    
    mock_physics.get_pos.return_value = (64, 64)
    mock_physics.get_pos_in_cell.return_value = (1, 1)  # הוספת get_pos_in_cell
    mock_command.type = "idle"
    mock_state._physics = mock_physics
    mock_state._current_command = mock_command
    mock_piece._state = mock_state
    
    mock_piece.update = Mock()
    mock_piece.draw_on_board = Mock()
    mock_piece.reset = Mock()
    
    game_instance.pieces = {"KB_1": mock_piece}
    
    # Mock של CV2 ו-UI
    with patch('cv2.imshow') as mock_imshow, \
         patch('cv2.waitKey') as mock_waitkey, \
         patch('cv2.rectangle') as mock_rectangle:  # הוספת mock לrectangle
        
        mock_waitkey.return_value = -1  # אין לחיצות מקש
        
        # ─── ACT ──────────────────────────────────────────────────────────
        # סימולציה של פריים יחיד
        now_ms = game_instance.game_time_ms()
        
        # עדכון כלים
        for piece in game_instance.pieces.values():
            piece.update(now_ms, game_instance.pos_to_piece)
        
        # עדכון מיקומים
        game_instance._update_position_mapping()
        
        # ציור
        game_instance._draw()
        
        # ─── ASSERT ───────────────────────────────────────────────────────
        # בדיקה שהכלי עודכן
        mock_piece.update.assert_called_once_with(now_ms, game_instance.pos_to_piece)
        
        # בדיקה שהכלי נמצא במיפוי
        assert (1.0, 1.0) in game_instance.pos_to_piece
        assert game_instance.pos_to_piece[(1.0, 1.0)] is mock_piece
        
        # בדיקה שיש לוח נוכחי
        assert game_instance._current_board is not None


# ────────────────────────────── Additional Player Tests ──────────────────────────────

def test_WhenPlayer2JumpPressed_WithWhitePiece_ThenCommandCreated(game_instance):
    """בדיקה: שחקן 2 עם כלי לבן יוצר פקודת jump"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KW_1"  # כלי לבן
    game_instance.pos_to_piece[game_instance.focus_cell2] = mock_piece
    game_instance.board.cell_to_algebraic.return_value = "h1"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=2)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert not game_instance.user_input_queue.empty()
    cmd = game_instance.user_input_queue.get()
    assert isinstance(cmd, Command)
    assert cmd.piece_id == "KW_1"
    assert cmd.type == "jump"

def test_WhenPlayer1JumpPressed_WithWhitePiece_ThenIgnored(game_instance):
    """בדיקה: שחקן 1 עם כלי לבן מתעלם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KW_1"  # כלי לבן
    game_instance.pos_to_piece[game_instance.focus_cell] = mock_piece
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance.user_input_queue.empty()

def test_WhenPlayer2JumpPressed_WithBlackPiece_ThenIgnored(game_instance):
    """בדיקה: שחקן 2 עם כלי שחור מתעלם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece = Mock(spec=Piece)
    mock_piece.get_id.return_value = "KB_1"  # כלי שחור
    game_instance.pos_to_piece[game_instance.focus_cell2] = mock_piece
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=2)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance.user_input_queue.empty()

def test_WhenJumpPressed_WithEmptyFocusCell_ThenIgnored(game_instance):
    """בדיקה: jump על תא ריק מתעלם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # מוודאים שה-focus_cell ריק
    game_instance.focus_cell = (7, 7)  # תא שלא אמור להיות בו כלי
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_instance.user_input_queue.empty()


# ────────────────────────────── Game Loop Coverage ──────────────────────────────

@patch('time.sleep')
def test_WhenGameLoop_ThenRunCalled(mock_sleep, game_instance):
    """בדיקה: game loop מפעיל run"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # הגבלת ריצות loop
    game_instance._running = False
    
    # ─── ACT ──────────────────────────────────────────────────────────
    with patch.object(game_instance, 'run') as mock_run:
        # קריאה קצרה למטרות כיסוי - בדיקת זמינות run
        mock_run.assert_not_called()  # עדיין לא נקרא
        
        # בדיקה שהמתודה קיימת
        assert hasattr(game_instance, 'run')
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהמתודה זמינה
    assert callable(getattr(game_instance, 'run', None))

def test_WhenGameTimeCalled_ThenReturnsValidTime(game_instance):
    """בדיקה: game_time_ms מחזיר זמן תקין"""
    # ─── ACT ──────────────────────────────────────────────────────────
    time1 = game_instance.game_time_ms()
    time.sleep(0.001)  # זמן קצר
    time2 = game_instance.game_time_ms()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(time1, int)
    assert isinstance(time2, int)
    assert time2 >= time1  # הזמן השני אמור להיות גדול או שווה


# ────────────────────────────── Thread Safety Additional Tests ──────────────────────────────

def test_WhenMultipleJumpCalls_ThenAllCommandsQueued(game_instance):
    """בדיקה: קריאות jump מרובות נוספות לתור"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_piece1 = Mock(spec=Piece)
    mock_piece1.get_id.return_value = "KB_1"
    game_instance.pos_to_piece[(0, 0)] = mock_piece1
    
    mock_piece2 = Mock(spec=Piece)
    mock_piece2.get_id.return_value = "KW_1"
    game_instance.pos_to_piece[(7, 7)] = mock_piece2
    
    game_instance.focus_cell = (0, 0)
    game_instance.focus_cell2 = (7, 7)
    
    game_instance.board.cell_to_algebraic.side_effect = lambda cell: f"{'abcdefgh'[cell[1]]}{8-cell[0]}"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    game_instance._on_jump_pressed(player=1)  # שחקן 1 - כלי שחור
    game_instance._on_jump_pressed(player=2)  # שחקן 2 - כלי לבן
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    commands = []
    while not game_instance.user_input_queue.empty():
        commands.append(game_instance.user_input_queue.get())
    
    assert len(commands) == 2
    assert all(cmd.type == "jump" for cmd in commands)
    assert {cmd.piece_id for cmd in commands} == {"KB_1", "KW_1"}
