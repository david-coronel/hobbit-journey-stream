#!/usr/bin/env python3
"""
The Hobbit Scene Generation Engine

Generates plausible scenes that fit between canonical events.
Uses narrative context, character states, and location data to maintain consistency.
"""

import json
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re

@dataclass
class CharacterState:
    """Tracks a character's state at a point in time."""
    name: str
    present: bool = True
    health: str = "well"  # well, injured, exhausted, etc.
    mood: str = "neutral"  # happy, anxious, angry, etc.
    has_item: List[str] = field(default_factory=list)
    location: str = ""
    
@dataclass
class SceneContext:
    """Context for scene generation."""
    before_entry: Dict  # The canonical scene before the gap
    after_entry: Dict   # The canonical scene after the gap
    gap_duration_days: int
    characters_present: List[str]
    location: str
    time_of_day: str
    narrative_tone: str  # tense, peaceful, ominous, etc.

class HobbitSceneGenerator:
    """Generates scenes that fit between canonical events."""
    
    # Character relationship dynamics
    CHARACTER_DYNAMICS = {
        ('Bilbo', 'Thorin'): ['tense', 'respectful', 'distant', 'conflicted'],
        ('Bilbo', 'Gandalf'): ['friendly', 'mentorly', 'reassuring'],
        ('Bilbo', 'Balin'): ['friendly', 'confiding', 'advisory'],
        ('Bilbo', 'Bombur'): ['amused', 'concerned', 'helpful'],
        ('Thorin', 'Gandalf'): ['respectful', 'demanding', 'grateful'],
        ('Fili', 'Kili'): ['playful', 'protective', 'competitive'],
        ('Bert', 'Tom'): ['argumentative', 'planning', 'squabbling'],
        ('Bert', 'William'): ['argumentative', 'planning'],
        ('Tom', 'William'): ['argumentative', 'planning'],
    }
    
    # Activities by location type
    ACTIVITIES = {
        'forest': [
            'gathering firewood', 'foraging for food', 'watching for danger',
            'telling stories around a small fire', 'mending gear', 'keeping watch',
            'whittling wood', 'sketching maps', 'checking supplies'
        ],
        'mountain': [
            'climbing carefully', 'resting on ledges', 'shielding from wind',
            'finding shelter in crevices', 'boiling snow for water',
            'securing ropes', 'scanning the path ahead'
        ],
        'cave': [
            'building a small fire', 'drying wet clothes', 'sharing rations',
            'telling tales to keep spirits up', 'checking weapons',
            'listening to distant sounds', 'trying to sleep'
        ],
        'camp': [
            'cooking a meal', 'setting up bedrolls', 'polishing weapons',
            'singing songs', 'arguing about the route', 'checking maps',
            'sharing pipe-weed', 'complaining about the food'
        ],
        'road': [
            'walking in single file', 'humming traveling songs',
            'watching the horizon', 'discussing plans',
            'admiring the view', 'keeping alert for danger'
        ],
        'river': [
            'filling water skins', 'washing faces', 'fording carefully',
            'resting on the bank', 'watching for fish',
            'skipping stones', 'checking the current'
        ],
        'settlement': [
            'buying supplies', 'gathering news', 'resting in proper beds',
            'eating hot meals', 'repairing equipment', 'negotiating',
            'observing local customs'
        ]
    }
    
    # Weather by region and season
    WEATHER_PATTERNS = {
        'shire': ['sunny', 'mild', 'rainy', 'foggy'],
        'trollshaws': ['overcast', 'chilly', 'windy', 'rainy'],
        'misty_mountains': ['snowy', 'freezing', 'foggy', 'stormy'],
        'mirkwood': ['gloomy', 'damp', 'stagnant', 'misty'],
        'lake_town': ['damp', 'cold', 'windy', 'overcast'],
        'erebor': ['desolate', 'dry', 'windy', 'clear'],
        'wilderland': ['variable', 'windy', 'sunny', 'stormy']
    }
    
    # Dialogue snippets by character (in style of the book)
    DIALOGUE_SNIPPETS = {
        'Bilbo': [
            "I do wish I was at home in my nice hole by the fire",
            "We seem to be getting nowhere very fast",
            "Is there no end to this [PLACE]?",
            "I suppose we must keep going",
            "My toes are quite numb, but I suppose that's normal",
            "I do hope there's something to eat soon",
            "If only Gandalf were here",
            "This is not what I expected when I signed the contract",
        ],
        'Thorin': [
            "We must press on. Every day matters",
            "The Mountain is not getting any closer while we rest",
            "I remember when [PLACE] was different...",
            "We are Durin's folk. We do not falter",
            "Keep your spirits up, lads. We're near now",
            "Double the watch. I trust nothing in these lands",
        ],
        'Gandalf': [
            "All is not lost, my friends. Not yet",
            "There are older and fouler things than orcs in the deep places",
            "Patience. The path reveals itself to those who wait",
            "I have business elsewhere, but I shall return",
            "Trust your burglar. He has more in him than you know",
        ],
        'Balin': [
            "In my youth, I remember tales of this place",
            "Thorin has the right of it, but mind your tempers",
            "The old maps show a path through here",
            "Best to rest while we can. Who knows what lies ahead",
        ],
        'Bombur': [
            "My legs are aching something fierce",
            "Is it time to eat yet?",
            "I could sleep for a week",
            "My belly thinks my throat's been cut",
            "Couldn't we rest just a little longer?",
        ],
        'Dori': [
            "Watch where you're putting those big feet, Bombur",
            "Someone help the poor fellow up",
            "I've had about enough of this journey",
        ],
        'Kili': [
            "Fili and I can scout ahead",
            "A bit of adventure never hurt anyone",
            "I bet I could hit that target from here",
        ],
        'Fili': [
            "Come on, brother. Let's see what's over that ridge",
            "These old bones are still good for something",
            "Race you to the top!",
        ],
    }
    
    # Scene templates
    SCENE_TEMPLATES = [
        {
            'type': 'conversation',
            'template': """{setting_description}

{character_list} {activity}.

{dialogue}

{narrative_continuation}"""
        },
        {
            'type': 'observation',
            'template': """{setting_description}

{observer} paused to look {direction}. {observation_description}

{narrative_continuation}"""
        },
        {
            'type': 'camp',
            'template': """{setting_description}

The camp was {camp_state}. {character_list} {activity}.

{dialogue}

{narrative_continuation}"""
        },
        {
            'type': 'journey',
            'template': """{setting_description}

They {travel_action} for {time_description}. {travel_description}

{narrative_continuation}"""
        }
    ]
    
    def __init__(self, timeline_path="hobbit_narrative_analysis.json"):
        """Initialize with timeline data."""
        with open(timeline_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.timeline = data.get('entries', [])
        
        # Load character and place data
        try:
            with open('../data/hobbit_characters.json', 'r') as f:
                self.characters_data = json.load(f).get('characters', {})
            with open('../data/hobbit_places.json', 'r') as f:
                self.places_data = json.load(f).get('places', {})
        except FileNotFoundError:
            self.characters_data = {}
            self.places_data = {}
        
        # Identify major gaps
        self.gaps = self._identify_gaps()
    
    def _identify_gaps(self) -> List[Dict]:
        """Identify gaps between scenes where we can insert generated content."""
        gaps = []
        
        for i in range(len(self.timeline) - 1):
            current = self.timeline[i]
            next_entry = self.timeline[i + 1]
            
            # Only consider gaps between scene-type entries
            if current.get('narrative_type') == 'scene' and next_entry.get('narrative_type') == 'scene':
                # Parse dates
                try:
                    current_date = datetime.fromisoformat(current['timestamp'])
                    next_date = datetime.fromisoformat(next_entry['timestamp'])
                    gap_days = (next_date - current_date).days
                    
                    # Only gaps of 1-30 days (reasonable for scene insertion)
                    if 1 <= gap_days <= 30:
                        gaps.append({
                            'index': i,
                            'before': current,
                            'after': next_entry,
                            'gap_days': gap_days,
                            'chapter': current.get('chapter', 'Unknown')
                        })
                except (KeyError, ValueError):
                    continue
        
        return gaps
    
    def _infer_location(self, entry: Dict) -> str:
        """Infer location from entry content."""
        content = entry.get('content', '').lower()
        
        # Check for place mentions
        location_keywords = {
            'shire': ['shire', 'hobbiton', 'bag end', 'hill'],
            'trollshaws': ['troll', 'trolls', 'clearing'],
            'rivendell': ['rivendell', 'last homely house'],
            'misty_mountains': ['misty mountain', 'goblin', 'mountain pass', 'high pass'],
            'mirkwood': ['mirkwood', 'forest', 'wood', 'spider'],
            'lake_town': ['lake-town', 'esgaroth', 'lake town'],
            'erebor': ['lonely mountain', 'erebor', 'dragon', 'smaug', 'mountain'],
            'dale': ['dale', 'desolation'],
            'beorn': ['beorn', 'carrock'],
            'wilderland': ['wilderland', 'wild', 'open lands']
        }
        
        for location, keywords in location_keywords.items():
            if any(kw in content for kw in keywords):
                return location
        
        return 'wilderland'  # Default
    
    def _detect_characters(self, entry: Dict) -> List[str]:
        """Detect which characters are mentioned in an entry."""
        content = entry.get('content', '')
        characters_found = []
        
        key_characters = ['Bilbo', 'Thorin', 'Gandalf', 'Balin', 'Bombur', 'Fili', 'Kili',
                         'Dori', 'Nori', 'Ori', 'Oin', 'Gloin', 'Bifur', 'Bofur', 'Dwalin',
                         'Beorn', 'Elrond', 'Bard', 'Smaug', 'Gollum', 'Elvenking']
        
        for char in key_characters:
            if char in content or char.lower() in content.lower():
                characters_found.append(char)
        
        return characters_found
    
    def _get_activity(self, location: str) -> str:
        """Get appropriate activity for location."""
        location_type = 'camp'  # default
        
        if 'forest' in location or 'wood' in location:
            location_type = 'forest'
        elif 'mountain' in location:
            location_type = 'mountain'
        elif 'cave' in location:
            location_type = 'cave'
        elif 'road' in location or 'path' in location:
            location_type = 'road'
        elif 'river' in location or 'lake' in location:
            location_type = 'river'
        elif 'town' in location or 'shire' in location:
            location_type = 'settlement'
        
        activities = self.ACTIVITIES.get(location_type, self.ACTIVITIES['camp'])
        return random.choice(activities)
    
    def _get_weather(self, location: str) -> str:
        """Get appropriate weather for location."""
        patterns = self.WEATHER_PATTERNS.get(location, ['clear', 'mild'])
        return random.choice(patterns)
    
    def _generate_dialogue(self, characters: List[str], location: str) -> str:
        """Generate dialogue between characters."""
        if len(characters) < 2:
            return ""
        
        lines = []
        speaker1 = random.choice(characters)
        speaker2 = random.choice([c for c in characters if c != speaker1])
        
        # Get dialogue for speaker1
        snippets1 = self.DIALOGUE_SNIPPETS.get(speaker1, ["..."])
        line1 = random.choice(snippets1)
        if '[PLACE]' in line1:
            line1 = line1.replace('[PLACE]', location.replace('_', ' '))
        
        lines.append(f'"{line1}," said {speaker1}.')
        
        # Get response
        snippets2 = self.DIALOGUE_SNIPPETS.get(speaker2, ["..."])
        line2 = random.choice(snippets2)
        if '[PLACE]' in line2:
            line2 = line2.replace('[PLACE]', location.replace('_', ' '))
        
        lines.append(f'"{line2}," {speaker2} replied.')
        
        # Maybe a third line
        if random.random() < 0.3 and len(characters) > 2:
            speaker3 = random.choice([c for c in characters if c not in [speaker1, speaker2]])
            snippets3 = self.DIALOGUE_SNIPPETS.get(speaker3, ["..."])
            line3 = random.choice(snippets3)
            lines.append(f'{speaker3} added, "{line3}"')
        
        return '\n\n'.join(lines)
    
    def _generate_setting(self, location: str, time_of_day: str, weather: str) -> str:
        """Generate setting description."""
        location_name = location.replace('_', ' ').title()
        
        setting_parts = []
        
        # Time
        if time_of_day == 'morning':
            setting_parts.append(f"The morning light filtered through {self._get_location_detail(location)}.")
        elif time_of_day == 'evening':
            setting_parts.append(f"Evening drew on, and shadows lengthened across {location_name}.")
        elif time_of_day == 'night':
            setting_parts.append(f"Stars wheeled overhead in the {weather} night above {location_name}.")
        else:
            setting_parts.append(f"The {time_of_day} found them in {location_name}.")
        
        # Weather
        if weather == 'rainy':
            setting_parts.append("A light rain had begun to fall, making everything damp and miserable.")
        elif weather == 'snowy':
            setting_parts.append("Snow lay thick on the ground, and their breath steamed in the cold air.")
        elif weather == 'sunny':
            setting_parts.append("The sun shone clear and bright, lifting their spirits somewhat.")
        elif weather == 'foggy':
            setting_parts.append("A thick fog made it difficult to see more than a few yards ahead.")
        
        return ' '.join(setting_parts)
    
    def _get_location_detail(self, location: str) -> str:
        """Get a descriptive detail for a location."""
        details = {
            'shire': 'the well-ordered hedgerows',
            'trollshaws': 'the twisted trees',
            'misty_mountains': 'the jagged peaks',
            'mirkwood': 'the dense black branches',
            'lake_town': 'the dilapidated buildings',
            'erebor': 'the vast desolation',
            'wilderland': 'the open wilderness'
        }
        return details.get(location, 'the landscape')
    
    def generate_scene(self, gap_index: int = None, max_length: int = 500) -> Dict:
        """Generate a scene for a specific gap or random gap."""
        if gap_index is None:
            gap = random.choice(self.gaps)
        else:
            gap = self.gaps[gap_index % len(self.gaps)]
        
        before = gap['before']
        after = gap['after']
        
        # Extract context
        location = self._infer_location(before)
        characters = self._detect_characters(before)
        
        # If no characters detected, try after
        if not characters:
            characters = self._detect_characters(after)
        
        # Default characters if still none
        if not characters:
            characters = ['Bilbo', 'Thorin', 'Balin']
        
        # Generate scene components
        time_of_day = random.choice(['morning', 'midday', 'evening', 'night'])
        weather = self._get_weather(location)
        activity = self._get_activity(location)
        
        # Build the scene
        setting = self._generate_setting(location, time_of_day, weather)
        dialogue = self._generate_dialogue(characters, location) if len(characters) >= 2 else ""
        
        # Character list description
        if len(characters) == 1:
            char_list = characters[0]
        elif len(characters) == 2:
            char_list = f"{characters[0]} and {characters[1]}"
        else:
            char_list = ", ".join(characters[:-1]) + f", and {characters[-1]}"
        
        # Travel description if journey scene
        travel_desc = f"The way was {random.choice(['hard', 'tiring', 'uneventful', 'slow'])}."
        
        # Select and fill template
        template = random.choice(self.SCENE_TEMPLATES)
        
        scene_text = template['template'].format(
            setting_description=setting,
            character_list=char_list,
            activity=activity,
            dialogue=dialogue,
            observer=random.choice(characters) if characters else "Bilbo",
            direction=random.choice(['about', 'ahead', 'behind', 'up at the sky']),
            observation_description=f"The {location.replace('_', ' ')} stretched out before them.",
            camp_state=random.choice(['quiet', 'bustling with activity', 'weary but organized']),
            travel_action=random.choice(['trudged onward', 'made their way', 'pressed forward']),
            time_description=random.choice(['some hours', 'the better part of the day', 'until their legs ached']),
            travel_description=travel_desc,
            narrative_continuation=f"Little did they know what awaited them in the days to come."
        )
        
        # Truncate if too long
        if len(scene_text) > max_length:
            scene_text = scene_text[:max_length].rsplit('.', 1)[0] + '.'
        
        return {
            'type': 'generated_scene',
            'template_type': template['type'],
            'text': scene_text,
            'gap_info': {
                'chapter': gap['chapter'],
                'gap_days': gap['gap_days'],
                'before_date': before.get('date'),
                'after_date': after.get('date'),
                'characters': characters,
                'location': location
            },
            'metadata': {
                'time_of_day': time_of_day,
                'weather': weather,
                'activity': activity
            }
        }
    
    def generate_scenes_for_chapter(self, chapter: str, count: int = 3) -> List[Dict]:
        """Generate multiple scenes for a specific chapter."""
        chapter_gaps = [g for g in self.gaps if g['chapter'] == chapter]
        
        if not chapter_gaps:
            return []
        
        scenes = []
        for i in range(min(count, len(chapter_gaps))):
            gap_idx = self.gaps.index(chapter_gaps[i % len(chapter_gaps)])
            scene = self.generate_scene(gap_idx)
            scenes.append(scene)
        
        return scenes
    
    def export_generated_scenes(self, scenes: List[Dict], output_path: str = "generated_scenes.json"):
        """Export generated scenes to JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_count': len(scenes),
                'scenes': scenes
            }, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(scenes)} scenes to {output_path}")
    
    def export_readable(self, scenes: List[Dict], output_path: str = "generated_scenes.txt"):
        """Export scenes as readable text."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Generated Scenes for The Hobbit\n\n")
            f.write("These scenes are AI-generated to fill narrative gaps between canonical events.\n")
            f.write("They maintain consistency with character presence, locations, and timeline.\n\n")
            f.write("---\n\n")
            
            for i, scene in enumerate(scenes, 1):
                gap = scene['gap_info']
                meta = scene['metadata']
                
                f.write(f"## Scene {i}: {gap['chapter']}\n\n")
                f.write(f"**Date:** Between {gap['before_date']} and {gap['after_date']}  \n")
                f.write(f"**Gap:** {gap['gap_days']} days  \n")
                f.write(f"**Location:** {gap['location'].replace('_', ' ').title()}  \n")
                f.write(f"**Characters:** {', '.join(gap['characters'])}  \n")
                f.write(f"**Time:** {meta['time_of_day']}, {meta['weather']}  \n")
                f.write(f"**Activity:** {meta['activity']}  \n")
                f.write(f"**Template:** {scene['template_type']}\n\n")
                f.write(f"{scene['text']}\n\n")
                f.write("---\n\n")
        
        print(f"Exported readable version to {output_path}")


