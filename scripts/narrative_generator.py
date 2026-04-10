#!/usr/bin/env python3
"""
Narrative Generator for Hobbit Journey Stream
Pre-generates rich storytelling content for all scenes.
Supports multiple narrative modes and pacing styles.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class NarrativeStyle:
    """Configuration for a narrative style."""
    name: str
    description: str
    prompt_template: str
    max_words: int
    tone: str


# Define narrative styles
NARRATIVE_STYLES = {
    "immersive": NarrativeStyle(
        name="immersive",
        description="Second-person immersive experience",
        prompt_template="""You are experiencing this moment firsthand. 
Describe the scene using second-person perspective ('you feel', 'you see').
Include sensory details: sights, sounds, smells, temperature, textures.
Scene: {title}
Location: {location}
Time: {time}, {date}
Characters present: {characters}
Content: {content}

Write 2-3 paragraphs of immersive prose.""",
        max_words=200,
        tone="intimate, sensory-rich"
    ),
    
    "cinematic": NarrativeStyle(
        name="cinematic",
        description="Movie-like scene description",
        prompt_template="""Describe this scene as if directing a film.
Include: camera movements, lighting, framing, atmosphere.
Scene: {title}
Location: {location}
Time: {time}, {date}
Characters: {characters}
Content: {content}

Write a cinematic scene description in present tense.""",
        max_words=150,
        tone="visual, dramatic"
    ),
    
    "literary": NarrativeStyle(
        name="literary",
        description="Tolkien-esque prose style",
        prompt_template="""Write in the style of J.R.R. Tolkien.
Use elevated language, attention to landscape, mythic resonance.
Scene: {title}
Location: {location}
Time: {time}, {date}
Characters: {characters}
Content: {content}

Write 1-2 paragraphs in Tolkien's narrative voice.""",
        max_words=180,
        tone="elevated, pastoral, mythic"
    ),
    
    "minimal": NarrativeStyle(
        name="minimal",
        description="Sparse, haiku-like descriptions",
        prompt_template="""Distill this scene to its essence.
Use brief, evocative phrases. Minimal adjectives. Maximum impact.
Scene: {title}
Location: {location}
Content: {content}

Write 2-3 short sentences.""",
        max_words=50,
        tone="sparse, poetic"
    ),
    
    "character_pov": NarrativeStyle(
        name="character_pov",
        description="First-person character perspective",
        prompt_template="""Write from {pov_character}'s perspective.
Show their thoughts, fears, hopes, observations.
Use first-person ('I', 'me', 'my').
Scene: {title}
Location: {location}
Content: {content}

Write as {pov_character}'s personal account.""",
        max_words=150,
        tone="personal, subjective"
    )
}


