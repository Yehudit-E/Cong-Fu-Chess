import csv
import pathlib
import time
import queue
import cv2
from typing import Dict, Tuple, Optional
import threading
import keyboard
from Board import Board
from Command import Command
from Piece import Piece
from img import Img
from PieceFactory import PieceFactory
from Bus.EventBus import EventBus

class Game:
    def __init__(self, board: Board, pieces_root: pathlib.Path, placement_csv: pathlib.Path, event_bus: EventBus):
        self.board = board
        self.user_input_queue = queue.Queue()
        self.start_time = time.monotonic()
        self.piece_factory = PieceFactory(board, pieces_root, event_bus)
        self.pieces: Dict[str, Piece] = {}
        self.pos_to_piece: Dict[Tuple[int, int], Piece] = {}
        self._current_board = None
        self._load_pieces_from_csv(placement_csv)
        self.focus_cell = (0, 0)
        self._selection_mode = "source"  # עבור משתמש ראשון
        self._selected_source: Optional[Tuple[int, int]] = None
        self.event_bus = event_bus

        # --- משתנים למשתמש השני ---
        self.focus_cell2 = (self.board.H_cells - 1, 0)  # התחלה בתחתית
        self._selection_mode2 = "source"
        self._selected_source2: Optional[Tuple[int, int]] = None
        
        self._lock = threading.Lock()
        self._running = True

    def _load_pieces_from_csv(self, csv_path: pathlib.Path):
        with csv_path.open() as f:
            reader = csv.reader(f)
            for row_idx, row in enumerate(reader):
                for col_idx, code in enumerate(row):
                    code = code.strip()
                    if not code:
                        continue
                    cell = (row_idx, col_idx)
                    piece = self.piece_factory.create_piece(code, cell)
                    self.pieces[piece.get_id()] = piece
                    self.pos_to_piece[cell] = piece

    def game_time_ms(self) -> int:
        return int((time.monotonic() - self.start_time) * 1000)

    def clone_board(self) -> Board:
        return self.board.clone()

    def start_keyboard_thread(self):
        def keyboard_loop():
            while self._running:
                time.sleep(0.05)
                with self._lock:
                    # --- טיפול בקלט למשתמש הראשון ---
                    dy, dx = 0, 0
                    if keyboard.is_pressed('esc'):
                        self._running = False
                        break
                    if keyboard.is_pressed('left'):
                        dx = -1
                    elif keyboard.is_pressed('right'):
                        dx = 1
                    if keyboard.is_pressed('up'):
                        dy = -1
                    elif keyboard.is_pressed('down'):
                        dy = 1
                    if dx != 0 or dy != 0:
                        h, w = self.board.H_cells, self.board.W_cells
                        y, x = self.focus_cell
                        self.focus_cell = ((y + dy) % h, (x + dx) % w)
                        time.sleep(0.2)
                    if keyboard.is_pressed('enter'):
                        self._on_enter_pressed()
                        time.sleep(0.2)

                    # --- טיפול בקלט למשתמש השני ---
                    dy2, dx2 = 0, 0
                    if keyboard.is_pressed('a'):
                        dx2 = -1
                    elif keyboard.is_pressed('d'):
                        dx2 = 1
                    if keyboard.is_pressed('w'):
                        dy2 = -1
                    elif keyboard.is_pressed('s'):
                        dy2 = 1
                    if dx2 != 0 or dy2 != 0:
                        h, w = self.board.H_cells, self.board.W_cells
                        y2, x2 = self.focus_cell2
                        self.focus_cell2 = ((y2 + dy2) % h, (x2 + dx2) % w)
                        time.sleep(0.2)
                    if keyboard.is_pressed('space'):
                        self._on_space_pressed()
                        time.sleep(0.2)
                    if keyboard.is_pressed('right shift'):
                        self._on_jump_pressed(player=1)
                        time.sleep(0.2)

                    if keyboard.is_pressed('left shift'):
                        self._on_jump_pressed(player=2)
                        time.sleep(0.2)
        threading.Thread(target=keyboard_loop, daemon=True).start()

    def _on_jump_pressed(self, player: int):
        if player == 1:
            if self.focus_cell in self.pos_to_piece:
                piece = self.pos_to_piece[self.focus_cell]
                if not piece.get_id()[1] == 'B':
                    print("User 1 cannot jump with this piece.")
                    return
                src_alg = self.board.cell_to_algebraic(self.focus_cell)
                cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=piece.get_id(),
                    type="jump",
                    params=[src_alg,src_alg]
                )
                self.user_input_queue.put(cmd)

        elif player == 2:
            if self.focus_cell2 in self.pos_to_piece:
                piece = self.pos_to_piece[self.focus_cell2]
                if not piece.get_id()[1] == 'W':
                    print("User 2 cannot jump with this piece.")
                    return
                src_alg = self.board.cell_to_algebraic(self.focus_cell2)
                cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=piece.get_id(),
                    type="jump",
                    params=[src_alg,src_alg]
                )
                self.user_input_queue.put(cmd)

    def _wait_for_enter(self, message: str, background: Optional[Img] = None):
        if background:
            img = Img()
            img.img = background.img.copy()
        else:
            img = Img()
            img.img = self.board.img.img.copy()

        lines = message.split('\n')
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.4
        thickness = 2
        color = (0, 0, 255, 255)

        total_height = 0
        line_sizes = []
        for line in lines:
            (w, h), _ = cv2.getTextSize(line, font, font_scale, thickness)
            line_sizes.append((w, h))
            total_height += h + 10

        y0 = (img.img.shape[0] - total_height) // 2

        for i, line in enumerate(lines):
            w, h = line_sizes[i]
            x = (img.img.shape[1] - w) // 2
            y = y0 + h + i * (h + 10)
            img.put_text(line, x, y, font_scale, color=color, thickness=thickness)

        cv2.imshow("Chess", img.img)
        print(message)

        while True:
            key = cv2.waitKey(100)
            if key == 13:
                break

        cv2.destroyAllWindows()



    # def run(self):

    #     self._wait_for_enter("Press ENTER\n to start the game")
    #     # אתחול ת'ראד הקלט
    #     self.start_keyboard_thread()

    #     start_ms = self.game_time_ms()
    #     for piece in self.pieces.values():
    #         piece.reset(start_ms)

    #     while self._running and not self._is_win():
    #         now = self.game_time_ms()

    #         # עדכון הכלים
    #         for piece in self.pieces.values():
    #             piece.update(now , self.pos_to_piece)

    #         # עידכון המפה של המיקומים
    #         self._update_position_mapping()

    #         # טיפול בפקודות המתינות בתור
    #         while not self.user_input_queue.empty():
    #             cmd = self.user_input_queue.get()
    #             cell = self.board.algebraic_to_cell(cmd.params[0])
    #             if cell in self.pos_to_piece:
    #                 self.pos_to_piece[cell].on_command(cmd, now,self.pos_to_piece)

    #         self._draw()

    #         cv2.imshow("Chess", self._current_board.img.img)
    #         # שימוש ב-waitKey קצר לצורך צביעת החלון בלבד
    #         cv2.waitKey(1)

    #     self._announce_win()
    #     self._running = False
    #     cv2.destroyAllWindows()

    def run(self):
        self.start_keyboard_thread()

        # --- רקע ---
        background = Img().read("../background.png")
        board_offset = (450, 100)
        self._wait_for_enter("Press ENTER\n to start the game",background)

        start_ms = self.game_time_ms()
        for piece in self.pieces.values():
            piece.reset(start_ms)

        while self._running and not self._is_win():
            now = self.game_time_ms()

            for piece in self.pieces.values():
                piece.update(now , self.pos_to_piece)

            self._update_position_mapping()

            while not self.user_input_queue.empty():
                cmd = self.user_input_queue.get()
                cell = self.board.algebraic_to_cell(cmd.params[0])
                if cell in self.pos_to_piece:
                     self.pos_to_piece[cell].on_command(cmd, now, self.pos_to_piece)

            self._draw()

            # יצירת תמונת מסך חדשה כל פריים
            frame = Img()
            frame.img = background.img.copy()
            self._current_board.img.draw_on(frame, *board_offset)

            cv2.imshow("Chess", frame.img)
            cv2.waitKey(1)

        self._announce_win()
        self._running = False
        cv2.destroyAllWindows()


    def _update_position_mapping(self):
        self.pos_to_piece.clear()
        to_remove = set()

        for piece in list(self.pieces.values()):  # שימוש ב-list כדי להקפיא את הערכים בזמן הלולאה
            x, y = map(int, piece._state._physics.get_pos())
            cell_x = x / self.board.cell_W_pix
            cell_y = y / self.board.cell_H_pix
            pos = (cell_y, cell_x)
            if pos in self.pos_to_piece:
                opponent = self.pos_to_piece[pos]
                print(piece._state._current_command)
                print(opponent._state._current_command)
                print(opponent._state._current_command.type in ["idle", "long_rest", "short_rest"])
                print()
                if (opponent._state._current_command.type in ["idle", "long_rest", "short_rest"] or
                        (piece._state._current_command and
                         piece._state._current_command.type not in ["idle", "long_rest", "short_rest"] and
                        opponent._state._physics.start_time > piece._state._physics.start_time and
                        opponent._state._current_command.type != "jump") or
                        piece._state._current_command.type == "jump"):
                    print(f"Removing opponent {opponent.get_id()} at {pos}")
                    self.pos_to_piece[pos] = piece
                    to_remove.add(opponent.get_id())
                else:
                    print(f"Removing piece {piece.get_id()} at {pos}")
                    to_remove.add(piece.get_id())
            else:
                self.pos_to_piece[pos] = piece

        for k in to_remove:
            self.event_bus.publish("piece_captured", {"piece": k})
            self.pieces.pop(k, None)  # pop עם None כדי למנוע שגיאת KeyError



    def _draw(self):
        board = self.clone_board()
        now_ms = self.game_time_ms()

        for piece in self.pieces.values():
            piece.draw_on_board(board, now_ms)

        # ציור ריבוע פוקוס למשתמש ראשון (צהוב)
        y, x = self.focus_cell
        x1 = x * self.board.cell_W_pix
        y1 = y * self.board.cell_H_pix
        x2 = (x + 1) * self.board.cell_W_pix
        y2 = (y + 1) * self.board.cell_H_pix
        cv2.rectangle(board.img.img, (x1, y1), (x2, y2), (0, 255, 255), 2)

        # ציור ריבוע פוקוס למשתמש שני (כחול)
        y2_, x2_ = self.focus_cell2
        sx1 = x2_ * self.board.cell_W_pix
        sy1 = y2_ * self.board.cell_H_pix
        sx2 = (x2_ + 1) * self.board.cell_W_pix
        sy2 = (y2_ + 1) * self.board.cell_H_pix
        cv2.rectangle(board.img.img, (sx1, sy1), (sx2, sy2), (255, 0, 0), 2)

        # ציור ריבוע בחירה של המקור עבור משתמש ראשון
        if self._selected_source:
            sy, sx = self._selected_source
            sx1 = sx * self.board.cell_W_pix
            sy1 = sy * self.board.cell_H_pix
            sx2 = (sx + 1) * self.board.cell_W_pix
            sy2 = (sy + 1) * self.board.cell_H_pix
            cv2.rectangle(board.img.img, (sx1, sy1), (sx2, sy2), (0, 0, 255), 2)

        # ציור ריבוע בחירה של המקור עבור משתמש שני
        if self._selected_source2:
            sy, sx = self._selected_source2
            sx1 = sx * self.board.cell_W_pix
            sy1 = sy * self.board.cell_H_pix
            sx2 = (sx + 1) * self.board.cell_W_pix
            sy2 = (sy + 1) * self.board.cell_H_pix
            cv2.rectangle(board.img.img, (sx1, sy1), (sx2, sy2), (0, 255, 0), 2)

        self._current_board = board

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces.values() if p.get_id().lower().startswith("k")]
        return len(kings) <= 1

    def _announce_win(self):
        img = Img()
        img.img = self.board.img.img.copy()

        kings = [p for p in self.pieces.values() if p.get_id().startswith("KW") or p.get_id().startswith("KB")]

        if len(kings) == 2:
            message = "Both kings still on board. No winner yet."
            color = (255, 255, 255, 255)  # לבן
        elif len(kings) == 1:
            winner_king = kings[0]
            winner_color = "White" if winner_king.get_id().startswith("KW") else "Black"
            message = f"{winner_color} Wins!"
            color = (0, 0, 255, 255)
        else:
            message = "Draw – both kings are gone."
            color = (0, 0, 255, 255)  # אפור

        # מרכז הטקסט על התמונה
        text_size, _ = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)
        text_x = (img.img.shape[1] - text_size[0]) // 2
        text_y = (img.img.shape[0] + text_size[1]) // 2

        img.put_text(message, text_x, text_y, font_size=2, color=color, thickness=3)

        cv2.imshow("Chess", img.img)
        print("Press ENTER to exit...")

        # מחכים עד שלחצו Enter (key code 13) ואז סוגרים
        while True:
            key = cv2.waitKey(100)
            if key == 13:  # Enter
                break

        cv2.destroyAllWindows()

    def _on_enter_pressed(self):
        # טיפול בבחירה עבור משתמש ראשון
        if self._selection_mode == "source":
            if self.focus_cell in self.pos_to_piece:
                piece = self.pos_to_piece[self.focus_cell]
                # בדיקה שהכלי שייך למשתמש הראשון (מזהה שמתחיל ב-"B")
                if not piece.get_id()[1] == 'B':
                    print("User 1 cannot select this piece.")
                    return
                src_alg = self.board.cell_to_algebraic(self.focus_cell)
                # print(f"User 1 source selected at {self.focus_cell} -> {src_alg}")
                self._selected_source = self.focus_cell
                self._selection_mode = "dest"
        elif self._selection_mode == "dest":
            if self._selected_source is None:
                return
            src_cell = self._selected_source
            dst_cell = self.focus_cell
            src_alg = self.board.cell_to_algebraic(src_cell)
            dst_alg = self.board.cell_to_algebraic(dst_cell)
            # print(f"User 1 destination selected at {dst_cell} -> {dst_alg}")
            piece = self.pos_to_piece.get(src_cell)
            if piece:
                cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=piece.get_id(),  # או get_id() לפי מה שמשמש בפקודות
                    type="move",
                    params=[src_alg, dst_alg]
                )
                self.user_input_queue.put(cmd)
            self._reset_selection()

    def _on_space_pressed(self):
        # טיפול בבחירה עבור משתמש שני
        if self._selection_mode2 == "source":
            if self.focus_cell2 in self.pos_to_piece:
                piece = self.pos_to_piece[self.focus_cell2]
                # בדיקה שהכלי שייך למשתמש השני (מזהה שמתחיל ב-"W")
                if not piece.get_id()[1] == 'W':
                    print("User 2 cannot select this piece.")
                    return
                src_alg = self.board.cell_to_algebraic(self.focus_cell2)
                # print(f"User 2 source selected at {self.focus_cell2} -> {src_alg}")
                self._selected_source2 = self.focus_cell2
                self._selection_mode2 = "dest"
        elif self._selection_mode2 == "dest":
            if self._selected_source2 is None:
                return
            src_cell = self._selected_source2
            dst_cell = self.focus_cell2
            src_alg = self.board.cell_to_algebraic(src_cell)
            dst_alg = self.board.cell_to_algebraic(dst_cell)
            print(f"User 2 destination selected at {dst_cell} -> {dst_alg}")
            piece = self.pos_to_piece.get(src_cell)
            if piece:
                cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=piece.get_id(),
                    type="move",
                    params=[src_alg, dst_alg]
                )
                self.user_input_queue.put(cmd)
            self._reset_selection2()

    def _reset_selection(self):
        self._selection_mode = "source"
        self._selected_source = None

    def _reset_selection2(self):
        self._selection_mode2 = "source"
        self._selected_source2 = None