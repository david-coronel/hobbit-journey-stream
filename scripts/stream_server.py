#!/usr/bin/env python3
"""
The Hobbit Journey Stream - Web Server
Serves HTML frontend and provides API for scene data and controls
"""

import os
import sys

# Change to project root for correct file paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)
sys.path.insert(0, project_root)

from flask import Flask, send_from_directory, send_file, jsonify, request
from flask_cors import CORS
import json
import sqlite3
import threading
import time
import queue
import uuid
from datetime import datetime, timedelta, timezone, date

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# ── Simple in-memory SSE broadcast ──
class SSEBroadcast:
    def __init__(self):
        self._lock = threading.Lock()
        self._clients = {}

    def register(self):
        q = queue.Queue(maxsize=100)
        cid = str(uuid.uuid4())
        with self._lock:
            self._clients[cid] = q
        return cid, q

    def unregister(self, cid):
        with self._lock:
            self._clients.pop(cid, None)

    def publish(self, data):
        with self._lock:
            dead = []
            for cid, q in self._clients.items():
                try:
                    q.put_nowait(data)
                except queue.Full:
                    pass
                except Exception:
                    dead.append(cid)
            for cid in dead:
                self._clients.pop(cid, None)

sse = SSEBroadcast()

class StreamEngine:
    def __init__(self):
        self.load_data()
        self.load_config()
        self.load_estimated_durations()
        self.current_scene_idx = 0
        self.is_playing = False
        self.current_beat_idx = 0
        self.beat_progress = 0.0
        self.scene_progress = 0.0
        self.timer_thread = None
        self.last_update = time.time()

    def load_estimated_durations(self):
        """Load non-canonical estimated durations for canonical scenes."""
        try:
            with open('data/scene_estimated_durations.json', 'r') as f:
                self.estimated_durations = {item['scene_id']: item for item in json.load(f)}
        except Exception as e:
            print(f"[Server] Estimated durations not loaded: {e}")
            self.estimated_durations = {}

    def load_data(self):
        """Load all scene data"""
        with open('data/stream_scenes.json', 'r') as f:
            stream_data = json.load(f)
            self.canonical_scenes = stream_data.get('scenes', [])
        with open('data/generated_gap_scenes.json', 'r') as f:
            gaps_data = json.load(f)
            self.generated_scenes = gaps_data.get('generated_scenes', [])
        with open('data/scene_narratives.json', 'r') as f:
            narratives_data = json.load(f)
            self.narratives = narratives_data.get('scenes', {})
        with open('data/scene_beats.json', 'r') as f:
            beats_data = json.load(f)
            self.beats = beats_data.get('scenes', {})
            
        # Merge and sort scenes by date and order
        self.scenes = []
        for i, s in enumerate(self.canonical_scenes):
            s['is_canonical'] = True
            # progress might be a dict, use a numeric sort key
            progress_val = s.get('progress', 0)
            if isinstance(progress_val, dict):
                progress_val = progress_val.get('start', 0)
            s['sort_key'] = (s.get('journey_day', 0), progress_val, i)
            self.scenes.append(s)
        for i, s in enumerate(self.generated_scenes):
            s['is_canonical'] = False
            # Parse date for sorting
            date_parts = s.get('date_iso', '0000-01-01').split('-')
            year = int(date_parts[0]) if date_parts[0].isdigit() else 0
            month = int(date_parts[1]) if len(date_parts) > 1 and date_parts[1].isdigit() else 1
            day = int(date_parts[2]) if len(date_parts) > 2 and date_parts[2].isdigit() else 1
            # Parse position_in_gap (e.g., "1/3")
            pos_str = s.get('position_in_gap', '1/1')
            try:
                pos = int(pos_str.split('/')[0]) if '/' in pos_str else 1
            except:
                pos = 1
            # Calculate journey_day from date_iso (start of journey = 2941-04-25 = day 0)
            try:
                scene_date = date(year, month, day)
                start_date = date(2941, 4, 25)
                journey_day = (scene_date - start_date).days
            except Exception:
                journey_day = 0
            s['journey_day'] = journey_day
            # Use same sort key structure: (day, progress/order, index)
            s['sort_key'] = (journey_day, pos, i + len(self.canonical_scenes))
            self.scenes.append(s)
        self.scenes.sort(key=lambda x: x['sort_key'])
        
    def load_config(self):
        """Load pacing configuration"""
        try:
            with open('data/stream_config.json', 'r') as f:
                config_data = json.load(f)
                self.config = {
                    'pacing_mode': config_data.get('pacing_mode', {}).get('value', 'dramatic'),
                    'pacing_factor': config_data.get('pacing', {}).get('value', 0.2),
                    'base_delay': config_data.get('base_delay', {}).get('value', 10000) / 1000  # convert to seconds
                }
        except Exception as e:
            print(f"Config load error: {e}")
            self.config = {
                'pacing_mode': 'dramatic',
                'pacing_factor': 0.2,
                'base_delay': 10
            }
    
    def get_scene_duration_ms(self, scene):
        """Get scene duration in milliseconds based on pacing"""
        if scene.get('is_canonical'):
            # Use estimated duration if available, fall back to story_duration
            est = self.estimated_durations.get(scene.get('id'), {})
            hours = est.get('estimated_duration_hours', None)
            if hours is None:
                duration_str = scene.get('story_duration', '2h')
                try:
                    if 'h' in duration_str.lower():
                        hours = float(duration_str.lower().replace('h', '').strip())
                    else:
                        hours = 2.0
                except:
                    hours = 2.0
        else:
            # Generated scenes use duration_hours directly
            hours = scene.get('duration_hours', 2)
        
        factor = self.config.get('pacing_factor', 0.2)
        base = self.config.get('base_delay', 10)  # in seconds
        # Convert to milliseconds: hours * pacing factor + base delay
        return int(hours * 3600000 * factor + base * 1000)
    
    def get_current_scene_data(self):
        """Get full data for current scene"""
        if not self.scenes:
            return None
        scene = self.scenes[self.current_scene_idx]
        scene_id = scene['id']
        
        # Get narrative
        narrative = self.narratives.get(scene_id, {})
        
        # Get beats - handle different structures
        beat_data = self.beats.get(scene_id, {})
        if isinstance(beat_data, dict) and 'beats' in beat_data:
            beat_list = beat_data['beats']
        elif isinstance(beat_data, list):
            beat_list = beat_data
        else:
            beat_list = []
        
        # Normalize beat structure
        normalized_beats = []
        for b in beat_list:
            if isinstance(b, dict):
                normalized_beats.append({
                    'start': b.get('start', 0),
                    'end': b.get('end', 1),
                    'text': b.get('text', '')
                })
        
        beat_data = {'beats': normalized_beats, 'duration_hours': scene.get('duration_hours', 2)}
        
        # Calculate time remaining
        duration_ms = self.get_scene_duration_ms(scene)
        elapsed_ms = self.scene_progress * duration_ms
        remaining_ms = duration_ms - elapsed_ms
        
        # Format countdown
        remaining_sec = int(remaining_ms / 1000)
        if remaining_sec >= 86400:
            countdown = f"{remaining_sec // 86400:02d}:{(remaining_sec % 86400) // 3600:02d}:{(remaining_sec % 3600) // 60:02d}:{remaining_sec % 60:02d}"
        elif remaining_sec >= 3600:
            countdown = f"{(remaining_sec % 86400) // 3600:02d}:{(remaining_sec % 3600) // 60:02d}:{remaining_sec % 60:02d}"
        else:
            countdown = f"{(remaining_sec % 3600) // 60:02d}:{remaining_sec % 60:02d}"
        
        # Estimated duration info for canonical scenes
        est = self.estimated_durations.get(scene.get('id'), {})
        
        return {
            'scene': scene,
            'narrative': narrative,
            'beats': beat_data,
            'current_beat': self.current_beat_idx,
            'beat_progress': self.beat_progress,
            'scene_progress': self.scene_progress,
            'countdown': countdown,
            'remaining_ms': remaining_ms,
            'duration_ms': duration_ms,
            'estimated_duration_hours': est.get('estimated_duration_hours', None),
            'estimated_confidence': est.get('confidence', None),
            'estimated_reasoning': est.get('reasoning', None),
            'scene_number': self.current_scene_idx + 1,
            'total_scenes': len(self.scenes),
            'is_playing': self.is_playing,
            'pacing': self.config.get('pacing_mode', 'dramatic')
        }
    
    def next_scene(self):
        """Go to next scene"""
        if self.current_scene_idx < len(self.scenes) - 1:
            self.current_scene_idx += 1
            self.reset_scene_state()
            return True
        return False
    
    def prev_scene(self):
        """Go to previous scene"""
        if self.current_scene_idx > 0:
            self.current_scene_idx -= 1
            self.reset_scene_state()
            return True
        return False
    
    def reset_scene_state(self):
        """Reset state when changing scenes"""
        self.current_beat_idx = 0
        self.beat_progress = 0.0
        self.scene_progress = 0.0
        self.last_update = time.time()
    
    def toggle_play(self):
        """Toggle play/pause"""
        self.is_playing = not self.is_playing
        self.last_update = time.time()
        return self.is_playing
    
    def update(self):
        """Update timer and progress"""
        if not self.is_playing:
            return
        
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        
        scene = self.scenes[self.current_scene_idx]
        duration_ms = self.get_scene_duration_ms(scene)
        
        # Update scene progress
        self.scene_progress += (dt * 1000) / duration_ms
        if self.scene_progress >= 1.0:
            if self.current_scene_idx < len(self.scenes) - 1:
                self.current_scene_idx += 1
                self.reset_scene_state()
            else:
                self.scene_progress = 1.0
                self.is_playing = False
        
        # Update beat progress
        beat_data = self.beats.get(scene['id'], {'beats': []})
        num_beats = len(beat_data.get('beats', []))
        if num_beats > 0:
            beat_duration = 1.0 / num_beats
            self.current_beat_idx = min(int(self.scene_progress / beat_duration), num_beats - 1)
            beat_start = self.current_beat_idx * beat_duration
            self.beat_progress = (self.scene_progress - beat_start) / beat_duration
    
    def run_timer(self):
        """Background timer thread"""
        while True:
            self.update()
            time.sleep(0.1)

