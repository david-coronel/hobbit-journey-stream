# Gap Planner

Generates narrative arc trees for the gaps between canonical Hobbit scenes. The output is a structured timeline that interleaves 96 canonical scenes with 59 generated gaps, ready for a real-time procedural stream engine.

## Overview

The planner uses `data/canonical_scene_states.json` (96 state snapshots) and `data/stream_scenes.json` (96 canonical scenes with corrected hours) to compute the exact time between consecutive canonical scenes.

If two scenes are contiguous or overlapping, no gap is generated (`arc: null`). Otherwise, the gap receives a nested narrative tree of **subplots → sequences → beats**.

## Gap Categories

Gaps are classified by their real duration in hours:

| Type | Duration | Count | Description |
|------|----------|-------|-------------|
| `none` | ≤ 0.1 h | 36 | Scenes are contiguous or intentionally parallel. No gap generated. |
| `micro` | ≤ 3 h | 11 | Immediate bridges: a pause, a short walk, a conversation. |
| `small` | 3–24 h | 27 | Interludes: meals, rests, short marches, overnight waits. |
| `travel` | 1–10 d | 17 | Multi-day journeys with departure, daily road cycles, and approach. |
| `long` | > 10 d | 4 | Compressed macro-arcs for the major narrative pauses. |

**Total gap narrative time:** ~9,868 hours (~411 days).

### Canonical Coverage

- **Scene time:** ~56.9 days of canonical content
- **Gap time:** ~411 days of generated narrative
- **Stream pacing:** 1 Middle-earth day = 1 real day (with 1-minute updates)

## Node Hierarchy

Every generated gap (`arc`) is a tree with three node types:

- **`subplot`** — Thematic container (e.g., "Travel: X → Y", "The Long Captivity"). Holds sequences and beats.
- **`sequence`** — Temporal container (e.g., "Departure", "Day 3 of Travel", "Approach"). Holds beats.
- **`beat`** — Atomic narrative unit (e.g., "Morning march", "Making camp", "Night watches"). Has a fixed `duration_hours`.

The procedural engine will walk these leaves beat-by-beat, generating minute-by-minute content.

## Special Long Gaps

The 4 `long` gaps have hand-crafted templates because they span weeks or months:

1. **`gap_canon_044_canon_045`** — 128 days: Elvenking's dungeons  
   *Into the Dungeons → Weeks of Imprisonment (compressed) → The Plan Matures*

2. **`gap_canon_064_canon_065`** — 16 days: Smaug departs, Lake-town burns  
   *Smaug Departs → Days of Tense Waiting (compressed) → The Attack Begins*

3. **`gap_canon_093_canon_094`** — 159 days: Winter in Rivendell  
   *Last Stretch → Rivendell Winter Rest (compressed) → Farewell to the Elves*

4. **`gap_canon_094_canon_095`** — 52 days: Final journey to the Shire  
   *Rivendell to Shire Borders → Homecoming Eve*

The "compressed" beats inside long gaps will be narrated with time-dilation (e.g., one beat summarizing a full week), while the surrounding sequences can still play in real-time.

## Running the Planner

```bash
python3 scripts/gap_planner.py
```

### Output

- `data/gap_plans.json` — 95 gap entries with metadata and arc trees.

```json
{
  "meta": {
    "total_gaps": 95,
    "none_gaps": 36,
    "micro_gaps": 11,
    "small_gaps": 27,
    "travel_gaps": 17,
    "long_gaps": 4,
    "estimated_total_hours": 9867.7
  },
  "gaps": [
    {
      "gap_id": "gap_canon_001_canon_002",
      "from_scene_id": "canon_001",
      "to_scene_id": "canon_002",
      "duration_hours": 0,
      "gap_type": "none",
      "arc": null,
      "state_in_snapshot": { ... },
      "state_out_snapshot": { ... }
    },
    ...
  ]
}
```

## Key Input Files

| File | Purpose |
|------|---------|
| `data/canonical_scene_states.json` | 96 `state_in` / `state_out` snapshots per canonical scene |
| `data/stream_scenes.json` | Canonical scenes with corrected `start_hour`, `end_hour`, `duration_hours` |

## From Gaps to Stream Timeline

The next step is building a unified timeline that flattens canonical scenes + gap arcs into a single ordered list of 155 events with absolute start times. This will feed the minute-by-minute procedural generator.

## Differences from the Old Generator

- **No LLM pre-generation:** We no longer generate 74 AI-written scenes upfront. Content is produced procedurally at stream time.
- **No `generated_gap_scenes.json`:** The source of truth is now `gap_plans.json` (structure), not pre-written prose.
- **Exact hours:** Gap duration is calculated from `(next_day - prev_day - 1) * 24 + (24 - prev_end) + next_start`, not rounded to whole days.
- **Intentional overlaps preserved:** Parallel scenes (e.g., day 13 Bilbo vs. company, day 181 flashbacks) result in `gap_type: none`.
