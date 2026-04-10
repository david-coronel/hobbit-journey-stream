#!/usr/bin/env python3
"""
Gap Planner — Generates narrative arc trees for the gaps between canonical scenes.
Each arc is a tree of beats, sequences, and subplots that can be nested arbitrarily.
Gaps with <= 0.1 hours (contiguous or overlapping) return arc=null.

Small gaps (3–24h) are now composed of reusable generic blocks chosen from a location-aware
bag. Each block carries a prompt template, update mode, and strict canonical constraints.
"""

import json
import math
import random
from typing import List, Dict, Any


# ─────────────────────── 10-minute helpers ───────────────────────
def m(minutes: int) -> float:
    """Convert minutes to hours, snapping to exact 10-min increments."""
    return (minutes // 10 * 10) / 60.0


def snap10min(hours: float) -> float:
    """Snap hours to nearest 10-minute increment."""
    return round(hours * 60 / 10) * 10 / 60.0


# ─────────────────────── Data Loading ───────────────────────

def load_data():
    with open('data/canonical_scene_states.json') as f:
        canonical_states = json.load(f)
    with open('data/stream_scenes.json') as f:
        stream_scenes = {s['id']: s for s in json.load(f)['scenes']}
    for state in canonical_states:
        sid = state['scene_id']
        if sid in stream_scenes:
            s = stream_scenes[sid]
            state['start_hour'] = s.get('start_hour', 0)
            state['end_hour'] = s.get('end_hour', s.get('start_hour', 0) + s.get('duration_hours', 0))
            state['duration_hours'] = s.get('duration_hours', 0)
            state['journey_day'] = s.get('journey_day', state.get('journey_day', 0))
    return canonical_states


# ─────────────────────── Node Factory ───────────────────────

def make_node(node_type: str, title: str, duration_hours: float = 0, **kwargs) -> Dict[str, Any]:
    node = {
        "type": node_type,
        "title": title,
        "duration_hours": snap10min(duration_hours),
    }
    node.update(kwargs)
    if node_type in ("subplot", "sequence"):
        node.setdefault("children", [])
    return node


def split_duration(total_hours: float, parts: int, min_hour: float = 0.5) -> List[float]:
    if parts <= 0:
        return []
    if total_hours <= 0:
        return [0.0] * parts
    total_mins = round(total_hours * 60 / 10) * 10
    min_mins = round(min_hour * 60 / 10) * 10
    base = max(min_mins, total_mins // parts)
    base = (base // 10) * 10
    chunks = [base] * parts
    # scale down if oversized
    while sum(chunks) > total_mins and any(c > min_mins for c in chunks):
        for i in range(parts):
            if sum(chunks) <= total_mins:
                break
            if chunks[i] > min_mins:
                chunks[i] -= 10
    rem = total_mins - sum(chunks)
    i = 0
    while rem > 0:
        chunks[i % parts] += 10
        rem -= 10
        i += 1
    return [c / 60.0 for c in chunks]


# ─────────────────────── Canonical Constraints ───────────────────────

def build_canon_constraints(prev_state: dict, next_state: dict) -> List[str]:
    """Build strict constraints from state_out of prev and state_in of next."""
    constraints = []
    prev_chars = prev_state.get('state_out', {}).get('characters', {})
    next_chars = next_state.get('state_in', {}).get('characters', {})

    for name, pdata in prev_chars.items():
        ndata = next_chars.get(name, {})
        pstatus = pdata.get('status', 'alive')
        nstatus = ndata.get('status', 'alive')
        if pstatus == 'dead' and nstatus == 'dead':
            constraints.append(f"{name} is dead and must not appear alive, speak, or act in any way.")
        elif pstatus != 'dead' and nstatus == 'dead':
            constraints.append(f"DO NOT kill {name} in this gap; their canonical death occurs in the next scene ('{next_state['title']}').")
        elif pstatus == 'dead' and nstatus != 'dead':
            constraints.append(f"{name} is dead in the previous scene. They must remain dead unless canonically resurrected (which does not happen here).")

        ploc = pdata.get('location', 'unknown')
        nloc = ndata.get('location', 'unknown')
        if ploc != nloc:
            constraints.append(f"If {name} travels during this gap, they must end at '{nloc}' exactly as required by the next scene.")
        else:
            constraints.append(f"{name} should generally stay at '{ploc}' unless briefly stepping away and returning.")

    prev_members = set(prev_state.get('state_out', {}).get('company', {}).get('members', []))
    next_members = set(next_state.get('state_in', {}).get('company', {}).get('members', []))
    if prev_members != next_members:
        if prev_members - next_members:
            constraints.append(f"Do not permanently separate {', '.join(prev_members - next_members)} from the company before the next scene.")
        if next_members - prev_members:
            constraints.append(f"Do not add {', '.join(next_members - prev_members)} to the company prematurely.")

    if next_state.get('title'):
        constraints.append(f"This gap must flow naturally into the next canonical scene: '{next_state['title']}'. Do not anticipate its climax or resolve its conflict.")

    return constraints


def get_time_of_day(hour: float) -> str:
    h = int(hour) % 24
    if 5 <= h < 11:
        return "morning"
    elif 11 <= h < 14:
        return "noon"
    elif 14 <= h < 18:
        return "afternoon"
    elif 18 <= h < 22:
        return "evening"
    else:
        return "night"


# ─────────────────────── Small Gap Block Templates ───────────────────────

SMALL_GAP_BLOCKS = [
    {
        "block_id": "wake_and_ritual",
        "title": "Despertar y ritual matutino",
        "duration_range": (20, 45),
        "update_mode": "mixed",
        "participants": "group",
        "time_preference": "morning",
        "prompt_template": (
            "La Compañía despierta en {location} durante la {time_of_day}. "
            "Algunos se quejan del frío, de la dureza del suelo o de la luz temprana. "
            "Hay peinado de barbas, revisión de armas, estiramientos con gemidos, y conversaciones susurradas sobre quién dormía peor. "
            "NO adelantes eventos de '{next_scene}'. El ambiente debe ser de resignación o determinación silenciosa."
        ),
        "constraints": [],
    },
    {
        "block_id": "meal_preparation",
        "title": "Preparación de comida",
        "duration_range": (20, 35),
        "update_mode": "mixed",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "En {location}, durante la {time_of_day}, la Compañía intenta preparar una comida. "
            "Puede haber dificultad con el fuego, discusión sobre quién cocina, reclamos de hambre, o alguien que encuentra algo inesperado en sus provisiones. "
            "El tono debe ser doméstico y ligeramente cómico. NO inventes comida abundante si las raciones son escasas. "
            "NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "group_meal",
        "title": "Comida grupal",
        "duration_range": (30, 60),
        "update_mode": "chat",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "La Compañía come junta en {location}. Es {time_of_day}. "
            "Se habla con la boca llena, se cuentan anécdotas breves, se quejan de la comida o se recuerdan banquetes pasados. "
            "Thorin puede comer apartado con solemnidad. Gandalf puede fumar en pipa observando. "
            "NO adelantes eventos de '{next_scene}'. NO cambies el estado de ánimo general de forma abrupta."
        ),
        "constraints": [],
    },
    {
        "block_id": "after_meal_talk",
        "title": "Diálogo de sobremesa",
        "duration_range": (20, 40),
        "update_mode": "chat",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "Tras comer en {location}, durante la {time_of_day}, la conversación continúa con más calma. "
            "Algunos descansan. Otros hablan de planes, recuerdos o temores contenidos. "
            "Es un momento de vulnerabilidad o de camaradería. NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "individual_task",
        "title": "Tarea individual",
        "duration_range": (30, 60),
        "update_mode": "mixed",
        "participants": "solo",
        "time_preference": "any",
        "prompt_template": (
            "Un solo personaje ({participants}) realiza una tarea en {location} durante la {time_of_day}: revisar armas, cuidar ponis, escribir en un diario, o simplemente observar el paisaje. "
            "Puede haber un monólogo interior breve o una observación detallada del entorno. "
            "NO adelantes eventos de '{next_scene}'. NO generes diálogo con personajes que no están presentes."
        ),
        "constraints": [],
    },
    {
        "block_id": "pair_dialogue",
        "title": "Conversación a solas",
        "duration_range": (15, 35),
        "update_mode": "chat",
        "participants": "pair",
        "time_preference": "any",
        "prompt_template": (
            "Dos personajes ({participants}) conversan a solas en {location} durante la {time_of_day}. "
            "Puede ser una confesión, una discusión táctica, una lección, o una tensión no resuelta. "
            "El diálogo debe sentirse natural, con interrupciones y silencios. "
            "NO adelantes eventos de '{next_scene}'. NO reveles información que solo debería conocerse en escenas futuras."
        ),
        "constraints": [],
    },
    {
        "block_id": "inner_monologue",
        "title": "Monólogo interior",
        "duration_range": (10, 25),
        "update_mode": "chat",
        "participants": "solo",
        "time_preference": "any",
        "prompt_template": (
            "{participants} está solo en {location} durante la {time_of_day}. "
            "Sus pensamientos vagan entre el miedo, la nostalgia, el orgullo o la duda. "
            "Si es Bilbo, puede pensar en Hobbiton. Si es Thorin, en Erebor. Si es Gandalf, en responsabilidades mayores. "
            "NO adelantes eventos de '{next_scene}'. NO generes visiones precisas del futuro."
        ),
        "constraints": [],
    },
    {
        "block_id": "ambient_pause",
        "title": "Pausa ambiental",
        "duration_range": (30, 90),
        "update_mode": "ambiental",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "En {location}, durante la {time_of_day}, la Compañía descansa en silencio. "
            "Solo el sonido del viento, el crujir de las armas, o la respiración de los durmientes. "
            "Este es un bloque de atmósfera pura: clima, luz, sonidos lejanos. "
            "NO se requiere diálogo ni acción importante. NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "comic_relief",
        "title": "Alivio cómico",
        "duration_range": (10, 20),
        "update_mode": "mixed",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "Un momento de humor absurdo en {location} durante la {time_of_day}. "
            "Alguien tropieza, una discusión ridícula estalla, un pony se niega a obedecer, o un malentendido provoca risas incómodas. "
            "El tono debe ser ligero y físico, sin consecuencias graves. "
            "NO adelantes eventos de '{next_scene}'. NO hieras de verdad a nadie."
        ),
        "constraints": [],
    },
    {
        "block_id": "evening_ritual",
        "title": "Preparativos nocturnos",
        "duration_range": (15, 30),
        "update_mode": "mixed",
        "participants": "group",
        "time_preference": "evening",
        "prompt_template": (
            "En {location}, al atardecer, la Compañía prepara el campamento para la noche. "
            "Se reparten turnos de guardia, se ajustan mantas, se discute dónde dormir. "
            "Hay una mezcla de cansancio y cautela. NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "night_watch",
        "title": "Vigilia nocturna",
        "duration_range": (60, 120),
        "update_mode": "ambiental",
        "participants": "pair",
        "time_preference": "night",
        "prompt_template": (
            "Dos guardias ({participants}) vigilan en {location} durante la noche. "
            "El mundo está en silencio. Pueden intercambiar pocas palabras susurradas, o simplemente escuchar. "
            "De vez en cuando, un ruido lejano tensa el ambiente. "
            "NO adelantes eventos de '{next_scene}'. NO generes peligros que no están en el canon."
        ),
        "constraints": [],
    },
    {
        "block_id": "restless_sleep",
        "title": "Sueño fraccionado",
        "duration_range": (45, 90),
        "update_mode": "mixed",
        "participants": "solo",
        "time_preference": "night",
        "prompt_template": (
            "{participants} intenta dormir en {location} durante la noche, pero el sueño es irregular. "
            "Puede haber una pesadilla breve, un despertar sobresaltado, o una meditación melancólica mirando las estrellas o las brasas. "
            "NO adelantes eventos de '{next_scene}'. NO generes visiones proféticas explícitas."
        ),
        "constraints": [],
    },
    {
        "block_id": "cultural_ritual",
        "title": "Ritual cultural",
        "duration_range": (20, 40),
        "update_mode": "mixed",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "En {location}, durante la {time_of_day}, la Compañía realiza un ritual cultural: canto enano, reparación de armas, peinado de barbas, o una canción improvisada sobre un evento reciente. "
            "El momento debe revelar identidad y costumbres sin ser solemnemente religioso. "
            "NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "casual_encounter",
        "title": "Encuentro casual",
        "duration_range": (10, 25),
        "update_mode": "chat",
        "participants": "pair",
        "time_preference": "any",
        "prompt_template": (
            "Dos personajes ({participants}) se cruzan inesperadamente en {location} durante la {time_of_day}. "
            "Puede ser una conversación breve e incómoda, un gesto de ayuda, o el intercambio de una queja. "
            "NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "strategic_discussion",
        "title": "Discusión de planes",
        "duration_range": (20, 40),
        "update_mode": "chat",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "La Compañía discute planes en {location} durante la {time_of_day}. "
            "Thorin u otro líder intenta imponer orden. Hay desacuerdos, optimismo forzado, o miedo contenido. "
            "NO resuelvas conflictos que pertenecen a '{next_scene}'. NO tomes decisiones que el canon ya toma más adelante."
        ),
        "constraints": [],
    },
    {
        "block_id": "exploration",
        "title": "Exploración de los alrededores",
        "duration_range": (30, 60),
        "update_mode": "mixed",
        "participants": "pair",
        "time_preference": "any",
        "prompt_template": (
            "Dos personajes ({participants}) exploran brevemente los alrededores de {location} durante la {time_of_day}. "
            "Pueden encontrar huellas, una vista inesperada, o simplemente confirmar que el camino sigue adelante. "
            "NO descubras tesoros o amenazas que no están en el canon. NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
    {
        "block_id": "farewell_arrival",
        "title": "Llegada o despedida",
        "duration_range": (15, 30),
        "update_mode": "event",
        "participants": "group",
        "time_preference": "any",
        "prompt_template": (
            "Alguien llega a {location} o alguien parte durante la {time_of_day}. "
            "Hay gestos de despedida, instrucciones de último momento, o el alivio de una reunión inesperada. "
            "Este bloque debe funcionar como transición. NO adelantes eventos de '{next_scene}'."
        ),
        "constraints": [],
    },
]


def choose_participants(participant_type: str, present_characters: List[str], preferred: str = "Bilbo") -> str:
    if not present_characters:
        return "Bilbo"
    if participant_type == "solo":
        if preferred in present_characters:
            return preferred
        return random.choice(present_characters)
    elif participant_type == "pair":
        pool = present_characters[:]
        if len(pool) < 2:
            return ", ".join(pool)
        a = random.choice(pool)
        pool.remove(a)
        b = random.choice(pool)
        return f"{a} y {b}"
    else:  # group
        return ", ".join(present_characters[:min(5, len(present_characters))])


def score_block(block: dict, current_hour: float, remaining_minutes: float, location: str,
                 recent_block_ids: List[str], block_counts: Dict[str, int]) -> float:
    score = 100.0
    # Avoid recent repeats
    if block["block_id"] in recent_block_ids:
        score -= 400 * (recent_block_ids.count(block["block_id"]) + 1)
    # Limit total occurrences of any single block type
    if block_counts.get(block["block_id"], 0) >= 3:
        score -= 800
    time_of_day = get_time_of_day(current_hour)
    pref = block.get("time_preference", "any")
    if pref != "any" and pref != time_of_day:
        score -= 60
    elif pref == "any":
        score += 10
    elif pref == time_of_day:
        score += 30
    if block["duration_range"][1] > remaining_minutes + 5:
        score -= 300
    if block["duration_range"][0] > remaining_minutes + 2:
        score -= 300
    avoid = block.get("avoid_locations", [])
    if location in avoid:
        score -= 1000
    priority = block.get("priority_locations", [])
    if location in priority:
        score += 40
    # Prefer blocks whose max duration can actually absorb a good chunk when remaining is large
    if remaining_minutes > 60 and block["duration_range"][1] < 30:
        score -= 20
    return score


def compose_small_gap(prev_state: dict, next_state: dict, total_hours: float) -> Dict[str, Any]:
    """Compose a small gap from reusable generic blocks."""
    total_minutes = round(total_hours * 60 / 10) * 10
    current_hour = prev_state.get('end_hour', 0)
    location = prev_state['state_out']['characters'].get('Bilbo', {}).get('location', 'unknown')

    # Determine who is present at the start
    present = []
    for name, data in prev_state.get('state_out', {}).get('characters', {}).items():
        if data.get('location') == location and data.get('status') != 'dead':
            present.append(name)
    if not present:
        present = ["Bilbo"]

    canon_constraints = build_canon_constraints(prev_state, next_state)
    gap_id = f"gap_{prev_state['scene_id']}_{next_state['scene_id']}"

    arc = make_node("subplot", f"Pause: {prev_state['title']} → {next_state['title']}", total_minutes / 60.0)
    arc["children"] = []

    remaining = total_minutes
    recent_block_ids = []
    block_counts: Dict[str, int] = {}
    block_index = 0
    max_blocks = 40

    while remaining > 0 and block_index < max_blocks:
        candidates = [
            b for b in SMALL_GAP_BLOCKS
            if b["duration_range"][0] <= remaining + 5
        ]
        if not candidates:
            break

        scored = [(b, score_block(b, current_hour, remaining, location, recent_block_ids, block_counts)) for b in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:3]
        chosen = random.choice(top)[0]

        dur_min = chosen["duration_range"][0]
        dur_max = min(chosen["duration_range"][1], remaining)
        if dur_max < dur_min:
            dur = remaining
        else:
            # snap to 10-minute increments
            dur = random.randint(dur_min // 10, dur_max // 10) * 10
        if dur <= 0:
            dur = remaining
        dur = min(dur, remaining)

        # Only absorb remaining time if it's truly small (< 20 min)
        if remaining <= 20:
            dur = remaining

        dur_hours = dur / 60.0
        time_of_day = get_time_of_day(current_hour)
        participants_str = choose_participants(chosen["participants"], present)

        prompt = chosen["prompt_template"].format(
            location=location,
            time_of_day=time_of_day,
            next_scene=next_state.get('title', 'the next scene'),
            participants=participants_str,
        )

        block_node = make_node(
            "sequence" if chosen["update_mode"] in ("mixed", "chat") else "beat",
            chosen["title"],
            dur_hours,
            block_id=chosen["block_id"],
            update_mode=chosen["update_mode"],
            participants=participants_str,
            prompt=prompt,
            canon_constraints=canon_constraints,
            time_of_day=time_of_day,
            location=location,
        )

        arc["children"].append(block_node)

        remaining -= dur
        current_hour = (current_hour + dur / 60.0) % 24
        recent_block_ids.append(chosen["block_id"])
        if len(recent_block_ids) > 3:
            recent_block_ids.pop(0)
        block_counts[chosen["block_id"]] = block_counts.get(chosen["block_id"], 0) + 1
        block_index += 1

    # If something remains, add a small closing transition block rather than inflating the last one
    if remaining > 0:
        arc["children"].append(make_node(
            "beat", "Closing moments", remaining / 60.0,
            update_mode="ambiental",
            prompt=f"Los últimos momentos en {location} antes de '{next_state.get('title', 'the next scene')}'. Transición silenciosa.",
            canon_constraints=canon_constraints,
        ))

    return arc


# ─────────────────────── Long Gap Phase Engine ───────────────────────

DAY_PATTERNS = {
    "dungeon_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "The waking is cold and abrupt in the elven cells."},
        {"block_id": "meal_preparation", "duration_hours": m(30), "prompt_suffix": "An elven guard leaves cold rations in the corridor."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "They eat in silence, each in their own cell or in small watched groups."},
        {"block_id": "ambient_pause", "duration_hours": m(210), "prompt_suffix": "Dungeon silence. Only dripping water and distant guard footsteps."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Second ration of the day. The bread is hard and the soup is tasteless."},
        {"block_id": "inner_monologue", "duration_hours": m(90), "prompt_suffix": "Someone meditates on their captivity as the sun moves slowly through a slit."},
        {"block_id": "pair_dialogue", "duration_hours": m(60), "prompt_suffix": "Two prisoners exchange whispered words between the bars."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Evening meal. Darkness falls outside the high windows."},
        {"block_id": "night_watch", "duration_hours": m(120), "prompt_suffix": "The elven guards change shift. The prisoners listen closely."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Fragmented sleep in cold cells. Nightmares of chains and darkness."},
        {"block_id": "ambient_pause", "duration_hours": m(90), "prompt_suffix": "The dungeon sleeps. Absolute silence until dawn."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "Brief cold sleep before the guards stir."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A guard passes close. The prisoners freeze in their blankets."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence returns, heavy as iron."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "Shallow dreams before the distant bell of morning."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The last hours of night drag on in darkness."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "Final restless hour before the cell door creaks."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A guard changes shift in the corridor beyond."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence stretches until the first grey light."},
    ],
    "prison_routine_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Mechanical waking. They are no longer surprised by where they are."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Morning ration. Low-voiced conversations about meals long past."},
        {"block_id": "individual_task", "duration_hours": m(240), "prompt_suffix": "Bilbo uses his invisibility to explore the palace unseen."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Midday meal. Some dwarves play cards in silence."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "Afternoon emptiness. Few move. Time seems to stand still."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. A dwarf tells a story everyone already knows but listens to again."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Bilbo visits another cell to exchange news and hope."},
        {"block_id": "night_watch", "duration_hours": m(120), "prompt_suffix": "Elven guards watch. The prisoners pretend to sleep."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Night of heavy dreams. Some wake not knowing what day it is."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The palace sleeps around them."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deeper sleep before the distant footsteps of dawn guards."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence stretches toward morning."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "The last cold hour before waking."},
    ],
    "planning_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Early waking. There is a new electricity in the air."},
        {"block_id": "meal_preparation", "duration_hours": m(60), "prompt_suffix": "They prepare food in haste, eager for the day's meetings."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Bilbo reports to Thorin from the door of his cell about what he has seen."},
        {"block_id": "exploration", "duration_hours": m(180), "prompt_suffix": "Bilbo mentally maps escape routes, counting guards and doors."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Quick meal. The conversation is conspiratorial and tense."},
        {"block_id": "pair_dialogue", "duration_hours": m(180), "prompt_suffix": "Bilbo contacts another dwarf, passing instructions of the barrel plan."},
        {"block_id": "strategic_discussion", "duration_hours": m(120), "prompt_suffix": "Thorin and the leaders discuss the plan: who goes first, which barrel, when."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. The mood is a mixture of fear and contained hope."},
        {"block_id": "night_watch", "duration_hours": m(120), "prompt_suffix": "Tense vigil. Every sound could be an opportunity or a betrayal."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Sleep interrupted by excitement. Tomorrow might be the day."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The palace breathes around them in darkness."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Half-dreams of barrels and rushing water."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence before the first grey light."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "The final cold hour before dawn."},
    ],
    "escape_eve_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Waking with knots in the stomach. Tonight might be the night."},
        {"block_id": "meal_preparation", "duration_hours": m(60), "prompt_suffix": "Last ration before action. They eat little, speak less."},
        {"block_id": "strategic_discussion", "duration_hours": m(240), "prompt_suffix": "They review the plan one last time. Signals, passwords, roles."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Midday meal with hands that tremble slightly."},
        {"block_id": "individual_task", "duration_hours": m(240), "prompt_suffix": "Physical preparations: hiding weapons, loosening barrel lids, creating distractions."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Last whispered instructions. There is no turning back."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. Some cannot eat. Others eat for the last time in captivity."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "They wait for the agreed signal. Every minute is an eternity."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Deadly silence. Waiting for the exact moment."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "The signal arrives. The escape begins. Furtive movement in the dark."},
        {"block_id": "individual_task", "duration_hours": m(120), "prompt_suffix": "Bilbo guides the dwarves one by one toward the barrels. Every step is a heartbeat."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "The last watch before the river takes them."},
        {"block_id": "ambient_pause", "duration_hours": m(30), "prompt_suffix": "A pause in the dark, hearts pounding."},
        {"block_id": "restless_sleep", "duration_hours": m(30), "prompt_suffix": "No one truly sleeps, but they close their eyes for a few minutes."},
        {"block_id": "ambient_pause", "duration_hours": m(30), "prompt_suffix": "The palace breathes, unaware."},
        {"block_id": "restless_sleep", "duration_hours": m(30), "prompt_suffix": "The last minutes before the escape begins in earnest."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The palace breathes, unaware."},
    ],
    "dragon_departure_day": [
        {"block_id": "ambient_pause", "duration_hours": m(120), "prompt_suffix": "Smaug wakes in fury. His wing-beats thunder like a storm. He flies south."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "Deafening silence after the dragon's departure. No one dares to speak."},
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Collective waking among the dwarves. Was it a dream? No. The air smells of sulfur."},
        {"block_id": "meal_preparation", "duration_hours": m(60), "prompt_suffix": "They prepare food with trembling hands. Eyes constantly look toward the sky."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Breakfast in silence. No one is hungry, but they eat out of discipline."},
        {"block_id": "strategic_discussion", "duration_hours": m(240), "prompt_suffix": "Should we leave? Will he return? Thorin orders to wait. Others argue in low voices."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Midday meal interrupted by glances at the southern horizon."},
        {"block_id": "exploration", "duration_hours": m(300), "prompt_suffix": "The dwarves cautiously explore Erebor, counting treasures and looking for alternative exits."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. The gold gleams with a sinister light. No one mentions it."},
        {"block_id": "night_watch", "duration_hours": m(120), "prompt_suffix": "Tripled watch. Every shadow might be Smaug's return."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "Uneasy sleep in the halls of gold."},
    ],
    "siege_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Waking with the first thought on Smaug. Where is he now?"},
        {"block_id": "meal_preparation", "duration_hours": m(60), "prompt_suffix": "They check the provisions once more. Rationing begins to be strict."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Morning meal with conversations about rumors and speculations."},
        {"block_id": "exploration", "duration_hours": m(240), "prompt_suffix": "They roam Erebor looking for signs of return, useful treasures, or safe exits."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Midday meal. Someone tells a story to break the tension."},
        {"block_id": "pair_dialogue", "duration_hours": m(240), "prompt_suffix": "Private conversations about fear, family in Lake-town, and the dragon's fate."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. They discuss whether to send a messenger. Thorin forbids it."},
        {"block_id": "night_watch", "duration_hours": m(120), "prompt_suffix": "Guards at the entrance. The south wind brings the smell of smoke."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Sleep interrupted by dreams of flames and roars."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The Mountain breathes around them in darkness."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deeper sleep despite the tension."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence stretches toward dawn."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "The last heavy hour before waking."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The first grey light touches the eastern gate."},
    ],
    "aftermath_eve_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Waking with the confirmed news: Smaug has fallen."},
        {"block_id": "meal_preparation", "duration_hours": m(60), "prompt_suffix": "They prepare a meal more generous than usual, almost like a celebration."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Ambivalent celebration: joy for the victory, mourning for Lake-town."},
        {"block_id": "pair_dialogue", "duration_hours": m(240), "prompt_suffix": "Private conversations about guilt, responsibility, and the future of the Mountain."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Midday meal. The gold begins to weigh in their glances."},
        {"block_id": "strategic_discussion", "duration_hours": m(240), "prompt_suffix": "What follows now? Who will claim the treasure? Who will arrive first?"},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper. Thorin speaks of restored Erebor. Some believe; others doubt."},
        {"block_id": "cultural_ritual", "duration_hours": m(120), "prompt_suffix": "A dwarven chant for the fallen of Lake-town. Then, silence."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Uneasy sleep. Victory tastes like ash."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The halls are dark and silent."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Dreams of fire and water mixed together."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence before the first grey light."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "The last cold hour before dawn."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Morning approaches over the Lonely Mountain."},
    ],
    "homeward_travel_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Early waking to make use of the light. The road west is long."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "Slow march under grey skies or fine rain. The Mountain grows small behind them."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Rest to eat. Melancholy conversations about the ending adventure."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "They continue walking. The landscape softens: green hills instead of black rocks."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Evening meal. Gandalf smokes his pipe, watching the horizon."},
        {"block_id": "evening_ritual", "duration_hours": m(60), "prompt_suffix": "They make camp for the last times in wild lands."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Conversations of anticipated farewell. Each night might be the last together."},
        {"block_id": "cultural_ritual", "duration_hours": m(60), "prompt_suffix": "Dwarven song about journeys and returns. Some join, others listen in silence."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Quiet but nostalgic sleep. Dreams of home and gold mixed together."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The camp breathes softly in the dark."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A single watchman keeps the embers alive."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deeper sleep under familiar stars."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The last hours of night pass in stillness."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The final doze before dawn."},
    ],
    "rivendell_welcome_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Late waking in soft, luminous Rivendell rooms."},
        {"block_id": "individual_task", "duration_hours": m(120), "prompt_suffix": "A solitary stroll through the gardens, listening to the murmur of the river."},
        {"block_id": "exploration", "duration_hours": m(120), "prompt_suffix": "Exploration of Rivendell gardens and halls. Everything is beautiful and ancient."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Festive meal with the elves. Fruits, sweet breads, and clear wines."},
        {"block_id": "pair_dialogue", "duration_hours": m(180), "prompt_suffix": "Conversation with elves or Gandalf about ancient stories and uncertain futures."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Contemplative pause beside a fountain or overlook."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Supper with elven music in the background. Wounds of body and soul heal slowly."},
        {"block_id": "cultural_ritual", "duration_hours": m(120), "prompt_suffix": "Elvish poetry recital, song, or dance. The dwarves watch with feigned respect."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The valley sleeps in starlight."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deep, restorative sleep, protected by the magic of the valley."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence in the halls of the Last Homely House."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Dreams of green valleys and distant mountains."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "An elf patrol passes without a sound."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last gentle hour before waking."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The valley sleeps under a blanket of stars."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "A last dream of distant mountains."},
    ],
    "rivendell_winter_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Waking to snow on the windowsill. The fire was lit by silent elves."},
        {"block_id": "individual_task", "duration_hours": m(180), "prompt_suffix": "Bilbo writes in his diary. Others read, play games, or simply gaze at the fire."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Light midday meal. Slow conversations about nothing in particular."},
        {"block_id": "pair_dialogue", "duration_hours": m(180), "prompt_suffix": "Quiet chat by the fire. Memories of the war, worries about the future."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Pause of snow and silence. The world outside seems frozen in time."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Early supper. The food is simple but comforting."},
        {"block_id": "cultural_ritual", "duration_hours": m(120), "prompt_suffix": "Evening of stories, poems, or improvised board games between dwarves and elves."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "Ritual night round. There is no danger, but the elves keep watch."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The valley sleeps under snow."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Long, heavy sleep. Sometimes dreams of Erebor, sometimes of Hobbiton."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence in the snow-covered halls."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deeper sleep before the pale winter dawn."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "An elf guard shifts silently in the corridor."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last warm hour before waking."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Snow falls softly outside the window."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last peaceful hour before the winter dawn."},
    ],
    "rivendell_farewell_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(60), "prompt_suffix": "Waking knowing the Rivendell days are ending."},
        {"block_id": "exploration", "duration_hours": m(240), "prompt_suffix": "Last walk through the valley's favorite gardens and paths."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Farewell meal with the elf-friends they made during the winter."},
        {"block_id": "pair_dialogue", "duration_hours": m(180), "prompt_suffix": "Farewell conversations with Elrond, Gandalf, or elf-friends. Promises to return."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Moment of solitude contemplating the valley one last time."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Emotional supper. Exchange of small gifts between dwarves and elves."},
        {"block_id": "cultural_ritual", "duration_hours": m(120), "prompt_suffix": "Last elvish song. The dwarves applaud with genuine respect."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The valley breathes quietly beneath the stars."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Light sleep. The packs are ready by the door."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence in the guest rooms."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "Half-dreams of roads already walked."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "An elf stands guard over the sleeping travellers."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last gentle hour before the farewell morning."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The valley breathes quietly beneath farewell stars."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "A last dream of Rivendell gardens."},
    ],
    "wet_road_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Waking under grey skies. The rain soaked everything during the night."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "Slow march under fine but persistent rain. Mud clings to the boots."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Rest beneath a large tree. They eat cold but gratefully."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "They keep walking. The landscape is green and humble, without great perils."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Supper in a clearing. The fire struggles to catch because of the damp wood."},
        {"block_id": "evening_ritual", "duration_hours": m(60), "prompt_suffix": "They set up camp with soaked cloaks and resigned complaints."},
        {"block_id": "cultural_ritual", "duration_hours": m(60), "prompt_suffix": "Sad farewell song of the wild roads."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Melancholy conversations about what they left behind and what awaits."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Sleep interrupted by leaks in the tent or by the damp cold."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The rain taps against the canvas through the night."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A sodden watchman stares into the dark."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deeper sleep despite the dripping water."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The rain slows to a whisper before dawn."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last damp hour before waking."},
    ],
    "familiar_road_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Waking with the sun. The road is gentler and familiar."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "Relaxed walk through rounded hills and friendly woods."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Rest in the shade of an oak. Spirits lift with the good weather."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "They continue at a good pace. They recognize the landscape more and more."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Evening meal with laughter and jokes about what they will do upon arrival."},
        {"block_id": "evening_ritual", "duration_hours": m(60), "prompt_suffix": "Quiet camp. There is no need to watch so closely."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Lively supper. The dwarves bet on who will reach home first."},
        {"block_id": "pair_dialogue", "duration_hours": m(60), "prompt_suffix": "Last nocturnal confidences before the final parting."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Peaceful sleep. Tomorrow they will be one day closer to the end."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The camp sleeps under familiar stars."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A brief watch out of habit rather than need."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deep sleep on safe ground."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The night is still and warm."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last easy hour before waking."},
    ],
    "shire_border_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Waking before dawn from excitement. Today they cross another border."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "They walk on roads that are no longer wild: orderly hedges, soft meadows."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Rest beside a crystal stream. The water tastes of home."},
        {"block_id": "ambient_pause", "duration_hours": m(240), "prompt_suffix": "The Hill of Hobbiton is visible in the distance. The pace quickens without anyone ordering it."},
        {"block_id": "group_meal", "duration_hours": m(60), "prompt_suffix": "Last shared meal before the final farewells."},
        {"block_id": "evening_ritual", "duration_hours": m(60), "prompt_suffix": "Camp in lands that are already the Shire. The dwarves observe with curiosity."},
        {"block_id": "pair_dialogue", "duration_hours": m(120), "prompt_suffix": "Final confessions, promises to visit, and the recognition of an unbreakable fellowship."},
        {"block_id": "cultural_ritual", "duration_hours": m(60), "prompt_suffix": "Dwarven farewell song dedicated to Bilbo. He does not know whether to laugh or cry."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Light sleep of expectation. Tomorrow they arrive."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The Shire sleeps peacefully around the camp."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "A last watch in friendly lands."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Dreams of Bag End and the auction."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The night is soft and full of summer smells."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last hour before the final morning."},
    ],
    "homecoming_day": [
        {"block_id": "wake_and_ritual", "duration_hours": m(120), "prompt_suffix": "Waking on the edge of Hobbiton. The last day of the journey."},
        {"block_id": "exploration", "duration_hours": m(240), "prompt_suffix": "Arrival in Hobbiton. Surprised folk, the auction in progress, the Sackville-Bagginses bewildered."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "Reunion meal with old acquaintances, or solitude amid the curious crowd."},
        {"block_id": "pair_dialogue", "duration_hours": m(240), "prompt_suffix": "Explanations, awkward embraces, and the reclaiming of Bag End."},
        {"block_id": "group_meal", "duration_hours": m(120), "prompt_suffix": "First real supper at home. Something simple but perfect."},
        {"block_id": "inner_monologue", "duration_hours": m(60), "prompt_suffix": "Bilbo alone in his parlour. Everything is the same and everything is different."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Silence of peace. The clock on the mantelpiece ticks. The journey has ended."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "First true night of sleep in one's own bed. No guards, no dragons, no mountains."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "Bag End breathes softly in the dark."},
        {"block_id": "night_watch", "duration_hours": m(60), "prompt_suffix": "Bilbo wakes briefly, remembering old fears, then smiles and sleeps again."},
        {"block_id": "restless_sleep", "duration_hours": m(120), "prompt_suffix": "Deep sleep of the returned traveller."},
        {"block_id": "ambient_pause", "duration_hours": m(60), "prompt_suffix": "The Shire night is quiet and safe."},
        {"block_id": "restless_sleep", "duration_hours": m(60), "prompt_suffix": "The last peaceful hour before a normal morning."},
    ],
}

LONG_GAP_ARCHETYPES = {
    "gap_canon_044_canon_045": {
        "title": "The Long Captivity",
        "location": "Elvenking's Halls",
        "phases": [
            {"phase_id": "captivity_fall", "title": "Act I: The Fall", "days": 7, "mood": "fear", "day_pattern": "dungeon_day",
             "special_events": [
                 {"day": 1, "title": "Disarming and separation", "prompt": "Los elfos quitan armas y separan a la Compañía. Thorin protesta. Bilbo, invisible, observa desde un rincón.", "update_mode": "event"},
                 {"day": 3, "title": "Thorin to the deepest cell", "prompt": "Thorin es arrastrado a la celda más profunda. Los demás enanos lo ven irse en silencio impotente.", "update_mode": "event"},
                 {"day": 5, "title": "Bilbo discovers freedom", "prompt": "Bilbo se da cuenta de que su invisibilidad le permite moverse entre las celdas sin ser detectado. Una mezcla de pánico y esperanza.", "update_mode": "mixed"},
             ]},
            {"phase_id": "captivity_routine", "title": "Act II-III: The Long Routine", "days": 83, "mood": "monotony", "day_pattern": "prison_routine_day",
             "special_events": [
                 {"day": 22, "title": "Distant elf feast", "prompt": "Los elfos celebran una gran fiesta. Música y luces llegan hasta las celdas. Los enanos sienten envidia, repulsión y hambre.", "update_mode": "mixed"},
                 {"day": 45, "title": "Season change", "prompt": "Un cambio de temperatura anuncia el paso del tiempo. Alguien cuenta los días y se equivoca.", "update_mode": "ambiental"},
                 {"day": 68, "title": "Bilbo contacts all dwarves", "prompt": "Bilbo ha logrado susurrar a cada enano al menos una vez. La red de comunicación está completa.", "update_mode": "chat"},
             ]},
            {"phase_id": "captivity_planning", "title": "Act IV: The Plan", "days": 25, "mood": "rising_hope", "day_pattern": "planning_day",
             "special_events": [
                 {"day": 12, "title": "The barrel idea", "prompt": "Bilbo propone escapar en barriles por la Puerta del Agua. Al principio parece absurdo; luego, la única opción.", "update_mode": "chat"},
             ]},
            {"phase_id": "captivity_escape", "title": "Act V: Escape Eve", "days": 13, "mood": "thriller", "day_pattern": "escape_eve_day",
             "special_events": [
                 {"day": 10, "title": "The right night", "prompt": "Todo está listo. Esperan la noche correcta: luna nueva, guardias distraídos, fiesta de despedida de los elfos.", "update_mode": "mixed"},
             ]},
        ],
    },
    "gap_canon_064_canon_065": {
        "title": "The Siege of Silence",
        "location": "Erebor",
        "phases": [
            {"phase_id": "smaug_departure", "title": "Act I: The Departure", "days": 1, "mood": "terror", "day_pattern": "dragon_departure_day",
             "special_events": [
                 {"day": 1, "title": "Smaug rises", "prompt": "Smaug despierta en furia, destruye una estalactita con su cola, y vuela hacia el sur en una columna de fuego. El silencio que sigue es peor que el ruido.", "update_mode": "event"},
             ]},
            {"phase_id": "siege_wait", "title": "Act II-III: The Wait", "days": 12, "mood": "paranoia", "day_pattern": "siege_day",
             "special_events": [
                 {"day": 4, "title": "Distant roar", "prompt": "Un eco lejano de rugido resuena desde el sur. Todos se congelan. No vuelve a repetirse.", "update_mode": "event"},
                 {"day": 7, "title": "Crow brings rumors", "prompt": "Un cuervo negro llega a la entrada de Erebor con noticias confusas: humo al sur, pánico en el lago.", "update_mode": "mixed"},
                 {"day": 9, "title": "Debate to leave", "prompt": "Fili y Kili insisten en salir a ayudar. Thorin se niega rotundamente. La tensión casi rompe el grupo.", "update_mode": "chat"},
             ]},
            {"phase_id": "smaug_confirmed_dead", "title": "Act IV: Confirmation", "days": 3, "mood": "aftermath", "day_pattern": "aftermath_eve_day",
             "special_events": [
                 {"day": 2, "title": "Lake-town burns", "prompt": "La luz roja del sur ya no es un atardecer: es el resplandor de una ciudad en llamas. Nadie duerme.", "update_mode": "ambiental"},
                 {"day": 3, "title": "Smaug is dead", "prompt": "La noticia llega de forma inequívoca: el dragón ha caído. Celebración contenida, luto por los muertos, y la sombra de la codicia que se avecina.", "update_mode": "event"},
             ]},
        ],
    },
    "gap_canon_093_canon_094": {
        "title": "Winter in Rivendell",
        "location": "Rivendell",
        "phases": [
            {"phase_id": "last_stretch", "title": "Act I: Last Stretch", "days": 10, "mood": "nostalgia", "day_pattern": "homeward_travel_day",
             "special_events": [
                 {"day": 4, "title": "Last night at Beorn's", "prompt": "Última cena con Beorn. Miel, pan recién horneado, y la compañía de animales que lo obedecen.", "update_mode": "chat"},
                 {"day": 10, "title": "Arrival at Rivendell", "prompt": "Cruzan el puente hacia Rivendell. Canciones élficas los reciben. El cansancio de meses empieza a disiparse.", "update_mode": "event"},
             ]},
            {"phase_id": "rivendell_welcome", "title": "Act II: Welcome", "days": 20, "mood": "warmth", "day_pattern": "rivendell_welcome_day",
             "special_events": [
                 {"day": 5, "title": "Elf concert", "prompt": "Un concierto nocturno en el salón de Elrond. Música que cura heridas invisibles.", "update_mode": "mixed"},
                 {"day": 12, "title": "Gandalf's whispered news", "prompt": "Gandalf habla en voz baja con Elrond sobre Dol Guldur. Bilbo escucha a medias, sin entender del todo.", "update_mode": "mixed"},
                 {"day": 18, "title": "Healing of wounds", "prompt": "Fili y Kili reciben atención médica por heridas que habían ocultado. Thorin observa con culpa.", "update_mode": "event"},
             ]},
            {"phase_id": "rivendell_winter", "title": "Act III: Deep Winter", "days": 110, "mood": "stillness", "day_pattern": "rivendell_winter_day",
             "special_events": [
                 {"day": 25, "title": "Bilbo starts his book", "prompt": "Bilbo compra un cuaderno de pergamino y empieza a escribir las primeras líneas de 'There and Back Again'.", "update_mode": "mixed"},
                 {"day": 50, "title": "Moria tales by Balin", "prompt": "Una noche especialmente fría. Balin cuenta la historia de Moria con detalles que nunca había compartido.", "update_mode": "chat"},
                 {"day": 80, "title": "Thorin and Bilbo talk", "prompt": "Thorin y Bilbo caminan por los jardines helados. Hablan del oro, de la codicia, y del perdón. Un punto de inflexión silencioso.", "update_mode": "chat"},
                 {"day": 100, "title": "Bilbo finishes a chapter", "prompt": "Bilbo cierra el cuaderno satisfecho. Ha terminado el capítulo de las arañas. Un elfo le pregunta si es poesía.", "update_mode": "mixed"},
             ]},
            {"phase_id": "rivendell_farewell", "title": "Act IV: Farewell", "days": 20, "mood": "hope", "day_pattern": "rivendell_farewell_day",
             "special_events": [
                 {"day": 5, "title": "First thaw", "prompt": "El hielo del río empieza a agrietarse. Los elfos cantan canciones de primavera.", "update_mode": "ambiental"},
                 {"day": 15, "title": "Last feast with Elrond", "prompt": "Cena de despedida con Elrond. Regalos son intercambiados. Promesas de volver algún día.", "update_mode": "chat"},
                 {"day": 20, "title": "Departure west", "prompt": "La Compañía parte de Rivendell hacia el oeste. El sol de primavera ilumina el Alto Paso.", "update_mode": "event"},
             ]},
        ],
    },
    "gap_canon_094_canon_095": {
        "title": "The Final Journey Home",
        "location": "The Shire borders",
        "phases": [
            {"phase_id": "wet_road", "title": "Act I: Wet Road", "days": 20, "mood": "melancholy", "day_pattern": "wet_road_day",
             "special_events": [
                 {"day": 8, "title": "Trollshaws gold", "prompt": "Desentierran el oro que habían escondido en los Trollshaws. Algunos enanos quieren quedárselo todo; Bilbo insiste en repartirlo.", "update_mode": "chat"},
                 {"day": 12, "title": "Torrential rain", "prompt": "Una tormenta los obliga a refugiarse bajo un saliente de roca durante medio día. Nadie se queja demasiado.", "update_mode": "event"},
                 {"day": 15, "title": "Hobbit wanderer", "prompt": "Se cruzan con un hobbit errante que no reconoce a Bilbo. Este se da cuenta de cuánto ha cambiado su apariencia.", "update_mode": "mixed"},
             ]},
            {"phase_id": "familiar_road", "title": "Act II: Familiar Road", "days": 20, "mood": "friendship", "day_pattern": "familiar_road_day",
             "special_events": [
                 {"day": 5, "title": "Treasure division debate", "prompt": "Última discusión formal sobre el reparto del tesoro. Acuerdos firmados con el puño en el pecho.", "update_mode": "chat"},
                 {"day": 10, "title": "Gandalf announces departure", "prompt": "Gandalf anuncia que se separará de la Compañía antes de llegar a Hobbiton. Nadie se sorprende, pero todos sienten pesar.", "update_mode": "chat"},
                 {"day": 15, "title": "Bilbo gives gifts", "prompt": "Bilbo regala pequeños objetos de plata y esmeraldas a los enanos que lo acompañan hasta el final.", "update_mode": "event"},
             ]},
            {"phase_id": "shire_border", "title": "Act III: Shire Border", "days": 8, "mood": "eager", "day_pattern": "shire_border_day",
             "special_events": [
                 {"day": 3, "title": "First sight of the Hill", "prompt": "Desde una colina distante, ven la Colina de Hobbiton al atardecer. Bilbo se queda en silencio varios minutos.", "update_mode": "mixed"},
                 {"day": 5, "title": "Dwarves farewell", "prompt": "Los últimos enanos que no van a Hobbiton se despiden. Abrazos enanos: fuertes, breves, incómodos.", "update_mode": "event"},
                 {"day": 7, "title": "Gandalf and Bilbo alone", "prompt": "Gandalf y Bilbo caminan solos los últimos kilómetros. No hablan mucho. No necesitan hacerlo.", "update_mode": "chat"},
             ]},
            {"phase_id": "homecoming", "title": "Act IV: Homecoming", "days": 4, "mood": "climax", "day_pattern": "homecoming_day",
             "special_events": [
                 {"day": 1, "title": "Arrival at Hobbiton", "prompt": "Llegan a Hobbiton. Los hobbits los miran con curiosidad. Bilbo reconoce cada casa, cada árbol, cada olor.", "update_mode": "event"},
                 {"day": 2, "title": "The auction", "prompt": "Bilbo descubre que sus parientes los Sackville-Baggins están vendiendo sus pertenencias. Confusión, ira contenida, y un toque de humor negro.", "update_mode": "chat"},
                 {"day": 4, "title": "Bag End at last", "prompt": "Bilbo entra solo a Bolsón Cerrado. Está vacío, pero es suyo. Enciende la chimenea y se sienta en su sillón favorito.", "update_mode": "mixed"},
             ]},
        ],
    },
}


def make_phase_node(phase: dict, gap_hours: float, canon_constraints: List[str], next_title: str) -> Dict[str, Any]:
    days = phase["days"]
    hours = days * 24
    pattern_id = phase["day_pattern"]
    schedule = DAY_PATTERNS.get(pattern_id, [])
    node = make_node(
        "phase",
        phase["title"],
        hours,
        phase_id=phase["phase_id"],
        day_pattern=pattern_id,
        day_pattern_schedule=schedule,
        days=days,
        mood=phase["mood"],
        prompt=(
            f"Esta fase dura {days} días. El tono general es '{phase['mood']}'. "
            f"Cada día sigue el patrón '{pattern_id}', generando bloques de chat, evento y pausa ambiental según la hora. "
            f"NO adelantes eventos de '{next_title}'. "
            f"Los eventos especiales de esta fase deben ocurrir en los días indicados y sustituir un bloque normal."
        ),
        canon_constraints=canon_constraints,
        special_events=phase.get("special_events", []),
    )
    return node


def plan_long_gap(gap_id: str, prev_state: dict, next_state: dict, total_hours: float) -> Dict[str, Any]:
    """Gaps >10 days: phase-based narrative arcs with day patterns."""
    canon_constraints = build_canon_constraints(prev_state, next_state)
    archetype = LONG_GAP_ARCHETYPES.get(gap_id)

    if not archetype:
        # Generic fallback
        arc = make_node("subplot", f"Long Gap: {prev_state['title']} → {next_state['title']}", total_hours)
        arc["children"].append(make_node(
            "beat", "Compressed long-gap narration", total_hours,
            update_mode="ambiental",
            prompt="Narración comprimida de gap largo.",
            canon_constraints=canon_constraints,
        ))
        return arc

    arc = make_node("subplot", archetype["title"], total_hours)
    arc["children"] = []

    allocated = 0
    for phase in archetype["phases"]:
        node = make_phase_node(phase, total_hours, canon_constraints, next_state.get('title', 'the next scene'))
        arc["children"].append(node)
        allocated += node["duration_hours"]

    remainder = total_hours - allocated
    if remainder > 0.5:
        arc["children"].append(make_node(
            "beat", "Closing transition", remainder,
            update_mode="ambiental",
            prompt=f"Transición final hacia '{next_state.get('title', 'the next scene')}'.",
            canon_constraints=canon_constraints,
        ))

    return arc


# ─────────────────────── Remaining Gap Types ───────────────────────

def plan_micro_gap(gap_id: str, prev_state: dict, next_state: dict, total_hours: float) -> Dict[str, Any]:
    """Gaps of up to ~3 hours: immediate transitions, brief pauses, short conversations."""
    arc = make_node("subplot", f"Bridge: {prev_state['title']} → {next_state['title']}", total_hours)
    canon_constraints = build_canon_constraints(prev_state, next_state)
    location = prev_state['state_out']['characters'].get('Bilbo', {}).get('location', 'unknown')
    present = [n for n, d in prev_state.get('state_out', {}).get('characters', {}).items()
               if d.get('location') == location and d.get('status') != 'dead']
    if not present:
        present = ["Bilbo"]

    same_loc = prev_state['state_out']['characters'].get('Bilbo', {}).get('location') == \
               next_state['state_in']['characters'].get('Bilbo', {}).get('location')

    if same_loc:
        if total_hours <= 1.5:
            arc["children"].append(make_node(
                "beat", "Immediate Continuation", total_hours,
                update_mode="mixed",
                prompt=f"Transición inmediata en {location} hacia '{next_state.get('title')}'. "
                       f"Personajes presentes: {', '.join(present[:5])}.",
                canon_constraints=canon_constraints,
            ))
        else:
            c = split_duration(total_hours, 2)
            arc["children"].extend([
                make_node("beat", "Moment of Pause", c[0],
                    update_mode="mixed",
                    prompt=f"Pausa breve en {location}. Conversación ligera o silencio compartido.",
                    canon_constraints=canon_constraints,
                ),
                make_node("beat", "Resuming", c[1],
                    update_mode="mixed",
                    prompt=f"La acción se reanuda en {location} antes de '{next_state.get('title')}'.",
                    canon_constraints=canon_constraints,
                ),
            ])
    else:
        chunks = split_duration(total_hours, 3)
        seq = make_node("sequence", "Short Transition", sum(chunks))
        seq["children"] = [
            make_node("beat", "Breaking Camp / Gathering", chunks[0],
                update_mode="event",
                prompt="Preparativos para moverse. Recoger equipaje.",
                canon_constraints=canon_constraints,
            ),
            make_node("beat", "Brief Walk", chunks[1],
                update_mode="ambiental",
                prompt="Caminata corta entre ubicaciones. Descripción del terreno.",
                canon_constraints=canon_constraints,
            ),
            make_node("beat", "Arrival and Adjustment", chunks[2],
                update_mode="mixed",
                prompt="Llegada al nuevo lugar. Reconocimiento del entorno.",
                canon_constraints=canon_constraints,
            ),
        ]
        arc["children"].append(seq)
    return arc


def plan_travel_gap(gap_id: str, prev_state: dict, next_state: dict, total_hours: float) -> Dict[str, Any]:
    """Gaps of 1–10 days: march, camp, night watch cycles."""
    arc = make_node("subplot", f"Travel: {prev_state['title']} → {next_state['title']}", total_hours)
    canon_constraints = build_canon_constraints(prev_state, next_state)
    duration_days = total_hours / 24.0
    num_days = max(1, int(duration_days))

    dep_hours = min(8, total_hours * 0.25)
    if dep_hours >= 1:
        c = split_duration(dep_hours, 3)
        departure = make_node("sequence", "Departure", sum(c))
        departure["children"] = [
            make_node("beat", "Preparing to leave", c[0],
                update_mode="event", prompt="Preparativos de marcha.", canon_constraints=canon_constraints),
            make_node("beat", "Morning march", c[1],
                update_mode="ambiental", prompt="Primera etapa de la marcha.", canon_constraints=canon_constraints),
            make_node("beat", "Midday rest", c[2],
                update_mode="mixed", prompt="Descanso breve a medio camino.", canon_constraints=canon_constraints),
        ]
        arc["children"].append(departure)

    remaining = total_hours - dep_hours

    if remaining > 16:
        mid_hours = remaining - min(8, remaining * 0.25)
        approach_hours = remaining - mid_hours
        middle_days = max(1, math.ceil(mid_hours / 24))
        if middle_days >= 1:
            middle = make_node("subplot", f"Days on the Road ({middle_days}d)", mid_hours)
            for d in range(middle_days):
                day_h = min(24, mid_hours - d * 24)
                if day_h <= 0:
                    break
                day_arc = make_node("sequence", f"Day {d + 2} of Travel", day_h)
                # 6 blocks of 4.0h for a full 24h day, or fewer for partial days
                num_beats = 6 if day_h >= 24 else max(3, int(day_h / 4))
                beats = split_duration(day_h, num_beats)
                beat_templates = [
                    ("Morning march", "ambiental", "Marcha matutina."),
                    ("Afternoon march", "ambiental", "Marcha vespertina."),
                    ("Making camp", "event", "Montar campamento."),
                    ("Evening meal and conversation", "chat", "Cena y conversación en el campamento."),
                    ("Night watches", "ambiental", "Vigilias nocturnas."),
                    ("Late night rest", "ambiental", "Descanso nocturno en el campamento."),
                ]
                day_arc["children"] = [
                    make_node("beat", beat_templates[i][0], beats[i],
                              update_mode=beat_templates[i][1], prompt=beat_templates[i][2], canon_constraints=canon_constraints)
                    for i in range(min(num_beats, len(beat_templates)))
                ]
                middle["children"].append(day_arc)
            arc["children"].append(middle)
        else:
            approach_hours = remaining
    else:
        approach_hours = remaining

    if approach_hours >= 1:
        c = split_duration(min(8, approach_hours), 3)
        approach = make_node("sequence", "Approach", sum(c))
        approach["children"] = [
            make_node("beat", "Early start", c[0], update_mode="mixed", prompt="Salida temprana.", canon_constraints=canon_constraints),
            make_node("beat", "Final stretch", c[1], update_mode="ambiental", prompt="Último tramo antes del destino.", canon_constraints=canon_constraints),
            make_node("beat", "Arrival at destination", c[2], update_mode="event", prompt="Llegada al destino final.", canon_constraints=canon_constraints),
        ]
        arc["children"].append(approach)

    used = sum(c["duration_hours"] for c in arc["children"])
    remainder = total_hours - used
    if remainder > 0.5:
        arc["children"].append(make_node("beat", "Unaccounted hours / rests", remainder,
            update_mode="ambiental", prompt="Tiempo no especificado.", canon_constraints=canon_constraints))

    return arc


# ─────────────────────── Main Dispatch ───────────────────────

def plan_gap(prev_state: dict, next_state: dict) -> Dict[str, Any]:
    gap_id = f"gap_{prev_state['scene_id']}_{next_state['scene_id']}"

    gap_hours = (next_state['journey_day'] - prev_state['journey_day'] - 1) * 24 \
                + (24 - prev_state['end_hour']) + next_state['start_hour']
    gap_hours = round(max(0.0, gap_hours), 2)

    if gap_hours <= 0.1:
        return {
            "gap_id": gap_id,
            "from_scene_id": prev_state['scene_id'],
            "to_scene_id": next_state['scene_id'],
            "from_title": prev_state['title'],
            "to_title": next_state['title'],
            "duration_hours": 0,
            "gap_type": "none",
            "state_in_snapshot": {
                "location": prev_state['state_out']['characters'].get('Bilbo', {}).get('location', 'unknown'),
                "date_iso": prev_state['state_out'].get('date_iso'),
                "company_members": prev_state['state_out']['company']['members'],
            },
            "state_out_snapshot": {
                "location": next_state['state_in']['characters'].get('Bilbo', {}).get('location', 'unknown'),
                "date_iso": next_state['state_in'].get('date_iso'),
                "company_members": next_state['state_in']['company']['members'],
            },
            "arc": None,
        }

    duration_days = gap_hours / 24.0

    if duration_days > 10:
        arc = plan_long_gap(gap_id, prev_state, next_state, gap_hours)
        gap_type = "long"
    elif duration_days > 1:
        arc = plan_travel_gap(gap_id, prev_state, next_state, gap_hours)
        gap_type = "travel"
    elif gap_hours > 3:
        arc = compose_small_gap(prev_state, next_state, gap_hours)
        gap_type = "small"
    else:
        arc = plan_micro_gap(gap_id, prev_state, next_state, gap_hours)
        gap_type = "micro"

    return {
        "gap_id": gap_id,
        "from_scene_id": prev_state['scene_id'],
        "to_scene_id": next_state['scene_id'],
        "from_title": prev_state['title'],
        "to_title": next_state['title'],
        "duration_hours": gap_hours,
        "gap_type": gap_type,
        "state_in_snapshot": {
            "location": prev_state['state_out']['characters'].get('Bilbo', {}).get('location', 'unknown'),
            "date_iso": prev_state['state_out'].get('date_iso'),
            "company_members": prev_state['state_out']['company']['members'],
        },
        "state_out_snapshot": {
            "location": next_state['state_in']['characters'].get('Bilbo', {}).get('location', 'unknown'),
            "date_iso": next_state['state_in'].get('date_iso'),
            "company_members": next_state['state_in']['company']['members'],
        },
        "arc": arc,
    }


# ─────────────────────── Entry Point ───────────────────────

def main():
    canonical_states = load_data()
    gap_plans = []

    for i in range(1, len(canonical_states)):
        prev = canonical_states[i - 1]
        nxt = canonical_states[i]
        plan = plan_gap(prev, nxt)
        gap_plans.append(plan)

    summary = {
        "total_gaps": len(gap_plans),
        "none_gaps": sum(1 for g in gap_plans if g["gap_type"] == "none"),
        "micro_gaps": sum(1 for g in gap_plans if g["gap_type"] == "micro"),
        "small_gaps": sum(1 for g in gap_plans if g["gap_type"] == "small"),
        "travel_gaps": sum(1 for g in gap_plans if g["gap_type"] == "travel"),
        "long_gaps": sum(1 for g in gap_plans if g["gap_type"] == "long"),
        "estimated_total_hours": round(sum(g["duration_hours"] for g in gap_plans), 1),
    }

    output = {
        "meta": summary,
        "gaps": gap_plans,
    }

    with open('data/gap_plans.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Generated {summary['total_gaps']} gap plans.")
    print(f"  None (<=0.1h):  {summary['none_gaps']}")
    print(f"  Micro (<=3h):   {summary['micro_gaps']}")
    print(f"  Small (3-24h):  {summary['small_gaps']}")
    print(f"  Travel (1-10d): {summary['travel_gaps']}")
    print(f"  Long (>10d):    {summary['long_gaps']}")
    print(f"  Total narrative hours: {summary['estimated_total_hours']}")


if __name__ == "__main__":
    main()
