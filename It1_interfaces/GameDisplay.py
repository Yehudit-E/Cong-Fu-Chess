import cv2
import numpy as np
from typing import List, Tuple
from Bus.EventBus import Event, EventBus
from img import Img

class GameDisplay:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.white_moves: List[str] = []
        self.black_moves: List[str] = []
        self.white_score = 0
        self.black_score = 0
        
        # רישום לאירועים
        self.event_bus.subscribe("piece_captured", self.on_piece_captured)
        self.event_bus.subscribe("piece_moved", self.on_piece_moved)
        self.event_bus.subscribe("game_start", self.on_game_start)
        self.event_bus.subscribe("game_end", self.on_game_end)
        
        # הגדרות עיצוב
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 1
        self.white_color = (255, 255, 255)
        self.black_color = (0, 0, 0)
        self.bg_color = (200, 200, 200)
        
    def on_piece_captured(self, event: Event):
        """מעדכן את הניקוד כאשר כלי נתפס"""
        piece = event.data["piece"]
        piece_values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}
        
        piece_type = piece[0]
        piece_color = piece[1]
        value = piece_values.get(piece_type, 0)
        
        if piece_color == "B":  # שחור נתפס - לבן מקבל נקודות
            self.white_score += value
        else:  # לבן נתפס - שחור מקבל נקודות
            self.black_score += value
            
    def on_piece_moved(self, event: Event):
        """מעדכן את רשימת המהלכים"""
        piece = event.data["piece"]
        move_desc = event.data["move"]
        time_str = event.data["time"]
        
        move_text = f"{piece}: {move_desc} ({time_str})"
        
        if piece[1] == "W":  # כלי לבן
            self.white_moves.append(move_text)
            # שמירה על 15 המהלכים האחרונים
            if len(self.white_moves) > 15:
                self.white_moves.pop(0)
        else:  # כלי שחור
            self.black_moves.append(move_text)
            if len(self.black_moves) > 15:
                self.black_moves.pop(0)
                
    def on_game_start(self, event: Event):
        """הודעה בתחילת המשחק"""
        print("🏁 המשחק מתחיל! Kung Fu Chess")
        
    def on_game_end(self, event: Event):
        """הודעה בסוף המשחק"""
        winner = event.data.get("winner", "תיקו")
        print(f"🏆 המשחק הסתיים! מנצח: {winner}")
        
    def draw_score_panel(self, img: Img, x: int, y: int, width: int, height: int):
        """מציר את לוח הניקוד"""
        # רקע ללוח הניקוד
        cv2.rectangle(img.img, (x, y), (x + width, y + height), self.bg_color, -1)
        cv2.rectangle(img.img, (x, y), (x + width, y + height), self.black_color, 2)
        
        # כותרת
        title = "SCORE"
        title_size = cv2.getTextSize(title, self.font, self.font_scale, self.font_thickness)[0]
        title_x = x + (width - title_size[0]) // 2
        cv2.putText(img.img, title, (title_x, y + 25), self.font, self.font_scale, self.black_color, self.font_thickness)
        
        # ניקוד לבן
        white_text = f"White: {self.white_score}"
        cv2.putText(img.img, white_text, (x + 10, y + 50), self.font, self.font_scale, self.black_color, self.font_thickness)
        
        # ניקוד שחור
        black_text = f"Black: {self.black_score}"
        cv2.putText(img.img, black_text, (x + 10, y + 75), self.font, self.font_scale, self.black_color, self.font_thickness)
        
    def draw_moves_panel(self, img: Img, x: int, y: int, width: int, height: int, moves: List[str], title: str):
        """מציר את לוח המהלכים"""
        # רקע ללוח המהלכים
        cv2.rectangle(img.img, (x, y), (x + width, y + height), self.bg_color, -1)
        cv2.rectangle(img.img, (x, y), (x + width, y + height), self.black_color, 2)
        
        # כותרת
        title_size = cv2.getTextSize(title, self.font, self.font_scale, self.font_thickness)[0]
        title_x = x + (width - title_size[0]) // 2
        cv2.putText(img.img, title, (title_x, y + 25), self.font, self.font_scale, self.black_color, self.font_thickness)
        
        # המהלכים
        line_height = 20
        start_y = y + 45
        
        for i, move in enumerate(moves[-12:]):  # מציג את 12 המהלכים האחרונים
            if start_y + i * line_height < y + height - 10:
                # קיצור הטקסט אם הוא ארוך מדי
                if len(move) > 25:
                    move = move[:22] + "..."
                cv2.putText(img.img, move, (x + 5, start_y + i * line_height), 
                           self.font, 0.4, self.black_color, 1)
                           
    def draw_ui(self, img: Img):
        """מציר את כל ה-UI על התמונה"""
        img_height, img_width = img.img.shape[:2]
        
        # פאנל ניקוד עליון
        score_width = 200
        score_height = 100
        score_x = (img_width - score_width) // 2
        score_y = 10
        self.draw_score_panel(img, score_x, score_y, score_width, score_height)
        
        # פאנל מהלכים לבן (שמאל)
        moves_width = 300
        moves_height = 400
        white_moves_x = 10
        white_moves_y = 150
        self.draw_moves_panel(img, white_moves_x, white_moves_y, moves_width, moves_height, 
                             self.white_moves, "WHITE MOVES")
        
        # פאנל מהלכים שחור (ימין)
        black_moves_x = img_width - moves_width - 10
        black_moves_y = 150
        self.draw_moves_panel(img, black_moves_x, black_moves_y, moves_width, moves_height, 
                             self.black_moves, "BLACK MOVES")
