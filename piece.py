#piece.py
import pygame
import os

# กำหนดขนาดและโฟลเดอร์รูปภาพ
DEFAULT_SQUARE_SIZE = 80
ASSET_DIR = "assets/pieces"  # ตรวจสอบว่า folder นี้มีอยู่จริง


class ChessPiece:
    def __init__(self, color: str, kind: str, square_size: int):
        self.color = color  # "white" หรือ "black"
        self.kind = kind  # "pawn", "rook", ...

        # สร้าง path รูปภาพอัตโนมัติ เช่น assets/pieces/white_pawn.png
        # (ไม่ต้องส่ง path ยาวๆ มาตอนสร้าง object แล้ว)
        self.image_path = os.path.join(ASSET_DIR, f"{color}_{kind}.png")

        try:
            self.base_image = pygame.image.load(self.image_path).convert_alpha()
        except FileNotFoundError:
            # ถ้าหาไม่เจอ สร้างสี่เหลี่ยมสีแดงแทน (กันโปรแกรมพัง)
            print(f"Warning: Image not found at {self.image_path}")
            self.base_image = pygame.Surface((square_size, square_size))
            self.base_image.fill((255, 0, 0))

        self.image = None
        self.size = None
        self.set_size(square_size)

    def set_size(self, square_size: int):
        if self.size == square_size:
            return
        self.size = square_size
        self.image = pygame.transform.smoothscale(
            self.base_image,
            (square_size, square_size)
        )

    def draw(self, screen, x, y):
        if self.image:
            screen.blit(self.image, (x, y))

    def get_valid_moves(self, board):
        # เดี๋ยวเราค่อยมาเติม Logic พิเศษตรงนี้ถ้าต้องการ
        pass


# --- สร้าง Class ลูก (Inheritance) ---
# เพื่อให้เรียกใช้ง่ายๆ เช่น Pawn("white", 80)

class Pawn(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "pawn", square_size)


class Rook(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "rook", square_size)


class Knight(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "knight", square_size)


class Bishop(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "bishop", square_size)


class Queen(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "queen", square_size)


class King(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "king", square_size)