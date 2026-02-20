import pygame
import os

DEFAULT_SQUARE_SIZE = 80
ASSET_DIR = "assets/pieces"

# ==========================================
# Superclass (คลาสแม่) - Inheritance
# ==========================================
# ChessPiece เป็นคลาสแม่ที่เก็บคุณสมบัติร่วมของหมากทุกตัว (color, kind, โหลดรูป, ขนาด)
class ChessPiece:
    def __init__(self, color: str, kind: str, square_size: int):
        self.color = color  # "white" or "black"
        self.kind = kind  # "pawn", "rook", etc.

        # Auto-generate image path
        self.image_path = os.path.join(ASSET_DIR, f"{color}_{kind}.png")

        try:
            self.base_image = pygame.image.load(self.image_path).convert_alpha()
        except FileNotFoundError:
            # Fallback if image missing
            print(f"Warning: Image not found at {self.image_path}")
            self.base_image = pygame.Surface((square_size, square_size))
            self.base_image.fill((255, 0, 0))

        # Encapsulation: เก็บ state ภายใน (image, size) ไม่ให้ภายนอกแก้โดยตรง ใช้ set_size() แทน
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

    # Polymorphism: เมธอด draw() ใช้ได้กับทุก subclass (Pawn, Rook, ...) โดยไม่ต้องรู้ชนิดหมาก
    def draw(self, screen, x, y):
        if self.image:
            screen.blit(self.image, (x, y))

# ==========================================
# Subclasses (คลาสลูก) - Inheritance จาก ChessPiece
# ==========================================


class Pawn(ChessPiece):
    def __init__(self, color, square_size):
        super().__init__(color, "pawn", square_size)  # Inheritance: เรียก constructor ของ Superclass


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