def main():
    """Generate sample scenes."""
    print("Initializing Hobbit Scene Generator...")
    generator = HobbitSceneGenerator()
    
    print(f"\nFound {len(generator.gaps)} suitable gaps in the narrative")
    
    # Generate a few sample scenes
    print("\n" + "="*70)
    print("GENERATING SAMPLE SCENES")
    print("="*70)
    
    scenes = []
    
    # Generate scenes for different chapters
    sample_chapters = ['Chapter I', 'Chapter II', 'Chapter VIII', 'Chapter XI']
    
    for chapter in sample_chapters:
        chapter_scenes = generator.generate_scenes_for_chapter(chapter, count=1)
        scenes.extend(chapter_scenes)
        
        if chapter_scenes:
            print(f"\n--- {chapter} ---")
            print(chapter_scenes[0]['text'][:300] + "...")
    
    # Add some random scenes
    for _ in range(3):
        scene = generator.generate_scene()
        scenes.append(scene)
        print(f"\n--- Random Scene ({scene['gap_info']['chapter']}) ---")
        print(scene['text'][:300] + "...")
    
    # Export
    generator.export_generated_scenes(scenes, "generated_scenes.json")
    generator.export_readable(scenes, "generated_scenes.txt")
    
    print(f"\n\nTotal scenes generated: {len(scenes)}")
    print("\nFiles created:")
    print("  - generated_scenes.json (structured data)")
    print("  - generated_scenes.txt (readable format)")


if __name__ == '__main__':
    main()
