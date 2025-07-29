"""
קובץ בדיקות עבור מחלקת GameSounds
בודק את כל הפונקציונליות של ניהול הקולות במשחק
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
import threading
from pathlib import Path
import pygame

# Import the class under test
import sys
sys.path.append('..')
from GameSounds import GameSounds
from Bus.EventBus import Event


class TestGameSounds:
    """
    מחלקת בדיקות עבור GameSounds
    בודקת את כל הפונקציות עם דפוס Arrange-Act-Assert
    """

    def test_init_with_successful_pygame_initialization(self):
        """
        בדיקת אתחול מוצלח של GameSounds עם pygame
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None
        
        Notes:
            בודק שהמערכת מאותחלת נכון כאשר pygame עובד
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            
            # Act
            game_sounds = GameSounds()
            
            # Assert
            assert game_sounds.sound_enabled == True
            assert game_sounds.sounds_folder == Path("..") / "snd"
            assert game_sounds.sound_cooldown == 0.1
            assert isinstance(game_sounds.last_sound_time, dict)

    def test_init_with_failed_pygame_initialization(self):
        """
        בדיקת אתחול כאשר pygame נכשל
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת עובדת במצב שקט כאשר pygame נכשל
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            
            # Act
            game_sounds = GameSounds()
            
            # Assert
            assert game_sounds.sound_enabled == False

    def test_init_with_custom_sounds_folder(self):
        """
        בדיקת אתחול עם תיקיית קולות מותאמת אישית
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת יכולה לעבוד עם תיקייה מותאמת אישית
        """
        # Arrange
        custom_folder = "custom_sounds"
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            
            # Act
            game_sounds = GameSounds(sounds_folder=custom_folder)
            
            # Assert
            assert game_sounds.sounds_folder == Path("..") / custom_folder

    def test_load_sounds_when_sound_disabled(self):
        """
        בדיקת טעינת קולות כאשר השמע מושבת
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהפונקציה לא עושה כלום כאשר השמע מושבת
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            game_sounds = GameSounds()
            
            # Act
            game_sounds._load_sounds()
            
            # Assert
            assert len(game_sounds.sounds) == 0

    def test_load_sounds_with_existing_files(self):
        """
        בדיקת טעינת קולות עם קבצים קיימים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שקבצי קול קיימים נטענים בהצלחה
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pygame.mixer.Sound') as mock_sound:
            
            # Act
            game_sounds = GameSounds()
            
            # Assert
            assert mock_sound.call_count > 0
            assert len(game_sounds.sounds) > 0

    def test_load_sounds_with_missing_files(self):
        """
        בדיקת טעינת קולות עם קבצים חסרים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם קבצים חסרים
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('pathlib.Path.exists', return_value=False):
            
            # Act
            game_sounds = GameSounds()
            
            # Assert
            assert len(game_sounds.sounds) == 0

    def test_load_sounds_with_file_loading_error(self):
        """
        בדיקת טעינת קולות עם שגיאה בטעינת קובץ
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם שגיאות טעינה
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pygame.mixer.Sound', side_effect=Exception("Load failed")):
            
            # Act
            game_sounds = GameSounds()
            
            # Assert
            assert len(game_sounds.sounds) == 0

    def test_can_play_sound_first_time(self):
        """
        בדיקת יכולת נגינת קול בפעם הראשונה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שקול יכול להיות מנוגן בפעם הראשונה
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            game_sounds = GameSounds()
            
            # Act
            result = game_sounds._can_play_sound("test_sound")
            
            # Assert
            assert result == True
            assert "test_sound" in game_sounds.last_sound_time

    def test_can_play_sound_within_cooldown(self):
        """
        בדיקת יכולת נגינת קול בתוך תקופת ההמתנה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שקול לא יכול להיות מנוגן שוב בתוך תקופת ההמתנה
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            game_sounds = GameSounds()
            game_sounds._can_play_sound("test_sound")  # First call
            
            # Act
            result = game_sounds._can_play_sound("test_sound")  # Second call immediately
            
            # Assert
            assert result == False

    def test_can_play_sound_after_cooldown(self):
        """
        בדיקת יכולת נגינת קול אחרי תקופת ההמתנה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שקול יכול להיות מנוגן שוב אחרי תקופת ההמתנה
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            game_sounds = GameSounds()
            game_sounds.sound_cooldown = 0.01  # Short cooldown for testing
            game_sounds._can_play_sound("test_sound")  # First call
            
            # Act
            time.sleep(0.02)  # Wait for cooldown
            result = game_sounds._can_play_sound("test_sound")  # Second call after cooldown
            
            # Assert
            assert result == True

    def test_play_sound_when_disabled(self):
        """
        בדיקת נגינת קול כאשר השמע מושבת
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהפונקציה לא עושה כלום כאשר השמע מושבת
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")):
            game_sounds = GameSounds()
            
            # Act
            result = game_sounds.play_sound(["test.wav"])
            
            # Assert
            assert result is None

    def test_play_sound_with_empty_list(self):
        """
        בדיקת נגינת קול עם רשימה רקה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהפונקציה לא עושה כלום עם רשימה רקה
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            
            # Act
            result = game_sounds.play_sound([])
            
            # Assert
            assert result is None

    def test_play_sound_with_valid_file(self):
        """
        בדיקת נגינת קול עם קובץ תקף
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שקול מנוגן בהצלחה עם קובץ תקף
        """
        # Arrange
        mock_sound = Mock()
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            game_sounds.sounds["test.wav"] = mock_sound
            
            # Act
            game_sounds.play_sound(["test.wav"])
            
            # Assert
            mock_sound.set_volume.assert_called_once_with(0.7)
            mock_sound.play.assert_called_once()

    def test_play_sound_with_nonexistent_file(self):
        """
        בדיקת נגינת קול עם קובץ שלא קיים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם קובץ שלא קיים
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            
            # Act
            result = game_sounds.play_sound(["nonexistent.wav"])
            
            # Assert
            assert result is None

    def test_play_sound_with_exception(self):
        """
        בדיקת נגינת קול עם שגיאה בנגינה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם שגיאות נגינה
        """
        # Arrange
        mock_sound = Mock()
        mock_sound.play.side_effect = Exception("Play failed")
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            game_sounds.sounds["test.wav"] = mock_sound
            
            # Act
            result = game_sounds.play_sound(["test.wav"])
            
            # Assert
            assert result is None

    def test_handle_game_start_with_cooldown_allowed(self):
        """
        בדיקת טיפול באירוע התחלת משחק כאשר ניתן לנגן
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתחילה רצף קולות התחלה כאשר מותר
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch('threading.Thread') as mock_thread:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_game_start(mock_event)
            
            # Assert
            mock_thread.assert_called_once()

    def test_handle_game_start_with_cooldown_blocked(self):
        """
        בדיקת טיפול באירוע התחלת משחק כאשר חסום על ידי cooldown
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת לא מתחילה רצף כאשר בתקופת המתנה
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch('threading.Thread') as mock_thread:
            game_sounds = GameSounds()
            game_sounds.handle_game_start(mock_event)  # First call
            
            # Act
            game_sounds.handle_game_start(mock_event)  # Second call immediately
            
            # Assert
            assert mock_thread.call_count == 1  # Should only be called once

    def test_handle_game_end(self):
        """
        בדיקת טיפול באירוע סיום משחק
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מנגנת קול ניצחון בסיום המשחק
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_game_end(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.victory_sounds, volume=0.8)

    def test_handle_piece_command_jump(self):
        """
        בדיקת טיפול בפקודת קפיצה של כלי
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מזהה ומנגנת קול קפיצה
        """
        # Arrange
        mock_event = Mock()
        mock_event.data = {"description": "knight jumps to e4"}
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_command(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.jump_sounds, volume=0.6)

    def test_handle_piece_command_move(self):
        """
        בדיקת טיפול בפקודת תנועה של כלי
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מזהה ומנגנת קול תנועה
        """
        # Arrange
        mock_event = Mock()
        mock_event.data = {"description": "pawn moves to e4"}
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_command(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.move_sounds, volume=0.5)

    def test_handle_piece_command_no_description(self):
        """
        בדיקת טיפול בפקודת כלי ללא תיאור
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם פקודה ללא תיאור
        """
        # Arrange
        mock_event = Mock()
        mock_event.data = {}
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_command(mock_event)
            
            # Assert
            mock_play.assert_not_called()

    def test_handle_piece_command_with_cooldown_blocked(self):
        """
        בדיקת טיפול בפקודת כלי כאשר חסום על ידי cooldown
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת לא מנגנת כאשר בתקופת המתנה
        """
        # Arrange
        mock_event = Mock()
        mock_event.data = {"description": "knight jumps to e4"}
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            game_sounds.handle_piece_command(mock_event)  # First call
            
            # Act
            game_sounds.handle_piece_command(mock_event)  # Second call immediately
            
            # Assert
            assert mock_play.call_count == 1  # Should only be called once

    def test_handle_piece_captured(self):
        """
        בדיקת טיפול באירוע אכילת כלי
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מנגנת קול אכילה כאשר כלי נאכל
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_captured(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.capture_sounds, volume=0.7)

    def test_handle_piece_move(self):
        """
        בדיקת טיפול באירוע תנועת כלי
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מנגנת קול תנועה כאשר כלי זז
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_move(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.move_sounds, volume=0.5)

    def test_handle_piece_jump(self):
        """
        בדיקת טיפול באירוע קפיצת כלי
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מנגנת קול קפיצה כאשר כלי קופץ
        """
        # Arrange
        mock_event = Mock()
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_jump(mock_event)
            
            # Assert
            mock_play.assert_called_once_with(game_sounds.jump_sounds, volume=0.6)

    def test_cleanup_when_sound_enabled(self):
        """
        בדיקת ניקוי כאשר השמע מופעל
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מנקה נכון את pygame כאשר השמע מופעל
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('pygame.mixer.quit') as mock_quit:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.cleanup()
            
            # Assert
            mock_quit.assert_called_once()

    def test_cleanup_when_sound_disabled(self):
        """
        בדיקת ניקוי כאשר השמע מושבת
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת לא מנקה את pygame כאשר השמע מושבת
        """
        # Arrange
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch('pygame.mixer.quit') as mock_quit:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.cleanup()
            
            # Assert
            mock_quit.assert_not_called()

    def test_play_start_sequence_with_all_sounds(self):
        """
        בדיקת רצף התחלה עם כל הקולות קיימים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שרצף ההתחלה עובד נכון כאשר כל הקולות קיימים
        """
        # Arrange
        mock_ready = Mock()
        mock_steady = Mock()
        mock_go = Mock()
        
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('time.sleep'):
            game_sounds = GameSounds()
            game_sounds.sounds["Ready.wav"] = mock_ready
            game_sounds.sounds["Steady.wav"] = mock_steady
            game_sounds.sounds["Go!.wav"] = mock_go
            
            # Act
            game_sounds._play_start_sequence()
            
            # Assert
            mock_ready.set_volume.assert_called_once_with(0.8)
            mock_ready.play.assert_called_once()
            mock_steady.set_volume.assert_called_once_with(0.8)
            mock_steady.play.assert_called_once()
            mock_go.set_volume.assert_called_once_with(0.9)
            mock_go.play.assert_called_once()

    def test_play_start_sequence_with_missing_sounds(self):
        """
        בדיקת רצף התחלה עם קולות חסרים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שרצף ההתחלה עובד נכון גם כאשר חלק מהקולות חסרים
        """
        # Arrange
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'), \
             patch('time.sleep'):
            game_sounds = GameSounds()
            
            # Act
            result = game_sounds._play_start_sequence()
            
            # Assert
            assert result is None  # Should complete without error

    def test_play_start_sequence_with_exception(self):
        """
        בדיקת רצף התחלה עם שגיאה
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שרצף ההתחלה מתמודד נכון עם שגיאות
        """
        # Arrange
        mock_sound = Mock()
        mock_sound.play.side_effect = Exception("Play failed")
        
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            game_sounds.sounds["Ready.wav"] = mock_sound
            
            # Act
            result = game_sounds._play_start_sequence()
            
            # Assert
            assert result is None  # Should complete without crashing

    def test_event_subscription(self):
        """
        בדיקת רישום לאירועים
        
        Args:
            None
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת נרשמת נכון לכל האירועים הנדרשים
        """
        # Arrange
        mock_event_bus = Mock()
        
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'):
            game_sounds = GameSounds()
            game_sounds.event_bus = mock_event_bus
            
            # Act
            game_sounds._subscribe_to_events()
            
            # Assert
            expected_calls = [
                call("game_start", game_sounds.handle_game_start),
                call("game_end", game_sounds.handle_game_end),
                call("piece_command", game_sounds.handle_piece_command),
                call("piece_captured", game_sounds.handle_piece_captured),
                call("piece_move", game_sounds.handle_piece_move),
                call("piece_jump", game_sounds.handle_piece_jump)
            ]
            mock_event_bus.subscribe.assert_has_calls(expected_calls, any_order=True)

    @pytest.mark.parametrize("description,expected_sound", [
        ("knight jumps to e4", "jump"),
        ("pawn moves to e4", "move"),
        ("queen JUMPS to h8", "jump"),
        ("rook MOVES forward", "move"),
        ("", None),
        ("invalid command", None)
    ])
    def test_handle_piece_command_various_descriptions(self, description, expected_sound):
        """
        בדיקת טיפול בפקודות שונות של כלים
        
        Args:
            description (str): תיאור הפקודה
            expected_sound (str): הקול הצפוי
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מזהה נכון סוגי פקודות שונים
        """
        # Arrange
        mock_event = Mock()
        mock_event.data = {"description": description}
        with patch('pygame.mixer.pre_init', side_effect=Exception("Sound failed")), \
             patch.object(GameSounds, 'play_sound') as mock_play:
            game_sounds = GameSounds()
            
            # Act
            game_sounds.handle_piece_command(mock_event)
            
            # Assert
            if expected_sound == "jump":
                mock_play.assert_called_once_with(game_sounds.jump_sounds, volume=0.6)
            elif expected_sound == "move":
                mock_play.assert_called_once_with(game_sounds.move_sounds, volume=0.5)
            else:
                mock_play.assert_not_called()

    @pytest.mark.parametrize("volume", [0.0, 0.5, 1.0, 1.5, -0.1])
    def test_play_sound_with_different_volumes(self, volume):
        """
        בדיקת נגינת קול עם רמות עוצמה שונות
        
        Args:
            volume (float): רמת העוצמה לבדיקה
        
        Returns:
            None
            
        Raises:
            None
        
        Notes:
            בודק שהמערכת מתמודדת נכון עם רמות עוצמה שונות
        """
        # Arrange
        mock_sound = Mock()
        with patch('pygame.mixer.pre_init'), \
             patch('pygame.mixer.init'), \
             patch('pygame.mixer.get_init'), \
             patch.object(GameSounds, '_load_sounds'), \
             patch.object(GameSounds, '_subscribe_to_events'):
            game_sounds = GameSounds()
            game_sounds.sounds["test.wav"] = mock_sound
            
            # Act
            game_sounds.play_sound(["test.wav"], volume=volume)
            
            # Assert
            mock_sound.set_volume.assert_called_once_with(volume)
            mock_sound.play.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
