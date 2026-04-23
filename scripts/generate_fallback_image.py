#!/usr/bin/env python3
"""Generate a 'technical difficulties' fallback image for the stream."""
from PIL import Image, ImageDraw, ImageFont
import os

# --- Config ---
W, H = 1920, 1080
OUTPUT = "assets/fallback_tecnicas.png"
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"

# --- Palette (Hobbit theme) ---
BG_TOP = (26, 23, 18)       # dark brown
BG_BOTTOM = (15, 13, 10)    # almost black
GOLD = (212, 175, 55)       # #d4af37
GOLD_DIM = (160, 140, 70)   # muted gold
SAND = (192, 176, 160)      # #c0b0a0
BORDER = (60, 50, 40)       # dark border

# --- Create canvas ---
img = Image.new("RGB", (W, H), BG_TOP)
draw = ImageDraw.Draw(img)

# Gradient background
for y in range(H):
    ratio = y / H
    r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
    g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
    b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# --- Decorative border ---
margin = 60
for i in range(3):
    offset = i * 2
    color = GOLD if i == 0 else BORDER
    draw.rectangle(
        [margin + offset, margin + offset, W - margin - offset, H - margin - offset],
        outline=color, width=1
    )

# Corner ornaments
ornament_size = 20
corners = [
    (margin, margin), (W - margin, margin),
    (margin, H - margin), (W - margin, H - margin)
]
for cx, cy in corners:
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        x = cx + dx * ornament_size
        y = cy + dy * ornament_size
        draw.line([(cx, y), (cx, cy), (x, cy)], fill=GOLD_DIM, width=2)

# --- Load fonts ---
try:
    font_title = ImageFont.truetype(FONT_BOLD, 64)
    font_sub = ImageFont.truetype(FONT_PATH, 32)
    font_small = ImageFont.truetype(FONT_PATH, 20)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_small = ImageFont.load_default()

# --- Main title ---
title = "Experimentando dificultades técnicas"
bbox = draw.textbbox((0, 0), title, font=font_title)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
draw.text(((W - tw) // 2, H // 2 - th - 40), title, font=font_title, fill=GOLD)

# --- Decorative line ---
line_y = H // 2 + 20
line_width = 400
draw.line([(W // 2 - line_width // 2, line_y), (W // 2 + line_width // 2, line_y)], fill=GOLD_DIM, width=2)
# Diamond in middle
diamond_size = 8
diamond = [(W // 2, line_y - diamond_size), (W // 2 + diamond_size, line_y),
           (W // 2, line_y + diamond_size), (W // 2 - diamond_size, line_y)]
draw.polygon(diamond, fill=GOLD)

# --- Subtitle ---
sub = "El viaje continuará en breve"
bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
tw2 = bbox2[2] - bbox2[0]
draw.text(((W - tw2) // 2, line_y + 40), sub, font=font_sub, fill=SAND)

# --- Bottom note ---
note = "The Hobbit: An Unexpected Journey — Stream"
bbox3 = draw.textbbox((0, 0), note, font=font_small)
tw3 = bbox3[2] - bbox3[0]
draw.text(((W - tw3) // 2, H - margin - 40), note, font=font_small, fill=BORDER)

# --- Pulsing circle indicator (static, 3 dots) ---
dot_y = line_y + 110
dot_radius = 6
dot_spacing = 24
dot_colors = [GOLD, GOLD_DIM, (80, 70, 50)]  # fade left to right
for i, col in enumerate(dot_colors):
    cx = W // 2 + (i - 1) * dot_spacing
    draw.ellipse([cx - dot_radius, dot_y - dot_radius, cx + dot_radius, dot_y + dot_radius], fill=col)

# --- Save ---
img.save(OUTPUT)
print(f"Saved: {OUTPUT} ({W}x{H})")
