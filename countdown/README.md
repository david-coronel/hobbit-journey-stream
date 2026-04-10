# Hobbit Journey Stream — Countdown

A minimal, configurable countdown stream that runs 24/7 until the canonical start of The Hobbit journey.

## Canonical Start Date

**April 26, 2026 at 11:00 AM (local time)**  
This is the day Gandalf arrives at Bag End — the inciting incident of *The Hobbit*.

## What It Does

- Streams a **live countdown** to Twitch (or any RTMP endpoint)
- Displays **days : hours : minutes : seconds**
- Shows a **progress bar** filling up as the date approaches
- Rotates **canon-inspired quotes** every hour
- Loops **ambient Shire audio** underneath (optional)
- Serves a **web-based mirror** at `/countdown`

## Files

```
countdown/
├── config.json          # Theme, date, quotes, Twitch config
├── stream.py            # Python overlay generator (Pillow → ffmpeg)
├── stream.sh            # Bash launcher (orchestrates ffmpeg)
├── generate_assets.py   # Generates the default Shire background
├── assets/
│   ├── background.png   # Generated thematic background
│   └── shire_ambient.mp3# (Optional) your ambient audio
└── README.md            # This file
```

## Quick Start

### 1. Set your Twitch stream key

```bash
export TWITCH_STREAM_KEY="live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 2. (Optional) Add ambient audio

Place an MP3 file at:
```
countdown/assets/shire_ambient.mp3
```

If missing, the stream will use silence.

### 3. Launch the stream

```bash
cd /home/didi/code/hobbit
countdown/stream.sh
```

This will:
1. Generate the background image (if missing)
2. Start the Python overlay generator
3. Start `ffmpeg` and stream to Twitch

Press `Ctrl+C` to stop.

## Web Countdown

If the main Flask server is running, you can also view the countdown in a browser:

```bash
python3 scripts/stream_server.py
```

Then open: **http://localhost:5000/countdown**

There's also a JSON API at:

```bash
curl http://localhost:5000/api/countdown
```

## Configuration

Edit `countdown/config.json`:

| Field | Description |
|-------|-------------|
| `start_date` | ISO datetime when the countdown hits zero |
| `quotes` | Array of rotating quotes |
| `quote_rotation_minutes` | How often to rotate quotes |
| `output.resolution` | Stream resolution (default `1920x1080`) |
| `output.fps` | Stream framerate (default `30`) |
| `output.bitrate` | Video bitrate (default `4500k`) |
| `output.preset` | x264 preset (default `ultrafast`) |
| `colors.countdown` | Countdown text color |
| `colors.quote` | Quote text color |
| `progress_bar.width` | Width of ASCII progress bar |

## How It Works

The architecture is designed to be **extremely efficient** on CPU and bandwidth:

```
stream.py (Pillow)  →  raw RGBA frames  →  ffmpeg  →  Twitch RTMP
background.png                               ↑
audio.mp3  ──────────────────────────────────┘
```

- Python renders only **1 frame per second** with Pillow
- `ffmpeg` composites it over the static background and encodes to H.264
- Because the background is static, `tune=stillimage` keeps CPU usage very low
- Total bandwidth: ~4.5 Mbps (well within Hetzner's 20 TB/month limit)

This design also makes it trivial to upgrade to cinematic transitions later: just increase the frame rate in `stream.py` and render animations with Pillow.

## Hosting Recommendations

| Setup | Good For |
|-------|----------|
| **Your DL380 Gen9** | Perfect for 24/7. Plenty of cores for x264 encoding. |
| **Hetzner CX11 (~€4.50/mo)** | Fine for this static-image countdown. 20 TB bandwidth. |
| **Hetzner CPX31 (~€13/mo)** | Good if you add 1080p30 browser animations later. |

## Troubleshooting

### ffmpeg not found
Install ffmpeg on Debian/Ubuntu:
```bash
sudo apt-get update && sudo apt-get install ffmpeg
```

### No audio
The stream falls back to silence if `shire_ambient.mp3` is missing. Just place any MP3 at that path.

### BrokenPipeError in logs
This is normal when stopping the stream. `stream.py` handles it gracefully.

### Want a different background?
Replace `countdown/assets/background.png` with any 1920×1080 image. Or edit `generate_assets.py` to customize the generated gradient.

## Future Upgrades

Because the overlay is rendered in Python frame-by-frame, you can easily extend it:
- **Smooth transitions** (crossfades between quotes)
- **Weather effects** (rain over Mirkwood, snow over the Misty Mountains)
- **Seasonal backgrounds** that change based on the real-world date
- **Integration with the main stream** — seamlessly hand off to `gui_prototype.py` when the countdown hits zero
