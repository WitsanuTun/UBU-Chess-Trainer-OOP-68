import pygame
import os
import chess
from settings import *


class GameRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.theme = THEME_DARK
        self.icons = {}
        self.review_icons = {}
        self._init_fonts()
        self._load_all_icons()

    def set_theme(self, is_dark):
        self.theme = THEME_DARK if is_dark else THEME_LIGHT

    def _init_fonts(self):
        try:
            self.font_ui = pygame.font.SysFont("segoe ui", 15)
            self.font_ui_bold = pygame.font.SysFont("segoe ui", 15, bold=True)
            self.font_title = pygame.font.SysFont("segoe ui", 26, bold=True)
            self.font_pgn = pygame.font.SysFont("consolas", 14)
            self.font_arrow = pygame.font.SysFont("segoe ui symbol", 20)
            self.font_mate = pygame.font.SysFont("arial", 28, bold=True)  # เพิ่มขนาดฟอนต์ #
            self.font_icon = pygame.font.SysFont("segoe ui symbol", 20)
            self.font_piece_large = pygame.font.SysFont("segoe ui symbol", 60)
        except:
            self.font_ui = pygame.font.Font(None, 20)

    def _load_all_icons(self):
        def load(name, size):
            path = os.path.join(ICON_IMG_DIR, name)
            if os.path.exists(path):
                try:
                    return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), size)
                except:
                    pass
            return None

        self.icons['robot'] = load("robot.png", (24, 24))
        self.icons['search'] = load("search.png", (24, 24))
        names = ["brilliant", "great", "best", "excellent", "good", "book", "inaccuracy", "mistake", "miss", "blunder"]
        for n in names: self.review_icons[n] = load(f"{n}.png", (22, 22))

    def draw_game(self, game):
        self.screen.fill(self.theme["bg_main"])

        # 1. วาดกระดาน
        game.board_visual.draw_squares(self.screen, game.board_x, game.board_y, game.board_flipped)

        # 2. ไฮไลท์พื้นหลัง (Check / Premove)
        if game.in_check and game.checked_king_pos:
            self._draw_check_square(game)
        if game.premove_squares:
            self._draw_premove(game)
        self._draw_highlights_layer(game)

        # 3. คำนวณว่าจะ "ซ่อน" หมากตัวไหน (ตัวที่ลากอยู่ หรือ ตัวที่กำลังตาย/อนิเมชั่น หรือ **คิงที่ตายแล้ว**)
        hidden_sq = None
        if game.is_dragging:
            hidden_sq = game.dragging_piece
        elif game.animation:
            hidden_sq = game.animation["hide_square"]
        elif game.board_logic.is_checkmate() and game.checked_king_pos:
            # [IMPORTANT] ซ่อนคิงตัวปกติ เพื่อจะวาดตัวล้มแทน
            hidden_sq = game.checked_king_pos

        # 4. วาดตัวหมากปกติ (ยกเว้นตัวที่ซ่อน)
        game.board_visual.draw_pieces(
            self.screen, game.board_x, game.board_y,
            game.shake_pos, game.shake_offset,
            hidden_square=hidden_sq, flipped=game.board_flipped
        )

        # 5. วาดไอคอนรีวิว
        self._draw_review_icons(game)

        # 6. วาดเอฟเฟกต์พิเศษ (ลาก / อนิเมชั่น / คิงล้ม)
        if game.is_dragging and game.dragging_piece: self._draw_dragged_piece(game)
        if game.animation: self._draw_animated_piece(game)

        # [NEW] วาดคิงล้ม (Rotated King) ถ้า Checkmate
        if game.board_logic.is_checkmate() and game.checked_king_pos:
            self._draw_fallen_king(game)
            self._draw_checkmate_badge(game)  # วาดเครื่องหมาย # ทับบนสุด

        # 7. UI ส่วนที่เหลือ
        game.board_visual.draw_coordinates(self.screen, game.board_x, game.board_y, self.font_pgn, game.board_flipped)
        if game.review_mode: self._draw_eval_bar(game)
        self._draw_panel(game)
        if game.is_promoting: self._draw_promotion_popup(game)

        pygame.display.flip()

    # --- NEW: ฟังก์ชันวาดคิงล้ม ---
    def _draw_fallen_king(self, game):
        r, c = game.checked_king_pos
        piece = game.board_visual.get_piece(r, c)
        if piece and piece.image:
            # หมุนภาพ 90 องศา (นอนตาย)
            rotated_img = pygame.transform.rotate(piece.image, -90)  # ล้มไปทางขวา

            # คำนวณตำแหน่ง
            x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)

            # จัดกึ่งกลางภาพหมุนให้ตรงช่อง
            rect = rotated_img.get_rect()
            rect.center = (x + game.square_size // 2, y + game.square_size // 2)

            self.screen.blit(rotated_img, rect)

    def _draw_checkmate_badge(self, game):
        r, c = game.checked_king_pos
        x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
        s = game.square_size

        # วาด Badge # มุมขวาบน
        bx, by = x + s - 10, y + 10
        pygame.draw.circle(self.screen, (0, 0, 0, 80), (bx + 2, by + 2), 16)  # เงา
        pygame.draw.circle(self.screen, self.theme["mate_badge"], (bx, by), 16)  # พื้นหลังแดง
        pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 16, 2)  # ขอบขาว

        txt = self.font_mate.render("#", True, (255, 255, 255))
        tr = txt.get_rect(center=(bx, by))
        self.screen.blit(txt, tr)

    # --- ฟังก์ชันเดิม (คงไว้) ---
    def _draw_check_square(self, game):
        r, c = game.checked_king_pos
        x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
        col = self.theme["mate_bg"] if game.board_logic.is_checkmate() else self.theme["check_bg"]
        pygame.draw.rect(self.screen, col, (x, y, game.square_size, game.square_size))

    def _draw_premove(self, game):
        s = game.square_size
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        for r, c in game.premove_squares:
            x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
            pygame.draw.rect(overlay, self.theme["premove"], (x, y, s, s))
        self.screen.blit(overlay, (0, 0))

    def _draw_highlights_layer(self, game):
        if game.selected_square:
            s = game.square_size
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            for r, c in game.valid_moves:
                x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
                cx, cy = x + s // 2, y + s // 2
                piece = game.board_visual.get_piece(r, c)
                if piece:
                    pygame.draw.circle(overlay, self.theme["capture_hint"], (cx, cy), s // 2 - 2, 6)
                else:
                    pygame.draw.circle(overlay, self.theme["move_hint"], (cx, cy), s // 6)
            self.screen.blit(overlay, (0, 0))

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        for r, c in game.user_highlights:
            x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
            pygame.draw.rect(overlay, self.theme["highlight_green"], (x, y, game.square_size, game.square_size))

        for start, end in game.user_arrows:
            self._draw_arrow(overlay, game, start, end, self.theme["arrow_green"])

        if game.right_click_start:
            mx, my = pygame.mouse.get_pos()
            if game.board_x <= mx < game.board_x + game.square_size * 8 and game.board_y <= my < game.board_y + game.square_size * 8:
                curr = game.screen_to_board(mx, my)
                if curr != game.right_click_start:
                    self._draw_arrow(overlay, game, game.right_click_start, curr, self.theme["arrow_green"])
        self.screen.blit(overlay, (0, 0))

    def _draw_arrow(self, surface, game, start, end, color):
        s = game.square_size
        sx, sy = game.board_visual.to_screen(start[0], start[1], game.board_x, game.board_y, game.board_flipped)
        ex, ey = game.board_visual.to_screen(end[0], end[1], game.board_x, game.board_y, game.board_flipped)
        start_vec = pygame.Vector2(sx + s / 2, sy + s / 2)
        end_vec = pygame.Vector2(ex + s / 2, ey + s / 2)
        arrow = end_vec - start_vec
        length = arrow.length()
        if length < 1: return
        shaft_w = s * 0.18;
        head_w = s * 0.45;
        head_h = s * 0.35
        if length < s * 1.2: head_h, head_w = s * 0.3, s * 0.4
        direction = arrow.normalize();
        perp = pygame.Vector2(-direction.y, direction.x)
        p1 = start_vec + perp * (shaft_w / 2);
        p2 = start_vec - perp * (shaft_w / 2)
        neck = end_vec - direction * head_h
        p3 = neck - perp * (shaft_w / 2);
        p4 = neck + perp * (shaft_w / 2)
        p5 = neck - perp * (head_w / 2);
        p6 = neck + perp * (head_w / 2)
        pygame.draw.polygon(surface, color, [p2, p3, p5, end_vec, p6, p4, p1])

    def _draw_review_icons(self, game):
        if game.review_mode and game.analysis_results:
            idx = game.current_move_idx - 1
            if 0 <= idx < len(game.analysis_results):
                data = game.analysis_results[idx]
                icon = self.review_icons.get(data.get("class"))
                if icon:
                    last_move = game.move_history_obj[idx]
                    r, c = self._chess_sq_to_rowcol(last_move.to_square)
                    x, y = game.board_visual.to_screen(r, c, game.board_x, game.board_y, game.board_flipped)
                    self.screen.blit(icon, (x + game.square_size - 22, y + 2))

    def _draw_dragged_piece(self, game):
        r, c = game.dragging_piece
        piece = game.board_visual.get_piece(r, c)
        if piece:
            mx, my = pygame.mouse.get_pos()
            piece.draw(self.screen, mx - game.square_size // 2, my - game.square_size // 2)

    def _draw_animated_piece(self, game):
        piece = game.animation["piece"]
        cx, cy = game.animation["current_pos"]
        piece.draw(self.screen, cx, cy)

    def _draw_eval_bar(self, game):
        if game.eval_cp is None and game.eval_mate is None: return
        bx, by = game.board_x - 15, game.board_y
        bw, bh = 8, game.square_size * 8
        pygame.draw.rect(self.screen, (50, 50, 50), (bx, by, bw, bh))
        score = game.eval_cp if game.eval_cp else 0
        if game.eval_mate: score = 1000 if game.eval_mate > 0 else -1000
        clamped = max(-500, min(500, score))
        ratio = (clamped + 500) / 1000
        white_h = int(bh * ratio)
        pygame.draw.rect(self.screen, (220, 220, 220), (bx, by + (bh - white_h), bw, white_h))

    def _draw_panel(self, game):
        theme = self.theme
        rect = pygame.Rect(game.panel_x, 0, game.panel_w, game.window_height)
        pygame.draw.rect(self.screen, theme["bg_panel"], rect)
        x, y = game.panel_x + 20, 25;
        cw = game.panel_w - 40
        self._draw_text("Chess Trainer", x, y, self.font_title, theme["text_main"])
        tog_w, tog_h = 54, 28;
        tog_x = game.panel_x + game.panel_w - tog_w - 20
        game.ui_buttons["theme_toggle"] = self._draw_toggle(tog_x, y + 4, tog_w, tog_h, self.theme["name"] == "Dark")
        icon_size = 32;
        eng_x = tog_x - icon_size - 15
        eng_rect = pygame.Rect(eng_x, y + 2, icon_size, icon_size)
        ecol = (255, 255, 255) if game.engine_enabled else (
            (150, 150, 150) if self.theme["name"] == "Dark" else (100, 100, 100))
        ebg = theme["green_mint"] if game.engine_enabled else theme["btn_idle"]
        pygame.draw.rect(self.screen, theme["btn_shadow"], eng_rect.move(0, 3), border_radius=8)
        pygame.draw.rect(self.screen, ebg, eng_rect, border_radius=8)
        self._draw_icon_centered("robot", eng_rect.center, ecol)
        game.ui_buttons["engine_toggle"] = eng_rect
        rev_x = eng_x - icon_size - 10;
        rev_rect = pygame.Rect(rev_x, y + 2, icon_size, icon_size)
        rcol = (255, 255, 255) if game.review_mode else (
            (150, 150, 150) if self.theme["name"] == "Dark" else (100, 100, 100))
        rbg = theme["blue_baby"] if game.review_mode else theme["btn_idle"]
        pygame.draw.rect(self.screen, theme["btn_shadow"], rev_rect.move(0, 3), border_radius=8)
        pygame.draw.rect(self.screen, rbg, rev_rect, border_radius=8)
        self._draw_icon_centered("search", rev_rect.center, rcol)
        game.ui_buttons["review_toggle"] = rev_rect
        y += 65

        if game.engine_enabled:
            h = 125;
            card = pygame.Rect(x - 5, y - 5, cw + 10, h)
            pygame.draw.rect(self.screen, theme["card_bg"], card, border_radius=12)
            pygame.draw.rect(self.screen, theme["card_border"], card, 2, 12)
            self._draw_text("Engine Config", x + 5, y + 5, self.font_ui_bold, theme["text_main"])
            y += 35;
            bw = (cw - 10) // 2
            c_w = theme["eng_btn_active"] if game.engine_color == chess.BLACK else theme["eng_btn_inactive"]
            c_b = theme["eng_btn_active"] if game.engine_color == chess.WHITE else theme["eng_btn_inactive"]
            t_w = theme["eng_text_active"] if game.engine_color == chess.BLACK else theme["eng_text_inactive"]
            t_b = theme["eng_text_active"] if game.engine_color == chess.WHITE else theme["eng_text_inactive"]
            game.ui_buttons["side_white"] = self._draw_btn("Play White", x, y, bw, 36, c_w, None, t_w)
            game.ui_buttons["side_black"] = self._draw_btn("Play Black", x + bw + 10, y, bw, 36, c_b, None, t_b)
            y += 48
            elo = f"Strength: {game.engine_elo} {'▲' if game.elo_dropdown_open else '▼'}"
            game.ui_buttons["elo_head"] = self._draw_btn(elo, x, y, cw, 36)
            if game.elo_dropdown_open:
                opts = [];
                dy = y + 40;
                drop_h = len(game.elo_options) * 32 + 10
                dd_rect = pygame.Rect(x, dy, cw, drop_h)
                game.dropdown_data = {"rect": dd_rect, "items": []}
                for val in game.elo_options:
                    r = pygame.Rect(x + 5, dy + 5, cw - 10, 28)
                    game.dropdown_data["items"].append((val, r));
                    dy += 32
                game.ui_buttons["elo_options"] = opts
            else:
                game.dropdown_data = None
            y += 60
        else:
            game.dropdown_data = None; y += 10

        st_col = theme["btn_idle"]
        if game.game_over:
            if "wins" in game.game_result_msg:
                st_col = (60, 100, 60) if self.theme["name"] == "Dark" else (200, 230, 200)
            else:
                st_col = (100, 60, 60) if self.theme["name"] == "Dark" else (230, 200, 200)
        st_rect = pygame.Rect(x, y, cw, 42)
        pygame.draw.rect(self.screen, st_col, st_rect, border_radius=10)
        msg = game.game_result_msg if game.game_over else f"Turn: {game.turn_color.title()}"
        dot_c = (255, 255, 255) if game.turn_color == "white" else (30, 30, 30)
        pygame.draw.circle(self.screen, (180, 180, 180), (x + 25, y + 21), 10)
        pygame.draw.circle(self.screen, dot_c, (x + 25, y + 21), 8)
        st_txt_col = theme["text_main"]
        if game.game_over and self.theme["name"] == "Light": st_txt_col = (40, 40, 40)
        self._draw_text(msg, x + 50, y + 11, self.font_ui_bold, st_txt_col)
        y += 58

        nw = 45
        game.ui_buttons["prev"] = self._draw_btn("◀", x, y, nw, 40, font=self.font_arrow)
        game.ui_buttons["next"] = self._draw_btn("▶", x + nw + 10, y, nw, 40, font=self.font_arrow)
        game.ui_buttons["new"] = self._draw_btn("New Game", x + nw * 2 + 20, y, cw - (nw * 2) - 20, 40,
                                                theme["green_mint"], None, (255, 255, 255))
        y += 50

        rw = (cw - 15) // 4
        game.ui_buttons["flip"] = self._draw_btn("Flip", x, y, rw, 36)
        game.ui_buttons["pgn"] = self._draw_btn("PGN", x + rw + 5, y, rw, 36)
        game.ui_buttons["undo"] = self._draw_btn("Undo", x + (rw + 5) * 2, y, rw, 36)
        game.ui_buttons["resign"] = self._draw_btn("Resign", x + (rw + 5) * 3, y, rw, 36, theme["red_soft"], None,
                                                   (255, 255, 255))
        y += 55

        self._draw_text("Move History", x, y, self.font_ui_bold, theme["text_main"])
        y += 30
        lh = game.window_height - y - 35
        game.pgn_view_rect = pygame.Rect(x, y, cw, lh)
        self._draw_pgn_list(game, game.pgn_view_rect)

        if game.dropdown_data:
            dd = game.dropdown_data
            pygame.draw.rect(self.screen, (0, 0, 0, 50), dd["rect"].move(0, 4), border_radius=12)
            pygame.draw.rect(self.screen, theme["popup_bg"], dd["rect"], border_radius=12)
            pygame.draw.rect(self.screen, theme["pgn_border"], dd["rect"], 1, 12)
            for val, rect in dd["items"]:
                hover = rect.collidepoint(pygame.mouse.get_pos())
                col = theme["pgn_border"] if hover else theme["popup_bg"]
                pygame.draw.rect(self.screen, col, rect, border_radius=8)
                self._draw_text_centered(str(val), rect, self.font_ui, theme["text_main"])

    def _draw_pgn_list(self, game, rect):
        theme = self.theme
        pygame.draw.rect(self.screen, theme["bg_panel"], rect, border_radius=12)
        pygame.draw.rect(self.screen, theme["pgn_border"], rect, 1, 12)
        hh = 30
        pygame.draw.rect(self.screen, theme["pgn_header"], (rect.x + 1, rect.y + 1, rect.w - 2, hh),
                         border_top_left_radius=12, border_top_right_radius=12)
        self._draw_text("#", rect.x + 10, rect.y + 7, self.font_pgn, theme["text_light"])
        self._draw_text("White", rect.x + 50, rect.y + 7, self.font_pgn, theme["text_light"])
        self._draw_text("Black", rect.x + 145, rect.y + 7, self.font_pgn, theme["text_light"])
        content = rect.inflate(-4, -(hh + 4))
        content.top += hh
        row_h = 28
        total_rows = (len(game.move_history_san) + 1) // 2
        total_h = total_rows * row_h
        vis_h = content.height
        game.max_scroll_y = max(0, total_h - vis_h)
        game.pgn_scroll_y = max(0, min(game.pgn_scroll_y, game.max_scroll_y))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(content)
        start_y = content.top - game.pgn_scroll_y
        game.pgn_click_zones = []
        for i in range(0, len(game.move_history_san), 2):
            y = start_y + (i // 2) * row_h
            if y + row_h < content.top: continue
            if y > content.bottom: break
            if (i // 2) % 2 == 1: pygame.draw.rect(self.screen, theme["pgn_zebra"], (rect.x + 2, y, rect.w - 4, row_h))
            self._draw_text(f"{i // 2 + 1}.", rect.x + 10, y + 6, self.font_pgn, theme["text_light"])
            wr = pygame.Rect(rect.x + 45, y + 2, 85, 24)
            if game.current_move_idx == i + 1:
                pygame.draw.rect(self.screen, theme["highlight"], wr, border_radius=6)
                tcol = (40, 40, 40)
            else:
                tcol = theme["text_main"]
            self._draw_text(game.move_history_san[i], rect.x + 50, y + 6, self.font_pgn, tcol)
            game.pgn_click_zones.append((i, wr))
            if i + 1 < len(game.move_history_san):
                br = pygame.Rect(rect.x + 140, y + 2, 85, 24)
                if game.current_move_idx == i + 2:
                    pygame.draw.rect(self.screen, theme["highlight"], br, border_radius=6)
                    tcol = (40, 40, 40)
                else:
                    tcol = theme["text_main"]
                self._draw_text(game.move_history_san[i + 1], rect.x + 145, y + 6, self.font_pgn, tcol)
                game.pgn_click_zones.append((i + 1, br))
        self.screen.set_clip(old_clip)
        if total_h > vis_h:
            track = pygame.Rect(rect.right - 10, content.top + 2, 8, vis_h - 4)
            thumb_h = max(30, int(vis_h * (vis_h / total_h)))
            thumb_y = track.top + (game.pgn_scroll_y / game.max_scroll_y) * (track.height - thumb_h)
            thumb = pygame.Rect(track.x, thumb_y, 8, thumb_h)
            pygame.draw.rect(self.screen, theme["scroll_track"], track, border_radius=4)
            pygame.draw.rect(self.screen, theme["scroll_thumb"], thumb, border_radius=4)
            game.ui_buttons["scrollbar_track"] = track
            game.ui_buttons["scrollbar_thumb"] = thumb

    def _draw_promotion_popup(self, game):
        sw, sh = game.window_width, game.window_height
        pw, ph = 480, 240
        x, y = (sw - pw) // 2, (sh - ph) // 2
        pygame.draw.rect(self.screen, (0, 0, 0, 60), (x + 5, y + 8, pw, ph), border_radius=16)
        bg = pygame.Rect(x, y, pw, ph)
        pygame.draw.rect(self.screen, self.theme["bg_panel"], bg, border_radius=16)
        pygame.draw.rect(self.screen, self.theme["btn_shadow"], bg, 1, 16)
        self._draw_text_centered("Promote Pawn", pygame.Rect(x, y + 20, pw, 40), self.font_title,
                                 self.theme["text_main"])
        opts = ["queen", "rook", "bishop", "knight"]
        syms = {"queen": "♛", "rook": "♜", "bishop": "♝", "knight": "♞"}
        bs = 90;
        gap = 20;
        sx = x + (pw - (bs * 4 + gap * 3)) // 2;
        by = y + 95
        game.promotion_data["rects"] = {}
        for i, name in enumerate(opts):
            bx = sx + i * (bs + gap)
            r = self._draw_btn(syms[name], bx, by, bs, bs, font=self.font_piece_large)
            game.promotion_data["rects"][name] = r

    def _draw_draw_popup(self, game):
        pass

    def _draw_btn(self, text, x, y, w, h, base_color=None, hover_color=None, text_color=None, font=None):
        if base_color is None: base_color = self.theme["btn_idle"]
        if hover_color is None: hover_color = self.theme["btn_hover"]
        if text_color is None: text_color = self.theme["text_main"]
        r = pygame.Rect(x, y, w, h)
        hover = r.collidepoint(pygame.mouse.get_pos())
        col = hover_color if hover else base_color
        pygame.draw.rect(self.screen, self.theme["btn_shadow"], r.move(0, 3), border_radius=10)
        pygame.draw.rect(self.screen, col, r, border_radius=10)
        if font is None: font = self.font_ui_bold
        self._draw_text_centered(text, r, font, text_color)
        return r

    def _draw_toggle(self, x, y, w, h, is_on):
        r = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.theme["toggle_bg"], r, border_radius=h // 2)
        p = 3;
        s = h - p * 2
        tx = x + w - s - p if is_on else x + p
        tr = pygame.Rect(tx, y + p, s, s)
        pygame.draw.circle(self.screen, self.theme["toggle_thumb"], tr.center, s // 2)
        icon = "☾" if is_on else "☀"
        self._draw_text_centered(icon, tr, self.font_icon, self.theme["toggle_icon"])
        return r

    def _draw_text(self, text, x, y, font, color):
        s = font.render(text, True, color)
        self.screen.blit(s, (x, y))

    def _draw_text_centered(self, text, rect, font, color):
        s = font.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=rect.center))

    def _draw_icon_centered(self, name, center, color=None):
        if name in self.icons and self.icons[name]:
            img = self.icons[name].copy()
            if color and color != (255, 255, 255) and self.theme["name"] == "Light":
                c = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                c.fill(color)
                img.blit(c, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(img, img.get_rect(center=center))

    def _chess_sq_to_rowcol(self, sq):
        return 7 - chess.square_rank(sq), chess.square_file(sq)