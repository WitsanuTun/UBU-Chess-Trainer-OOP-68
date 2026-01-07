import pygame
import os

# --- WINDOW & ASSETS ---
WINDOW_SIZE = (1200, 800)
DEFAULT_SQUARE_SIZE = 80
PIECE_IMG_DIR = "assets/pieces"
ICON_IMG_DIR = "assets/icons"

# --- THEME DEFINITIONS ---
THEME_DARK = {
    "name": "Dark",
    "bg_main": (30, 30, 30),
    "bg_panel": (45, 45, 45),
    "text_main": (230, 230, 230),
    "text_light": (160, 160, 160),
    "coord_color": (220, 220, 220), # <--- เพิ่มบรรทัดนี้ (สีขาวควันบุหรี่)
    # ... (ค่าเดิมอื่นๆ) ...
    "btn_idle": (70, 70, 70),
    "btn_hover": (90, 90, 90),
    "btn_shadow": (30, 30, 30),
    "green_mint": (100, 180, 80), "green_hover": (120, 200, 100),
    "blue_baby": (70, 140, 210), "blue_hover": (90, 160, 230),
    "red_soft": (220, 80, 80), "red_hover": (240, 100, 100),
    "highlight": (205, 210, 106), "highlight_green": (155, 199, 0, 160),
    "arrow_green": (155, 199, 0, 200),
    "move_hint": (255, 255, 255, 80), "capture_hint": (255, 255, 255, 80),
    "premove": (200, 50, 50, 180),
    "mate_bg": (220, 60, 60), "mate_badge": (220, 60, 60), "check_bg": (200, 50, 50, 200),
    "scroll_track": (40, 40, 40), "scroll_thumb": (100, 100, 100),
    "pgn_zebra": (55, 55, 55), "pgn_header": (35, 35, 35), "pgn_border": (60, 60, 60),
    "panel_line": (60, 60, 60), "popup_bg": (50, 50, 50), "popup_shadow": (0, 0, 0, 100),
    "toggle_bg": (60, 60, 60), "toggle_thumb": (220, 220, 220), "toggle_icon": (80, 80, 80),
    "card_bg": (55, 55, 55), "card_border": (70, 70, 70),
    "eng_btn_active": (70, 140, 210), "eng_btn_inactive": (70, 70, 70),
    "eng_text_active": (255, 255, 255), "eng_text_inactive": (200, 200, 200)
}

THEME_LIGHT = {
    "name": "Light",
    "bg_main": (245, 240, 235),
    "bg_panel": (255, 255, 255),
    "text_main": (60, 60, 60),
    "text_light": (140, 140, 140),
    "coord_color": (80, 60, 40), # <--- เพิ่มบรรทัดนี้ (สีน้ำตาลเข้มเดิม)
    # ... (ค่าเดิมอื่นๆ) ...
    "btn_idle": (230, 230, 235), "btn_hover": (215, 215, 220), "btn_shadow": (200, 200, 205),
    "green_mint": (110, 190, 80), "green_hover": (130, 210, 100),
    "blue_baby": (90, 170, 230), "blue_hover": (110, 190, 250),
    "red_soft": (235, 90, 90), "red_hover": (250, 110, 110),
    "highlight": (205, 210, 106), "highlight_green": (155, 199, 0, 160),
    "arrow_green": (155, 199, 0, 200),
    "move_hint": (20, 20, 20, 40), "capture_hint": (20, 20, 20, 40),
    "premove": (220, 80, 80, 160),
    "mate_bg": (220, 60, 60), "mate_badge": (220, 60, 60), "check_bg": (220, 60, 60, 180),
    "scroll_track": (240, 240, 240), "scroll_thumb": (180, 180, 180),
    "pgn_zebra": (250, 250, 252), "pgn_header": (240, 240, 245), "pgn_border": (230, 230, 230),
    "panel_line": (220, 220, 220), "popup_bg": (255, 255, 255), "popup_shadow": (0, 0, 0, 40),
    "toggle_bg": (220, 220, 225), "toggle_thumb": (255, 255, 255), "toggle_icon": (250, 180, 50),
    "card_bg": (250, 252, 255), "card_border": (220, 220, 230),
    "eng_btn_active": (60, 130, 200), "eng_btn_inactive": (255, 255, 255),
    "eng_text_active": (255, 255, 255), "eng_text_inactive": (60, 60, 60)
}