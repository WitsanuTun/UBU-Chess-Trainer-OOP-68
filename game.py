import pygame
import chess
import chess.pgn
import threading
import pyperclip
import math

# Import Modules
from settings import *
from board import Board
from renderer import GameRenderer
from engine_client import EngineClient


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Chess Trainer - Lite")

        # View
        self.renderer = GameRenderer(self.screen)

        # Model
        self.board_visual = Board(DEFAULT_SQUARE_SIZE)
        self.board_logic = chess.Board()

        self._init_game_state()
        self._init_engine()

        self.recalculate_layout()
        self.reset_game()

        self.running = True
        self.clock = pygame.time.Clock()

    def _init_game_state(self):
        self.is_dark_mode = True
        self.board_flipped = False
        self.selected_square = None
        self.valid_moves = []
        self.move_history_san = []
        self.move_history_obj = []
        self.current_move_idx = 0
        self.game_over = False
        self.game_result_msg = ""
        self.in_check = False
        self.checked_king_pos = None

        # Analysis Data (เหลือแค่ 3 ตัวนี้พอ)
        self.best_move_text = ""
        self.eval_cp = None
        self.eval_mate = None

        self.is_promoting = False
        self.promotion_data = {}
        self.is_dragging = False
        self.dragging_piece = None
        self.right_click_start = None
        self.user_arrows = []
        self.user_highlights = []
        self.pgn_scroll_y = 0
        self.max_scroll_y = 0
        self.is_dragging_scrollbar = False
        self.drag_offset_y = 0
        self.pgn_view_rect = None
        self.pgn_click_zones = []
        self.ui_buttons = {}
        self.dropdown_data = None
        self.premove_squares = []
        self.animation = None
        self.shake_pos = None
        self.shake_offset = (0, 0)
        self.shake_timer = 0

    def _init_engine(self):
        self.engine_enabled = False
        self.engine_color = chess.BLACK
        self.engine_elo = 1200
        self.engine_locked = False
        self.elo_dropdown_open = False
        self.elo_options = [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000]

        # Dual Engine: ตัวหนึ่งเล่น อีกตัวหนึ่งคำนวณกราฟ
        self.engine = EngineClient(elo=self.engine_elo, think_time=0.5)
        self.analysis_engine = EngineClient(elo=3000, think_time=0.1)

        # ใช้ตัวแปรนี้แทน review_mode เดิม (เอาไว้เปิดปิดกราฟ)
        self.show_eval = False

    def recalculate_layout(self):
        self.window_width, self.window_height = self.screen.get_size()
        w, h = self.window_width, self.window_height
        margin = 45
        self.panel_w = 360
        avail_w = w - (margin * 2) - self.panel_w - 25
        avail_h = h - (margin * 2)
        sq_size = max(32, min(avail_w // 8, avail_h // 8))
        self.square_size = sq_size
        self.board_visual.set_square_size(sq_size)
        bsize = sq_size * 8
        self.board_x = max(margin, (w - bsize - self.panel_w - 25) // 2)
        self.board_y = margin
        self.panel_x = self.board_x + bsize + 25

    def reset_game(self):
        self.board_logic.reset()
        self.board_visual.load_from_fen(self.board_logic.board_fen())
        self.turn_color = "white"
        self.board_flipped = False
        if self.engine_enabled and self.engine_color == chess.WHITE:
            self.board_flipped = True
        self.move_history_san = []
        self.move_history_obj = []
        self.current_move_idx = 0
        self.game_over = False
        self.game_result_msg = ""
        self.selected_square = None
        self.valid_moves.clear()
        self.in_check = False
        self.checked_king_pos = None
        self.is_promoting = False
        self.engine_locked = False
        self.user_arrows = []
        self.user_highlights = []
        self.best_move_text = ""
        self.eval_cp = None
        self.eval_mate = None

        # เริ่มวิเคราะห์ทันทีถ้าเปิดโหมดอยู่
        self.analyze_board()
        self.trigger_engine_move()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self.recalculate_layout()
                elif event.type == pygame.USEREVENT:
                    if hasattr(event, 'engine_move'): self.process_move(event.engine_move, animate=True)
                else:
                    self.handle_event(event)
            self.update_shake()
            self.update_animation()
            self.renderer.draw_game(self)
            self.clock.tick(60)
        self.engine.close()
        self.analysis_engine.close()
        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.is_promoting:
                    self._handle_promotion_sel(event.pos)
                elif self.elo_dropdown_open:
                    self._handle_dropdown(event.pos)
                else:
                    self._handle_click(event.pos)
            elif event.button == 3:
                self._handle_rclick(event.pos)
            elif event.button in (4, 5):
                d = 1 if event.button == 4 else -1
                self.pgn_scroll_y = max(0, min(self.max_scroll_y, self.pgn_scroll_y - d * 20))
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._handle_release(event.pos)
            elif event.button == 3:
                self._handle_rclick_up(event.pos)
        elif event.type == pygame.MOUSEWHEEL:
            self.pgn_scroll_y = max(0, min(self.max_scroll_y, self.pgn_scroll_y - event.y * 20))
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_scrollbar:
                new_y = event.pos[1] - self.drag_offset_y
                track = self.ui_buttons.get("scrollbar_track")
                thumb = self.ui_buttons.get("scrollbar_thumb")
                if track and thumb:
                    ratio = (new_y - track.top) / (track.height - thumb.height)
                    self.pgn_scroll_y = max(0, min(self.max_scroll_y, int(ratio * self.max_scroll_y)))
        elif event.type == pygame.KEYDOWN:
            if not self.is_promoting:
                if event.key == pygame.K_LEFT:
                    self.jump_to_move(self.current_move_idx - 1)
                elif event.key == pygame.K_RIGHT:
                    self.jump_to_move(self.current_move_idx + 1)

    def _handle_click(self, pos):
        if self.user_arrows or self.user_highlights: self.user_arrows = []; self.user_highlights = []
        x, y = pos
        if x >= self.panel_x: self._handle_panel_click(pos); return
        if self.game_over: return
        if self.current_move_idx != len(self.move_history_obj): return

        is_my_turn = not (self.engine_enabled and self.board_logic.turn == self.engine_color)
        if not is_my_turn: return

        if not (
                self.board_x <= x < self.board_x + self.square_size * 8 and self.board_y <= y < self.board_y + self.square_size * 8):
            self.selected_square = None;
            self.valid_moves = [];
            return

        r, c = self.screen_to_board(x, y)
        piece = self.board_visual.get_piece(r, c)
        if self.animation: return

        if piece and piece.color == self.turn_color:
            self.is_dragging = True;
            self.dragging_piece = (r, c);
            self.selected_square = (r, c)
            self.valid_moves = []
            src = chess.square(c, 7 - r)
            for m in self.board_logic.legal_moves:
                if m.from_square == src: self.valid_moves.append(self._chess_sq_to_rowcol(m.to_square))
        elif (r, c) in self.valid_moves:
            self._execute_move(r, c)
        else:
            self.selected_square = None; self.valid_moves = []

    def _handle_release(self, pos):
        self.is_dragging_scrollbar = False
        is_my_turn = not (self.engine_enabled and self.board_logic.turn == self.engine_color)
        if not is_my_turn: self.is_dragging = False; self.dragging_piece = None; return

        if self.is_dragging and self.dragging_piece:
            x, y = pos
            if self.board_x <= x < self.board_x + self.square_size * 8 and self.board_y <= y < self.board_y + self.square_size * 8:
                dr, dc = self.screen_to_board(x, y)
                if (dr, dc) != self.dragging_piece:
                    if (dr, dc) in self.valid_moves: self._execute_move(dr, dc)
            self.is_dragging = False;
            self.dragging_piece = None

    def _execute_move(self, r, c):
        start = self.selected_square
        if start is None: return
        p = self.board_visual.get_piece(*start)
        if p and p.kind == "pawn" and ((p.color == "white" and r == 0) or (p.color == "black" and r == 7)):
            self.is_promoting = True;
            self.promotion_data = {"from": start, "to": (r, c), "color": p.color}
            self.selected_square = None;
            self.valid_moves = [];
            return
        src = self.rowcol_to_uci(*start);
        dst = self.rowcol_to_uci(r, c)
        move = chess.Move.from_uci(src + dst)
        if move in self.board_logic.legal_moves: self.process_move(move, animate=True)
        self.selected_square = None;
        self.valid_moves = []

    def process_move(self, move, animate=True, is_replay=False):
        is_ep = False
        try:
            if self.board_logic.is_en_passant(move): is_ep = True
        except:
            pass

        if not is_replay:
            self.user_arrows = [];
            self.user_highlights = []
            san = self.board_logic.san(move)
            self.board_logic.push(move)
            self.move_history_san.append(san)
            self.move_history_obj.append(move)
            self.current_move_idx = len(self.move_history_obj)
            self.pgn_scroll_y = 999999

        self.turn_color = "black" if self.board_logic.turn == chess.BLACK else "white"
        src_r, src_c = self._chess_sq_to_rowcol(move.from_square)
        dst_r, dst_c = self._chess_sq_to_rowcol(move.to_square)
        piece = self.board_visual.get_piece(src_r, src_c)

        if animate and piece:
            sx, sy = self.board_visual.to_screen(src_r, src_c, self.board_x, self.board_y, self.board_flipped)
            ex, ey = self.board_visual.to_screen(dst_r, dst_c, self.board_x, self.board_y, self.board_flipped)
            self._visual_move(piece, src_r, src_c, dst_r, dst_c, move, is_ep)
            self.animation = {
                "piece": piece, "start_pos": (sx, sy), "end_pos": (ex, ey),
                "current_pos": (sx, sy), "t": 0.0, "speed": 0.12, "hide_square": (dst_r, dst_c)
            }
        else:
            if piece: self._visual_move(piece, src_r, src_c, dst_r, dst_c, move, is_ep)
            self._on_move_complete()

    def _visual_move(self, piece, sr, sc, dr, dc, move, is_ep=False):
        if piece.kind == "king" and abs(sc - dc) == 2:
            is_kingside = (dc == 6)
            rk_src = 7 if is_kingside else 0
            rk_dst = 5 if is_kingside else 3
            self.board_visual.move_piece(sr, sc, dr, dc)
            self.board_visual.move_piece(sr, rk_src, sr, rk_dst)
        elif is_ep:
            self.board_visual.move_piece(sr, sc, dr, dc)
            self.board_visual.remove_piece(sr, dc)
        elif move.promotion:
            self.board_visual.move_piece(sr, sc, dr, dc)
            self.board_visual.load_from_fen(self.board_logic.board_fen())
        else:
            self.board_visual.move_piece(sr, sc, dr, dc)

    def undo_move(self):
        if self.current_move_idx <= 0: return
        self.animation = None
        steps = 2 if self.engine_enabled and len(self.move_history_obj) >= 2 else 1
        target_idx = max(0, self.current_move_idx - steps)
        self.move_history_obj = self.move_history_obj[:target_idx]
        self.move_history_san = self.move_history_san[:target_idx]
        self.current_move_idx = target_idx
        self._hard_reset_board()

    def jump_to_move(self, target_idx):
        if self.animation: return
        target_idx = max(0, min(target_idx, len(self.move_history_obj)))
        self.current_move_idx = target_idx
        self._hard_reset_board()

    def _hard_reset_board(self):
        self.board_logic.reset()
        for i in range(self.current_move_idx):
            self.board_logic.push(self.move_history_obj[i])
        self.board_visual.load_from_fen(self.board_logic.board_fen())
        self.turn_color = "white" if self.board_logic.turn == chess.WHITE else "black"
        self.game_over = False
        self.game_result_msg = ""
        self.selected_square = None
        self.valid_moves = []
        self.user_arrows = []
        self.in_check = False
        self.checked_king_pos = None
        if self.current_move_idx == 0: self.engine_locked = False
        self.check_game_status()
        self.analyze_board()

    def update_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            offset = math.sin(self.shake_timer * 1.5) * 4
            self.shake_offset = (offset, 0)
            if self.shake_timer == 0: self.shake_pos = None

    def update_animation(self):
        if self.animation:
            self.animation["t"] += self.animation["speed"]
            t = self.animation["t"]
            clamped_t = max(0.0, min(1.0, t))
            progress = 1 - math.pow(1 - clamped_t, 3)
            sx, sy = self.animation["start_pos"]
            ex, ey = self.animation["end_pos"]
            cur_x = sx + (ex - sx) * progress
            cur_y = sy + (ey - sy) * progress
            self.animation["current_pos"] = (cur_x, cur_y)
            if t >= 1.0:
                self.animation = None
                self._on_move_complete()

    def _on_move_complete(self):
        self.turn_color = "white" if self.board_logic.turn == chess.WHITE else "black"
        self.check_game_status()
        self.analyze_board()
        self.trigger_engine_move()

    def check_game_status(self):
        self.in_check = self.board_logic.is_check()
        if self.board_logic.is_checkmate():
            self.game_over = True
            w = "Black" if self.board_logic.turn == chess.WHITE else "White"
            self.game_result_msg = f"Checkmate! {w} wins."
        elif self.board_logic.is_stalemate():
            self.game_over = True; self.game_result_msg = "Draw (Stalemate)"
        elif self.board_logic.is_insufficient_material():
            self.game_over = True; self.game_result_msg = "Draw (Material)"
        elif self.board_logic.can_claim_threefold_repetition():
            self.game_over = True; self.game_result_msg = "Draw (Repetition)"
        self.checked_king_pos = self.get_king_pos() if self.in_check else None
        if self.in_check: self.shake_pos = self.checked_king_pos; self.shake_timer = 25

    def analyze_board(self):
        # ถ้าไม่เปิดโหมด Eval (Show Eval) ก็ไม่ต้องคิด
        if not self.show_eval: return

        def task():
            try:
                current_fen = self.board_logic.fen()
                temp_board = chess.Board(current_fen)
                info = self.analysis_engine.analyse_position(temp_board)
                if info:
                    self.eval_cp = info.get("cp")
                    self.eval_mate = info.get("mate")
                    if "pv" in info and len(info["pv"]) > 0:
                        best_move = info["pv"][0]
                        self.best_move_text = temp_board.san(best_move)
                    else:
                        self.best_move_text = ""
            except Exception as e:
                pass

        threading.Thread(target=task, daemon=True).start()

    def trigger_engine_move(self):
        if self.animation: return
        if self.current_move_idx < len(self.move_history_obj): return
        if self.engine_enabled and not self.game_over and self.board_logic.turn == self.engine_color:
            self.make_engine_move()

    def make_engine_move(self):
        def task():
            m = self.engine.choose_move(self.board_logic)
            if m: pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'engine_move': m}))

        threading.Thread(target=task, daemon=True).start()

    def copy_pgn(self):
        try:
            pyperclip.copy(str(chess.pgn.Game.from_board(self.board_logic)))
        except:
            pass

    def screen_to_board(self, x, y):
        c = (x - self.board_x) // self.square_size
        r = (y - self.board_y) // self.square_size
        return (7 - r, 7 - c) if self.board_flipped else (r, c)

    def rowcol_to_uci(self, r, c):
        return chess.square_name(chess.square(c, 7 - r))

    def _chess_sq_to_rowcol(self, sq):
        return 7 - chess.square_rank(sq), chess.square_file(sq)

    def get_king_pos(self):
        k = self.board_logic.king(self.board_logic.turn)
        return self._chess_sq_to_rowcol(k) if k is not None else None

    # --- UI Handlers ---
    def _handle_panel_click(self, pos):
        x, y = pos
        b = self.ui_buttons
        if b.get("theme_toggle") and b["theme_toggle"].collidepoint(x, y): self.toggle_theme()
        if b.get("engine_toggle") and b["engine_toggle"].collidepoint(x, y):
            self.engine_enabled = not self.engine_enabled
            if self.engine_enabled: self.trigger_engine_move()

        # เปลี่ยนจาก Review เป็น Show Eval (เปิดปิดกราฟเฉยๆ)
        if b.get("review_toggle") and b["review_toggle"].collidepoint(x, y):
            self.show_eval = not self.show_eval
            self.analyze_board()

        if self.engine_enabled:
            if b.get("side_white") and b["side_white"].collidepoint(x, y): self.engine_color = chess.BLACK
            if b.get("side_black") and b["side_black"].collidepoint(x, y): self.engine_color = chess.WHITE
            if b.get("elo_head") and b["elo_head"].collidepoint(x,
                                                                y): self.elo_dropdown_open = not self.elo_dropdown_open
        if b.get("new") and b["new"].collidepoint(x, y): self.reset_game()
        if b.get("flip") and b["flip"].collidepoint(x, y): self.board_flipped = not self.board_flipped
        if b.get("pgn") and b["pgn"].collidepoint(x, y): self.copy_pgn()
        if b.get("undo") and b["undo"].collidepoint(x, y): self.undo_move()
        if b.get("resign") and b["resign"].collidepoint(x, y):
            if not self.game_over: self.game_over = True; self.game_result_msg = "Resigned."
        if b.get("prev") and b["prev"].collidepoint(x, y): self.jump_to_move(self.current_move_idx - 1)
        if b.get("next") and b["next"].collidepoint(x, y): self.jump_to_move(self.current_move_idx + 1)
        if b.get("scrollbar_track") and b["scrollbar_track"].collidepoint(x, y):
            if b["scrollbar_thumb"].collidepoint(x, y):
                self.is_dragging_scrollbar = True; self.drag_offset_y = y - b["scrollbar_thumb"].top
            else:
                if y < b["scrollbar_thumb"].top:
                    self.pgn_scroll_y -= 100
                else:
                    self.pgn_scroll_y += 100
                self.pgn_scroll_y = max(0, min(self.max_scroll_y, self.pgn_scroll_y))
        for idx, rect in self.pgn_click_zones:
            if rect.collidepoint(x, y): self.jump_to_move(idx + 1); break

    def _handle_dropdown(self, pos):
        if self.dropdown_data:
            for val, rect in self.dropdown_data["items"]:
                if rect.collidepoint(pos):
                    self.engine_elo = val;
                    self.engine.set_elo(val);
                    self.elo_dropdown_open = False;
                    return
        self.elo_dropdown_open = False

    def _handle_promotion_sel(self, pos):
        if "rects" in self.promotion_data:
            for name, rect in self.promotion_data["rects"].items():
                if rect.collidepoint(pos):
                    d = self.promotion_data
                    src = self.rowcol_to_uci(*d["from"])
                    dst = self.rowcol_to_uci(*d["to"])
                    char = {"queen": "q", "rook": "r", "bishop": "b", "knight": "n"}[name]
                    move = chess.Move.from_uci(f"{src}{dst}{char}")
                    if move in self.board_logic.legal_moves: self.process_move(move, animate=True)
                    self.is_promoting = False;
                    self.promotion_data = {};
                    break

    def _handle_rclick(self, pos):
        if self.selected_square or self.is_dragging:
            self.selected_square = None;
            self.is_dragging = False;
            return
        x, y = pos
        if self.board_x <= x < self.board_x + self.square_size * 8 and self.board_y <= y < self.board_y + self.square_size * 8:
            self.right_click_start = self.screen_to_board(x, y)

    def _handle_rclick_up(self, pos):
        if not self.right_click_start: return
        x, y = pos
        if self.board_x <= x < self.board_x + self.square_size * 8 and self.board_y <= y < self.board_y + self.square_size * 8:
            end = self.screen_to_board(x, y)
            start = self.right_click_start
            if start == end:
                if start in self.user_highlights:
                    self.user_highlights.remove(start)
                else:
                    self.user_highlights.append(start)
            else:
                arr = (start, end)
                if arr in self.user_arrows:
                    self.user_arrows.remove(arr)
                else:
                    self.user_arrows.append(arr)
        self.right_click_start = None

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.renderer.set_theme(self.is_dark_mode)