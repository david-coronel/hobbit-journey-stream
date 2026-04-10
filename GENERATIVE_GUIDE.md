# Generative Content Guide

This document explains how generative content is produced in the Hobbit Journey Stream. The project has shifted from **pre-generating thousands of AI-written scenes** to a **procedural engine** that generates narrative beats in real time from structured arc trees.

## Current Generative Strategy

### 1. Structured Gaps (`gap_planner.py`)

Instead of calling an LLM for every gap upfront, we first build a narrative tree for each gap:

```
subplot: "Travel: X → Y"
  └── sequence: "Departure"
        ├── beat: "Preparing to leave" (2h)
        ├── beat: "Morning march" (4h)
        └── beat: "Midday rest" (2h)
  └── sequence: "Day 2 of Travel"
        ├── beat: "Morning march" (6h)
        ├── beat: "Afternoon march" (6h)
        ├── beat: "Making camp" (3h)
        ├── beat: "Evening meal" (4h)
        └── beat: "Night watches" (5h)
```

These trees live in `data/gap_plans.json` and are categorized by duration:

| Type | Duration | Count |
|------|----------|-------|
| `none` | ≤ 0.1 h | 36 |
| `micro` | ≤ 3 h | 11 |
| `small` | 3–24 h | 27 |
| `travel` | 1–10 d | 17 |
| `long` | > 10 d | 4 |

### 2. Procedural Engine (Minute-by-Minute)

The stream engine will:

1. Maintain a unified timeline of 96 canonical scenes + 59 gap arcs.
2. Every real minute, advance the in-story clock and emit the current event.
3. For canonical scenes: play the audiobook segment and display pre-extracted text.
4. For gap beats: call a lightweight LLM prompt (or template) using the beat title, duration, and current world state to produce 1–3 sentences of narrative.

Because content is generated **just-in-time**, we avoid storing hundreds of megabytes of pre-written prose and can adapt tone based on live state.

### 3. Time-Dilation for Long Gaps

The 4 `long` gaps (128d, 16d, 159d, 52d) contain "compressed" beats. The engine will detect these and switch to summary narration:

- **Real-time mode:** 1 narrative hour = 12 real minutes (for normal beats).
- **Compressed mode:** 1 narrative day = 1 real minute (for compressed beats), producing paragraphs like *"Weeks passed in silence..."*

This keeps the total stream length manageable without breaking the real-time illusion.

## Pre-Generated Assets (Already Built)

### Audiobook — Kokoro TTS

All 19 chapters were synthesized using **Kokoro TTS** via Modal Labs. The resulting audio files are served during canonical scenes.

- **Runtime:** ~7.5 hours
- **Storage:** ~1.3 GB
- **Deployment:** `runpod-kokoro/chatterbox_modal.py`

### Chapter Colors

Each of the 19 chapters has a unique color used consistently across timelines and the web UI. These are hard-coded in the prototypes and derived from a fixed palette.

## Deprecated Pre-Generation Approach

Earlier iterations tried to pre-generate all gap content with DALL-E and OpenRouter LLMs:

- `scripts/gap_content_generator.py`
- `data/generated_gap_scenes.json`
- `data/generated_scenes.json`

This approach was abandoned because:
- **Cost:** ~$0.50–$1.00 per 74 scenes, but quality was inconsistent.
- **Scale:** 467 days of narrative would require tens of thousands of scenes.
- **Storage:** Hundreds of megabytes of rarely-viewed prose.
- **Inflexibility:** Pre-written text cannot react to state changes or viewer interactions.

The old scripts and outputs remain in the repository for reference but are **not part of the active pipeline**.

## Future Generative Enhancements

1. **Local LLM integration** — Run a small model (e.g., Llama 3B) on the server for zero-cost gap narration.
2. **Dynamic weather & season** — Procedural weather based on date and location.
3. **Character voice variations** — Kokoro voice switching per character for dialogue lines.
4. **Ambient audio cues** — Location-based soundscapes generated or selected procedurally.

## Quick Reference

### Generate / Refresh Gap Arcs
```bash
python3 scripts/gap_planner.py
```

### Deploy TTS (Modal)
```bash
cd runpod-kokoro
modal deploy chatterbox_modal.py
```

### Check a Specific Gap
```bash
python3 -c "
import json
with open('data/gap_plans.json') as f:
    gaps = json.load(f)['gaps']
for g in gaps:
    if g['gap_id'] == 'gap_canon_044_canon_045':
        print(json.dumps(g['arc'], indent=2))
"
```
