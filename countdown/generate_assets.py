#!/usr/bin/env python3
"""Generate default Shire-themed background for the countdown stream."""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "assets", "background.png")
WIDTH, HEIGHT = 1920, 1080


def draw_gradient(draw, width, height, color_top, color_bottom):
    """Draw a vertical gradient."""
    for y in range(height):
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * y / height)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * y / height)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def generate():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Shire-inspired gradient: warm sky green/brown to deep earth
    top = (45, 70, 35)      # deep moss green
    bottom = (20, 25, 15)   # dark earth
    draw_gradient(draw, WIDTH, HEIGHT, top, bottom)

    # Subtle sun glow top-center
    for radius in range(300, 0, -5):
        alpha = int(8 * (1 - radius / 300))
        color = (212, 175, 55)
        draw.ellipse(
            [WIDTH // 2 - radius, -radius, WIDTH // 2 + radius, radius],
            fill=(color[0] * alpha // 255 + top[0] * (255 - alpha) // 255,
                  color[1] * alpha // 255 + top[1] * (255 - alpha) // 255,
                  color[2] * alpha // 255 + top[2] * (255 - alpha) // 255),
        )

    # Decorative border lines
    draw.rectangle([40, 40, WIDTH - 40, HEIGHT - 40], outline="#3a3530", width=2)
    draw.rectangle([50, 50, WIDTH - 50, HEIGHT - 50], outline="#5a5045", width=1)

    # Small decorative ornaments in corners
    corner_size = 30
    corners = [
        (60, 60),
        (WIDTH - 60 - corner_size, 60),
        (60, HEIGHT - 60 - corner_size),
        (WIDTH - 60 - corner_size, HEIGHT - 60 - corner_size),
    ]
    for cx, cy in corners:
        draw.rectangle([cx, cy, cx + corner_size, cy + corner_size], outline="#8b7355", width=2)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    img.save(OUTPUT)
    print(f"[Assets] Generated background: {OUTPUT}")


if __name__ == "__main__":
    generate()
