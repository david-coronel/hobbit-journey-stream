# Generative Content System

AI-powered content generation for The Hobbit Journey Stream.

## Overview

This module provides generative capabilities for:
- **Images**: Scene illustrations using DALL-E
- **Audio**: Ambient soundscapes and effects
- **Voice**: Narration and character dialogue

## Quick Start

### 1. Install Dependencies

```bash
pip install openai elevenlabs
```

### 2. Set API Keys

```bash
export OPENAI_API_KEY="your-openai-key"
export ELEVENLABS_API_KEY="your-elevenlabs-key"
```

Or create a `.env` file:
```
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
```

### 3. Enable Features

Edit `generative/config.json`:
```json
{
  "images": { "enabled": true },
  "audio": { "enabled": true },
  "voice": { "enabled": true }
}
```

### 4. Start the Server

```bash
./start_server.sh
```

## Features

### Image Generation

Generates scene illustrations using DALL-E 3.

**Configuration:**
- `provider`: "openai" (currently only supported)
- `model`: "dall-e-3"
- `size`: "1024x1024" | "1792x1024" | "1024x1792"
- `quality`: "standard" | "hd"
- `style`: "vivid" | "natural"

**Prompt Template:**
The system builds prompts from scene data:
- Scene title
- Location
- Time of day (inferred from scene)
- Atmosphere
- Characters present
- Scene description

**Usage:**
- Click "Generate" button in the UI
- Or enable "Auto-Generate" for automatic generation

**Output:**
- Saved to `output/media/images/`
- Accessible via `/media/images/<filename>`

### Audio Generation

Generates ambient soundscapes based on location.

**Location Types:**
- forest, mountain, cave
- hobbiton, lake, dungeon
- battle, dragon, travel

**Usage:**
- Click "Generate" to create soundscape
- Use "Ambient" button to play/pause
- Adjust volume with slider

**Note:** Currently uses placeholder audio. Full AI generation coming soon.

### Voice Generation

Generates narration using ElevenLabs voices.

**Voice IDs:**
- `narrator`: Default storytelling voice
- `bilbo`: Main character voice
- `gandalf`: Wise, older voice
- `thorin`: Gruff, leadership voice
- `gollum`: (Configure with specific voice ID)
- `smaug`: (Configure with specific voice ID)

**Usage:**
- Click "Narrate Beat" to generate voice for current narrative beat
- Audio plays automatically

## API Endpoints

### Get Generation Status
```
GET /api/generate/status?scene=<scene_id>
```

### Generate Image
```
POST /api/generate/image
{
  "scene_id": "canon_001",
  "force": false
}
```

### Generate Audio
```
POST /api/generate/audio
{
  "scene_id": "canon_001",
  "force": false
}
```

### Generate Voice
```
POST /api/generate/voice
{
  "text": "The dragon lay sleeping...",
  "voice_id": "narrator",
  "scene_id": "canon_001"
}
```

### Pre-generate All Content
```
POST /api/generate/pregenerate
{
  "scene_id": "canon_001",
  "image": true,
  "audio": true,
  "voice": false
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ContentGenerator                        │
│                    (generative/engine.py)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Images    │  │    Audio    │  │       Voice         │  │
│  │  (DALL-E)   │  │  (ElevenLabs│  │   (ElevenLabs)      │  │
│  │             │  │    /Local)  │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                 Background Queue                        ││
│  │         (Asynchronous generation thread)                ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Caching

Generated content is cached to avoid regeneration:
- Images: `output/media/images/`
- Audio: `output/media/audio/`
- Voice: `output/media/voice/`

Cache key format: `{type}_{scene_id}_{hash}`

## Cost Estimation

Approximate costs per scene (USD):

| Feature | Provider | Cost per Generation |
|---------|----------|---------------------|
| Image | OpenAI DALL-E 3 | $0.04 (1024x1024) |
| Image HD | OpenAI DALL-E 3 | $0.08 (1024x1024) |
| Voice | ElevenLabs | ~$0.01 per 1000 chars |
| Audio | TBD | TBD |

For 170 scenes:
- Images only: ~$6.80 - $13.60
- Full package: ~$20-30

## Future Enhancements

### Image Generation
- [ ] Stable Diffusion support (local generation)
- [ ] Character portrait generation
- [ ] Location art style consistency
- [ ] Animation/video generation

### Audio Generation
- [ ] AI soundscape generation (ElevenLabs, AudioLDM)
- [ ] Dynamic audio mixing
- [ ] Weather-based ambient
- [ ] Time-of-day variations

### Voice Generation
- [ ] Character-specific voices
- [ ] Emotion control
- [ ] Real-time narration
- [ ] Multiple languages

## Troubleshooting

### Images not generating
- Check `OPENAI_API_KEY` is set
- Verify `images.enabled` in config
- Check server logs for errors

### Voice not playing
- Check `ELEVENLABS_API_KEY` is set
- Verify browser audio permissions
- Check volume slider

### High costs
- Disable auto-generate
- Use lower quality settings
- Clear cache to regenerate selectively

## License

Generative content respects the copyrights of:
- The Hobbit by J.R.R. Tolkien (HarperCollins)
- AI providers' terms of service

Generated content is for personal/educational use only.
