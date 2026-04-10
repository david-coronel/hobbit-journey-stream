#!/usr/bin/env python3
"""
Hobbit Journey Stream — Countdown Overlay Generator
Renders RGBA frames with Pillow and pipes them to ffmpeg for streaming.
"""

import json
import os
import sys
import time
import signal
import math
from datetime import datetime, timezone
from pathlib import Path

# Pillow is required
from PIL import Image, ImageDraw, ImageFont

# Paths
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = BASE_DIR / "config.json"

# Load config
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

START_DATE_STR = CONFIG["start_date"]
TZ = CONFIG.get("timezone", "local")
QUOTES = CONFIG.get("quotes", [])
QUOTE_ROTATION_MIN = CONFIG.get("quote_rotation_minutes", 60)
PROGRESS_WIDTH = CONFIG.get("progress_bar", {}).get("width", 40)
FILLED = CONFIG.get("progress_bar", {}).get("filled_char", "▓")
EMPTY = CONFIG.get("progress_bar", {}).get("empty_char", "░")
COLORS = CONFIG.get("colors", {})

RESOLUTION = CONFIG.get("output", {}).get("resolution", "1920x1080")
WIDTH, HEIGHT = (int(x) for x in RESOLUTION.split("x"))

# Font resolution helpers
def get_font(size):
    """Try to load a nice font, fallback to default."""
    font_name = CONFIG.get("assets", {}).get("font", "Cinzel")
    candidates = [
        font_name,
        "DejaVuSerif",
        "DejaVuSerif-Bold",
        "DejaVuSans",
        "LiberationSerif",
        "FreeSerif",
        "Georgia",
        "Times New Roman",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def parse_start_date():
    """Parse the configured start date."""
    dt = datetime.fromisoformat(START_DATE_STR)
    if dt.tzinfo is None:
        if TZ.lower() == "utc":
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone()
    return dt


def get_quote(now: datetime, start: datetime):
    """Pick a rotating quote based on time."""
    if not QUOTES:
        return ""
    # If we're past start, show a launch quote
    if now >= start:
        return "The journey has begun..."
    total_seconds = (start - now).total_seconds()
    period = QUOTE_ROTATION_MIN * 60
    idx = int(total_seconds // period) % len(QUOTES)
    return QUOTES[idx]


def format_countdown(now: datetime, start: datetime):
    """Return a formatted countdown string."""
    if now >= start:
        return "00 : 00 : 00 : 00"
    diff = start - now
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if days > 0:
        return f"{days:02d} : {hours:02d} : {minutes:02d} : {seconds:02d}"
    return f"{hours:02d} : {minutes:02d} : {seconds:02d}"


def format_countdown_labels(now: datetime, start: datetime):
    """Return labels matching the countdown format."""
    if now >= start:
        return ""
    diff = start - now
    days = diff.days
    if days > 0:
        return "DAYS        HOURS        MINUTES        SECONDS"
    return "HOURS        MINUTES        SECONDS"


def progress_bar(now: datetime, start: datetime):
    """Return ASCII progress bar and percentage."""
    if now >= start:
        return "▓" * PROGRESS_WIDTH, 100.0
    # Assume countdown started when the script was first run, or use a fixed window
    # Better: use a configurable countdown_window in config, default to 30 days before start
    window_days = CONFIG.get("countdown_window_days", 30)
    window_start = start.timestamp() - (window_days * 86400)
    total = start.timestamp() - window_start
    elapsed = now.timestamp() - window_start
    if elapsed < 0:
        elapsed = 0
    pct = min(100.0, max(0.0, (elapsed / total) * 100))
    filled_len = int(PROGRESS_WIDTH * pct / 100)
    bar = FILLED * filled_len + EMPTY * (PROGRESS_WIDTH - filled_len)
    return bar, pct


# Pre-load fonts
FONT_COUNTDOWN = get_font(120)
FONT_LABELS = get_font(20)
FONT_SUBTITLE = get_font(36)
FONT_PROGRESS = get_font(28)
FONT_QUOTE = get_font(24)

# Shadow offset
SHADOW_OFF = 3

running = True


def on_signal(signum, frame):
    global running
    running = False


signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)


def draw_text_shadow(draw, text, x, y, font, fill, shadow="#000000", offset=3):
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def render_frame():
    now = datetime.now().astimezone()
    start = parse_start_date()

    # Create transparent canvas
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    countdown_text = format_countdown(now, start)
    labels_text = format_countdown_labels(now, start)
    subtitle_text = CONFIG.get("subtitle", "")
    quote_text = get_quote(now, start)
    bar_text, pct = progress_bar(now, start)
    progress_text = f"{bar_text}  {pct:.1f}%"

    # Layout — centered vertically, compact
    # We'll measure text heights to pack them nicely
    _, top, _, bottom = draw.textbbox((0, 0), countdown_text, font=FONT_COUNTDOWN)
    countdown_h = bottom - top

    _, top, _, bottom = draw.textbbox((0, 0), labels_text, font=FONT_LABELS)
    labels_h = bottom - top

    _, top, _, bottom = draw.textbbox((0, 0), subtitle_text, font=FONT_SUBTITLE)
    subtitle_h = bottom - top

    _, top, _, bottom = draw.textbbox((0, 0), progress_text, font=FONT_PROGRESS)
    progress_h = bottom - top

    _, top, _, bottom = draw.textbbox((0, 0), quote_text, font=FONT_QUOTE)
    quote_h = bottom - top

    gap = 20
    total_block = countdown_h + gap + labels_h + gap + subtitle_h + gap + progress_h + gap + quote_h
    start_y = (HEIGHT - total_block) // 2

    # Draw countdown
    x = (WIDTH - draw.textlength(countdown_text, font=FONT_COUNTDOWN)) // 2
    y = start_y
    draw_text_shadow(draw, countdown_text, int(x), int(y), FONT_COUNTDOWN, COLORS.get("countdown", "#d4af37"))

    # Draw labels
    y += countdown_h + gap
    x = (WIDTH - draw.textlength(labels_text, font=FONT_LABELS)) // 2
    draw.text((int(x), int(y)), labels_text, font=FONT_LABELS, fill=COLORS.get("subtitle", "#a09070"))

    # Draw subtitle
    y += labels_h + gap + 10
    x = (WIDTH - draw.textlength(subtitle_text, font=FONT_SUBTITLE)) // 2
    draw_text_shadow(draw, subtitle_text, int(x), int(y), FONT_SUBTITLE, COLORS.get("subtitle", "#a09070"))

    # Draw progress bar
    y += subtitle_h + gap + 20
    x = (WIDTH - draw.textlength(progress_text, font=FONT_PROGRESS)) // 2
    draw.text((int(x), int(y)), progress_text, font=FONT_PROGRESS, fill=COLORS.get("progress", "#8b7355"))

    # Draw quote
    if quote_text:
        y += progress_h + gap + 30
        # Word-wrap quote if too long
        max_width = WIDTH - 200
        words = quote_text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if draw.textlength(test, font=FONT_QUOTE) <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        for line in lines:
            _, top, _, bottom = draw.textbbox((0, 0), line, font=FONT_QUOTE)
            lh = bottom - top
            lx = (WIDTH - draw.textlength(line, font=FONT_QUOTE)) // 2
            draw.text((int(lx), int(y)), line, font=FONT_QUOTE, fill=COLORS.get("quote", "#e0d0b0"))
            y += lh + 8

    return img


def main():
    # Generate frames at 1 fps and write raw RGBA bytes to stdout
    # ffmpeg will read this and composite it over the background
    try:
        while running:
            frame = render_frame()
            try:
                sys.stdout.buffer.write(frame.convert("RGBA").tobytes())
                sys.stdout.buffer.flush()
            except BrokenPipeError:
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
