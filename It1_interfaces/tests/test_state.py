import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# הוספת הנתיב למודולים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from State import State
from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics

# ────────────────────────────── Fixtures ──────────────────────────────

@pytest.fixture
def mock_moves():
    """יוצר mock Moves למטרות בדיקה"""
    return Mock(spec=Moves)

@pytest.fixture
def mock_graphics():
    """יוצר mock Graphics למטרות בדיקה"""
    return Mock(spec=Graphics)

@pytest.fixture
def mock_physics():
    """יוצר mock Physics למטרות בדיקה"""
    mock = Mock(spec=Physics)
    mock.update.return_value = None  # ברירת מחדל - אין פקודה חדשה
    return mock

@pytest.fixture
def mock_command():
    """יוצר mock Command למטרות בדיקה"""
    mock = Mock(spec=Command)
    mock.type = "move"
    return mock

@pytest.fixture
def state_instance(mock_moves, mock_graphics, mock_physics):
    """יוצר instance של State עם mocks"""
    return State(mock_moves, mock_graphics, mock_physics)

# ────────────────────────────── Basic Functionality Tests ──────────────────────────────

def test_WhenStateCreated_ThenInitializesCorrectly(mock_moves, mock_graphics, mock_physics):
    """בדיקה: יצירת State מאתחלת נכון את כל המאפיינים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # (mocks מוכנים)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state = State(mock_moves, mock_graphics, mock_physics)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert state._moves is mock_moves
    assert state._graphics is mock_graphics
    assert state._physics is mock_physics
    assert isinstance(state.transitions, dict)
    assert len(state.transitions) == 0
    assert state._current_command is None

def test_WhenSetTransition_ThenTransitionStored(state_instance):
    """בדיקה: הגדרת transition שומרת את המעבר בדיקטונרי"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    target_state = Mock(spec=State)
    event_name = "jump"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.set_transition(event_name, target_state)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert event_name in state_instance.transitions
    assert state_instance.transitions[event_name] is target_state

def test_WhenSetMultipleTransitions_ThenAllTransitionsStored(state_instance):
    """בדיקה: הגדרת מספר transitions שומרת את כולם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    target_state1 = Mock(spec=State)
    target_state2 = Mock(spec=State)
    target_state3 = Mock(spec=State)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.set_transition("move", target_state1)
    state_instance.set_transition("jump", target_state2)
    state_instance.set_transition("idle", target_state3)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert len(state_instance.transitions) == 3
    assert state_instance.transitions["move"] is target_state1
    assert state_instance.transitions["jump"] is target_state2
    assert state_instance.transitions["idle"] is target_state3

# ────────────────────────────── Reset Tests ──────────────────────────────

def test_WhenReset_ThenCommandSetAndComponentsReset(state_instance, mock_command):
    """בדיקה: reset מגדיר את הפקודה ומאפס את הרכיבים"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # (state_instance ו-mock_command מוכנים)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.reset(mock_command)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert state_instance._current_command is mock_command
    state_instance._graphics.reset.assert_called_once_with(mock_command)
    state_instance._physics.reset.assert_called_once_with(mock_command)

