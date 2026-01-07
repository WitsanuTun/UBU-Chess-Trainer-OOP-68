# board.py
import pygame
from piece import (
    DEFAULT_SQUARE_SIZE,
    Pawn, Rook, Knight, Bishop, Queen, King
)

BOARD_SIZE = 8
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)

HIGHLIGHT_SELECTED = (246, 246, 105)
HIGHLIGHT_MOVE = (106, 190, 48)


def _to_view_coords(row: int, col: int, flipped: bool):
    if not flipped:
        return row, col
    return 7 - row, 7 - col


class Board:
    def __init__(self, square_size: int = DEFAULT_SQUARE_SIZE):
        self.square_size = square_size
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.init_start_position()

    def set_square_size(self, new_size: int):
        if new_size == self.square_size:
            return
        self.resize(new_size)

    def resize(self, square_size: int):
        self.square_size = square_size
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.grid[r][c]
                if p:
                    p.set_size(square_size)

    def init_start_position(self):
        s = self.square_size
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for c in range(8):
            self.grid[1][c] = Pawn("black", s)
            self.grid[6][c] = Pawn("white", s)

        self.grid[0][0] = self.grid[0][7] = Rook("black", s)
        self.grid[7][0] = self.grid[7][7] = Rook("white", s)

        self.grid[0][1] = self.grid[0][6] = Knight("black", s)
        self.grid[7][1] = self.grid[7][6] = Knight("white", s)

        self.grid[0][2] = self.grid[0][5] = Bishop("black", s)
        self.grid[7][2] = self.grid[7][5] = Bishop("white", s)

        self.grid[0][3] = Queen("black", s)
        self.grid[7][3] = Queen("white", s)

        self.grid[0][4] = King("black", s)
        self.grid[7][4] = King("white", s)

    def draw_squares(self, screen, offset_x: int, offset_y: int, flipped: bool = False):
        s = self.square_size
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                view_row, view_col = _to_view_coords(row, col, flipped)
                x = offset_x + view_col * s
                y = offset_y + view_row * s
                pygame.draw.rect(screen, color, (x, y, s, s))

    def draw_highlights(self, screen, offset_x, offset_y,
                        selected, valid_moves, checked_king,
                        flipped: bool = False):
        s = self.square_size

        def draw_square(rc, color, width=0):
            if rc is None: return
            r, c = rc
            view_r, view_c = _to_view_coords(r, c, flipped)
            x = offset_x + view_c * s
            y = offset_y + view_r * s
            pygame.draw.rect(screen, color, (x, y, s, s), width)

        draw_square(checked_king, (220, 50, 50))
        draw_square(selected, HIGHLIGHT_SELECTED)
        for rc in valid_moves:
            draw_square(rc, HIGHLIGHT_MOVE, width=4)

    def draw_pieces(self, screen, offset_x: int, offset_y: int,
                    shake_square=None, shake_offset=(0, 0),
                    hidden_square=None,
                    flipped: bool = False):

        s = self.square_size
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # ถ้าเป็นช่องที่กำลังถูกลาก (hidden_square) ให้ข้ามไปเลย ไม่ต้องวาด
                if hidden_square == (row, col):
                    continue

                piece = self.grid[row][col]
                if not piece: continue

                view_row, view_col = _to_view_coords(row, col, flipped)
                x = offset_x + view_col * s
                y = offset_y + view_row * s

                if shake_square is not None and (row, col) == shake_square:
                    dx, dy = shake_offset
                    x += dx
                    y += dy

                piece.draw(screen, x, y)

    # --- ส่วนที่เพิ่มเข้ามาใหม่ ---
    def draw_coordinates(self, screen, offset_x: int, offset_y: int, font, flipped: bool = False):
        color = (80, 60, 40)
        s = self.square_size
        files = "abcdefgh"
        ranks = "12345678"

        board_left = offset_x
        board_top = offset_y
        board_bottom = offset_y + 8 * s

        # Left (Numbers)
        for view_row in range(8):
            if flipped:
                rank_label = ranks[view_row]
            else:
                rank_label = ranks[7 - view_row]

            surf = font.render(rank_label, True, color)
            rect = surf.get_rect()
            rect.centery = board_top + view_row * s + s * 0.5
            rect.right = board_left - 6
            screen.blit(surf, rect)

        # Bottom (Letters)
        for view_col in range(8):
            if flipped:
                file_label = files[7 - view_col]
            else:
                file_label = files[view_col]

            surf = font.render(file_label, True, color)
            rect = surf.get_rect()
            rect.centerx = board_left + view_col * s + s * 0.5
            rect.top = board_bottom + 2
            screen.blit(surf, rect)

    # ----------------------------

    def get_piece(self, row, col):
        if self.in_bounds(row, col):
            return self.grid[row][col]
        return None

    def in_bounds(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def move_piece(self, from_row, from_col, to_row, to_col):
        piece = self.grid[from_row][from_col]
        if piece is None: return
        target = self.grid[to_row][to_col]
        if target is not None and target.color == piece.color: return
        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None

    def remove_piece(self, row, col):
        self.grid[row][col] = None

    def load_from_fen(self, fen_str: str):
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        placement = fen_str.split()[0]
        rows = placement.split("/")
        piece_map = {"p": Pawn, "r": Rook, "n": Knight, "b": Bishop, "q": Queen, "k": King}

        for r, row_str in enumerate(rows):
            c = 0
            for ch in row_str:
                if ch.isdigit():
                    c += int(ch)
                else:
                    color = "white" if ch.isupper() else "black"
                    kind_letter = ch.lower()
                    PieceClass = piece_map[kind_letter]
                    self.grid[r][c] = PieceClass(color, self.square_size)
                    c += 1

    def to_screen(self, row, col, offset_x, offset_y, flipped: bool):
        s = self.square_size
        view_row, view_col = _to_view_coords(row, col, flipped)
        x = offset_x + view_col * s
        y = offset_y + view_row * s
        return x, y