class NarrativeGenerator:
    """Generates and manages narrative content for scenes."""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.scenes = []
        self.narratives = {}
        self.output_file = '../data/scene_narratives.json'
        
    def load_scenes(self):
        """Load merged scenes (canonical + generated)."""
        # Load canonical scenes
        with open('../data/stream_scenes.json', 'r') as f:
            canon_data = json.load(f)
        canonical = canon_data['scenes']
        
        # Load and merge generated scenes
        with open('../data/generated_gap_scenes.json', 'r') as f:
            gap_data = json.load(f)
        generated = gap_data['generated_scenes']
        
        self.scenes = self._merge_scenes(canonical, generated)
        print(f"Loaded {len(self.scenes)} total scenes")
        
    def _merge_scenes(self, canonical, generated):
        """Merge scenes in chronological order."""
        generated_by_gap = {}
        for scene in generated:
            gap_id = scene.get('parent_gap_id', '')
            if gap_id not in generated_by_gap:
                generated_by_gap[gap_id] = []
            generated_by_gap[gap_id].append(scene)
        
        def parse_position(pos):
            if not pos:
                return (1, 1)
            try:
                parts = str(pos).split('/')
                return (int(parts[0]), int(parts[1]))
            except:
                return (1, 1)
        
        for gap_id in generated_by_gap:
            generated_by_gap[gap_id].sort(
                key=lambda s: parse_position(s.get('position_in_gap', '1/1'))
            )
        
        canon_id_to_index = {s.get('id', f'canon_{i+1:03d}'): i 
                            for i, s in enumerate(canonical)}
        gap_insert_positions = {}
        
        if os.path.exists('../data/generated_gap_scenes.json'):
            with open('../data/generated_gap_scenes.json', 'r') as f:
                gap_data = json.load(f)
            for gap in gap_data.get('gaps', []):
                from_id = gap.get('from_scene', {}).get('id', '')
                if from_id in canon_id_to_index:
                    gap_insert_positions[gap['gap_id']] = canon_id_to_index[from_id]
        
        merged = []
        for i, canon_scene in enumerate(canonical):
            merged.append(canon_scene)
            for gap_id, insert_pos in gap_insert_positions.items():
                if insert_pos == i and gap_id in generated_by_gap:
                    merged.extend(generated_by_gap[gap_id])
        
        return merged
    
    def generate_template_narrative(self, scene: Dict, style: NarrativeStyle) -> str:
        """Generate narrative using template (no LLM)."""
        title = scene.get('title', 'Unknown Scene')
        location = scene.get('location', 'Unknown Location')
        time = scene.get('time', 'Unknown Time')
        date = scene.get('date', '')
        content = scene.get('content', scene.get('summary', ''))
        characters = scene.get('characters', [])
        
        # Determine POV character
        pov = 'Bilbo'
        if 'Gollum' in characters and 'Bilbo' not in characters:
            pov = 'Gollum'
        elif 'Smaug' in title:
            pov = 'Bilbo'
        
        # Truncate content for brevity
        content_preview = content[:200] + '...' if len(content) > 200 else content
        
        if style.name == "immersive":
            return self._immersive_template(title, location, time, characters, content_preview)
        elif style.name == "cinematic":
            return self._cinematic_template(title, location, time, characters, content_preview)
        elif style.name == "literary":
            return self._literary_template(title, location, time, date, characters, content_preview)
        elif style.name == "minimal":
            return self._minimal_template(title, location, characters)
        elif style.name == "character_pov":
            return self._character_pov_template(title, location, pov, content_preview)
        
        return content_preview
    
    def _immersive_template(self, title, location, time, characters, content):
        """Generate immersive second-person narrative."""
        atmosphere = self._get_location_atmosphere(location)
        
        lines = [
            f"You are in {location}. The {time.lower()} air {atmosphere['air']}.",
            f"{atmosphere['sensory']}",
            "",
            f"{content[:150]}...",
            "",
            f"Around you: {', '.join(characters[:5]) if characters else 'No one else is visible'}."
        ]
        return '\n'.join(lines)
    
    def _cinematic_template(self, title, location, time, characters, content):
        """Generate cinematic description."""
        lighting = self._get_lighting(time)
        
        lines = [
            f"[EXT. {location.upper()} - {time.upper()}]",
            "",
            f"The camera PANS across {location}. {lighting}",
            "",
            f"CHARACTERS: {', '.join(characters) if characters else 'None'}",
            "",
            f"ACTION: {content[:120]}..."
        ]
        return '\n'.join(lines)
    
    def _literary_template(self, title, location, time, date, characters, content):
        """Generate Tolkien-esque prose."""
        lines = [
            f"In those days, upon the {date if date else 'long road'}, the Company found themselves in {location}.",
            "",
            f"{content[:180]}...",
            "",
            f"Thus did {characters[0] if characters else 'the traveller'} ponder the ways of the world."
        ]
        return '\n'.join(lines)
    
    def _minimal_template(self, title, location, characters):
        """Generate minimal description."""
        desc = self._get_minimal_description(location)
        return f"{location}. {desc} {characters[0] if characters else 'A lone figure'}."
    
    def _character_pov_template(self, title, location, pov, content):
        """Generate first-person character perspective."""
        thoughts = self._get_character_thoughts(pov, location)
        
        lines = [
            f"I am {pov}, and this is my account:",
            "",
            f"{content[:120]}...",
            "",
            f"My thoughts: {thoughts}"
        ]
        return '\n'.join(lines)
    
    def _get_location_atmosphere(self, location: str) -> Dict:
        """Get atmospheric details for a location."""
        location_lower = location.lower()
        
        atmospheres = {
            'hobbiton': {'air': 'smells of pipe-weed and freshly baked bread', 
                        'sensory': "Birds chirp in the gardens. The Green Dragon's laughter drifts from down the hill."},
            'rivendell': {'air': 'carries the scent of elanor and clear water',
                         'sensory': 'Elvish songs echo through the Last Homely House. Waterfalls murmur nearby.'},
            'mirkwood': {'air': 'is thick with the smell of decay and pine',
                        'sensory': 'Darkness presses close. Spider webs catch what little light filters through.'},
            'erebor': {'air': 'tastes of stone and ancient dust',
                      'sensory': 'The vast halls of the Lonely Mountain loom. Gold glitters in shadows.'},
            'lake-town': {'air': 'smells of fish and woodsmoke',
                         'sensory': 'Wooden walkways creak. Water laps against the pilings of the town.'},
            'default': {'air': 'holds the promise of adventure',
                       'sensory': 'The road stretches on, leading to unknown destinations.'}
        }
        
        for key, value in atmospheres.items():
            if key in location_lower:
                return value
        return atmospheres['default']
    
    def _get_lighting(self, time: str) -> str:
        """Get lighting description for time of day."""
        time_lower = time.lower()
        
        if 'morning' in time_lower or 'dawn' in time_lower:
            return "Golden morning light breaks through, casting long shadows."
        elif 'noon' in time_lower or 'midday' in time_lower:
            return "Harsh midday sun beats down from above."
        elif 'evening' in time_lower or 'dusk' in time_lower:
            return "The dying light paints everything in shades of orange and purple."
        elif 'night' in time_lower or 'dark' in time_lower:
            return "Darkness envelops the scene, broken only by stars and firelight."
        return "Light filters through, revealing the scene."
    
    def _get_minimal_description(self, location: str) -> str:
        """Get minimal location description."""
        descriptions = {
            'hobbiton': 'Green hills. Round doors.',
            'rivendell': 'White towers. Waterfalls.',
            'mirkwood': 'Dark trees. Spider webs.',
            'erebor': 'Gold halls. Dragon shadow.',
            'lake-town': 'Wooden houses. Water.',
            'trollshaw': 'Stunted trees. Stone.',
            'carrock': 'Rising stone. Eagles overhead.'
        }
        
        location_lower = location.lower()
        for key, desc in descriptions.items():
            if key in location_lower:
                return desc
        return 'Unknown paths lead onward.'
    
    def _get_character_thoughts(self, character: str, location: str) -> str:
        """Get internal thoughts for a character."""
        thoughts = {
            'Bilbo': ['I wish I was back in my warm hole.', 
                     'Adventures are not all pony-rides in May-sunshine.',
                     'I wonder what Gandalf is planning.',
                     'I do believe the worst is behind us.'],
            'Thorin': ['The Arkenstone must be recovered.',
                      'These dwarves look to me for leadership.',
                      'We will reclaim Erebor or die trying.'],
            'Gandalf': ['There is more to this hobbit than meets the eye.',
                       'Darkness gathers. Time is short.',
                       'I have business elsewhere, but I must see them through.'],
            'Gollum': ['The Baggins has the Precious.',
                      'It wants it. It needs it.',
                      'We must be cunning, yes, precious.']
        }
        
        import random
        character_thoughts = thoughts.get(character, ['The road goes ever on.'])
        return random.choice(character_thoughts)
    
    def generate_all_narratives(self):
        """Generate narratives for all scenes in all styles."""
        if not self.scenes:
            self.load_scenes()
        
        print("Generating narratives for all scenes...")
        
        narratives = {}
        
        for i, scene in enumerate(self.scenes):
            scene_id = scene.get('id', f'scene_{i:03d}')
            
            narratives[scene_id] = {
                'title': scene.get('title', 'Unknown'),
                'styles': {}
            }
            
            for style_name, style in NARRATIVE_STYLES.items():
                narrative = self.generate_template_narrative(scene, style)
                narratives[scene_id]['styles'][style_name] = {
                    'text': narrative,
                    'word_count': len(narrative.split()),
                    'style': style.name
                }
            
            if (i + 1) % 50 == 0:
                print(f"  Generated {i + 1}/{len(self.scenes)} scenes...")
        
        self.narratives = narratives
        self.save_narratives()
        
        print(f"Generated {len(narratives)} scene narratives")
        print(f"Styles: {list(NARRATIVE_STYLES.keys())}")
    
    def save_narratives(self):
        """Save narratives to JSON file."""
        output = {
            'metadata': {
                'total_scenes': len(self.narratives),
                'styles': list(NARRATIVE_STYLES.keys()),
                'version': '1.0.0'
            },
            'scenes': self.narratives
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Saved narratives to {self.output_file}")
    
    def load_narratives(self) -> bool:
        """Load narratives from JSON file."""
        if not os.path.exists(self.output_file):
            return False
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.narratives = data.get('scenes', {})
        print(f"Loaded {len(self.narratives)} narratives from {self.output_file}")
        return True


def main():
    """Generate all scene narratives."""
    generator = NarrativeGenerator(use_llm=False)
    generator.load_scenes()
    generator.generate_all_narratives()
    
    # Print a sample
    print("\n" + "="*60)
    print("SAMPLE NARRATIVES")
    print("="*60)
    
    sample_ids = list(generator.narratives.keys())[:3]
    for scene_id in sample_ids:
        scene_data = generator.narratives[scene_id]
        print(f"\n{scene_data['title']} ({scene_id})")
        print("-" * 40)
        
        for style_name, style_data in scene_data['styles'].items():
            print(f"\n[{style_name}] ({style_data['word_count']} words):")
            print(style_data['text'][:200] + "..." if len(style_data['text']) > 200 else style_data['text'])


if __name__ == "__main__":
    main()
