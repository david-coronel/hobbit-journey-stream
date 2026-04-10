#!/usr/bin/bash
# Hobbit Journey Stream — Countdown Launcher
# Streams a countdown to Twitch (or other RTMP) until the canonical start date.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Load Twitch stream key from environment or fail
if [ -z "${TWITCH_STREAM_KEY:-}" ]; then
    echo "[Error] TWITCH_STREAM_KEY is not set."
    echo "        Export it before running this script:"
    echo "        export TWITCH_STREAM_KEY='live_...'"
    exit 1
fi

# Paths
CONFIG="$SCRIPT_DIR/config.json"
BACKGROUND="$SCRIPT_DIR/assets/background.png"
AUDIO="$SCRIPT_DIR/assets/shire_ambient.mp3"
PYTHON="${PYTHON:-python3}"

# Check dependencies
if ! command -v ffmpeg &>/dev/null; then
    echo "[Error] ffmpeg is not installed."
    exit 1
fi

# Generate background if missing
if [ ! -f "$BACKGROUND" ]; then
    echo "[Info] Background image missing. Generating default Shire background..."
    "$PYTHON" "$SCRIPT_DIR/generate_assets.py"
fi

# Audio: use silence if no audio file provided
AUDIO_INPUT=()
AUDIO_MAP=()
if [ -f "$AUDIO" ]; then
    echo "[Info] Using ambient audio: $AUDIO"
    AUDIO_INPUT=(-stream_loop -1 -i "$AUDIO")
    AUDIO_MAP=(-map 2:a)
else
    echo "[Warn] No ambient audio found at $AUDIO"
    echo "       Using silence. Place an MP3 at that path to add Shire ambience."
    AUDIO_INPUT=(-f lavfi -i anullsrc=r=44100:cl=stereo)
    AUDIO_MAP=(-map 2:a)
fi

# Resolution / output settings
RES="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['resolution'])")"
FPS="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['fps'])")"
BITRATE="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['bitrate'])")"
MAXRATE="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['maxrate'])")"
BUFSIZE="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['bufsize'])")"
PRESET="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output']['preset'])")"
TUNE="$(python3 -c "import json; print(json.load(open('$CONFIG'))['output'].get('tune','stillimage'))")"

TWITCH_URL="$(python3 -c "import json; print(json.load(open('$CONFIG'))['twitch']['url'])")"

# Start the overlay generator in background
echo "[Info] Starting countdown overlay generator..."
"$PYTHON" -u "$SCRIPT_DIR/stream.py" &
OVERLAY_PID=$!

# Cleanup function
cleanup() {
    echo ""
    echo "[Info] Shutting down..."
    kill "$OVERLAY_PID" 2>/dev/null || true
    wait "$OVERLAY_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "[Info] Starting ffmpeg stream to Twitch..."
echo "[Info] Resolution: $RES | FPS: $FPS | Bitrate: $BITRATE"
echo "[Info] Target: $TWITCH_URL"
echo "[Info] Press Ctrl+C to stop."

# ffmpeg command:
#  0: rawvideo overlay from Python (RGBA, 1 fps)
#  1: background image (looped)
#  2: audio (looped or silence)
ffmpeg \
    -hide_banner -loglevel warning \
    -thread_queue_size 512 -probesize 32 \
    -f rawvideo -pix_fmt rgba -s "$RES" -r 1 -i - \
    -loop 1 -framerate "$FPS" -i "$BACKGROUND" \
    "${AUDIO_INPUT[@]}" \
    -filter_complex "[1:v][0:v]overlay=0:0:shortest=0:format=auto[vout]" \
    -map "[vout]" "${AUDIO_MAP[@]}" \
    -c:v libx264 -preset "$PRESET" -tune "$TUNE" -pix_fmt yuv420p -r "$FPS" \
    -g $((FPS * 2)) -keyint_min "$FPS" \
    -b:v "$BITRATE" -maxrate "$MAXRATE" -bufsize "$BUFSIZE" \
    -c:a aac -b:a 128k -ar 44100 \
    -f flv "$TWITCH_URL/$TWITCH_STREAM_KEY"
