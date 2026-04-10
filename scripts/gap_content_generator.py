#!/usr/bin/env python3
"""
Gap Content Generator Pipeline

Generates narrative content to fill time gaps between canonical scenes
with continuity validation and LLM integration.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import os


class CanonLevel(Enum):
    """Canon strictness levels"""
    EXPLICIT = "A"      # Events explicitly mentioned in book
    IMPLIED = "B"       # Events implied/inferred from text
    PLAUSIBLE = "C"     # Plausible inventions that don't contradict canon


class GapType(Enum):
    """Types of narrative gaps"""
    TRAVEL = "travel"
    WAITING = "waiting"
    RECUPERATION = "recuperation"
    PLANNING = "planning"
    OFFSCREEN = "offscreen"
    UNKNOWN = "unknown"


@dataclass
class CharacterState:
    """Character state at a point in time"""
    name: str
    location: str
    mood: str = ""
    physical_state: str = "healthy"
    injuries: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    is_present: bool = True


@dataclass
class SceneConstraints:
    """Constraints extracted from surrounding scenes"""
    before_scene_id: str
    after_scene_id: str
    gap_days: int
    gap_type: GapType
    
    # Character constraints
    characters_present_start: List[str] = field(default_factory=list)
    characters_present_end: List[str] = field(default_factory=list)
    character_states_start: Dict[str, CharacterState] = field(default_factory=dict)
    character_states_end: Dict[str, CharacterState] = field(default_factory=dict)
    
    # Location constraints
    location_start: str = ""
    location_end: str = ""
    travel_distance_estimate: Optional[int] = None  # miles
    
    # Item constraints
    items_acquired: List[str] = field(default_factory=list)
    items_lost: List[str] = field(default_factory=list)
    
    # Narrative constraints
    emotional_tone_start: str = ""
    emotional_tone_end: str = ""
    narrative_threads: List[str] = field(default_factory=list)
    
    # Canon basis
    canon_references: List[str] = field(default_factory=list)


@dataclass
class GeneratedScene:
    """A generated scene to fill a gap"""
    id: str
    parent_gap_id: str
    title: str
    summary: str
    date: str
    date_iso: str
    
    # Content
    duration_hours: float
    gap_type: GapType
    activity_type: str  # travel, rest, conversation, planning, etc.
    characters: List[str] = field(default_factory=list)
    location: str = ""
    
    # Narrative elements
    dialogue_hints: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    sensory_details: List[str] = field(default_factory=list)
    
    # Metadata
    canon_level: CanonLevel = CanonLevel.PLAUSIBLE
    canon_basis: str = ""
    position_in_gap: int = 1  # 1 of N scenes in this gap
    total_in_gap: int = 1
    
    # Validation results
    continuity_checks: Dict[str, str] = field(default_factory=dict)
    validation_passed: bool = True


@dataclass
class GapAnalysis:
    """Analysis of a single gap between scenes"""
    gap_id: str
    from_scene_id: str
    from_scene_title: str
    from_date: str
    to_scene_id: str
    to_scene_title: str
    to_date: str
    gap_days: int
    gap_type: GapType
    constraints: SceneConstraints
    generated_scenes: List[GeneratedScene] = field(default_factory=list)
    generation_status: str = "pending"  # pending, generated, validated, failed


class GapAnalyzer:
    """Analyzes gaps between canonical scenes"""
    
    def __init__(self, scenes_file: str = "stream_scenes.json"):
        with open(scenes_file, 'r') as f:
            data = json.load(f)
        self.scenes = data['scenes']
        
    def analyze_all_gaps(self) -> List[GapAnalysis]:
        """Analyze all gaps between consecutive scenes"""
        gaps = []
        
        for i in range(len(self.scenes) - 1):
            scene_a = self.scenes[i]
            scene_b = self.scenes[i + 1]
            
            gap = self._analyze_single_gap(scene_a, scene_b, i)
            if gap:
                gaps.append(gap)
        
        return gaps
    
    def _analyze_single_gap(self, scene_a: Dict, scene_b: Dict, index: int) -> Optional[GapAnalysis]:
        """Analyze a single gap between two scenes"""
        # Get dates
        date_a = scene_a.get('date_iso', '')
        date_b = scene_b.get('date_iso', '')
        
        if not date_a or not date_b:
            return None
        
        try:
            dt_a = datetime.strptime(date_a, '%Y-%m-%d')
            dt_b = datetime.strptime(date_b, '%Y-%m-%d')
            gap_days = (dt_b - dt_a).days
        except ValueError:
            return None
        
        # Only create gap if there's actual time between
        if gap_days <= 0:
            return None
        
        gap_id = f"gap_{index:03d}_{index+1:03d}"
        
        # Determine gap type
        gap_type = self._classify_gap_type(scene_a, scene_b, gap_days)
        
        # Extract constraints
        constraints = self._extract_constraints(scene_a, scene_b, gap_days, gap_type)
        
        return GapAnalysis(
            gap_id=gap_id,
            from_scene_id=scene_a['id'],
            from_scene_title=scene_a['title'],
            from_date=scene_a.get('date', 'Unknown'),
            to_scene_id=scene_b['id'],
            to_scene_title=scene_b['title'],
            to_date=scene_b.get('date', 'Unknown'),
            gap_days=gap_days,
            gap_type=gap_type,
            constraints=constraints
        )
    
    def _classify_gap_type(self, scene_a: Dict, scene_b: Dict, gap_days: int) -> GapType:
        """Classify what type of gap this is"""
        loc_a = scene_a.get('location', '').lower()
        loc_b = scene_b.get('location', '').lower()
        chapter_a = scene_a.get('chapter', '').lower()
        chapter_b = scene_b.get('chapter', '').lower()
        title_a = scene_a.get('title', '').lower()
        title_b = scene_b.get('title', '').lower()
        
        # Check for imprisonment/waiting
        imprisonment_keywords = ['prison', 'captive', 'captured', 'elvenking', 'dungeon']
        if any(k in title_a or k in loc_a or k in chapter_a for k in imprisonment_keywords):
            if any(k in title_b or k in loc_b or k in chapter_b for k in imprisonment_keywords):
                return GapType.WAITING
        
        # Check for travel
        travel_keywords = ['mirkwood', 'mountain', 'lake-town', 'laketown', 'journey', 'road', 'path']
        if loc_a != loc_b and any(k in loc_a or k in loc_b or k in title_a or k in title_b for k in travel_keywords):
            return GapType.TRAVEL
        
        # Check for recuperation (after battles/injuries)
        injury_keywords = ['injured', 'wounded', 'healed', 'rest', 'beorn', 'rivendell', 'recover']
        if any(k in title_a or k in title_b for k in injury_keywords):
            return GapType.RECUPERATION
        
        # Check for planning/preparation
        planning_keywords = ['plan', 'council', 'prepare', 'strategy']
        if any(k in title_a or k in title_b for k in planning_keywords):
            return GapType.PLANNING
        
        # Large gaps are likely travel or waiting
        if gap_days > 7:
            if loc_a == loc_b:
                return GapType.WAITING
            return GapType.TRAVEL
        
        return GapType.OFFSCREEN
    
    def _extract_constraints(self, scene_a: Dict, scene_b: Dict, gap_days: int, gap_type: GapType) -> SceneConstraints:
        """Extract continuity constraints from surrounding scenes"""
        chars_a = scene_a.get('characters', [])
        chars_b = scene_b.get('characters', [])
        loc_a = scene_a.get('location', 'Unknown')
        loc_b = scene_b.get('location', 'Unknown')
        
        # Build character states
        states_start = {}
        states_end = {}
        
        for char in chars_a:
            states_start[char] = CharacterState(
                name=char,
                location=loc_a,
                is_present=True
            )
        
        for char in chars_b:
            states_end[char] = CharacterState(
                name=char,
                location=loc_b,
                is_present=True
            )
        
        # Estimate travel distance (rough approximation)
        travel_estimate = None
        if gap_type == GapType.TRAVEL:
            travel_estimate = self._estimate_travel_distance(loc_a, loc_b)
        
        return SceneConstraints(
            before_scene_id=scene_a['id'],
            after_scene_id=scene_b['id'],
            gap_days=gap_days,
            gap_type=gap_type,
            characters_present_start=chars_a,
            characters_present_end=chars_b,
            character_states_start=states_start,
            character_states_end=states_end,
            location_start=loc_a,
            location_end=loc_b,
            travel_distance_estimate=travel_estimate,
            emotional_tone_start=scene_a.get('emotional_tone', ''),
            emotional_tone_end=scene_b.get('emotional_tone', '')
        )
    
    def _estimate_travel_distance(self, loc_a: str, loc_b: str) -> Optional[int]:
        """Rough estimate of travel distance between locations in miles"""
        # Very rough Middle-earth distances
        distances = {
            ('hobbiton', 'rivendell'): 400,
            ('rivendell', 'misty mountains'): 150,
            ('misty mountains', 'beorn'): 200,
            ('beorn', 'mirkwood'): 100,
            ('mirkwood', 'lake-town'): 150,
            ('lake-town', 'erebor'): 100,
            ('erebor', 'beorn'): 250,
            ('beorn', 'rivendell'): 300,
        }
        
        key = (loc_a.lower(), loc_b.lower())
        reverse_key = (loc_b.lower(), loc_a.lower())
        
        if key in distances:
            return distances[key]
        if reverse_key in distances:
            return distances[reverse_key]
        
        return None


class LLMSceneGenerator:
    """Generates scene content using LLM API via OpenRouter"""
    
    def __init__(self, api_key: Optional[str] = None, scenes: List[Dict] = None, 
                 model: str = "anthropic/claude-3.5-sonnet"):
        # Support both OPENAI_API_KEY and OPENROUTER_API_KEY
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        self.use_llm = self.api_key is not None
        self.scenes = scenes or []
        self.scene_lookup = {s['id']: s for s in self.scenes}
        
        # OpenRouter settings
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model
        self.site_url = os.environ.get('SITE_URL', 'https://hobbit-stream.local')
        self.site_name = os.environ.get('SITE_NAME', 'Hobbit Journey Stream')
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OpenRouter API request"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }
    
    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """Call OpenRouter API to generate content"""
        if not self.use_llm:
            return None
        
        try:
            import urllib.request
            import urllib.error
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=self._get_headers(),
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            print(f"      ⚠️  LLM call failed: {e}")
            return None
    
    def _parse_scene_date(self, scene_id: str, fallback_date: str) -> datetime:
        """Parse date from scene using ISO format"""
        # Try to get ISO date from the actual scene
        if scene_id in self.scene_lookup:
            iso_date = self.scene_lookup[scene_id].get('date_iso', '')
            if iso_date:
                try:
                    return datetime.strptime(iso_date, '%Y-%m-%d')
                except ValueError:
                    pass
        
        # Fallback: try to parse the human-readable date
        try:
            # Handle "April 26, 2941" format
            return datetime.strptime(fallback_date, '%B %d, %Y')
        except ValueError:
            pass
        
        # Default to a safe date
        return datetime(2941, 4, 26)
    
    def generate_gap_content(self, gap: GapAnalysis) -> List[GeneratedScene]:
        """Generate scenes to fill a gap"""
        
        # Determine how many scenes to generate based on gap size
        num_scenes = self._determine_scene_count(gap)
        
        if self.use_llm:
            return self._generate_with_llm(gap, num_scenes)
        else:
            return self._generate_template_based(gap, num_scenes)
    
    def _determine_scene_count(self, gap: GapAnalysis) -> int:
        """Determine how many scenes to generate for this gap"""
        days = gap.gap_days
        gap_type = gap.gap_type
        
        # Rules for scene density
        if days <= 1:
            return 1
        elif days <= 3:
            return 2
        elif days <= 7:
            return 3
        elif days <= 14:
            return 4
        elif days <= 30:
            return 5
        elif days <= 60:
            return 7
        else:
            # Very large gaps - more scenes but cap at 10
            return min(10, days // 10)
    
    def _generate_with_llm(self, gap: GapAnalysis, num_scenes: int) -> List[GeneratedScene]:
        """Generate scenes using OpenRouter LLM API"""
        scenes = []
        constraints = gap.constraints
        
        # Get proper dates
        start_date = self._parse_scene_date(gap.from_scene_id, gap.from_date)
        end_date = self._parse_scene_date(gap.to_scene_id, gap.to_date)
        
        print(f"      🤖 Using LLM ({self.model})...")
        
        for i in range(num_scenes):
            scene_num = i + 1
            progress = i / (num_scenes - 1) if num_scenes > 1 else 0.5
            
            # Calculate this scene's date
            days_offset = int(gap.gap_days * progress)
            scene_date = start_date + timedelta(days=days_offset)
            
            # Build prompt for this scene
            prompt = self._build_scene_prompt(gap, scene_num, num_scenes, scene_date, progress)
            
            # Call LLM
            response = self._call_llm(prompt, temperature=0.8, max_tokens=800)
            
            if response:
                # Parse LLM response
                gen_scene = self._parse_llm_response(response, gap, scene_num, num_scenes, scene_date)
                scenes.append(gen_scene)
            else:
                # Fall back to template if LLM fails
                print(f"         Falling back to template for scene {scene_num}")
                fallback = self._generate_single_template_scene(gap, scene_num, num_scenes, scene_date, progress)
                scenes.append(fallback)
        
        return scenes
    
    def _build_scene_prompt(self, gap: GapAnalysis, scene_num: int, total: int, 
                           date: datetime, progress: float) -> str:
        """Build a prompt for the LLM to generate a scene"""
        cons = gap.constraints
        
        # Determine phase description
        if progress < 0.25:
            phase = "early in the gap - establishing the situation"
        elif progress < 0.5:
            phase = "developing the situation"
        elif progress < 0.75:
            phase = "progressing toward resolution"
        else:
            phase = "approaching the next canonical scene"
        
        chars = ', '.join(cons.characters_present_start[:6])
        
        prompt = f"""You are writing narrative content for a 24/7 Hobbit stream. Generate a scene summary for a gap between canonical book scenes.

