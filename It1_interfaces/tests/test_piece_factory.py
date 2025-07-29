import pytest
from pathlib import Path
import json
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Board import Board
from PieceFactory import PieceFactory
from Piece import Piece
from State import State
from img import Img

# ────────────────────────────── Fixtures ──────────────────────────────

@pytest.fixture
def board():
    """יוצר board למטרות בדיקה"""
    img = Img()
    return Board(64, 64, 1, 1, 8, 8, img=img)

@pytest.fixture
def temp_pieces_dir():
    """יוצר תיקייה זמנית עם מבנה pieces לבדיקות"""
    temp_dir = tempfile.mkdtemp()
    pieces_root = Path(temp_dir) / "pieces"
    
    # יצירת מבנה תיקיות לכלי QW
    qw_dir = pieces_root / "QW"
    qw_dir.mkdir(parents=True)
    
    # יצירת קובץ moves.txt
    with open(qw_dir / "moves.txt", "w") as f:
        f.write("1,0\n0,1\n-1,0\n0,-1\n")
    
    # יצירת תיקיות states
    states_dir = qw_dir / "states"
    for state_name in ["idle", "move", "jump", "long_rest", "short_rest"]:
        state_dir = states_dir / state_name
        state_dir.mkdir(parents=True)
        
        # יצירת config.json לכל state
        config = {
            "physics": {"duration": 1000, "speed": 100},
            "graphics": {"frame_duration": 100, "loop": True}
        }
        with open(state_dir / "config.json", "w") as f:
            json.dump(config, f)
        
        # יצירת תיקיית sprites עם קובץ דמה
        sprites_dir = state_dir / "sprites"
        sprites_dir.mkdir()
        with open(sprites_dir / "1.png", "wb") as f:
            f.write(b"fake_image_data")
    
    yield pieces_root
    
    # ניקוי
    shutil.rmtree(temp_dir)

@pytest.fixture
def piece_factory(board, temp_pieces_dir):
    """יוצר PieceFactory עם mock לטיפול בקריאות התמונות"""
    with patch('cv2.imread') as mock_imread:
        # Mock שמחזיר תמונה דמה במקום לטעון קובץ אמיתי
        import numpy as np
        mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
        factory = PieceFactory(board, temp_pieces_dir)
        yield factory

@pytest.fixture
def invalid_pieces_dir():
    """יוצר תיקייה זמנית עם מבנה לא תקין"""
    temp_dir = tempfile.mkdtemp()
    pieces_root = Path(temp_dir) / "pieces"
    pieces_root.mkdir(parents=True)
    
    yield pieces_root
    
    # ניקוי
    shutil.rmtree(temp_dir)

# ────────────────────────────── Basic Functionality Tests ──────────────────────────────

def test_WhenPieceFactoryCreated_ThenInitializesCorrectly(board, temp_pieces_dir):
    """בדיקה: יצירת PieceFactory מאתחלת נכון את כל המאפיינים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # (הכנה בוצעה ב-fixtures)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    factory = PieceFactory(board, temp_pieces_dir)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert factory.board is board
    assert factory.pieces_root == temp_pieces_dir
    assert factory._physics_factory is not None
    assert factory._graphics_factory is not None
    assert isinstance(factory._templates, dict)
    assert len(factory._templates) == 0
    assert isinstance(factory.counter, dict)
    assert len(factory.counter) == 0

def test_WhenCreatePieceCalledWithValidType_ThenReturnsValidPiece(piece_factory):
    """בדיקה: יצירת כלי עם סוג תקין מחזירה Piece תקין"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    cell = (2, 3)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece = piece_factory.create_piece(piece_type, cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(piece, Piece)
    assert piece.get_id().startswith(piece_type)
    assert piece._state is not None
    assert piece._state._moves is not None
    assert piece._state._graphics is not None
    assert piece._state._physics is not None

