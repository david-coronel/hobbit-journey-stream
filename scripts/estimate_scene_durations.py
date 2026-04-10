#!/usr/bin/env python3
"""
Estimate canonical scene durations in story-time based on textual analysis,
narrative mode detection (continuous vs summary), and explicit anchors.

Outputs data/scene_estimated_durations.json
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_json(name):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name, data):
    with open(DATA_DIR / name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Narrative mode detection ──────────────────────────────────────────────

SUMMARY_MARKERS = [
    "days passed", "weeks passed", "months passed", "years passed",
    "day after day", "night after night", "day by day",
    "meanwhile", "at length", "before long",
    "after some time", "after a while", "eventually", "gradually",
    "by this time", "at the end of", "during the next", "for many days",
    "for several days", "the time went on", "as time passed",
    "summer passed", "autumn passed", "winter passed", "spring came",
    "on they went", "on and on", "far behind", "far ahead",
    "soon after", "not long after",
]

# Removed "for a long time" from summary markers — it's usually just a conversation length


def detect_narrative_mode(content: str) -> str:
    """Classify scene as continuous, summary, or mixed."""
    text = content.lower()
    summary_hits = sum(1 for m in SUMMARY_MARKERS if m in text)
    # Direct speech as proxy for continuous scenes
    speech_pairs = text.count('"') // 2
    # Also count action verbs
    action_words = ["said", "cried", "shouted", "whispered", "laughed",
                    "looked", "turned", "ran", "walked", "sat", "stood",
                    "drew", "struck", "fell", "rose"]
    action_hits = sum(len(re.findall(rf"\b{w}\b", text)) for w in action_words)
    direct_score = speech_pairs + (action_hits // 4)

    if summary_hits > direct_score:
        return "summary"
    if summary_hits > 0:
        return "mixed"
    return "continuous"


# ── Heuristic temporal patterns ───────────────────────────────────────────

# Strong clues for CONTINUOUS or MIXED scenes
CONTINUOUS_TIME_PATTERNS = {
    r"\bthree days\b|\b3 days\b": 72,
    r"\bfour days\b|\b4 days\b": 96,
    r"\bfive days\b|\b5 days\b": 120,
    r"\bsix days\b|\b6 days\b": 144,
    r"\bseven days\b|\b7 days\b|a week\b": 168,
    r"\bfortnight\b": 336,
    r"\bmany days\b": 72,
    r"\bseveral days\b": 60,
    r"\bfor days\b": 48,
    r"\bfor weeks\b": 336,
    r"\bfor months\b": 1440,
    r"\ball day\b|\ball that day\b": 12,
    r"\ball morning\b": 4,
    r"\ball afternoon\b": 4,
    r"\ball evening\b": 4,
    r"\ball night\b": 8,
    r"\bthe whole day\b": 12,
    r"\bfrom morning till night\b": 14,
    r"\bfrom dawn till dusk\b": 14,
    r"\bdawn to dusk\b": 14,
    r"\bhours passed\b|\bhours went by\b": 4,
}

# Weak clues that usually mean shorter durations within a scene
WEAK_TIME_PATTERNS = {
    r"\bmidday\b|\bnoon\b": 1,
    r"\bmidnight\b": 1,
    r"\bsunset\b|\bsunrise\b": 1,
    r"\bfor a long time\b": 2,  # long conversation, not days
}

EVENT_DURATIONS = {
    "feast": 3, "banquet": 3, "supper": 1.5, "dinner": 2,
    "breakfast": 1, "luncheon": 1, "tea": 1,
    "song": 0.5, "songs": 1, "speech": 0.5,
    "conversation": 1, "discussion": 1.5, "argument": 0.75,
    "quarrel": 0.5, "fight": 0.5, "battle": 2,
    "march": 8, "journey": 8, "walk": 3, "ride": 4,
    "climb": 4, "escape": 2, "rescue": 1,
    "council": 2, "meeting": 1.5, "planning": 2,
    "preparation": 3, "auction": 3, "sale": 2,
}

TIME_OF_DAY = {
    "dawn": 5, "early morning": 7, "morning": 8, "late morning": 10,
    "noon": 12, "midday": 12, "afternoon": 14, "late afternoon": 16,
    "evening": 18, "dusk": 19, "night": 21, "late night": 23,
    "midnight": 0,
}


def extract_continuous_hours(content: str) -> float | None:
    """Look for explicit duration clues in continuous/mixed text."""
    text = content.lower()
    best = None
    for pattern, hours in CONTINUOUS_TIME_PATTERNS.items():
        if re.search(pattern, text):
            if best is None or hours > best:
                best = hours
    if best is not None:
        return best
    for pattern, hours in WEAK_TIME_PATTERNS.items():
        if re.search(pattern, text):
            if best is None or hours > best:
                best = hours
    return best


def event_based_estimate(content: str) -> float | None:
    text = content.lower()
    scores = []
    for event, hours in EVENT_DURATIONS.items():
        count = len(re.findall(rf"\b{event}\b", text))
        if count:
            scores.extend([hours] * count)
    if not scores:
        return None
    return sum(sorted(scores, reverse=True)[:3]) / min(3, len(scores))


def infer_time_span(content: str, time_label: str) -> float | None:
    text = content.lower()
    found = []
    for name, hour in sorted(TIME_OF_DAY.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{name}\b", text):
            found.append(hour)
    if len(found) >= 2:
        span = max(found) - min(found)
        if span > 0:
            return max(span, 1.0)
    # If only one time mentioned and it's the scene label, give a small default
    if time_label:
        hour = TIME_OF_DAY.get(time_label.lower(), 12)
        if hour <= 8:
            return 1.5
        elif hour >= 18:
            return 2.5
        else:
            return 2.0
    return None


def estimate_scene(scene, beat_data) -> dict:
    content = scene.get("content", "")
    word_count = scene.get("word_count", len(content.split()))
    time_label = scene.get("time", "")
    explicit = scene.get("story_duration", {})
    beat_list = beat_data.get("beats", []) if beat_data else []
    beat_count = len(beat_list)
    mode = detect_narrative_mode(content)

    # Anchor from explicit data
    anchor_hours = None
    if explicit.get("method") == "explicit":
        val = explicit.get("duration", 2)
        unit = explicit.get("unit", "hours")
        mult = {"minutes": 1/60, "hours": 1, "days": 24, "weeks": 168}.get(unit, 1)
        anchor_hours = val * mult

    # Textual clues
    textual = extract_continuous_hours(content)
    event_est = event_based_estimate(content)
    span_est = infer_time_span(content, time_label)

    # Beat-based
    beat_hours = None
    if beat_count > 0:
        beat_hours = 0.5 + (beat_count * 0.35)
        words_per_beat = word_count / beat_count
        if words_per_beat > 400:
            beat_hours *= 0.8
        if words_per_beat < 100:
            beat_hours *= 1.2

    # Word-count base
    word_hours = None
    if word_count < 300:
        word_hours = 0.5
    elif word_count < 800:
        word_hours = 1.5
    elif word_count < 1500:
        word_hours = 2.5
    else:
        word_hours = 3.5

    reasoning_parts = []
    final = None
    confidence = "low"

    # ── Mode-aware combination ──
    if mode == "summary":
        # Summary scenes compress time. The duration is narrative compression,
        # not the full described span. Use word-count as primary proxy.
        # But if there's a strong explicit anchor, trust it.
        if anchor_hours is not None:
            final = anchor_hours
            confidence = "high"
            reasoning_parts.append(f"explicit anchor ({anchor_hours:.1f}h)")
        else:
            # Summary compression formula: ~2h per 100 words of summary text
            compressed = max(1.0, (word_count / 100) * 1.5)
            if textual is not None and textual > 24:
                # Multi-day summary: cap at a fraction of described time
                compressed = min(compressed, textual * 0.15)
            if event_est is not None:
                compressed = max(compressed, event_est * 0.5)
            final = compressed
            confidence = "medium"
            reasoning_parts.append(f"summary compression ({compressed:.1f}h, described={textual}h)")

    elif mode == "mixed":
        # Mixed scenes have some continuous action and some summary
        if anchor_hours is not None:
            base = anchor_hours
            reasoning_parts.append(f"explicit anchor ({anchor_hours:.1f}h)")
        elif textual is not None and textual <= 24:
            base = textual
            reasoning_parts.append(f"textual clue ({textual:.1f}h)")
        elif span_est is not None:
            base = span_est
            reasoning_parts.append(f"time span ({span_est:.1f}h)")
        else:
            candidates = [c for c in [beat_hours, event_est, word_hours] if c is not None]
            if candidates:
                base = sum(candidates) / len(candidates)
                reasoning_parts.append(f"blended heuristic")
            else:
                base = 2.0
                reasoning_parts.append("fallback")

        # If there's multi-day summary language inside, add a small compression bump
        if textual is not None and textual > 24:
            base = max(base, 4.0)  # mixed scene with weeks inside still takes some narrative time
            reasoning_parts.append(f"mixed-summary bump")
        final = base
        confidence = "medium" if textual or span_est or anchor_hours else "low"

    else:  # continuous
        if anchor_hours is not None:
            final = anchor_hours
            confidence = "high"
            reasoning_parts.append(f"explicit anchor ({anchor_hours:.1f}h)")
        elif textual is not None:
            final = textual
            confidence = "high"
            reasoning_parts.append(f"textual clue ({textual:.1f}h)")
        elif span_est is not None:
            final = span_est
            confidence = "medium"
            reasoning_parts.append(f"time span ({span_est:.1f}h)")
        else:
            candidates = [c for c in [beat_hours, event_est, word_hours] if c is not None]
            if candidates:
                # Weight beats and events higher for continuous scenes
                weights = []
                values = []
                if beat_hours is not None:
                    values.append(beat_hours); weights.append(2.0)
                if event_est is not None:
                    values.append(event_est); weights.append(1.5)
                if word_hours is not None:
                    values.append(word_hours); weights.append(1.0)
                final = sum(v * w for v, w in zip(values, weights)) / sum(weights)
                confidence = "medium"
                reasoning_parts.append(f"blended heuristic (beats={beat_hours:.1f}, event={event_est}, words={word_hours})")
            else:
                final = 2.0
                reasoning_parts.append("fallback default (2h)")

    # Sanity clamps
    if word_count < 300:
        final = min(final, 6.0)
    if word_count > 2000 and mode != "summary":
        final = max(final, 2.5)

    reasoning = "; ".join(reasoning_parts)

    return {
        "scene_id": scene["id"],
        "title": scene["title"],
        "chapter": scene.get("chapter", ""),
        "estimated_duration_hours": round(final, 2),
        "narrative_mode": mode,
        "confidence": confidence,
        "reasoning": reasoning,
        "explicit_anchor_hours": round(anchor_hours, 2) if anchor_hours else None,
        "textual_clue_hours": round(textual, 2) if textual else None,
        "span_estimate_hours": round(span_est, 2) if span_est else None,
        "beat_based_hours": round(beat_hours, 2) if beat_hours else None,
        "event_based_hours": round(event_est, 2) if event_est else None,
        "word_count": word_count,
        "beat_count": beat_count,
    }


def main():
    stream_data = load_json("stream_scenes.json")
    canonical_scenes = stream_data.get("scenes", [])

    beats_data = load_json("scene_beats.json")
    beats_by_id = beats_data.get("scenes", {})

    results = []
    for scene in canonical_scenes:
        bid = scene["id"]
        beat = beats_by_id.get(bid, beats_by_id.get(bid.replace("canon_", ""), None))
        est = estimate_scene(scene, beat)
        results.append(est)

    save_json("scene_estimated_durations.json", results)

    total_est = sum(r["estimated_duration_hours"] for r in results)
    total_anchor = sum(r["estimated_duration_hours"] for r in results if r["confidence"] == "high")
    high = sum(1 for r in results if r["confidence"] == "high")
    med = sum(1 for r in results if r["confidence"] == "medium")
    low = sum(1 for r in results if r["confidence"] == "low")
    modes = {}
    for r in results:
        modes[r["narrative_mode"]] = modes.get(r["narrative_mode"], 0) + 1

    print(f"Estimated {len(results)} canonical scenes")
    print(f"Total estimated story-time: {total_est:.1f} hours = {total_est/24:.1f} days")
    print(f"High-confidence ({high} scenes): {total_anchor:.1f}h")
    print(f"Medium-confidence: {med} scenes")
    print(f"Low-confidence: {low} scenes")
    print(f"Narrative modes: {modes}")
    print(f"Saved to data/scene_estimated_durations.json")


if __name__ == "__main__":
    main()
