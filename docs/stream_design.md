# Hobbit Journey Stream - Visual Design

## Overall Layout Concept

```
┌─────────────────────────────────────────────────────────────────┐
│  [SCENE IMAGE/ART]                              ┌─────────────┐ │
│  (AI-generated or curated artwork               │             │ │
│   depicting current scene)                      │    MAP      │ │
│                                                 │   (mini)    │ │
│  ┌─────────────────────────────────────┐       │   Shire ──► │ │
│  │  "The dwarves grumbled about      │       │   Rivendell │ │
│  │   the steep climb ahead..."       │       │   Mirkwood  │ │
│  │                                    │       │      ▼      │ │
│  │  Scrolling narrative text          │       │   Erebor    │ │
│  │  (like a typewriter/scroll effect) │       │             │ │
│  └─────────────────────────────────────┘       └─────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  📅 APRIL 28, YEAR 2941  │  ☀️ LATE AFTERNOON  │  ⏱️ 3 DAYS TO  │
│  (In-Story Date)          │  (Time of Day)      │  TROLLSHAWS   │
│                           │                      │  (Countdown)  │
├─────────────────────────────────────────────────────────────────┤
│  📍 CURRENT: The Misty Mountains foothills                      │
│  🎯 NEXT: The Trolls' Clearing (canonical event)                │
│  👥 PRESENT: Thorin, Gandalf, Bilbo, Fili, Kili (5/13 dwarves) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Element Specifications

### 1. Scene Image (Top-Left, ~60% width)
**Purpose:** Visual anchor showing the current environment/action

**Options:**
- AI-generated art via API (DALL-E, Midjourney, Stable Diffusion)
- Curated static image bank (pre-selected artworks)
- Animated/looping video background (wind, rain, fire effects)
- Gradient/atmospheric backdrop with overlay elements

**Display modes:**
- Full scene illustration
- Atmospheric gradient (color reflects location: green=Shire, dark=Mirkwood)
- Comic-style panel layout for action sequences

---

### 2. Text Display (Overlaid or below image)
**Purpose:** The narrative content - the "story"

**Layout options:**

**A. Typewriter Scroll (Classic)**
```
┌──────────────────────────────────┐
│ > The path wound steeply upward  │
│ > through broken ground. Bilbo   │
│ > found himself breathing hard,  │
│ > wondering how many more hills  │
│ > lay ahead...                   │
│                                  │
│ [█▀▀▀▀▀▀▀▀▀░░░░░] 68% complete   │
└──────────────────────────────────┘
```

**B. Scroll/Parchment Style**
- Background: Aged paper texture
- Font: Serif (Cinzel, Cormorant Garamond) or hand-lettered style
- Text appears line-by-line with fade-in

**C. Subtitle Bar (Minimal)**
- Bottom third overlay
- Current sentence only
- Fades between updates

---

### 3. Map (Top-Right, ~25% width)
**Purpose:** Geographic context - "Where are they now?"

**Features:**
- Static map of Middle-earth with current position marker
- Journey path drawn so far (faded line)
- Remaining path (dashed line)
- Zoomed section for detailed areas

**Display modes:**
- Mini map (always visible)
- Expandable full map (on hover/click)
- Animated dot moving along path

```
    ┌─────────────────┐
    │    ~MAP~        │
    │                 │
    │   The Shire   ●─┼── Start
    │      │        │ │
    │ Rivendell ○   │ │
    │      │        │ │
    │    ○──●───────┼─┘  ◄── YOU ARE HERE
    │   Mtn Pass    │
    │      │        │
    │   Mirkwood    │
    │      │        │
    │    Erebor   ○ │
    └─────────────────┘
```

---

### 4. Date/Time HUD (Bottom bar)
**Purpose:** Temporal grounding

**Elements:**
- **In-story date**: "April 28, 2941" (Shire Reckoning)
- **Day of journey**: "Day 12 of the Quest"
- **Time of day**: "Late Afternoon" with icon (☀️/🌅/🌙/⭐)
- **Season indicator**: Small leaf/snow/sun icon
- **Weather**: Current conditions (☀️ Clear, 🌧️ Rain, ❄️ Snow, 🌫️ Mist)

---

### 5. Countdown to Next Event (Bottom bar)
**Purpose:** Create anticipation, show narrative pacing

**Display:**
```
⏱️ 3 DAYS 4 HOURS until: The Trolls (canonical chapter)
━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━  [progress bar]
```

Or for near events:
```
⚡ NEXT EVENT: The Trolls' Clearing
   In: 2 hours │ Distance: 5 miles