# Create global engine instance
engine = StreamEngine()

# Start timer thread
timer_thread = threading.Thread(target=engine.run_timer, daemon=True)
timer_thread.start()

# API Routes
@app.route('/prototypes/<path:filename>')
def serve_prototypes(filename):
    return send_from_directory(os.path.join(project_root, 'prototypes'), filename)

@app.route('/')
def index():
    return send_file(os.path.join(project_root, 'stream_client.html'))

@app.route('/book')
def book_layout():
    return send_file(os.path.join(project_root, 'stream_book.html'))

@app.route('/monitor')
def stream_monitor():
    return send_file(os.path.join(project_root, 'stream_monitor.html'))

@app.route('/api/current')
def get_current():
    return jsonify(engine.get_current_scene_data())

@app.route('/api/next', methods=['POST'])
def next_scene():
    engine.next_scene()
    return jsonify(engine.get_current_scene_data())

@app.route('/api/prev', methods=['POST'])
def prev_scene():
    engine.prev_scene()
    return jsonify(engine.get_current_scene_data())

@app.route('/api/play', methods=['POST'])
def toggle_play():
    engine.toggle_play()
    return jsonify(engine.get_current_scene_data())

@app.route('/api/goto/<int:index>', methods=['POST'])
def goto_scene(index):
    if 0 <= index < len(engine.scenes):
        engine.current_scene_idx = index
        engine.reset_scene_state()
    return jsonify(engine.get_current_scene_data())