def test_WhenResetWithNoneCommand_ThenCommandSetToNone(state_instance):
    """בדיקה: reset עם None מגדיר את הפקודה ל-None"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # הגדרת פקודה קיימת
    state_instance._current_command = Mock(spec=Command)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.reset(None)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert state_instance._current_command is None
    state_instance._graphics.reset.assert_called_once_with(None)
    state_instance._physics.reset.assert_called_once_with(None)

# ────────────────────────────── Update Tests ──────────────────────────────

def test_WhenUpdate_WithNoNewCommand_ThenReturnsSelf(state_instance):
    """בדיקה: update ללא פקודה חדשה מחזיר את עצמו"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 1000
    state_instance._physics.update.return_value = None  # אין פקודה חדשה
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.update(now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is state_instance
    state_instance._graphics.update.assert_called_once_with(now_ms)
    state_instance._physics.update.assert_called_once_with(now_ms)

def test_WhenUpdate_WithNewCommand_ThenProcessesCommand(state_instance, mock_command):
    """בדיקה: update עם פקודה חדשה מעבד את הפקודה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 1500
    new_command = Mock(spec=Command)
    new_command.type = "jump"
    
    state_instance._physics.update.return_value = new_command
    
    # Mock process_command
    target_state = Mock(spec=State)
    from unittest.mock import patch
    with patch.object(state_instance, 'process_command', return_value=target_state) as mock_process:
        
        # ─── ACT ──────────────────────────────────────────────────────────
        result = state_instance.update(now_ms)
        
        # ─── ASSERT ───────────────────────────────────────────────────────
        assert result is target_state
        mock_process.assert_called_once_with(new_command, now_ms)
        state_instance._graphics.update.assert_called_once_with(now_ms)
        state_instance._physics.update.assert_called_once_with(now_ms)

# ────────────────────────────── Process Command Tests ──────────────────────────────

def test_WhenProcessCommand_WithValidTransition_ThenReturnsTargetState(state_instance):
    """בדיקה: process_command עם transition תקין מחזיר את state היעד"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 2000
    command = Mock(spec=Command)
    command.type = "move"
    
    target_state = Mock(spec=State)
    state_instance.set_transition("move", target_state)
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.process_command(command, now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is target_state
    target_state.reset.assert_called_once_with(command)

def test_WhenProcessCommand_WithInvalidTransition_ThenReturnsSelf(state_instance):
    """בדיקה: process_command עם transition לא קיים מחזיר את עצמו"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 2500
    command = Mock(spec=Command)
    command.type = "nonexistent_command"
    
    # לא מגדירים transition לפקודה הזו
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.process_command(command, now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is state_instance

def test_WhenProcessCommand_WithNoneCommandType_ThenReturnsSelf(state_instance):
    """בדיקה: process_command עם None command type מחזיר את עצמו"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 3000
    command = Mock(spec=Command)
    command.type = None
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.process_command(command, now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is state_instance

# ────────────────────────────── Can Transition Tests ──────────────────────────────

def test_WhenCanTransition_WithNoCommand_ThenReturnsFalse(state_instance):
    """בדיקה: can_transition ללא פקודה מחזיר False"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 3500
    state_instance._physics.update.return_value = None
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.can_transition(now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is False
    state_instance._physics.update.assert_called_once_with(now_ms)

def test_WhenCanTransition_WithCommand_ThenReturnsTrue(state_instance):
    """בדיקה: can_transition עם פקודה מחזיר True"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 4000
    command = Mock(spec=Command)
    state_instance._physics.update.return_value = command
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.can_transition(now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is True
    state_instance._physics.update.assert_called_once_with(now_ms)

# ────────────────────────────── Get Command Tests ──────────────────────────────

def test_WhenGetCommand_WithNoCommand_ThenReturnsNone(state_instance):
    """בדיקה: get_command ללא פקודה מחזיר None"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    # state_instance מאותחל עם None command
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.get_command()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is None

def test_WhenGetCommand_WithCommand_ThenReturnsCommand(state_instance, mock_command):
    """בדיקה: get_command עם פקודה מחזיר את הפקודה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    state_instance._current_command = mock_command
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.get_command()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is mock_command

def test_WhenGetCommand_AfterReset_ThenReturnsNewCommand(state_instance, mock_command):
    """בדיקה: get_command אחרי reset מחזיר את הפקודה החדשה"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    new_command = Mock(spec=Command)
    new_command.type = "jump"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.reset(new_command)
    result = state_instance.get_command()
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is new_command

# ────────────────────────────── Integration Tests ──────────────────────────────

def test_WhenCompleteStateTransition_ThenAllComponentsWork(state_instance):
    """בדיקה: מעבר state מלא עובד נכון"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 5000
    
    # יצירת target state
    target_state = Mock(spec=State)
    
    # הגדרת transition
    state_instance.set_transition("jump", target_state)
    
    # הגדרת פקודה חדשה מ-physics
    new_command = Mock(spec=Command)
    new_command.type = "jump"
    state_instance._physics.update.return_value = new_command
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.update(now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is target_state
    
    # וידוא שכל הרכיבים עודכנו
    state_instance._graphics.update.assert_called_once_with(now_ms)
    state_instance._physics.update.assert_called_once_with(now_ms)
    
    # וידוא שה-target state אופס
    target_state.reset.assert_called_once_with(new_command)

def test_WhenMultipleUpdatesWithoutTransition_ThenStaysInSameState(state_instance):
    """בדיקה: עדכונים מרובים ללא transition שומרים על אותו state"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    times = [1000, 2000, 3000, 4000]
    state_instance._physics.update.return_value = None  # תמיד אין פקודה
    
    # ─── ACT & ASSERT ─────────────────────────────────────────────────
    for time_ms in times:
        result = state_instance.update(time_ms)
        assert result is state_instance
    
    # וידוא שכל העדכונים התבצעו
    assert state_instance._graphics.update.call_count == len(times)
    assert state_instance._physics.update.call_count == len(times)

# ────────────────────────────── Edge Cases Tests ──────────────────────────────

def test_WhenOverwriteTransition_ThenNewTransitionReplacesPrevious(state_instance):
    """בדיקה: שכתוב transition מחליף את הקודם"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    first_target = Mock(spec=State)
    second_target = Mock(spec=State)
    event_name = "move"
    
    # ─── ACT ──────────────────────────────────────────────────────────
    state_instance.set_transition(event_name, first_target)
    state_instance.set_transition(event_name, second_target)  # שכתוב
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert state_instance.transitions[event_name] is second_target
    assert state_instance.transitions[event_name] is not first_target

def test_WhenProcessCommandWithEmptyType_ThenReturnsSelf(state_instance):
    """בדיקה: process_command עם type ריק מחזיר את עצמו"""
    # ─── ARRANGE ──────────────────────────────────────────────────────
    now_ms = 6000
    command = Mock(spec=Command)
    command.type = ""
    
    # ─── ACT ──────────────────────────────────────────────────────────
    result = state_instance.process_command(command, now_ms)
    
    # ─── ASSERT ───────────────────────────────────────────────────────
    assert result is state_instance
