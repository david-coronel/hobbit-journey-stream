#!/usr/bin/env python3
"""
Prompt Engine for The Hobbit Journey Stream.

Composes structured prompts for LLM generation from gap plans,
world state, and day-pattern block schedules.
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        # Support both data/.env and root .env
        for env_path in (
            os.path.join(PROJECT_ROOT, "data", ".env"),
            os.path.join(PROJECT_ROOT, ".env"),
        ):
            if os.path.exists(env_path):
                load_dotenv(env_path)
                break
    except ImportError:
        pass


def _resolve_env_vars(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], value)
    return value


_load_dotenv()


def load_openrouter_config(path: str = "config/openrouter.yaml") -> Dict[str, Any]:
    full_path = os.path.join(PROJECT_ROOT, path)
    with open(full_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["api_key"] = _resolve_env_vars(cfg.get("api_key", ""))
    return cfg


def load_json_data(filename: str) -> Any:
    path = os.path.join(PROJECT_ROOT, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class WorldStateResolver:
    """Resolves world state for a given gap and temporal offset."""

    def __init__(self):
        self.scene_states = {s["scene_id"]: s for s in load_json_data("canonical_scene_states.json")}
        # Override timeline fields with stream_scenes.json values
        stream_scenes = load_json_data("stream_scenes.json").get("scenes", [])
        for s in stream_scenes:
            sid = s.get("id")
            if sid and sid in self.scene_states:
                state = self.scene_states[sid]
                state["journey_day"] = s.get("journey_day", state.get("journey_day", 0))
                state["start_hour"] = s.get("start_hour", state.get("start_hour", 0))
                state["duration_hours"] = s.get("duration_hours", state.get("duration_hours", 0))
                state["end_hour"] = s.get("end_hour", state.get("start_hour", 0) + state.get("duration_hours", 0))
        self.gap_plans = load_json_data("gap_plans.json")
        self.gaps_by_id = {g["gap_id"]: g for g in self.gap_plans["gaps"]}

    def resolve(self, gap_id: str, day_offset: int = 0, hour: float = 0.0) -> Dict[str, Any]:
        gap = self.gaps_by_id.get(gap_id)
        if not gap:
            return {}
        prev_scene_id = gap["from_scene_id"]
        prev_state = self.scene_states.get(prev_scene_id, {})
        base = prev_state.get("state_out", {})
        # Merge with gap-level snapshot for safety
        snap = gap.get("state_out_snapshot", {})
        # Build a flat world_state dict for prompt consumption
        return self._flatten(base, snap, day_offset, hour)

    @staticmethod
    def _flatten(base: dict, snap: dict, day_offset: int, hour: float) -> dict:
        meta = base.get("meta", {})
        glob = base.get("global", {})
        company = base.get("company", {})
        chars = base.get("characters", {})

        # Determine season from date or meta
        season = meta.get("season", "spring")
        region = glob.get("region", "Middle-earth")
        weather = glob.get("weather", {})

        alive_chars = [name for name, data in chars.items() if data.get("is_alive", True)]
        present_chars = [name for name, data in chars.items() if data.get("is_with_company", False)]

        return {
            "season": season,
            "region": region,
            "weather_condition": weather.get("condition", "clear"),
            "temperature_c": weather.get("temperature_c", 15),
            "wind": weather.get("wind", "calm"),
            "precipitation": weather.get("precipitation", "none"),
            "daylight_hours": meta.get("daylight_hours", [6, 20]),
            "moon_phase": meta.get("moon_phase", "full_moon"),
            "active_flags": glob.get("active_flags", []),
            "company_members": company.get("members", present_chars or alive_chars),
            "company_leader": company.get("leader", "Thorin"),
            "company_morale": company.get("morale", "steady"),
            "characters": {k: v for k, v in chars.items() if v.get("is_alive", True)},
            "day_offset": day_offset,
            "hour": hour,
        }


# ─────────────────────── Prompt Templates ───────────────────────

BLOCK_TEMPLATES = {
    "wake_and_ritual": {
        "mode": "event",
        "instruction": (
            "Describe the waking and first rites of the day. "
            "Include sensory details: light, temperature, sounds. "
            "Mention who wakes first and what they do."
        ),
    },
    "meal_preparation": {
        "mode": "event",
        "instruction": (
            "Describe the preparation of a meal. "
            "Who cooks, what ingredients are at hand, what scents rise. "
            "Keep the tone warm or rustic according to the place."
        ),
    },
    "group_meal": {
        "mode": "chat",
        "instruction": (
            "Write a brief opening line to set the scene, then let the rest be pure dialogue among 2–4 present characters. "
            "Use dialogue tags or brief action beats between lines, but keep it mostly spoken words. "
            "End with a single closing atmospheric sentence if needed. Let them talk about the food, the journey, or memories."
        ),
    },
    "pair_dialogue": {
        "mode": "chat",
        "instruction": (
            "Give one brief sentence of setting, then write the scene as pure back-and-forth dialogue between the two characters. "
            "Use dialogue tags or tiny action beats, but keep it mostly spoken words. End with a short closing beat if needed."
        ),
    },
    "inner_monologue": {
        "mode": "event",
        "instruction": (
            "Write a brief inner monologue from the point of view of a present character. "
            "Reflect their worries, hopes, or memories at this exact moment."
        ),
    },
    "night_watch": {
        "mode": "event",
        "instruction": (
            "Describe a night watch. Who keeps guard, what they hear, what they fear or hope for. "
            "Atmosphere of contained tension or guarded peace."
        ),
    },
    "restless_sleep": {
        "mode": "ambiental",
        "instruction": (
            "Describe a fragment of sleep or night wakefulness. "
            "May include mild nightmares, distant noises, or the discomfort of the place."
        ),
    },
    "ambient_pause": {
        "mode": "ambiental",
        "instruction": (
            "Describe the atmosphere of the place at this moment. "
            "No action or dialogue: only sounds, light, smells, the feeling of time passing."
        ),
    },
    "individual_task": {
        "mode": "event",
        "instruction": (
            "Describe an individual task performed by a present character. "
            "It may be mending something, writing, exploring, or cooking. Show them in action."
        ),
    },
    "exploration": {
        "mode": "event",
        "instruction": (
            "Describe an exploration or movement through the environment. "
            "New discoveries, obstacles, or simply the sensation of pressing onward."
        ),
    },
    "strategic_discussion": {
        "mode": "chat",
        "instruction": (
            "Start with one brief scene-setting sentence, then write the rest as pure dialogue among the characters. "
            "Focus on back-and-forth spoken lines with minimal narration. End with a short atmospheric closing beat if needed."
        ),
    },
    "evening_ritual": {
        "mode": "event",
        "instruction": (
            "Describe the ritual of closing the day: making camp, lighting a fire, praying, or telling tales. "
            "Tone of closure, reflection, or fellowship."
        ),
    },
    "cultural_ritual": {
        "mode": "event",
        "instruction": (
            "Describe or transcribe a song, poem, or cultural rite. "
            "It may be dwarven, elvish, or of the Shire. Include the reactions of those witnessing it."
        ),
    },
    "comic_relief": {
        "mode": "chat",
        "instruction": (
            "One brief sentence of setting, then write the scene as rapid back-and-forth dialogue. "
            "Keep it mostly spoken words with short tags. End with a quick closing beat."
        ),
    },
    "accident_or_conflict": {
        "mode": "event",
        "instruction": (
            "Describe a small accident or conflict: a stumble, an argument, minor harm, or an unpleasant surprise. "
            "Keep tension proportional to context; do not alter the canonical plot."
        ),
    },
    "farewell_or_reunion": {
        "mode": "chat",
        "instruction": (
            "One brief sentence of setting, then write the scene as pure dialogue between the characters. "
            "Let emotions show through what they say, not through long descriptions. End with a short closing beat if needed."
        ),
    },
    "march_segment": {
        "mode": "ambiental",
        "instruction": (
            "Describe a segment of marching or travel. Rhythm of footsteps, changing landscape, weariness or mood of the company."
        ),
    },
}


def build_system_prompt(world_state: dict, cfg: dict) -> str:
    lang = cfg.get("narrative", {}).get("language", "en")
    voice = cfg.get("narrative", {}).get("voice", "Tolkien-esque narrator")
    tone = cfg.get("narrative", {}).get("tone", "warm, slightly archaic")
    perspective = cfg.get("narrative", {}).get("perspective", "third-person limited")

    region = world_state.get("region", "Middle-earth")
    season = world_state.get("season", "spring")
    weather = world_state.get("weather_condition", "clear")
    temp = world_state.get("temperature_c", 15)
    wind = world_state.get("wind", "calm")
    precip = world_state.get("precipitation", "none")
    members = world_state.get("company_members", [])
    morale = world_state.get("company_morale", "steady")
    flags = world_state.get("active_flags", [])

    flags_str = ", ".join(flags) if flags else "none"
    members_str = ", ".join(members) if members else "none"

    prompt = f"""You are a literary narrator with the voice of {voice}.