@app.route('/api/scenes')
def get_all_scenes():
    """Get all scene titles for timeline"""
    scenes = []
    for i, s in enumerate(engine.scenes):
        # Get day from appropriate field
        if s.get('is_canonical'):
            day = s.get('journey_day', 0)
        else:
            # Parse from date_iso
            date_iso = s.get('date_iso', '0000-01-01')
            try:
                parts = date_iso.split('-')
                day = int(parts[1]) * 30 + int(parts[2]) if len(parts) >= 3 else 0
            except:
                day = 0
        
        scenes.append({
            'index': i,
            'id': s['id'],
            'title': s.get('title', f'Scene {i+1}'),
            'is_canonical': s.get('is_canonical', True),
            'location': s.get('location', 'Unknown'),
            'day': day
        })
    return jsonify(scenes)

@app.route('/api/chapters')
def get_chapters():
    """Get chapters with their canonical scenes for splits."""
    chapters = {}
    chapter_order = []
    for s in engine.canonical_scenes:
        ch_title = s.get('chapter', 'Unknown')
        if ch_title not in chapters:
            chapters[ch_title] = {
                'title': ch_title,
                'scene_ids': [],
                'first_scene_id': s['id']
            }
            chapter_order.append(ch_title)
        chapters[ch_title]['scene_ids'].append(s['id'])
    
    result = []
    for i, title in enumerate(chapter_order, 1):
        ch = chapters[title]
        result.append({
            'number': i,
            'title': title,
            'scene_ids': ch['scene_ids'],
            'audio_url': f'/audio/chapter/{i}'
        })
    return jsonify(result)