```

---

## 🎨 Additional Suggested Elements

### 6. Party Roster Sidebar
Shows who's present in current scene:
```
┌─────────────┐
│ COMPANY     │
│ ─────────── │
│ ⚔️ Thorin   │
│ 🧙 Gandalf  │
│ 🎒 Bilbo    │
│ ⛏️ Fili     │
│ ⛏️ Kili     │
│ ...         │
│             │
│ 💀 8 others │
│   (scouting)│
└─────────────┘
```

**States:**
- Present (full color)
- Away (greyed)
- Injured/sick (amber tint)

---

### 7. Mood/Atmosphere Indicator
Visual representation of scene tone:
```
MOOD: ████░░░░░░ Tense
ATMOSPHERE: Ominous fog rolling in
MUSIC: Low strings, occasional harp
```

Or simple icon:
- 😌 Peaceful
- 😰 Tense  
- 😱 Danger
- 😊 Hopeful
- 😢 Melancholy

---

### 8. Inventory/Quest Items
For significant objects mentioned:
```
┌─────────────┐
│ NOTABLE     │
│ ─────────── │
│ 🗡️ Orcrist  │
│ 🗡️ Glamdring│
│ 🔪 Sting     │
│ 🗝️ Map Key   │
└─────────────┘
```

---

### 9. Recent Events Timeline
Mini history of last few scenes:
```
RECENT ──► NOW
[Camp]─[Breakfast]─[March]─[Rest]─[CURRENT]
```

---

### 10. Chat Integration (if streaming platform)
```
┌────────────────────────────────────────┐
│ Chat:                                  │
│ @user: "Thorin is so grumpy lol"       │
│ @user2: "When do they meet the elves?" │
│ @user3: "Bilbo MVP"                    │
└────────────────────────────────────────┘
```

Or themed:
```
Messages from the Shire:
- FrodoBagginz: "Uncle Bilbo tell us more!"
```

---

### 11. Dynamic Background Audio Info
```
🔊 Now Playing: "The Misty Mountains Cold"
   Ambient: Wind through pines, distant birds
```

---

### 12. Journey Statistics
Running totals for the quest:
```
┌─────────────────┐
│ JOURNEY STATS   │
│ ─────────────── │
│ Distance: 147mi │
│ Days: 12        │
│ Meals: 34       │
│ Songs: 3        │
│ Dangers: 0      │
└─────────────────┘
```

---

## 🎬 Animation Ideas

| Transition | Effect |
|------------|--------|
| Scene change | Page turn / scroll unroll |
| Day/Night | Gradual color shift |
| Location move | Map dot animates |
| Danger approaching | Red pulse on border |
| Discovery | Golden highlight flash |
| Rest | Fade to dark, stars appear |

---

## 📐 Layout Alternatives

### Compact Mode (Chat-Friendly)
```
┌─────────────────┬──────────┐
│ SCENE IMAGE     │ MAP      │
│                 │          │
├─────────────────┴──────────┤
│ TEXT (one line, subtitle)  │
├────────────────────────────┤
│ Date │ Time │ Countdown   │
└────────────────────────────┘
```

### Immersive Mode (Cinematic)
```
┌────────────────────────────┐
│                            │
│    FULL SCREEN IMAGE       │
│                            │
│    ┌─────────────────┐     │
│    │ TEXT OVERLAY    │     │
│    └─────────────────┘     │
│                            │
│  [minimal HUD corners]     │
└────────────────────────────┘
```

### Dashboard Mode (Information-Rich)
```
┌────────┬────────────┬────────┐
│ ROSTER │   IMAGE    │  MAP   │
│        │            │        │
│        ├────────────┤        │
│        │    TEXT    │        │
├────────┴────────────┴────────┤
│ DATE │ TIME │ MOOD │ COUNTDOWN│
├────────┴────────────┴────────┤
│ CHAT / RECENT EVENTS         │
└──────────────────────────────┘
```

---

## 🛠️ Technical Implementation Notes

### Image Sources
1. **AI Generation**: DALL-E 3, Midjourney, Stable Diffusion API
2. **Pre-made Bank**: Curate 50-100 thematic images
3. **Procedural**: Shader backgrounds based on location type

### Fonts Suggestions
- Headers: **Cinzel**, **MedievalSharp**, **Metamorphous**
- Body: **Cormorant Garamond**, **EB Garamond**
- UI: **Inter**, **Cascadia Code** (for technical elements)

### Color Palette by Region
| Region | Primary | Secondary | Accent |
|--------|---------|-----------|--------|
| The Shire | `#5D8C3A` | `#F4E4BC` | `#8B4513` |
| Wilderland | `#8B7355` | `#4682B4` | `#CD853F` |
| Mirkwood | `#2F4F2F` | `#4A4A4A` | `#8B0000` |
| Lake-town | `#4682B4` | `#708090` | `#DAA520` |
| Erebor | `#4A4A4A` | `#B8860B` | `#FF4500` |

---

## Next Steps

1. **Choose primary layout** (cinematic vs dashboard)
2. **Decide on image strategy** (AI vs curated)
3. **Prototype with sample scenes** from generated_scenes.json
4. **Set up streaming framework** (OBS Studio, browser source)
5. **Implement data binding** to timeline/scene data
