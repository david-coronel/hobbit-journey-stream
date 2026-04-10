# The Hobbit Journey Stream - Feature Backlog

## Completed ✅

- [x] Extract text from EPUB
- [x] Assign realistic in-story dates (Third Age 2941–2942)
- [x] Narrative analysis - classify paragraphs as scene/summary/transitional
- [x] Build 96 canonical scenes with corrected durations and start/end hours
- [x] Create world state schema and 96 `state_in`/`state_out` snapshots
- [x] Gap planner with 5 categories: `none`, `micro`, `small`, `travel`, `long`
- [x] Timeline visualizations (24h day grid, year overview, chapter colors)
- [x] Audiobook generation for all 19 chapters (Kokoro TTS)
- [x] Interactive web prototypes (`timeline_canon_gaps.html`, `stream_book.html`)

---

## In Progress 🚧

### Procedural Stream Engine
**Priority:** High | **Effort:** High

Build the minute-by-minute generator that walks the unified timeline (96 scenes + 59 gaps) and emits narrative events in real time.

**Key decisions:**
- 1 Middle-earth day = 1 real day
- 1-minute updates
- Normal beats play in real-time; compressed beats use time-dilation
- Ground every beat in the world state snapshots

---

## Proposed Features

### 1. Dialogue Extraction & Analysis
**Priority:** Medium | **Effort:** Medium

Extract and map all dialogue scenes with speaker attribution, dialogue density tracking, and conversation networks.

**Use cases:** Track Bilbo finding his voice, map Smaug's conversations, see character dominance by chapter.

---

### 2. Character Presence Tracking
**Priority:** High | **Effort:** Low (schema exists)

The world state already tracks `location`, `status`, and `is_with_company` for 25 characters. Next step: visualize Gandalf's absences, Bilbo's growing independence, and ensemble vs solo moments in the stream UI.

---

### 3. Location/Geography Visualization
**Priority:** Medium | **Effort:** High

Map the physical journey with GPS-like coordinates for Middle-earth locations. Show distance traveled, elevation profiles, and time spent at each location.

---

### 4. Emotional Arc Analysis
**Priority:** Medium | **Effort:** High

Sentiment analysis tracking tension, comedy, wonder, fear. Visualize the story's emotional rollercoaster and climax build-ups.

---

### 5. Narrative Pace Analysis
**Priority:** Low | **Effort:** Low

Words per in-story day by chapter. Compare Chapter I (15,000 words/day) vs Chapter II (242 words/day).

---

### 6. Theme Tracking
**Priority:** Low | **Effort:** Medium

Track recurring themes: home/longing, adventure/courage, greed/treasure, hunger/food, darkness vs light.

---

### 7. Interactive Timeline Explorer
**Priority:** Medium | **Effort:** Medium

Web interface to:
- Filter by character, location, narrative type
- Search text across the timeline
- Jump to specific dates/chapters
- Compare different views side-by-side

---

### 8. Event Extraction
**Priority:** Medium | **Effort:** Medium

Automatically identify and catalog events:
- Major plot points (finding the Ring, death of Smaug, Battle of Five Armies)
- Minor events (meals, camps, weather)
- Decisions made
- Discoveries/revelations

---

### 9. Comparison with Lord of the Rings
**Priority:** Low | **Effort:** High

If LotR data is processed:
- Compare narrative density (The Hobbit is much sparser)
- Compare timeline pacing
- Character crossover analysis (Gandalf, Elrond, etc.)
- Style evolution between books

---

### 10. Audio/Audiobook Correlation
**Priority:** Low | **Effort:** High

Map narrative structure to audio runtime:
- Which chapters are longest in audio?
- Does scene density correlate with audio pace?
- Pause detection vs narrative gaps

---

## Generative Engine Enhancements

### 11. Emotional Arc Integration for Beat Generation
**Priority:** Medium | **Effort:** Medium

Enhance the procedural engine with emotional context:
- Track tension building toward major events (Smaug's lair, spider attacks)
- Generate beats with appropriate emotional tone (ominous before danger, relief after)
- Match character moods to upcoming narrative beats
- Create "calm before the storm" and "decompressing after" beat templates

---

### 12. Character Relationship Evolution Tracking
**Priority:** Medium | **Effort:** Medium

Track how relationships change throughout the journey:
- Bilbo-Thorin arc: skepticism → respect → conflict → reconciliation
- Gandalf's presence/absence affecting group dynamics
- Fili-Kili brotherhood moments
- Dwarves gradually accepting Bilbo
- Generate beats that reflect current relationship state

---

### 13. Weather & Season Integration
**Priority:** Low | **Effort:** Low

Integrate realistic weather and seasonal progression:
- April departure from Shire (spring)
- Summer travel through Wilderland
- Autumn in Mirkwood
- Winter at Erebor
- Generate weather-appropriate beat descriptions
- Track seasonal food availability, clothing, travel conditions

---

### 14. Expanded Beat Type Variety
**Priority:** Medium | **Effort:** Medium

Add more beat types beyond march/observation/activity:
- **Meal beats**: Cooking, sharing food, hunger complaints
- **Conflict beats**: Arguments about direction, leadership tensions
- **Discovery beats**: Finding landmarks, signs of previous travelers
- **Rest beats**: Sleep, dreams, nightmares
- **Travel montages**: Multi-day journey summaries
- **Teaching moments**: Gandalf explaining, dwarves sharing skills
- **Humor beats**: Jokes, pranks, lightening the mood

---

## Technical Debt / Improvements

- [ ] Sentence-level classification (currently paragraph-level)
- [ ] Confidence scoring for narrative type classification
- [ ] Improved pronoun resolution (disambiguate "he" references)

---

## Data Export Formats

Future exports could include:
- CSV for spreadsheet analysis
- GEXF for network visualization (Gephi)
- KML for map visualization
- ICS (calendar) for timeline import
- Markdown for readable chapter summaries