Tone: {tone}.
Perspective: {perspective}.

WORLD CONTEXT (do not repeat it in the answer, use it as background):
- Region: {region}
- Season: {season}
- Current weather: {weather}, {temp}°C, wind {wind}, precipitation: {precip}
- Present company members: {members_str}
- General morale: {morale}
- Active world flags: {flags_str}

ABSOLUTE RESTRICTIONS:
- DO NOT foreshadow future canonical scenes.
- DO NOT revive dead characters.
- DO NOT move characters if they are confined or separated.
- Keep coherence with Tolkien lore.
- Generate a SINGLE narrative fragment (1–3 short paragraphs).
- Answer ALWAYS in {lang.upper()}.
"""
    return prompt.strip()


def build_user_prompt(
    world_state: dict,
    block: dict,
    gap_meta: dict,
    phase_meta: Optional[dict],
    day_number: int,
    hour_of_day: float,
) -> str:
    block_id = block.get("block_id", "ambient_pause")
    template = BLOCK_TEMPLATES.get(block_id, BLOCK_TEMPLATES["ambient_pause"])
    suffix = block.get("prompt_suffix", "")
    mood = (phase_meta or {}).get("mood", gap_meta.get("mood", "neutral"))
    gap_title = gap_meta.get("title", "Unknown Gap")
    phase_title = (phase_meta or {}).get("title", "")

    time_str = f"{int(hour_of_day):02d}:{int((hour_of_day % 1) * 60):02d}"

    header = f"""NARRATIVE MOMENT:
