# Hobbit Journey Stream

A real-time narrative stream of J.R.R. Tolkien's *The Hobbit*. One day in Middle-earth equals one day in the real world, delivered through a procedural engine that walks 96 canonical scenes and 59 generated narrative gaps minute by minute.

## Project Status

- **96 canonical scenes** extracted from the EPUB, with realistic in-story durations (~56.9 days total).
- **Audiobook generated** for all 19 chapters using Kokoro TTS (~7.5h, 1.3GB).
- **World state tracking** across the full journey: 25 characters, locations, inventories, and key events.
- **Gap planner** produces 59 narrative arcs (micro / small / travel / long) covering ~411 days of gap time.
- **Stream goal:** 1-minute updates, 1 Middle-earth day = 1 real day, procedural generation from structured trees.

## Architecture

```
EPUB
  ↓
scripts/extract_all_scenes_final.py
  ↓
data/hobbit_book_scenes.json
  ↓
Manual refinement + duration correction
  ↓
data/stream_scenes.json           (96 canonical scenes)
data/canonical_scene_states.json  (state_in / state_out per scene)
  ↓
scripts/gap_planner.py
  ↓
data/gap_plans.json               (59 arcs: subplot → sequence → beat)
  ↓
Procedural stream engine (minute-by-minute generator)
  ↓
Web client / streaming interface
```

## Key Data Files

| File | Purpose |
|------|---------|
| `data/stream_scenes.json` | 96 canonical scenes with corrected dates, hours, durations, and chapter colors |
| `data/canonical_scene_states.json` | World state snapshots (`state_in` / `state_out`) for every canonical scene |
| `data/gap_plans.json` | 59 generated narrative arcs (subplot / sequence / beat trees) |
| `data/world_state_schema.json` | Schema for characters, company, inventory, and knowledge flags |
| `data/world_state_initial.json` | Starting world state before the first scene |
| `data/scene_estimated_durations.json` | Realistic canonical durations derived from the text |

## Gap Categories

Gaps between canonical scenes are classified by exact duration:

| Type | Duration | Count | Description |
|------|----------|-------|-------------|
| `none` | ≤ 0.1 h | 36 | Contiguous or intentionally parallel scenes (no arc) |
| `micro` | ≤ 3 h | 11 | Immediate bridges: pauses, short walks, conversations |
| `small` | 3–24 h | 27 | Interludes: meals, rests, short marches |
| `travel` | 1–10 d | 17 | Multi-day journeys with daily cycles |
| `long` | > 10 d | 4 | Compressed macro-arcs (captivity, winter, siege, homecoming) |

See [`docs/GAP_GENERATOR_README.md`](docs/GAP_GENERATOR_README.md) for the full planner documentation.

## Running the Pipeline

### 1. Gap Planner

Generate or refresh gap arcs after any canonical scene change:

```bash
python3 scripts/gap_planner.py
```

### 2. Web Prototypes

Preview the timeline in a browser:

```bash
cd prototypes
python3 -m http.server 8888
# Open http://localhost:8888/timeline_canon_gaps.html
```

### 3. Flask Backend

Start the API server (used by some prototypes and the stream client):

```bash
./start_server.sh
```

## Interactive Prototypes

- **`prototypes/timeline_canon_gaps.html`** — 24-hour-day timeline of all 96 canonical scenes. Shows chapter colors, split multi-day segments, and a viewport indicator on the year overview.
- **`prototypes/stream_book.html`** — "Book Illuminated" layout with typewriter beats and chapter audio.
- **`prototypes/timeline_integrated.html`** — Unified timeline view (older data, may lag behind).

## Stream Design Decisions

- **Real-time pacing:** 1 narrative day = 1 real day. This means the ~56 days of canonical content plus ~411 days of gaps would take ~467 real days to stream. Compressed narration modes will be used for the 4 long gaps so viewers don't literally wait 5 months in Rivendell.
- **Minute-by-minute generation:** Instead of pre-generating thousands of AI-written scenes, a procedural engine will consume the gap arc trees (subplot → sequence → beat) and emit narrative events each minute.
- **World state driven:** Every gap beat is grounded in the canonical `state_in` / `state_out` snapshots, so character locations, deaths, and separations remain consistent.
- **Intentional overlaps preserved:** Two narratively parallel overlaps are kept as-is (day 13: Bilbo separated from company; day 181: Smaug flashback parallel).

## Audiobook (Kokoro TTS)

All 19 chapters were synthesized with Kokoro TTS via Modal Labs:

```bash
cd runpod-kokoro
modal deploy chatterbox_modal.py
```

See [`runpod-kokoro/CHATTERBOX_MODAL.md`](runpod-kokoro/CHATTERBOX_MODAL.md) for deployment details.

## Old Processing Scripts (Deprecated for New Runs)

These scripts were used during the initial EPUB extraction phase. They are kept for reference but are not part of the current real-time pipeline:

- `scripts/extract_all_scenes_final.py`
- `scripts/add_story_duration.py`
- `scripts/add_summaries.py`
- `scripts/gap_content_generator.py` (old LLM pre-generator)
- `scripts/narrative_generator.py`
- `scripts/narrative_beats_v2.py`

## Troubleshooting

### Missing JSON files

If `gap_planner.py` fails, ensure these exist:
- `data/canonical_scene_states.json`
- `data/stream_scenes.json`

### Timeline looks wrong

`stream_scenes.json` is the source of truth for canonical hours. The prototypes regenerate their embedded `dayEvents` from this file; if they drift, run the replacement script or refresh the prototype.

## License

This project is for educational purposes. The Hobbit text is copyright of the Tolkien Estate.
