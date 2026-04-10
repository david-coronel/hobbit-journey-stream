# First Pass Roadmap — Hobbit Journey Stream

> Status: generation pipeline is functional, 10-day batches are clean, server and data need hardening before full-scale generation.

---

## 1. Complete Generation Coverage (Critical)

**Current state**
- 1,413 events generated across 51 gaps.
- Only the **first 10 days** of each gap are done.
- Long gaps still have most of their content missing:
  - `gap_canon_044_canon_045`: 129 total days
  - `gap_canon_093_canon_094`: 161 total days
  - `gap_canon_094_canon_095`: 53 total days

**TODO**
- [ ] Remove or raise the `days=10` limit in `scripts/batch_first_20_gemini.py`.
- [ ] Add **resumable generation**: skip gaps already marked `completed` in `generation_batches`.
- [ ] Add **exponential backoff retries** in `EventGenerator._call_llm` (OpenRouter occasionally times out).
- [ ] Add **daily SQLite backup** (`cp generated_events.db …`) before starting a batch.
- [ ] Run the full batch. Estimated final event count: 8,000–10,000.

---

## 2. Fix Canonical Scene Data (Critical)

**Current state**
- 21 pairs of canonical scenes overlap temporally (see list below).
- The gap planner builds forbidden intervals from these timings, so overlaps create fuzzy boundaries and can push generated events into the wrong gaps.
- `stream_scenes.json` and `canonical_scene_states.json` are manually kept in sync; they have already drifted once.

**TODO**
- [ ] Decide for each overlap whether it is **intentional** (flashback / parallel action) or a data error.
- [ ] If erroneous, adjust `start_hour` / `duration_hours` in `stream_scenes.json` so scenes do not touch.
- [ ] Regenerate `canonical_scene_states.json` and `gap_plans.json` from the corrected `stream_scenes.json`.
- [ ] Make `stream_scenes.json` the **single source of truth**; derive `canonical_scene_states.json` automatically.
- [ ] Add a validation script (`scripts/validate_canonical_data.py`) that fails on divergence.

### Known canonical overlaps
| Pair | Overlap |
|---|---|
| `canon_005` ↔ `canon_006` | 1.00h |
| `canon_006` ↔ `canon_007` | 1.00h |
| `canon_008` ↔ `canon_010` | 2.00h |
| `canon_013` ↔ `canon_014` | 2.50h |
| `canon_024` ↔ `canon_027` | 1.00h |
| `canon_024` ↔ `canon_028` | 1.50h |
| `canon_025` ↔ `canon_028` | 1.50h |
| `canon_026` ↔ `canon_028` | 1.00h |
| `canon_025` ↔ `canon_026` | 1.50h |
| `canon_039` ↔ `canon_040` | **8.00h** (largest) |
| `canon_046` ↔ `canon_047` | 2.00h |
| `canon_046` ↔ `canon_048` | 2.50h |
| `canon_046` ↔ `canon_049` | 3.81h |
| `canon_051` ↔ `canon_052` | 3.57h |
| `canon_056` ↔ `canon_057` | 2.50h |
| `canon_058` ↔ `canon_059` | 2.00h |
| `canon_067` ↔ `canon_069` | 2.00h |
| `canon_068` ↔ `canon_070` | 2.50h |
| `canon_084` ↔ `canon_085` | 3.00h |
| `canon_084` ↔ `canon_086` | 2.50h |
| `canon_085` ↔ `canon_086` | 1.00h |

---

## 3. Harden Infrastructure (High)

**Current state**
- The Flask background task dies after 24 h and must be restarted manually.
- SQLite DB was accidentally deleted twice during debugging.
- No health monitoring.

**TODO**
- [ ] Replace the background-task Flask launch with a **systemd service** or a `while true` auto-restart loop.
- [ ] Enable **SQLite WAL mode** so the DB can be backed up while hot.
- [ ] Add a simple `/health` endpoint that returns DB size, last batch timestamp, and event count.
- [ ] (Optional) Add a small dashboard or CLI script that prints generation progress (% complete, tokens spent, ETA).

---

## 4. Timeline UX & Performance (High)

**Current state**
- Overlapping canonical scenes are marked with a red outline.
- Clicking overlapping bars directly is still hard because one bar covers the other.
- The scene selector dropdown works, but it is a workaround.

**TODO**
- [ ] Improve click handling on overlaps: either **stacked sub-tracks** inside a day row, or a **context menu** when clicking an overlap zone.
- [ ] Performance test the timeline with the full ~10 k event load.
- [ ] If scroll lags, implement **row virtualization** (render only visible days).

---

## 5. Quality Review & Delivery (Medium)

**TODO**
- [ ] Read a **random sample** of ~50 generated events to spot repetitive patterns, empty dialogue, or timeline contradictions.
- [ ] Tune prompts in `prompt_engine.py` if quality issues are found.
- [ ] Build `scripts/export_stream.py` that emits a clean chronological JSON or `.vtt` subtitle file for external playback.

---

## Quick Commands for Next Session

```bash
# Restart server
./start_server.sh

# Regenerate gap plans after fixing canonical data
python3 scripts/gap_planner.py

# Dry-run a single gap
python3 -c "from scripts.event_generator import EventGenerator; \
  EventGenerator().generate_gap('gap_canon_044_canon_045', days=3, dry_run=True)"

# Check DB stats
python3 -c "import sqlite3; c=sqlite3.connect('data/generated_events.db'); \
  print(c.execute('SELECT COUNT(*) FROM events').fetchone()[0], 'events')"
```