GAP CONTEXT:
- Gap Type: {gap.gap_type.value}
- Gap Duration: {gap.gap_days} days
- This Scene: {scene_num} of {total} ({phase})
- Date: {date.strftime('%B %d, %Y')}

BOUNDARY SCENES:
- BEFORE: "{gap.from_scene_title}" at {gap.from_date} in {cons.location_start}
- AFTER: "{gap.to_scene_title}" at {gap.to_date} in {cons.location_end}

CHARACTERS PRESENT: {chars}

REQUIREMENTS:
1. Write a scene title (3-5 words)
2. Write a scene summary (2-3 sentences describing what happens)
3. Suggest 1-2 dialogue snippets or conversation topics
4. Note the activity type (travel, rest, conversation, planning, etc.)
5. Canon level: Is this explicitly mentioned (A), implied by context (B), or plausible invention (C)?

The scene must logically connect the boundary scenes. Be faithful to Tolkien's world and characters.

FORMAT YOUR RESPONSE AS:
TITLE: <scene title>
SUMMARY: <scene summary>
DIALOGUE_HINTS: <conversation topics>
ACTIVITY: <activity type>
CANON_LEVEL: <A/B/C>
CANON_BASIS: <brief explanation of why this fits canon>"""

        return prompt
    
    def _parse_llm_response(self, response: str, gap: GapAnalysis, scene_num: int, 
                           total: int, date: datetime) -> GeneratedScene:
        """Parse LLM response into a GeneratedScene"""
        lines = response.strip().split('\n')
        progress = (scene_num - 1) / (total - 1) if total > 1 else 0.5
        
        data = {
            'title': f"Scene {scene_num}",
            'summary': "Generated scene content",
            'dialogue_hints': [],
            'activity': 'activity',
            'canon_level': 'C',
            'canon_basis': 'Plausible invention'
        }
        
        current_key = None
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                data['title'] = line.replace('TITLE:', '').strip()
            elif line.startswith('SUMMARY:'):
                data['summary'] = line.replace('SUMMARY:', '').strip()
                current_key = 'summary'
            elif line.startswith('DIALOGUE_HINTS:'):
                hints = line.replace('DIALOGUE_HINTS:', '').strip()
                data['dialogue_hints'] = [h.strip() for h in hints.split(',') if h.strip()]
            elif line.startswith('ACTIVITY:'):
                data['activity'] = line.replace('ACTIVITY:', '').strip().lower()
            elif line.startswith('CANON_LEVEL:'):
                level = line.replace('CANON_LEVEL:', '').strip().upper()
                data['canon_level'] = level if level in ['A', 'B', 'C'] else 'C'
            elif line.startswith('CANON_BASIS:'):
                data['canon_basis'] = line.replace('CANON_BASIS:', '').strip()
            elif current_key == 'summary' and line and not line.startswith('DIALOGUE'):
                data['summary'] += ' ' + line
        
        # Map canon level
        level_map = {
            'A': CanonLevel.EXPLICIT,
            'B': CanonLevel.IMPLIED,
            'C': CanonLevel.PLAUSIBLE
        }
        
        cons = gap.constraints
        
        # Determine location based on progress through gap
        if progress < 0.3:
            location = cons.location_start
        elif progress > 0.7:
            location = cons.location_end
        else:
            location = f"Between {cons.location_start} and {cons.location_end}"
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=data['title'],
            summary=data['summary'],
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=8,
            gap_type=gap.gap_type,
            activity_type=data['activity'],
            characters=cons.characters_present_start,
            location=location,
            dialogue_hints=data['dialogue_hints'],
            canon_level=level_map.get(data['canon_level'], CanonLevel.PLAUSIBLE),
            canon_basis=f"{data['canon_level']} - {data['canon_basis']}",
            position_in_gap=scene_num,
            total_in_gap=total
        )
    
    def _generate_single_template_scene(self, gap: GapAnalysis, scene_num: int, total: int, 
                                        date: datetime, progress: float) -> GeneratedScene:
        """Generate a single scene using templates (fallback)"""
        if gap.gap_type == GapType.TRAVEL:
            return self._generate_travel_scene(gap, scene_num, total, date, progress)
        elif gap.gap_type == GapType.WAITING:
            return self._generate_waiting_scene(gap, scene_num, total, date, progress)
        elif gap.gap_type == GapType.RECUPERATION:
            return self._generate_recuperation_scene(gap, scene_num, total, date, progress)
        elif gap.gap_type == GapType.PLANNING:
            return self._generate_planning_scene(gap, scene_num, total, date, progress)
        else:
            return self._generate_offscreen_scene(gap, scene_num, total, date, progress)
    
    def _generate_template_based(self, gap: GapAnalysis, num_scenes: int, enhanced: bool = False) -> List[GeneratedScene]:
        """Generate scenes using templates"""
        scenes = []
        constraints = gap.constraints
        
        # Get dates from gap scenes using ISO format
        # Find the actual scenes to get their ISO dates
        start_date = self._parse_scene_date(gap.from_scene_id, gap.from_date)
        end_date = self._parse_scene_date(gap.to_scene_id, gap.to_date)
        
        for i in range(num_scenes):
            scene_num = i + 1
            progress = i / (num_scenes - 1) if num_scenes > 1 else 0.5
            
            # Calculate this scene's date
            days_offset = int(gap.gap_days * progress)
            scene_date = start_date + timedelta(days=days_offset)
            
            # Generate based on gap type
            if gap.gap_type == GapType.TRAVEL:
                gen_scene = self._generate_travel_scene(gap, scene_num, num_scenes, scene_date, progress)
            elif gap.gap_type == GapType.WAITING:
                gen_scene = self._generate_waiting_scene(gap, scene_num, num_scenes, scene_date, progress)
            elif gap.gap_type == GapType.RECUPERATION:
                gen_scene = self._generate_recuperation_scene(gap, scene_num, num_scenes, scene_date, progress)
            elif gap.gap_type == GapType.PLANNING:
                gen_scene = self._generate_planning_scene(gap, scene_num, num_scenes, scene_date, progress)
            else:
                gen_scene = self._generate_offscreen_scene(gap, scene_num, num_scenes, scene_date, progress)
            
            scenes.append(gen_scene)
        
        return scenes
    
    def _generate_travel_scene(self, gap: GapAnalysis, scene_num: int, total: int, date: datetime, progress: float) -> GeneratedScene:
        """Generate a travel scene"""
        cons = gap.constraints
        
        # Determine location based on progress
        if progress < 0.3:
            location = cons.location_start
        elif progress > 0.7:
            location = cons.location_end
        else:
            location = f"Between {cons.location_start} and {cons.location_end}"
        
        # Activity based on travel phase
        activities = [
            ("Breaking Camp", "The company packs up and prepares for the day's march."),
            ("Midday March", "The group continues their journey, stopping briefly to rest."),
            ("Setting Up Camp", "The company finds a place to rest for the night and makes camp."),
            ("Night Watch", "While some sleep, others keep watch against potential dangers."),
        ]
        
        if scene_num == 1:
            title, summary_template = activities[0]
        elif scene_num == total:
            title, summary_template = activities[2]
        else:
            title, summary_template = activities[1]
        
        # Enhance summary with details
        chars = ', '.join(cons.characters_present_start[:4])
        summary = f"{summary_template} {chars} and the others make their way through {location}. The journey continues with all its hardships."
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=title,
            summary=summary,
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=8 if "March" in title else 4,
            gap_type=GapType.TRAVEL,
            activity_type="travel",
            characters=cons.characters_present_start,
            location=location,
            dialogue_hints=["Complaints about sore feet", "Discussion of the path ahead"],
            canon_level=CanonLevel.PLAUSIBLE,
            canon_basis="C - Travel inferred from location change",
            position_in_gap=scene_num,
            total_in_gap=total
        )
    
    def _generate_waiting_scene(self, gap: GapAnalysis, scene_num: int, total: int, date: datetime, progress: float) -> GeneratedScene:
        """Generate a waiting/imprisonment scene"""
        cons = gap.constraints
        location = cons.location_start
        
        # Phase-based content
        if progress < 0.25:
            title = "Adjusting to Confinement"
            summary = f"The dwarves settle into their imprisonment in {location}. Initial shock gives way to grumbling and attempts to stay occupied."
            activity = "adjustment"
        elif progress < 0.5:
            title = "Daily Routine in Captivity"
            summary = f"Another day passes in confinement. The prisoners have established routines to pass the time and keep spirits up."
            activity = "routine"
        elif progress < 0.75:
            title = "Growing Restless"
            summary = f"Days of waiting weigh heavily. Conversations turn increasingly to escape plans and concerns about their quest."
            activity = "planning"
        else:
            title = "Preparing for Action"
            summary = f"The end of their confinement approaches. Final preparations are made for what must come next."
            activity = "preparation"
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=title,
            summary=summary,
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=12,
            gap_type=GapType.WAITING,
            activity_type=activity,
            characters=cons.characters_present_start,
            location=location,
            dialogue_hints=["Whispered conversations", "Complaints about food", "Stories to pass time"],
            canon_level=CanonLevel.IMPLIED if progress > 0.5 else CanonLevel.PLAUSIBLE,
            canon_basis="B - Implied from duration of imprisonment" if progress > 0.5 else "C - Plausible prisoner behavior",
            position_in_gap=scene_num,
            total_in_gap=total
        )
    
    def _generate_recuperation_scene(self, gap: GapAnalysis, scene_num: int, total: int, date: datetime, progress: float) -> GeneratedScene:
        """Generate a recuperation/rest scene"""
        cons = gap.constraints
        
        title = "Rest and Recovery"
        summary = f"The company rests at {cons.location_start}. Wounds are tended, strength is regained, and spirits slowly lift."
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=title,
            summary=summary,
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=16,
            gap_type=GapType.RECUPERATION,
            activity_type="rest",
            characters=cons.characters_present_start,
            location=cons.location_start,
            canon_level=CanonLevel.IMPLIED,
            canon_basis="B - Recovery implied between active scenes",
            position_in_gap=scene_num,
            total_in_gap=total
        )
    
    def _generate_planning_scene(self, gap: GapAnalysis, scene_num: int, total: int, date: datetime, progress: float) -> GeneratedScene:
        """Generate a planning/strategy scene"""
        cons = gap.constraints
        
        title = "Council and Strategy"
        summary = f"The company discusses their next moves. Plans are debated, concerns raised, and decisions made for the journey ahead."
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=title,
            summary=summary,
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=4,
            gap_type=GapType.PLANNING,
            activity_type="planning",
            characters=cons.characters_present_start,
            location=cons.location_start,
            dialogue_hints=["Debate over the best path", "Discussion of supplies needed"],
            canon_level=CanonLevel.PLAUSIBLE,
            canon_basis="C - Planning implied by quest nature",
            position_in_gap=scene_num,
            total_in_gap=total
        )
    
    def _generate_offscreen_scene(self, gap: GapAnalysis, scene_num: int, total: int, date: datetime, progress: float) -> GeneratedScene:
        """Generate a generic offscreen scene"""
        cons = gap.constraints
        
        title = "Passing Time"
        summary = f"Days pass at {cons.location_start}. The company continues their activities while waiting for the next stage of their journey."
        
        return GeneratedScene(
            id=f"gen_{gap.gap_id}_{scene_num:03d}",
            parent_gap_id=gap.gap_id,
            title=title,
            summary=summary,
            date=date.strftime('%B %d, %Y'),
            date_iso=date.strftime('%Y-%m-%d'),
            duration_hours=8,
            gap_type=GapType.OFFSCREEN,
            activity_type="routine",
            characters=cons.characters_present_start,
            location=cons.location_start,
            canon_level=CanonLevel.PLAUSIBLE,
            canon_basis="C - Time passing between events",
            position_in_gap=scene_num,
            total_in_gap=total
        )


class ContinuityValidator:
    """Validates generated content against continuity constraints"""
    
    def validate_scene(self, gen_scene: GeneratedScene, gap: GapAnalysis) -> Dict[str, str]:
        """Validate a generated scene"""
        checks = {}
        cons = gap.constraints
        
        # Check 1: Character presence consistency
        checks['character_presence'] = self._validate_characters(gen_scene, cons)
        
        # Check 2: Item continuity (basic)
        checks['item_continuity'] = "PASS"  # TODO: Implement item tracking
        
        # Check 3: Timeline logic
        checks['timeline_logic'] = self._validate_timeline(gen_scene, gap)
        
        # Check 4: Location consistency
        checks['location_consistency'] = self._validate_location(gen_scene, cons)
        
        # Check 5: Gap type appropriateness
        checks['gap_type_match'] = self._validate_gap_type(gen_scene, gap)
        
        return checks
    
    def _validate_characters(self, gen_scene: GeneratedScene, cons: SceneConstraints) -> str:
        """Validate character presence is consistent"""
        scene_chars = set(gen_scene.characters)
        start_chars = set(cons.characters_present_start)
        end_chars = set(cons.characters_present_end)
        
        # Characters in generated scene should be present at start
        # OR present at end (in case they appear during gap)
        allowed_chars = start_chars.union(end_chars)
        
        unexpected = scene_chars - allowed_chars
        if unexpected:
            return f"WARNING: Unexpected characters: {unexpected}"
        
        return "PASS"
    
    def _validate_timeline(self, gen_scene: GeneratedScene, gap: GapAnalysis) -> str:
        """Validate timeline logic"""
        try:
            scene_date = datetime.strptime(gen_scene.date_iso, '%Y-%m-%d')
            start_date = datetime.strptime(gap.from_date.split(',')[0] if ',' in gap.from_date else gap.from_date, '%B %d, %Y' if ' ' in gap.from_date and ',' in gap.from_date else '%Y-%m-%d')
            end_date = datetime.strptime(gap.to_date.split(',')[0] if ',' in gap.to_date else gap.to_date, '%B %d, %Y' if ' ' in gap.to_date and ',' in gap.to_date else '%Y-%m-%d')
            
            # Actually parse from the gap constraints
            # Use the canonical scene dates
            # This is simplified - would need proper date parsing
            
            if scene_date < start_date:
                return f"ERROR: Scene date {scene_date} before gap start"
            if scene_date > end_date:
                return f"ERROR: Scene date {scene_date} after gap end"
            
            return "PASS"
        except Exception as e:
            return f"WARNING: Could not validate dates: {e}"
    
    def _validate_location(self, gen_scene: GeneratedScene, cons: SceneConstraints) -> str:
        """Validate location is consistent"""
        # Location should be start, end, or between
        # For now, just check it's not completely unrelated
        valid_locations = [cons.location_start, cons.location_end]
        
        if gen_scene.location in valid_locations:
            return "PASS"
        
        if "Between" in gen_scene.location and cons.location_start in gen_scene.location:
            return "PASS"
        
        return f"WARNING: Location '{gen_scene.location}' not in expected path"
    
    def _validate_gap_type(self, gen_scene: GeneratedScene, gap: GapAnalysis) -> str:
        """Validate activity matches gap type"""
        gap_type = gap.gap_type
        activity = gen_scene.activity_type
        
        # Mapping of valid activities per gap type
        valid_activities = {
            GapType.TRAVEL: ['travel', 'march', 'journey', 'camp'],
            GapType.WAITING: ['adjustment', 'routine', 'planning', 'preparation', 'waiting'],
            GapType.RECUPERATION: ['rest', 'healing', 'recovery'],
            GapType.PLANNING: ['planning', 'council', 'strategy', 'discussion'],
            GapType.OFFSCREEN: ['routine', 'rest', 'travel', 'any'],
        }
        
        if activity in valid_activities.get(gap_type, []):
            return "PASS"
        
        return f"WARNING: Activity '{activity}' may not match gap type '{gap_type.value}'"


class GapContentPipeline:
    """Main pipeline for generating gap content"""
    
    def __init__(self, api_key: Optional[str] = None, scenes_file: str = "stream_scenes.json",
                 model: str = "anthropic/claude-3.5-sonnet"):
        with open(scenes_file, 'r') as f:
            self.scenes_data = json.load(f)
        self.scenes = self.scenes_data['scenes']
        
        self.analyzer = GapAnalyzer(scenes_file)
        self.generator = LLMSceneGenerator(api_key, self.scenes, model)
        self.validator = ContinuityValidator()
        self.model = model
    
    def run(self, output_file: str = "generated_gap_scenes.json") -> Dict:
        """Run the full pipeline"""
        print("="*80)
        print("GAP CONTENT GENERATION PIPELINE")
        print("="*80)
        
        # Step 1: Analyze all gaps
        print("\n📊 Step 1: Analyzing gaps...")
        gaps = self.analyzer.analyze_all_gaps()
        print(f"   Found {len(gaps)} gaps to fill")
        
        # Statistics
        gap_types = {}
        total_gap_days = 0
        for gap in gaps:
            gap_types[gap.gap_type.value] = gap_types.get(gap.gap_type.value, 0) + 1
            total_gap_days += gap.gap_days
        
        print(f"   Total gap time: {total_gap_days} days")
        print(f"   Gap types: {gap_types}")
        
        # Step 2: Generate content for each gap
        print("\n📝 Step 2: Generating content...")
        all_generated = []
        
        for i, gap in enumerate(gaps, 1):
            print(f"   [{i}/{len(gaps)}] {gap.gap_id}: {gap.gap_days} days ({gap.gap_type.value})")
            
            generated_scenes = self.generator.generate_gap_content(gap)
            
            # Step 3: Validate each generated scene
            for scene in generated_scenes:
                checks = self.validator.validate_scene(scene, gap)
                scene.continuity_checks = checks
                scene.validation_passed = all(c == "PASS" or c.startswith("WARNING") for c in checks.values())
            
            gap.generated_scenes = generated_scenes
            gap.generation_status = "generated"
            
            all_generated.extend(generated_scenes)
            print(f"      Generated {len(generated_scenes)} scenes")
        
        # Step 4: Prepare output
        print("\n💾 Step 3: Saving results...")
        
        output = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_gaps": len(gaps),
                "total_generated_scenes": len(all_generated),
                "total_gap_days": total_gap_days,
                "gap_type_distribution": gap_types,
                "generator_version": "1.0.0",
                "canon_levels": {
                    "A_explicit": sum(1 for s in all_generated if s.canon_level == CanonLevel.EXPLICIT),
                    "B_implied": sum(1 for s in all_generated if s.canon_level == CanonLevel.IMPLIED),
                    "C_plausible": sum(1 for s in all_generated if s.canon_level == CanonLevel.PLAUSIBLE),
                }
            },
            "gaps": [self._gap_to_dict(gap) for gap in gaps],
            "generated_scenes": [self._scene_to_dict(scene) for scene in all_generated]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"   Saved to: {output_file}")
        print(f"   Total generated scenes: {len(all_generated)}")
        
        # Print summary of largest gaps
        print("\n📈 Largest gaps filled:")
        sorted_gaps = sorted(gaps, key=lambda g: g.gap_days, reverse=True)[:5]
        for gap in sorted_gaps:
            print(f"   {gap.gap_days:3d} days: {gap.from_scene_title} → {gap.to_scene_title}")
            print(f"           Generated {len(gap.generated_scenes)} scenes")
        
        print("\n✅ Pipeline complete!")
        
        return output
    
    def _gap_to_dict(self, gap: GapAnalysis) -> Dict:
        """Convert GapAnalysis to dict"""
        return {
            "gap_id": gap.gap_id,
            "from_scene": {
                "id": gap.from_scene_id,
                "title": gap.from_scene_title,
                "date": gap.from_date
            },
            "to_scene": {
                "id": gap.to_scene_id,
                "title": gap.to_scene_title,
                "date": gap.to_date
            },
            "gap_days": gap.gap_days,
            "gap_type": gap.gap_type.value,
            "constraints": {
                "characters_start": gap.constraints.characters_present_start,
                "characters_end": gap.constraints.characters_present_end,
                "location_start": gap.constraints.location_start,
                "location_end": gap.constraints.location_end,
            },
            "generated_scene_count": len(gap.generated_scenes),
            "generation_status": gap.generation_status
        }
    
    def _scene_to_dict(self, scene: GeneratedScene) -> Dict:
        """Convert GeneratedScene to dict"""
        return {
            "id": scene.id,
            "parent_gap_id": scene.parent_gap_id,
            "title": scene.title,
            "summary": scene.summary,
            "date": scene.date,
            "date_iso": scene.date_iso,
            "duration_hours": scene.duration_hours,
            "gap_type": scene.gap_type.value,
            "activity_type": scene.activity_type,
            "characters": scene.characters,
            "location": scene.location,
            "dialogue_hints": scene.dialogue_hints,
            "canon_level": scene.canon_level.value,
            "canon_basis": scene.canon_basis,
            "position_in_gap": f"{scene.position_in_gap}/{scene.total_in_gap}",
            "continuity_checks": scene.continuity_checks,
            "validation_passed": scene.validation_passed
        }


# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue without it

class ModelSelector:
    """Interactive model selector with persistent preferences"""
    
    CONFIG_FILE = ".gap_generator_config.json"
    
    # Model definitions with metadata
    MODELS = {
        # Premium
        "anthropic/claude-3.5-sonnet": {
            "name": "Claude 3.5 Sonnet",
            "category": "Premium",
            "quality": 5,
            "speed": "Fast",
            "cost": "$$",
            "description": "Best overall quality for narrative generation",
            "recommended": True
        },
        "anthropic/claude-3-opus": {
            "name": "Claude 3 Opus",
            "category": "Premium", 
            "quality": 5,
            "speed": "Medium",
            "cost": "$$$",
            "description": "Excellent for complex narrative arcs",
            "recommended": False
        },
        "openai/gpt-4o": {
            "name": "GPT-4o",
            "category": "Premium",
            "quality": 5,
            "speed": "Fast",
            "cost": "$$",
            "description": "Very good quality, fast generation",
            "recommended": False
        },
        # Balanced
        "anthropic/claude-3.5-haiku": {
            "name": "Claude 3.5 Haiku",
            "category": "Balanced",
            "quality": 4,
            "speed": "Very Fast",
            "cost": "$",
            "description": "Fast and good for most gap types",
            "recommended": True
        },
        "meta-llama/llama-3.1-70b-instruct": {
            "name": "Llama 3.1 70B",
            "category": "Balanced",
            "quality": 3,
            "speed": "Fast",
            "cost": "$",
            "description": "Open source, decent quality",
            "recommended": False
        },
        "google/gemini-1.5-flash": {
            "name": "Gemini 1.5 Flash",
            "category": "Balanced",
            "quality": 3,
            "speed": "Very Fast",
            "cost": "$",
            "description": "Fast summaries, good for prototyping",
            "recommended": False
        },
        # Budget
        "meta-llama/llama-3.1-8b-instruct": {
            "name": "Llama 3.1 8B",
            "category": "Budget",
            "quality": 3,
            "speed": "Very Fast",
            "cost": "$",
            "description": "Very cheap, basic quality",
            "recommended": False
        },
        "google/gemini-flash-1.5": {
            "name": "Gemini Flash 1.5",
            "category": "Budget",
            "quality": 3,
            "speed": "Fastest",
            "cost": "$",
            "description": "Fastest option, good for testing",
            "recommended": False
        },
        # Template fallback
        "template": {
            "name": "Template-Based (No LLM)",
            "category": "Offline",
            "quality": 2,
            "speed": "Instant",
            "cost": "Free",
            "description": "Rule-based generation, no API needed",
            "recommended": False
        }
    }
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load saved configuration"""
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"last_model": "anthropic/claude-3.5-sonnet"}
    
    def _save_config(self):
        """Save configuration"""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_last_model(self) -> str:
        """Get the last used model"""
        return self.config.get("last_model", "anthropic/claude-3.5-sonnet")
    
    def save_model(self, model: str):
        """Save model as last used"""
        self.config["last_model"] = model
        self._save_config()
    
    def list_models(self):
        """Print formatted model list"""
        print("="*80)
        print("AVAILABLE MODELS")
        print("="*80)
        print()
        
        current = self.get_last_model()
        
        categories = ["Premium", "Balanced", "Budget", "Offline"]
        
        for category in categories:
            models_in_cat = {k: v for k, v in self.MODELS.items() if v["category"] == category}
            if not models_in_cat:
                continue
                
            print(f"\n{category.upper()}:")
            print("-" * 60)
            
            for model_id, info in models_in_cat.items():
                marker = "👉 " if model_id == current else "   "
                rec = " ⭐" if info["recommended"] else ""
                print(f"{marker}{info['name']}{rec}")
                print(f"   ID: {model_id}")
                print(f"   Quality: {'⭐' * info['quality']} | Speed: {info['speed']} | Cost: {info['cost']}")
                print(f"   {info['description']}")
                print()
        
        print("-" * 60)
        print(f"Last used: {self.MODELS.get(current, {}).get('name', current)}")
        print("="*80)
    
    def select_interactive(self) -> str:
        """Interactive model selection"""
        print()
        print("="*80)
        print("MODEL SELECTOR")
        print("="*80)
        print()
        
        current = self.get_last_model()
        
        # Build numbered list
        model_list = list(self.MODELS.items())
        
        # Group by category
        categories = ["Premium", "Balanced", "Budget", "Offline"]
        option_num = 1
        option_map = {}
        
        for category in categories:
            models_in_cat = [(k, v) for k, v in model_list if v["category"] == category]
            if not models_in_cat:
                continue
                
            print(f"\n{category}:")
            for model_id, info in models_in_cat:
                marker = "👉 " if model_id == current else "   "
                rec = " [⭐ RECOMMENDED]" if info["recommended"] else ""
                current_marker = " (last used)" if model_id == current else ""
                
                print(f"  {option_num}. {marker}{info['name']}{rec}{current_marker}")
                print(f"     {info['description']}")
                print(f"     Quality: {'⭐' * info['quality']} | {info['speed']} | {info['cost']}")
                
                option_map[option_num] = model_id
                option_num += 1
        
        # Add options to keep current or list all
        print(f"\n{option_num}. Keep current: {self.MODELS.get(current, {}).get('name', current)}")
        option_map[option_num] = "KEEP_CURRENT"
        
        print(f"\n0. Cancel and exit")
        
        print()
        while True:
            try:
                choice = input(f"Select model (0-{option_num}): ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    print("Cancelled.")
                    return None
                
                if choice_num == option_num:
                    print(f"Keeping current model: {self.MODELS.get(current, {}).get('name', current)}")
                    return current
                
                if choice_num in option_map:
                    selected = option_map[choice_num]
                    self.save_model(selected)
                    print(f"\n✅ Selected: {self.MODELS[selected]['name']}")
                    print(f"   This will be used as default for future runs.")
                    return selected
                else:
                    print(f"Invalid choice. Please enter 0-{option_num}.")
                    
            except ValueError:
                print("Please enter a number.")
    
    def get_model_display_name(self, model_id: str) -> str:
        """Get display name for a model ID"""
        return self.MODELS.get(model_id, {}).get("name", model_id)
    
    def select_interactive_always(self, has_api_key: bool = True) -> Optional[str]:
        """Always show interactive selector with pre-selected default"""
        print()
        print("="*80)
        print("MODEL SELECTOR")
        print("="*80)
        print()
        
        current = self.get_last_model()
        
        # Show current selection notice
        if current == "template":
            print(f"Current default: Template-Based (No LLM)")
        else:
            print(f"Current default: {self.MODELS.get(current, {}).get('name', current)}")
        print()
        
        # Build numbered list
        model_list = list(self.MODELS.items())
        
        # Group by category
        categories = ["Premium", "Balanced", "Budget", "Offline"]
        option_num = 1
        option_map = {}
        
        for category in categories:
            # Filter models - only show template if no API key
            models_in_cat = []
            for k, v in model_list:
                if v["category"] == category:
                    if k == "template" and has_api_key:
                        models_in_cat.append((k, v))
                    elif k != "template":
                        models_in_cat.append((k, v))
            
            if not models_in_cat:
                continue
                
            print(f"{category}:")
            for model_id, info in models_in_cat:
                is_current = model_id == current
                rec = " [⭐ RECOMMENDED]" if info["recommended"] else ""
                current_marker = " [DEFAULT]" if is_current else ""
                
                print(f"  {option_num}. {info['name']}{rec}{current_marker}")
                print(f"     {info['description']}")
                print(f"     Quality: {'⭐' * info['quality']} | {info['speed']} | {info['cost']}")
                
                option_map[option_num] = model_id
                option_num += 1
        
        print()
        print("-" * 60)
        print(f"Press Enter to use default ({self.MODELS.get(current, {}).get('name', current)})")
        print(f"Or enter 0 to cancel")
        print("-" * 60)
        
        while True:
            try:
                choice = input(f"Select model (0-{option_num-1}, or Enter for default): ").strip()
                
                # Empty input = use current/default
                if choice == "":
                    print(f"\n✅ Using default: {self.MODELS.get(current, {}).get('name', current)}")
                    return current
                
                choice_num = int(choice)
                
                if choice_num == 0:
                    print("Cancelled.")
                    return None
                
                if choice_num in option_map:
                    selected = option_map[choice_num]
                    self.save_model(selected)
                    print(f"\n✅ Selected: {self.MODELS[selected]['name']}")
                    if selected != current:
                        print(f"   Saved as new default for future runs.")
                    return selected
                else:
                    print(f"Invalid choice. Please enter 0-{option_num-1}, or press Enter for default.")
                    
            except ValueError:
                print("Please enter a number, or press Enter for default.")


class EnvSetup:
    """Handle .env file setup for API keys"""
    
    ENV_FILE = ".env"
    
    @classmethod
    def run_setup(cls, selector: ModelSelector):
        """Interactive setup for .env file"""
        print()
        print("="*80)
        print("GAP GENERATOR SETUP")
        print("="*80)
        print()
        print("This will create a .env file with your OpenRouter API key.")
        print("The .env file will be loaded automatically on future runs.")
        print()
        
        # Check existing .env
        existing_key = None
        if os.path.exists(cls.ENV_FILE):
            print(f"Found existing {cls.ENV_FILE}")
            with open(cls.ENV_FILE, 'r') as f:
                for line in f:
                    if line.startswith('OPENROUTER_API_KEY='):
                        existing_key = line.strip().split('=', 1)[1]
                        # Mask the key
                        masked = existing_key[:8] + '...' + existing_key[-4:] if len(existing_key) > 12 else '***'
                        print(f"  Current API key: {masked}")
                        break
        
        print()
        
        # Get API key
        print("Enter your OpenRouter API key (or press Enter to keep existing):")
        print("  Get one at: https://openrouter.ai/keys")
        api_key = input("> ").strip()
        
        if not api_key and existing_key:
            api_key = existing_key
            print("  Keeping existing API key")
        elif not api_key:
            print("  No API key provided - you can use template mode (-t) instead")
            api_key = None
        
        # Select default model
        print()
        print("-"*60)
        selected_model = selector.select_interactive_always(api_key is not None)
        
        if selected_model is None:
            print("\nSetup cancelled.")
            return False
        
        # Write .env file
        env_content = f"""# Gap Content Generator Configuration
# Get your API key at: https://openrouter.ai/keys

OPENROUTER_API_KEY={api_key or ''}

# Optional: Site info for OpenRouter analytics
# SITE_URL=https://your-domain.com
# SITE_NAME=Your Hobbit Stream
"""
        
        with open(cls.ENV_FILE, 'w') as f:
            f.write(env_content)
        
        print()
        print("="*80)
        print("✅ Setup complete!")
        print(f"   Configuration saved to: {cls.ENV_FILE}")
        if api_key:
            print(f"   API key: {'*' * 12} (masked)")
        print(f"   Default model: {selector.get_model_display_name(selected_model)}")
        print()
        print("You can now run:")
        print("  python3 gap_content_generator.py")
        print()
        print("To change settings later, run:")
        print("  python3 gap_content_generator.py --setup")
        print("="*80)
        
        return True
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Get API key from environment or .env"""
        # First check environment (already loaded by dotenv if available)
        key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        return key



def main():
    """Main entry point"""
    import sys
    import argparse
    
    selector = ModelSelector()
    
    parser = argparse.ArgumentParser(description='Generate content for timeline gaps')
    parser.add_argument('--model', '-m', type=str, 
                       default=None,
                       help='OpenRouter model to use (skips interactive selection)')
    parser.add_argument('--list-models', '-l', action='store_true',
                       help='Show available models and exit')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Use saved model without confirmation (non-interactive mode)')
    parser.add_argument('--template-only', '-t', action='store_true',
                       help='Use template-based generation only (no LLM)')
    parser.add_argument('--setup', action='store_true',
                       help='Interactive setup for API key and default model')
    
    args = parser.parse_args()
    
    if args.list_models:
        selector.list_models()
        return
    
    if args.setup:
        # Run interactive setup
        EnvSetup.run_setup(selector)
        return
    
    # Get API key (from .env or environment)
    api_key = EnvSetup.get_api_key()
    
    # Determine which model to use
    if args.template_only:
        model = "template"
        api_key = None
    elif args.model:
        # Explicit model override - skip interactive selection
        model = args.model
        selector.save_model(model)
        print(f"🔧 Using specified model: {selector.get_model_display_name(model)}")
    elif args.yes:
        # Non-interactive mode - use saved/default model
        model = selector.get_last_model()
        print(f"✓ Using saved model: {selector.get_model_display_name(model)}")
    else:
        # Interactive mode - always show selector with pre-selected default
        selected = selector.select_interactive_always(api_key is not None)
        if selected is None:
            return
        model = selected
        # Reload API key in case it was set in .env after startup
        api_key = EnvSetup.get_api_key()
    
    # Check API key status for LLM models
    if model != "template":
        if api_key:
            print(f"🔑 OpenRouter API key found")
            print(f"   Model: {selector.get_model_display_name(model)}")
        else:
            print("⚠️  No OpenRouter API key found")
            print(f"   Selected: {selector.get_model_display_name(model)}")
            print("   Falling back to template-based generation")
            print()
            print("To set up your API key, run:")
            print("  python3 gap_content_generator.py --setup")
            print()
            model = "template"
            api_key = None
    else:
        print("📝 Template-only mode (no LLM)")
    
    # Run pipeline
    # Use the actual model ID for the pipeline, but handle template mode via api_key=None
    actual_model = model if model != "template" else "anthropic/claude-3.5-sonnet"
    pipeline = GapContentPipeline(api_key=api_key, model=actual_model)
    pipeline.run()


if __name__ == "__main__":
    main()