def test_WhenCreateMultiplePiecesOfSameType_ThenEachHasUniqueId(piece_factory):
    """בדיקה: יצירת מספר כלים מאותו סוג מחזירה ID ייחודי לכל אחד"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    cell1 = (1, 1)
    cell2 = (2, 2)
    cell3 = (3, 3)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece1 = piece_factory.create_piece(piece_type, cell1)
    piece2 = piece_factory.create_piece(piece_type, cell2)
    piece3 = piece_factory.create_piece(piece_type, cell3)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    ids = [piece1.get_id(), piece2.get_id(), piece3.get_id()]
    assert len(set(ids)) == 3  # כל ה-IDs ייחודיים
    assert all(id_val.startswith(piece_type) for id_val in ids)
    assert piece1.get_id() == "QW_1"
    assert piece2.get_id() == "QW_2"
    assert piece3.get_id() == "QW_3"

def test_WhenCreatePiecesOfDifferentTypes_ThenCountersAreIndependent(piece_factory, temp_pieces_dir):
    """בדיקה: מונים של סוגי כלים שונים עצמאיים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת סוג כלי נוסף
    kb_dir = temp_pieces_dir / "KB"
    kb_dir.mkdir()
    
    # העתקת מבנה מ-QW ל-KB
    qw_dir = temp_pieces_dir / "QW"
    shutil.copy2(qw_dir / "moves.txt", kb_dir / "moves.txt")
    shutil.copytree(qw_dir / "states", kb_dir / "states")
    
    cell = (1, 1)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece_qw1 = piece_factory.create_piece("QW", cell)
    piece_kb1 = piece_factory.create_piece("KB", cell)
    piece_qw2 = piece_factory.create_piece("QW", cell)
    piece_kb2 = piece_factory.create_piece("KB", cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert piece_qw1.get_id() == "QW_1"
    assert piece_kb1.get_id() == "KB_1"
    assert piece_qw2.get_id() == "QW_2"
    assert piece_kb2.get_id() == "KB_2"

# ────────────────────────────── State Machine Tests ──────────────────────────────

def test_WhenBuildStateMachineCalledWithValidDir_ThenReturnsCorrectStates(piece_factory, temp_pieces_dir):
    """בדיקה: בניית state machine עם תיקייה תקינה מחזירה states נכונים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_dir = temp_pieces_dir / "QW"
    cell = (0, 0)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    initial_state = piece_factory._build_state_machine(piece_dir, cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(initial_state, State)
    assert initial_state is not None
    
    # בדיקת transitions
    assert "move" in initial_state.transitions
    assert "jump" in initial_state.transitions
    
    move_state = initial_state.transitions["move"]
    jump_state = initial_state.transitions["jump"]
    
    assert isinstance(move_state, State)
    assert isinstance(jump_state, State)
    assert "long_rest" in move_state.transitions
    assert "short_rest" in jump_state.transitions

def test_WhenBuildStateMachineCalledWithValidDir_ThenStatesHaveCorrectComponents(piece_factory, temp_pieces_dir):
    """בדיקה: כל state במכונת הסטטים מכיל את הרכיבים הנדרשים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_dir = temp_pieces_dir / "QW"
    cell = (0, 0)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    initial_state = piece_factory._build_state_machine(piece_dir, cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקת idle state
    assert initial_state._moves is not None
    assert initial_state._graphics is not None
    assert initial_state._physics is not None
    
    # בדיקת move state
    move_state = initial_state.transitions["move"]
    assert move_state._moves is not None
    assert move_state._graphics is not None
    assert move_state._physics is not None
    
    # בדיקת jump state
    jump_state = initial_state.transitions["jump"]
    assert jump_state._moves is not None
    assert jump_state._graphics is not None
    assert jump_state._physics is not None

# ────────────────────────────── Error Handling Tests ──────────────────────────────

def test_WhenCreatePieceCalledWithNonExistentType_ThenRaisesFileNotFoundError(piece_factory):
    """בדיקה: יצירת כלי עם סוג לא קיים זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    non_existent_type = "INVALID_PIECE"
    cell = (0, 0)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises((FileNotFoundError, ValueError)):
        piece_factory.create_piece(non_existent_type, cell)

def test_WhenCreatePieceCalledWithInvalidCell_ThenStillCreatesValidPiece(piece_factory):
    """בדיקה: יצירת כלי עם תא לא תקין עדיין יוצרת כלי (התיקוף הוא אחריות אחרת)"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    invalid_cell = (-1, -1)  # תא מחוץ לגבולות
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece = piece_factory.create_piece(piece_type, invalid_cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(piece, Piece)
    assert piece.get_id().startswith(piece_type)

def test_WhenBuildStateMachineCalledWithMissingStates_ThenRaisesKeyError(piece_factory, temp_pieces_dir):
    """בדיקה: בניית state machine עם states חסרים זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # יצירת תיקיית כלי עם state אחד בלבד
    incomplete_dir = temp_pieces_dir / "INCOMPLETE"
    incomplete_dir.mkdir()
    
    # העתקת moves.txt
    qw_dir = temp_pieces_dir / "QW"
    shutil.copy2(qw_dir / "moves.txt", incomplete_dir / "moves.txt")
    
    # יצירת תיקיית states עם state אחד בלבד
    states_dir = incomplete_dir / "states"
    states_dir.mkdir()
    
    idle_dir = states_dir / "idle"
    idle_dir.mkdir()
    
    config = {"physics": {"duration": 1000}, "graphics": {"fps": 10}}
    with open(idle_dir / "config.json", "w") as f:
        json.dump(config, f)
    
    sprites_dir = idle_dir / "sprites"
    sprites_dir.mkdir()
    with open(sprites_dir / "1.png", "wb") as f:
        f.write(b"fake_image_data")
    
    cell = (0, 0)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises(KeyError):
        piece_factory._build_state_machine(incomplete_dir, cell)

@patch('builtins.open', side_effect=FileNotFoundError)
def test_WhenBuildStateMachineCalledWithMissingConfig_ThenRaisesFileNotFoundError(mock_open, piece_factory, temp_pieces_dir):
    """בדיקה: בניית state machine עם config.json חסר זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_dir = temp_pieces_dir / "QW"
    cell = (0, 0)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises(FileNotFoundError):
        piece_factory._build_state_machine(piece_dir, cell)

@patch('builtins.open', mock_open(read_data='invalid json'))
def test_WhenBuildStateMachineCalledWithInvalidConfig_ThenRaisesJSONDecodeError(piece_factory, temp_pieces_dir):
    """בדיקה: בניית state machine עם JSON לא תקין זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_dir = temp_pieces_dir / "QW"
    cell = (0, 0)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises(json.JSONDecodeError):
        piece_factory._build_state_machine(piece_dir, cell)

# ────────────────────────────── Edge Cases Tests ──────────────────────────────

def test_WhenCreatePieceCalledWithZeroCell_ThenCreatesValidPiece(piece_factory):
    """בדיקה: יצירת כלי בתא (0,0) עובדת נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    zero_cell = (0, 0)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece = piece_factory.create_piece(piece_type, zero_cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(piece, Piece)
    assert piece.get_id() == "QW_1"

def test_WhenCreatePieceCalledWithMaxBoardCell_ThenCreatesValidPiece(piece_factory):
    """בדיקה: יצירת כלי בתא הגדול ביותר של הלוח עובדת נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    max_cell = (7, 7)  # הלוח הוא 8x8
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece = piece_factory.create_piece(piece_type, max_cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(piece, Piece)
    assert piece.get_id() == "QW_1"

def test_WhenCreateManyPiecesOfSameType_ThenCounterIncrementsCorrectly(piece_factory):
    """בדיקה: יצירת הרבה כלים מאותו סוג מגדילה נכון את המונה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    cell = (0, 0)
    num_pieces = 100
    
    # ─── ACT ──────────────────────────────────────────────────────────
    pieces = []
    for i in range(num_pieces):
        piece = piece_factory.create_piece(piece_type, cell)
        pieces.append(piece)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert len(pieces) == num_pieces
    
    # בדיקת ID ייחודיים
    ids = [piece.get_id() for piece in pieces]
    assert len(set(ids)) == num_pieces
    
    # בדיקת המונה
    assert piece_factory.counter[piece_type] == num_pieces
    
    # בדיקת הסדר
    assert pieces[0].get_id() == "QW_1"
    assert pieces[num_pieces-1].get_id() == f"QW_{num_pieces}"

def test_WhenCreatePieceCalledWithEmptyString_ThenRaisesError(piece_factory):
    """בדיקה: יצירת כלי עם string ריק זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    empty_type = ""
    cell = (0, 0)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises((FileNotFoundError, OSError, ValueError)):
        piece_factory.create_piece(empty_type, cell)

def test_WhenCreatePieceCalledWithNoneCell_ThenRaisesTypeError(piece_factory):
    """בדיקה: יצירת כלי עם cell=None זורקת שגיאה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    none_cell = None
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    with pytest.raises(TypeError):
        piece_factory.create_piece(piece_type, none_cell)

# ────────────────────────────── Performance Tests ──────────────────────────────

def test_WhenCreateMultiplePiecesSequentially_ThenPerformanceIsReasonable(piece_factory):
    """בדיקה: יצירת מספר כלים ברצף מתבצעת בזמן סביר"""
    import time
    
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    cell = (0, 0)
    num_pieces = 10
    
    # ─── ACT ──────────────────────────────────────────────────────────
    start_time = time.time()
    pieces = []
    for i in range(num_pieces):
        piece = piece_factory.create_piece(piece_type, cell)
        pieces.append(piece)
    end_time = time.time()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    execution_time = end_time - start_time
    assert execution_time < 5.0  # צריך להסתיים תוך 5 שניות
    assert len(pieces) == num_pieces

# ────────────────────────────── Integration Tests ──────────────────────────────

def test_WhenPieceFactoryUsedWithRealPiecesDirectory_ThenWorksCorrectly(board):
    """בדיקה: PieceFactory עובד נכון עם תיקיית הכלים האמיתית"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # שימוש בתיקיית הכלים האמיתית
    current_dir = Path(__file__).parent.parent
    real_pieces_root = current_dir / ".." / "pieces"
    
    # דילוג על הבדיקה אם התיקייה לא קיימת
    if not real_pieces_root.exists():
        pytest.skip("Real pieces directory not found")
    
    factory = PieceFactory(board, real_pieces_root)
    cell = (0, 0)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    piece = factory.create_piece("QW", cell)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert isinstance(piece, Piece)
    assert piece.get_id().startswith("QW")

def test_WhenFactoryUsedWithMultipleThreads_ThenCountersRemainConsistent(piece_factory):
    """בדיקה: שימוש במפעל עם threads מרובים שומר על עקביות המונים"""
    import threading
    import time
    
    # ─── ARRANGE ──────────────────────────────────────────────────────
    piece_type = "QW"
    cell = (0, 0)
    num_threads = 5
    pieces_per_thread = 5
    all_pieces = []
    threads = []
    
    def create_pieces():
        thread_pieces = []
        for i in range(pieces_per_thread):
            piece = piece_factory.create_piece(piece_type, cell)
            thread_pieces.append(piece)
            time.sleep(0.01)  # סימולציה של עבודה
        all_pieces.extend(thread_pieces)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    for i in range(num_threads):
        thread = threading.Thread(target=create_pieces)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    total_pieces = num_threads * pieces_per_thread
    assert len(all_pieces) == total_pieces
    
    # בדיקת ID ייחודיים
    ids = [piece.get_id() for piece in all_pieces]
    assert len(set(ids)) == total_pieces
    
    # בדיקת המונה
    assert piece_factory.counter[piece_type] == total_pieces