@app.route('/audio/chapter/<int:chapter_num>')
def serve_chapter_audio(chapter_num):
    """Serve pre-generated chapter audiobook WAV."""
    audio_path = os.path.join(project_root, f'output/chapter{chapter_num}_audio/chapter{chapter_num}_complete.wav')
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    return jsonify({"error": "Audio not found"}), 404

@app.route('/api/estimated_durations')
def get_estimated_durations():
    """Get non-canonical estimated durations for all canonical scenes."""
    return jsonify(engine.estimated_durations)

# ==================== Countdown API ====================

import json as _json

def _load_countdown_config():
    cfg_path = os.path.join(project_root, 'countdown', 'config.json')
    try:
        with open(cfg_path, 'r') as f:
            return _json.load(f)
    except Exception:
        return None

@app.route('/countdown')
def countdown_page():
    """Serve a web-based countdown page."""
    cfg = _load_countdown_config()
    if not cfg:
        return "<h1>Countdown not configured</h1>", 404
    start = cfg.get('start_date', '2026-04-26T11:00:00')
    title = cfg.get('title', 'The Hobbit: An Unexpected Journey')
    subtitle = cfg.get('subtitle', 'Until The Unexpected Party')
    quotes = cfg.get('quotes', [])
    colors = cfg.get('colors', {})
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Countdown</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Georgia', serif;
    background: linear-gradient(180deg, #2d4a22 0%, #141a0f 100%);
    color: #e0d0b0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}}
.countdown {{
    font-size: clamp(48px, 10vw, 120px);
    color: {colors.get('countdown', '#d4af37')};
    font-family: 'Courier New', monospace;
    letter-spacing: 8px;
    text-shadow: 0 0 20px rgba(212,175,55,0.3);
    margin-bottom: 10px;
}}
.labels {{
    font-size: 14px;
    color: {colors.get('subtitle', '#a09070')};
    letter-spacing: 6px;
    margin-bottom: 40px;
}}
.subtitle {{
    font-size: clamp(18px, 3vw, 32px);
    color: {colors.get('subtitle', '#a09070')};
    margin-bottom: 30px;
}}
.progress {{
    font-size: clamp(16px, 2.5vw, 24px);
    color: {colors.get('progress', '#8b7355')};
    font-family: 'Courier New', monospace;
    margin-bottom: 40px;
}}
.quote {{
    font-size: clamp(16px, 2vw, 22px);
    color: {colors.get('quote', '#e0d0b0')};
    font-style: italic;
    max-width: 800px;
    padding: 0 20px;
    line-height: 1.6;
}}
.footer {{
    position: absolute;
    bottom: 20px;
    font-size: 12px;
    color: #5a5045;
}}
</style>
</head>
<body>
<div class="countdown" id="countdown">-- : -- : -- : --</div>
<div class="labels" id="labels">DAYS &nbsp;&nbsp; HOURS &nbsp;&nbsp; MINUTES &nbsp;&nbsp; SECONDS</div>
<div class="subtitle">{subtitle}</div>
<div class="progress" id="progress">▓▓▓▓░░░░░░ 0%</div>
<div class="quote" id="quote">Loading...</div>
<div class="footer">Canonical start: {start}</div>
<script>
const START_DATE = new Date("{start}").getTime();
const QUOTES = {quotes};
const QUOTE_ROTATION_MIN = {cfg.get('quote_rotation_minutes', 60)};
const PROGRESS_WIDTH = {cfg.get('progress_bar', {}).get('width', 40)};
const FILLED = "{cfg.get('progress_bar', {}).get('filled_char', '▓')}";
const EMPTY = "{cfg.get('progress_bar', {}).get('empty_char', '░')}";
const WINDOW_DAYS = {cfg.get('countdown_window_days', 30)};

function pad(n) {{ return n.toString().padStart(2, '0'); }}

function getQuote(now, start) {{
    if (now >= start) return "The journey has begun...";
    const secondsLeft = Math.floor((start - now) / 1000);
    const period = QUOTE_ROTATION_MIN * 60;
    const idx = Math.floor(secondsLeft / period) % QUOTES.length;
    return QUOTES[idx];
}}

function update() {{
    const now = Date.now();
    const diff = START_DATE - now;
    const elCountdown = document.getElementById('countdown');
    const elLabels = document.getElementById('labels');
    const elProgress = document.getElementById('progress');
    const elQuote = document.getElementById('quote');

    if (diff <= 0) {{
        elCountdown.textContent = "00 : 00 : 00 : 00";
        elLabels.textContent = "";
        elProgress.textContent = "▓".repeat(PROGRESS_WIDTH) + " 100%";
        elQuote.textContent = "The journey has begun...";
        return;
    }}

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    if (days > 0) {{
        elCountdown.textContent = `${{pad(days)}} : ${{pad(hours)}} : ${{pad(minutes)}} : ${{pad(seconds)}}`;
        elLabels.innerHTML = "DAYS &nbsp;&nbsp;&nbsp;&nbsp; HOURS &nbsp;&nbsp;&nbsp;&nbsp; MINUTES &nbsp;&nbsp;&nbsp;&nbsp; SECONDS";
    }} else {{
        elCountdown.textContent = `${{pad(hours)}} : ${{pad(minutes)}} : ${{pad(seconds)}}`;
        elLabels.innerHTML = "HOURS &nbsp;&nbsp;&nbsp;&nbsp; MINUTES &nbsp;&nbsp;&nbsp;&nbsp; SECONDS";
    }}

    const windowStart = START_DATE - (WINDOW_DAYS * 24 * 60 * 60 * 1000);
    const total = START_DATE - windowStart;
    const elapsed = now - windowStart;
    let pct = Math.min(100, Math.max(0, (elapsed / total) * 100));
    const filledLen = Math.floor(PROGRESS_WIDTH * pct / 100);
    const bar = FILLED.repeat(filledLen) + EMPTY.repeat(PROGRESS_WIDTH - filledLen);
    elProgress.textContent = `${{bar}}  ${{pct.toFixed(1)}}%`;

    elQuote.textContent = getQuote(now, START_DATE);
}}

setInterval(update, 1000);
update();
</script>
</body>
</html>"""

@app.route('/api/countdown')
def countdown_api():
    """Return countdown data as JSON."""
    cfg = _load_countdown_config()
    if not cfg:
        return jsonify({"error": "Countdown not configured"}), 404
    start_str = cfg.get('start_date', '2026-04-26T11:00:00')
    try:
        start = datetime.fromisoformat(start_str)
        if start.tzinfo is None:
            start = start.astimezone()
    except Exception as e:
        return jsonify({"error": f"Invalid start_date: {e}"}), 500
    now = datetime.now().astimezone()
    diff = start - now
    seconds = max(0, diff.total_seconds())
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    window_days = cfg.get('countdown_window_days', 30)
    window_start = start.timestamp() - (window_days * 86400)
    total = start.timestamp() - window_start
    elapsed = now.timestamp() - window_start
    pct = min(100.0, max(0.0, (elapsed / total) * 100))
    quotes = cfg.get('quotes', [])
    q_rot = cfg.get('quote_rotation_minutes', 60)
    q_idx = int(seconds // (q_rot * 60)) % len(quotes) if quotes else 0
    return jsonify({
        "start_date": start_str,
        "now": now.isoformat(),
        "remaining": {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": secs,
            "total_seconds": int(seconds)
        },
        "progress_percent": round(pct, 2),
        "quote": quotes[q_idx] if quotes else "",
        "title": cfg.get('title'),
        "subtitle": cfg.get('subtitle')
    })

# ==================== Generative Content API ====================

# Initialize generative content engine
try:
    from generative import ContentGenerator, GenerativeConfig
    gen_config = GenerativeConfig.from_file("generative/config.json")
    content_generator = ContentGenerator(gen_config)
    print("[Server] Generative content engine initialized")
except Exception as e:
    print(f"[Server] Generative content not available: {e}")
    content_generator = None

@app.route('/api/generate/status')
def generate_status():
    """Get generation status"""
    if not content_generator:
        return jsonify({"enabled": False, "error": "Generative content not available"})
    
    scene_id = request.args.get('scene')
    return jsonify({
        "enabled": True,
        "config": {
            "images_enabled": content_generator.config.images.enabled,
            "audio_enabled": content_generator.config.audio.enabled,
            "voice_enabled": content_generator.config.voice.enabled
        },
        "status": content_generator.get_status(scene_id)
    })

@app.route('/api/generate/image', methods=['POST'])
def generate_image():
    """Request scene image generation"""
    if not content_generator:
        return jsonify({"error": "Generative content not available"}), 503
    
    data = request.get_json()
    scene_id = data.get('scene_id')
    force = data.get('force', False)
    
    # Find scene data
    scene_data = None
    for s in engine.scenes:
        if s['id'] == scene_id:
            scene_data = s
            break
    
    if not scene_data:
        return jsonify({"error": "Scene not found"}), 404
    
    result = content_generator.generate_scene_image(scene_data, force)
    return jsonify(result.to_dict())

@app.route('/api/generate/audio', methods=['POST'])
def generate_audio():
    """Request ambient audio generation"""
    if not content_generator:
        return jsonify({"error": "Generative content not available"}), 503
    
    data = request.get_json()
    scene_id = data.get('scene_id')
    force = data.get('force', False)
    
    scene_data = None
    for s in engine.scenes:
        if s['id'] == scene_id:
            scene_data = s
            break
    
    if not scene_data:
        return jsonify({"error": "Scene not found"}), 404
    
    result = content_generator.generate_ambient_audio(scene_data, force)
    return jsonify(result.to_dict())

@app.route('/api/generate/voice', methods=['POST'])
def generate_voice():
    """Request voice narration generation"""
    if not content_generator:
        return jsonify({"error": "Generative content not available"}), 503
    
    data = request.get_json()
    text = data.get('text', '')
    voice_id = data.get('voice_id')
    scene_id = data.get('scene_id', 'unknown')
    
    if not text:
        return jsonify({"error": "Text required"}), 400
    
    result = content_generator.generate_narration(text, voice_id, scene_id)
    return jsonify(result.to_dict())

@app.route('/api/generate/pregenerate', methods=['POST'])
def pregenerate_scene():
    """Pre-generate all content for a scene"""
    if not content_generator:
        return jsonify({"error": "Generative content not available"}), 503
    
    data = request.get_json()
    scene_id = data.get('scene_id')
    include_image = data.get('image', True)
    include_audio = data.get('audio', True)
    include_voice = data.get('voice', False)
    
    scene_data = None
    for s in engine.scenes:
        if s['id'] == scene_id:
            scene_data = s
            break
    
    if not scene_data:
        return jsonify({"error": "Scene not found"}), 404
    
    content_generator.pregenerate_scene(
        scene_data, include_image, include_audio, include_voice
    )
    
    return jsonify({
        "status": "queued",
        "scene_id": scene_id,
        "queued": {
            "image": include_image,
            "audio": include_audio,
            "voice": include_voice
        }
    })

# ==================== Events API ====================

EVENTS_DB = os.path.join(project_root, 'data', 'generated_events.db')


def _events_conn():
    if not os.path.exists(EVENTS_DB):
        return None
    conn = sqlite3.connect(EVENTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _build_event_filter_sql(params: list) -> str:
    """Build common event filter SQL from request args."""
    sql = ""
    batch_id = request.args.get('batch_id', '')
    gap_id = request.args.get('gap_id', '')
    if batch_id:
        sql += " AND batch_id = ?"
        params.append(batch_id)
    else:
        sql += " AND is_active = 1"
    if gap_id:
        sql += " AND gap_id = ?"
        params.append(gap_id)
    return sql


@app.route('/api/events/range')
def events_range():
    """Get events in a time range. Query params: from, to (ISO8601)."""
    conn = _events_conn()
    if not conn:
        return jsonify({"events": [], "count": 0})
    from_ts = request.args.get('from', '')
    to_ts = request.args.get('to', '')
    limit = request.args.get('limit', 100, type=int)
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM events WHERE 1=1"
        params = []
        sql += _build_event_filter_sql(params)
        if from_ts:
            sql += " AND timestamp >= ?"
            params.append(from_ts)
        if to_ts:
            sql += " AND timestamp <= ?"
            params.append(to_ts)
        sql += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"events": rows, "count": len(rows)})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/events/current')
def events_current():
    """Get the most recent event at or before a given timestamp."""
    conn = _events_conn()
    if not conn:
        return jsonify({"event": None})
    ts = request.args.get('timestamp', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM events WHERE timestamp <= ?"
        params = [ts]
        sql += _build_event_filter_sql(params)
        sql += " ORDER BY timestamp DESC LIMIT 1"
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return jsonify({"event": dict(row) if row else None})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/events/next')
def events_next():
    """Get the next event after a given timestamp."""
    conn = _events_conn()
    if not conn:
        return jsonify({"event": None})
    ts = request.args.get('timestamp', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM events WHERE timestamp > ?"
        params = [ts]
        sql += _build_event_filter_sql(params)
        sql += " ORDER BY timestamp ASC LIMIT 1"
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return jsonify({"event": dict(row) if row else None})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/events/recent')
def events_recent():
    """Get most recent N events."""
    conn = _events_conn()
    if not conn:
        return jsonify({"events": [], "count": 0})
    limit = request.args.get('limit', 20, type=int)
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM events WHERE 1=1"
        params = []
        sql += _build_event_filter_sql(params)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"events": rows, "count": len(rows)})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/batches')
def generation_batches():
    """Get generation batch log."""
    conn = _events_conn()
    if not conn:
        return jsonify({"batches": [], "count": 0})
    limit = request.args.get('limit', 50, type=int)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM generation_batches ORDER BY started_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"batches": rows, "count": len(rows)})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/events/stream')
def events_stream():
    """Server-Sent Events stream for live generation updates."""
    def gen():
        cid, q = sse.register()
        try:
            while True:
                data = q.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
        except queue.Empty:
            yield "data: {}\n\n"
        finally:
            sse.unregister(cid)
    return app.response_class(gen(), mimetype='text/event-stream')


@app.route('/api/events/hook', methods=['POST'])
def events_hook():
    """Internal hook called by event_generator.py when a batch finishes."""
    payload = request.get_json(force=True, silent=True) or {}
    sse.publish(payload)
    return jsonify({"ok": True})


@app.route('/api/batches/for-gap')
def batches_for_gap():
    """Get batches for a specific gap_id."""
    conn = _events_conn()
    if not conn:
        return jsonify({"batches": [], "count": 0})
    gap_id = request.args.get('gap_id', '')
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM generation_batches WHERE gap_id = ? ORDER BY started_at DESC",
            (gap_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"batches": rows, "count": len(rows)})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


# Serve generated media files
@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve generated media files"""
    media_dir = os.path.join(project_root, 'output', 'media')
    return send_from_directory(media_dir, filename)

# ==================== Main Entry Point ====================

if __name__ == '__main__':
    print("Starting Hobbit Stream Server...")
    print("Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=False)
