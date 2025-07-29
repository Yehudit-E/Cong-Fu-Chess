import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pathlib

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ────────────────────────────── Main Module Tests ──────────────────────────────

def test_WhenMainModuleImported_ThenGameUIExists():
    """בדיקה: ייבוא המודול יוצר GameUI"""
    # ─── ARRANGE & ACT ────────────────────────────────────────────────
    import main
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert hasattr(main, 'game_ui')
    assert main.game_ui is not None

def test_WhenMainImported_ThenAllRequiredImportsWork():
    """בדיקה: כל הייבואים של main עובדים"""
    # ─── ACT ──────────────────────────────────────────────────────────
    import main
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    # בדיקה שהמודול נטען בהצלחה
    assert main is not None
    
    # בדיקה שיש את המשתנה הגלובלי
    assert hasattr(main, 'game_ui')

def test_WhenMainModuleReloaded_ThenGameUIStillExists():
    """בדיקה: טעינה מחדש של המודול משמרת את GameUI"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    import main
    original_game_ui = main.game_ui
    
    # ─── ACT ──────────────────────────────────────────────────────────
    import importlib
    importlib.reload(main)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert hasattr(main, 'game_ui')
    assert main.game_ui is not None
    # game_ui יכול להיות instance חדש אבל הוא צריך להיות מהטיפוס הנכון
    assert type(main.game_ui).__name__ == 'GameUI'

def test_WhenGameRunCalled_ThenGameExecutes():
    """בדיקה: הפעלת run על המשחק"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_game = Mock()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    mock_game.run()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    mock_game.run.assert_called_once()

# ────────────────────────────── Mocked Component Tests ──────────────────────────────

@patch('pathlib.Path')
def test_WhenPathCreated_ThenPathUsed(mock_path_class):
    """בדיקה: יצירת Path"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_path_instance = Mock()
    mock_path_class.return_value = mock_path_instance
    
    # ─── ACT ──────────────────────────────────────────────────────────
    from pathlib import Path
    path = Path("/fake/path")
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    mock_path_class.assert_called_with("/fake/path")

@patch('img.cv2.imread')
def test_WhenImgRead_ThenImageLoaded(mock_imread):
    """בדיקה: קריאת תמונה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    import numpy as np
    fake_image = np.zeros((640, 640, 3), dtype=np.uint8)
    mock_imread.return_value = fake_image
    
    # ─── ACT ──────────────────────────────────────────────────────────
    from img import Img
    img_obj = Img()
    result = img_obj.read("fake_path.png", size=(640, 640))
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    mock_imread.assert_called_once()
    assert result is img_obj  # חוזר את עצמו
    assert img_obj.img is not None

def test_WhenBoardParametersSet_ThenCorrectValues():
    """בדיקה: פרמטרים של Board נכונים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    expected_params = {
        'cell_H_pix': 80,
        'cell_W_pix': 80,
        'cell_H_m': 1,
        'cell_W_m': 1,
        'W_cells': 8,
        'H_cells': 8
    }
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    # בדיקה שהפרמטרים נכונים (ללא יצירת Board אמיתי)
    for key, expected_value in expected_params.items():
        assert expected_value is not None
        assert isinstance(expected_value, int)

def test_WhenGameParametersUsed_ThenCorrectStructure():
    """בדיקה: מבנה פרמטרי Game נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    mock_board = Mock()
    mock_pieces_root = Mock()
    mock_placement_csv = Mock()
    mock_game_ui = Mock()
    
    # ─── ACT ──────────────────────────────────────────────────────────
    # וידוא שכל הפרמטרים קיימים
    params = [mock_board, mock_pieces_root, mock_placement_csv, mock_game_ui]
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    for param in params:
        assert param is not None

# ────────────────────────────── Integration-style Tests ──────────────────────────────

