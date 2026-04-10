# The Hobbit Journey Stream - Web Version

A web-based frontend for The Hobbit Journey Stream with a Python Flask backend.

## Quick Start

```bash
# Start the server
./start_server.sh

# Or manually:
python3 scripts/stream_server.py
```

Then open http://localhost:5000 in your browser.

## Architecture

```
┌─────────────────┐     HTTP/REST      ┌─────────────────┐
│  Web Browser    │ ◄────────────────► │  Flask Server   │
│  (HTML/CSS/JS)  │                    │  (Python)       │
└─────────────────┘                    └─────────────────┘
                                               │
                                               ▼
                                        ┌─────────────────┐
                                        │  JSON Data Files│
                                        │  - stream_scenes│
                                        │  - gap_scenes   │
                                        │  - narratives   │
                                        │  - beats        │
                                        └─────────────────┘
                                               │
                                               ▼
                                        ┌─────────────────┐
                                        │  AI Generation  │
                                        │  - Images       │
                                        │  - Audio        │
                                        │  - Voice        │
                                        └─────────────────┘
```

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the HTML client |
| `/api/current` | GET | Get current scene data |
| `/api/scenes` | GET | Get all scene titles for timeline |
| `/api/next` | POST | Go to next scene |
| `/api/prev` | POST | Go to previous scene |
| `/api/play` | POST | Toggle play/pause |
| `/api/goto/<index>` | POST | Jump to specific scene |

### Generative Content Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate/status` | GET | Get generation status |
| `/api/generate/image` | POST | Generate scene image |
| `/api/generate/audio` | POST | Generate ambient audio |
| `/api/generate/voice` | POST | Generate narration |
| `/api/generate/pregenerate` | POST | Generate all content for scene |
| `/media/<path>` | GET | Serve generated media files |

## Features

### Core Features
- **170 Scenes**: 96 canonical + 74 generated gap scenes
- **Progressive Narrative Beats**: Typewriter-style text reveal
- **Real-time Progress Bars**: Scene and beat progress synchronized
- **Countdown Timer**: DD:HH:MM:SS format
- **Interactive Timeline**: Click to navigate between scenes
- **Pacing Modes**: Compressed, Dramatic, Synced, Realtime
- **Sidebar Info**: Journey stats, present characters, upcoming events

### AI Generative Features
- **Scene Images**: AI-generated illustrations using DALL-E 3
- **Ambient Audio**: Location-based soundscapes
- **Voice Narration**: AI voice narration for narrative beats
- **Auto-Generation**: Optional automatic generation on scene change

## Setup

### Basic Setup
```bash
# Install Flask
pip install flask flask-cors

# Start server
./start_server.sh
```

### With AI Features
```bash
# Install AI dependencies
pip install openai elevenlabs

# Set API keys
export OPENAI_API_KEY="your-key"
export ELEVENLABS_API_KEY="your-key"

# Enable in config
# Edit generative/config.json: set enabled: true

# Start server
./start_server.sh
```

## File Structure

```
├── scripts/
│   └── stream_server.py      # Flask backend
├── generative/
│   ├── __init__.py
│   ├── engine.py             # Content generation engine
│   ├── config.py             # Configuration classes
│   └── config.json           # User settings
├── output/media/             # Generated content cache
│   ├── images/
│   ├── audio/
│   └── voice/
├── stream_client.html        # Web frontend
├── data/                     # Scene data
│   ├── stream_scenes.json
│   ├── generated_gap_scenes.json
│   ├── scene_narratives.json
│   ├── scene_beats.json
│   └── stream_config.json
└── start_server.sh           # Launcher script
```

## AI Features Guide

### Enabling Image Generation

1. Get OpenAI API key: https://platform.openai.com
2. Set environment variable: `export OPENAI_API_KEY="sk-..."`
3. Enable in UI: Click "✨ AI" button → Toggle "Scene Images"
4. Generate: Click "Generate" button in image section

### Enabling Voice Narration

1. Get ElevenLabs API key: https://elevenlabs.io
2. Set environment variable: `export ELEVENLABS_API_KEY="..."`
3. Enable in UI: Click "✨ AI" button → Toggle "Voice Narration"
4. Generate: Click "Narrate Beat" button during playback

### Cost Estimation

| Feature | Cost per Scene | 170 Scenes Total |
|---------|---------------|------------------|
| Image (Standard) | $0.04 | ~$6.80 |
| Image (HD) | $0.08 | ~$13.60 |
| Voice | ~$0.01 | ~$1.70 |

## Keyboard Shortcuts

- `Space` - Play/Pause
- `←` / `→` - Previous/Next Scene
- `I` - Toggle Image section
- `A` - Toggle Audio section
- `N` - Generate narration for current beat

## Configuration

Edit `generative/config.json`:

```json
{
  "images": {
    "enabled": true,
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard"
  },
  "audio": {
    "enabled": true,
    "ambient_enabled": true
  },
  "voice": {
    "enabled": true,
    "default_voice": "narrator"
  },
  "auto_generate": false
}
```

See `generative/README.md` for detailed configuration options.