- Gap: {gap_title}
- Phase: {phase_title or 'N/A'}
- Day {day_number} of the gap, time {time_str}
- Mood: {mood}
- Generation mode: {template['mode']}
"""

    body = f"""INSTRUCTION:
{template['instruction']}
"""

    if suffix:
        body += f"\nSPECIFIC CONTEXT:\n{suffix}\n"

    body += "\nGENERATE THE NARRATIVE FRAGMENT NOW:\n"
    return (header + body).strip()


class PromptEngine:
    """High-level prompt composer for gap events."""

    def __init__(self, config_path: str = "config/openrouter.yaml"):
        self.cfg = load_openrouter_config(config_path)
        self.resolver = WorldStateResolver()

    def compose(
        self,
        gap_id: str,
        block: dict,
        day_number: int,
        hour_of_day: float,
        phase_meta: Optional[dict] = None,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        gap = self.resolver.gaps_by_id.get(gap_id)
        if not gap:
            raise ValueError(f"Gap {gap_id} not found")

        world_state = self.resolver.resolve(gap_id, day_number, hour_of_day)
        system_prompt = build_system_prompt(world_state, self.cfg)
        user_prompt = build_user_prompt(world_state, block, gap, phase_meta, day_number, hour_of_day)

        return {
            "model": model_override or self.cfg.get("default_model", "openai/gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.cfg.get("generation", {}).get("temperature", 0.85),
            "max_tokens": self.cfg.get("generation", {}).get("max_tokens", 256),
            "top_p": self.cfg.get("generation", {}).get("top_p", 0.95),
            "frequency_penalty": self.cfg.get("generation", {}).get("frequency_penalty", 0.2),
            "presence_penalty": self.cfg.get("generation", {}).get("presence_penalty", 0.1),
            "metadata": {
                "gap_id": gap_id,
                "block_id": block.get("block_id", "ambient_pause"),
                "day_number": day_number,
                "hour_of_day": hour_of_day,
                "mode": BLOCK_TEMPLATES.get(block.get("block_id"), BLOCK_TEMPLATES["ambient_pause"])["mode"],
            },
        }

    @staticmethod
    def _snap10min(hours: float) -> float:
        return round(hours * 6) / 6.0

    @staticmethod
    def _m(minutes: int) -> float:
        return (minutes // 10 * 10) / 60.0

    def _flatten_arc(
        self, node: dict, day_cursor: float, prev_journey_day: int, base_dt: datetime, gap_id: str
    ):
        """Recursively flatten an arc node into scheduled blocks."""
        blocks = []
        node_type = node.get("type")

        if node_type == "phase":
            days = node.get("days", 1)
            schedule = node.get("day_pattern_schedule", [])
            for d in range(days):
                day_num = day_cursor + d + 1
                hour_cursor = 0.0
                for slot in schedule:
                    slot_copy = dict(slot)
                    slot_copy["gap_id"] = gap_id
                    slot_copy["phase_id"] = node.get("phase_id")
                    slot_copy["phase_title"] = node.get("title")
                    slot_copy["mood"] = node.get("mood")
                    slot_copy["day_number"] = day_num
                    slot_copy["journey_day"] = prev_journey_day + day_num - 1
                    slot_copy["hour_start"] = self._snap10min(hour_cursor)
                    slot_copy["timestamp"] = (base_dt + timedelta(days=day_num - 1, hours=hour_cursor)).isoformat()
                    blocks.append(slot_copy)
                    hour_cursor += slot.get("duration_hours", 1.0)
            day_cursor += days

        elif node_type == "beat":
            hour_start = self._snap10min((day_cursor % 1) * 24.0)
            dur = node.get("duration_hours", 1.0)
            blocks.append({
                "block_id": node.get("beat_type") or self._infer_block_id(node.get("title", ""), node.get("prompt", "")),
                "duration_hours": dur,
                "prompt_suffix": node.get("prompt", ""),
                "gap_id": gap_id,
                "phase_id": None,
                "phase_title": None,
                "mood": "neutral",
                "day_number": max(1, int(day_cursor) + 1),
                "journey_day": prev_journey_day + max(0, int(day_cursor)),
                "hour_start": hour_start,
                "timestamp": (base_dt + timedelta(hours=day_cursor * 24)).isoformat(),
            })
            day_cursor += dur / 24.0

        elif node_type == "sequence" and node.get("block_id") and not node.get("children"):
            # Direct sequence block (small gaps)
            hour_start = self._snap10min((day_cursor % 1) * 24.0)
            dur = node.get("duration_hours", 1.0)
            blocks.append({
                "block_id": node.get("block_id", "ambient_pause"),
                "duration_hours": dur,
                "prompt_suffix": node.get("prompt", ""),
                "gap_id": gap_id,
                "phase_id": node.get("phase_id"),
                "phase_title": node.get("title"),
                "mood": node.get("mood", "neutral"),
                "day_number": max(1, int(day_cursor) + 1),
                "journey_day": prev_journey_day + max(0, int(day_cursor)),
                "hour_start": hour_start,
                "timestamp": (base_dt + timedelta(hours=day_cursor * 24)).isoformat(),
            })
            day_cursor += dur / 24.0

        elif node_type in ("sequence", "subplot"):
            # Recurse into children regardless of depth
            for child in node.get("children", []):
                child_blocks, day_cursor = self._flatten_arc(child, day_cursor, prev_journey_day, base_dt, gap_id)
                blocks.extend(child_blocks)

        return blocks, day_cursor

    def expand_gap_blocks(
        self, gap_id: str
    ) -> List[Dict[str, Any]]:
        """Expand a gap plan into a flat list of scheduled blocks with timestamps."""
        gap = self.resolver.gaps_by_id.get(gap_id)
        if not gap:
            raise ValueError(f"Gap {gap_id} not found")

        arc = gap.get("arc") or {}
        children = arc.get("children", [])

        base_date_str = gap.get("from_date_iso") or self._infer_date(gap)
        base_dt = datetime.fromisoformat(base_date_str) if base_date_str else datetime(2941, 4, 25, 10, 0, 0)

        prev_scene_id = gap.get("from_scene_id")
        prev_scene_state = self.resolver.scene_states.get(prev_scene_id, {})
        prev_journey_day = prev_scene_state.get("journey_day", 0)

        blocks = []
        day_cursor = 0.0
        for node in children:
            child_blocks, day_cursor = self._flatten_arc(node, day_cursor, prev_journey_day, base_dt, gap_id)
            blocks.extend(child_blocks)

        blocks = self._normalize_and_filter_blocks(blocks, gap, base_dt)
        return blocks

    def _normalize_and_filter_blocks(
        self, blocks: List[Dict[str, Any]], gap: dict, base_dt: datetime
    ) -> List[Dict[str, Any]]:
        prev_scene_id = gap.get("from_scene_id")
        next_scene_id = gap.get("to_scene_id")
        prev_state = self.resolver.scene_states.get(prev_scene_id, {})
        next_state = self.resolver.scene_states.get(next_scene_id, {})

        gap_start_day = prev_state.get("journey_day", 0)
        gap_start_hour = prev_state.get("end_hour", prev_state.get("start_hour", 0) + prev_state.get("duration_hours", 0))
        gap_end_day = next_state.get("journey_day", 0)
        gap_end_hour = next_state.get("start_hour", 0)

        gap_start_total = self._snap10min(gap_start_day * 24 + gap_start_hour)
        gap_end_total = self._snap10min(gap_end_day * 24 + gap_end_hour)
        eps = self._m(10)  # 10 minutes tolerance expressed in hours

        # Build forbidden intervals (canonical scenes that intersect the gap window)
        forbidden = []
        for sid, state in self.resolver.scene_states.items():
            day = state.get("journey_day", 0)
            start = self._snap10min(day * 24 + state.get("start_hour", 0))
            end = self._snap10min(start + state.get("duration_hours", 0))
            if start < gap_end_total and end > gap_start_total:
                forbidden.append((max(gap_start_total, start), min(gap_end_total, end)))
        forbidden.sort()

        # Merge overlapping forbidden intervals
        merged = []
        for s, e in forbidden:
            if merged and s <= merged[-1][1] + eps:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))

        normalized = []
        cursor = gap_start_total
        fidx = 0

        for b in blocks:
            raw_dur = b.get("duration_hours", 1.0)

            # Skip past any forbidden intervals that end before cursor
            while fidx < len(merged) and merged[fidx][1] <= cursor + eps:
                fidx += 1

            # If cursor is inside a forbidden interval, jump to its end
            if fidx < len(merged) and merged[fidx][0] <= cursor < merged[fidx][1]:
                cursor = merged[fidx][1]
                fidx += 1

            # Determine block boundaries
            block_start = cursor
            block_end = block_start + raw_dur

            # Trim if it runs into a forbidden interval
            if fidx < len(merged) and block_start < merged[fidx][0] < block_end:
                raw_dur = merged[fidx][0] - block_start
                block_end = block_start + raw_dur

            # Trim if it exceeds gap end
            if block_end > gap_end_total:
                raw_dur = gap_end_total - block_start
                block_end = gap_end_total

            dur = self._snap10min(raw_dur)
            if dur < self._m(10):
                continue

            nb = dict(b)
            nb["duration_hours"] = dur
            nb["journey_day"] = int(block_start // 24)
            nb["hour_start"] = self._snap10min(block_start % 24)
            nb["day_number"] = max(1, nb["journey_day"] - gap_start_day + 1)
            nb["timestamp"] = (base_dt + timedelta(hours=block_start - gap_start_day * 24)).isoformat()
            normalized.append(nb)
            cursor = block_end

        return normalized

    @staticmethod
    def _infer_block_id(title: str, prompt: str) -> str:
        t = (title or "").lower()
        p = (prompt or "").lower()
        if "march" in t or "march" in p or "camin" in p:
            return "march_segment"
        if "meal" in t or "comida" in p or "food" in p or "cena" in p or "desayuno" in p:
            return "group_meal"
        if "dialogue" in t or "conversation" in t or "charla" in p or "hablan" in p:
            return "pair_dialogue"
        if "camp" in t or "campamento" in p or "acamp" in p:
            return "evening_ritual"
        if "prepar" in t or "prepar" in p:
            return "meal_preparation"
        if "explor" in t or "explor" in p:
            return "exploration"
        if "rest" in t or "sleep" in t or "sueño" in p or "descans" in p:
            return "restless_sleep"
        if "watch" in t or "guardia" in p or "vigil" in p:
            return "night_watch"
        return "ambient_pause"

    @staticmethod
    def _infer_date(gap: dict) -> Optional[str]:
        # Try to get date from previous canonical scene state
        prev_id = gap.get("from_scene_id")
        if not prev_id:
            return None
        states = {s["scene_id"]: s for s in load_json_data("canonical_scene_states.json")}
        prev = states.get(prev_id, {})
        return prev.get("date_iso")


if __name__ == "__main__":
    engine = PromptEngine()
    # Demo: compose first block of first long gap
    gap_id = "gap_canon_044_canon_045"
    blocks = engine.expand_gap_blocks(gap_id)
    if blocks:
        b = blocks[0]
        prompt = engine.compose(
            gap_id=gap_id,
            block=b,
            day_number=b["day_number"],
            hour_of_day=b["hour_start"],
            phase_meta={"title": b["phase_title"], "mood": b["mood"]},
        )
        print(json.dumps(prompt, indent=2, ensure_ascii=False))
    else:
        print("No blocks expanded")