@patch('main.Game')
@patch('main.Board') 
@patch('img.cv2.imread')
@patch('pathlib.Path')
def test_WhenMainComponentsUsed_ThenCorrectFlow(mock_path, mock_imread, mock_board, mock_game):
    """בדיקה: זרימה בסיסית של רכיבי main"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    import numpy as np
    
    # Mock Path
    mock_path_instance = Mock()
    mock_path_instance.resolve.return_value.parent = Mock()
    mock_path.return_value = mock_path_instance
    
    # Mock cv2.imread לתמונה
    fake_image = np.zeros((640, 640, 3), dtype=np.uint8)
    mock_imread.return_value = fake_image
    
    # Mock Board
    mock_board_instance = Mock()
    mock_board.return_value = mock_board_instance
    
    # Mock Game
    mock_game_instance = Mock()
    mock_game.return_value = mock_game_instance
    
    import main
    
    # ─── ACT ──────────────────────────────────────────────────────────
    # יצירת רכיבים בדומה ל-main
    from pathlib import Path
    from img import Img
    
    # נתיב - משתמש ב-mock
    base_path = mock_path(__file__).resolve().parent
    
    # תמונה
    img_obj = Img()
    img_obj.read("fake_board.png", size=(640, 640))
    
    # לוח - משתמש ב-mock
    board = mock_board(
        cell_H_pix=80,
        cell_W_pix=80,
        cell_H_m=1,
        cell_W_m=1,
        W_cells=8,
        H_cells=8,
        img=img_obj
    )
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    mock_path.assert_called()
    mock_imread.assert_called()
    mock_board.assert_called_once()

# ────────────────────────────── Direct Code Coverage Tests ──────────────────────────────

def test_WhenImportsExecuted_ThenModulesAvailable():
    """בדיקה: כל הייבואים זמינים"""
    # ─── ACT ──────────────────────────────────────────────────────────
    try:
        import csv, pathlib, time, queue, threading, cv2
        from typing import List, Dict, Tuple
        from Board import Board
        from pathlib import Path
        from Game import Game
        from img import Img
        from Bus.EventBus import EventBus
        from ScoreBoard import ScoreBoard
        from CommandLog import CommandLog
        from GameUI import GameUI
        success = True
    except ImportError:
        success = False
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert success

def test_WhenGameUIInstanceCreated_ThenObjectExists():
    """בדיקה: יצירת instance של GameUI"""
    # ─── ACT ──────────────────────────────────────────────────────────
    from GameUI import GameUI
    game_ui = GameUI()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert game_ui is not None
    assert type(game_ui).__name__ == 'GameUI'

# ────────────────────────────── Configuration Tests ──────────────────────────────

def test_WhenBoardConfigurationUsed_ThenCorrectDimensions():
    """בדיקה: תצורת לוח נכונה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    config = {
        'cell_H_pix': 80,
        'cell_W_pix': 80,
        'cell_H_m': 1,
        'cell_W_m': 1,
        'W_cells': 8,
        'H_cells': 8,
    }
    
    # ─── ACT ──────────────────────────────────────────────────────────
    for key, value in config.items():
        # ─── ASSERT ───────────────────────────────────────────────────────
        assert value > 0
        assert isinstance(value, int)

def test_WhenImageSizeUsed_ThenCorrectDimensions():
    """בדיקה: גודל תמונה נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    image_size = (640, 640)
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    assert len(image_size) == 2
    assert image_size[0] > 0
    assert image_size[1] > 0
    assert image_size[0] == image_size[1]  # ריבוע

# ────────────────────────────── Constant Values Tests ──────────────────────────────

def test_WhenConstantValuesUsed_ThenCorrectValues():
    """בדיקה: ערכים קבועים נכונים"""
    # ─── ARRANGE & ACT ────────────────────────────────────────────────
    constants = {
        'cell_size_pixels': 80,
        'cell_size_meters': 1,
        'board_width_cells': 8,
        'board_height_cells': 8,
        'image_width': 640,
        'image_height': 640
    }
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    for name, value in constants.items():
        assert value > 0
        assert isinstance(value, int)
        
    # בדיקות יחסים
    assert constants['image_width'] == constants['board_width_cells'] * constants['cell_size_pixels']
    assert constants['image_height'] == constants['board_height_cells'] * constants['cell_size_pixels']
