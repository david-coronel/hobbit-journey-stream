#!/usr/bin/env python3
"""
Narrative Beat System for Hobbit Journey Stream
Generates time-based narrative beats for progressive revelation.
"""

import json
import os
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class NarrativeBeat:
    """A single narrative beat with timing info."""
    start_percent: float
    end_percent: float
    text: str
    beat_type: str


class NarrativeBeatGenerator:
    """Generates narrative beats for scenes based on duration and type."""
    
    def __init__(self):
        self.scenes = []
        self.beats = {}
        
    def load_scenes(self):
        """Load merged scenes."""
        with open('../data/stream_scenes.json', 'r') as f:
            canon_data = json.load(f)
        canonical = canon_data['scenes']
        
        with open('../data/generated_gap_scenes.json', 'r') as f:
            gap_data = json.load(f)
        generated = gap_data['generated_scenes']
        
        self.scenes = self._merge_scenes(canonical, generated)
        print(f"Loaded {len(self.scenes)} scenes")
        
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
            generated_by_gap[gap_id].sort(key=lambda s: parse_position(s.get('position_in_gap', '1/1')))
        
        canon_id_to_index = {s.get('id', f'canon_{i+1:03d}'): i for i, s in enumerate(canonical)}
        gap_insert_positions = {}
        
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
    
    def determine_scene_type(self, scene: Dict) -> str:
        """Determine the narrative type of a scene."""
        content = scene.get('content', '').lower()
        title = scene.get('title', '').lower()
        gap_type = scene.get('gap_type', '')
        
        action_keywords = ['attack', 'battle', 'fight', 'escape', 'captured', 'flee', 'rescue']
        if any(kw in title or kw in content for kw in action_keywords):
            return 'action'
        
        if '"' in scene.get('content', '') or 'conversation' in title:
            return 'conversation'
        
        if gap_type == 'recuperation' or any(kw in title for kw in ['camp', 'rest', 'sleep', 'night']):
            return 'rest'
        
        return 'travel'
    
    def get_duration_hours(self, scene: Dict) -> float:
        """Get scene duration in hours."""
        if 'story_duration' in scene:
            sd = scene['story_duration']
            dur = sd.get('duration', 1)
            unit = sd.get('unit', 'hours')
            if unit == 'days':
                return dur * 24
            elif unit == 'minutes':
                return dur / 60
            return dur
        elif 'duration_hours' in scene:
            return scene['duration_hours']
        return 2.0
    
    def generate_beats(self, scene: Dict) -> List[NarrativeBeat]:
        """Generate narrative beats for a scene."""
        scene_type = self.determine_scene_type(scene)
        duration_hours = self.get_duration_hours(scene)
        location = scene.get('location', 'Unknown')
        time_of_day = scene.get('time', 'Day')
        
        # Determine number of beats based on duration
        if duration_hours < 1:
            num_beats = 3
        elif duration_hours < 4:
            num_beats = 4
        elif duration_hours < 8:
            num_beats = 5
        else:
            num_beats = 6
        
        beats = []
        
        # Generate beats based on scene type
        if scene_type == 'travel':
            beat_types = self._get_travel_structure(num_beats)
        elif scene_type == 'conversation':
            beat_types = self._get_conversation_structure(num_beats)
        elif scene_type == 'action':
            beat_types = self._get_action_structure(num_beats)
        else:
            beat_types = self._get_rest_structure(num_beats)
        
        for i, beat_type in enumerate(beat_types):
            start_pct = i / len(beat_types)
            end_pct = (i + 1) / len(beat_types)
            
            text = self._generate_beat_text(
                beat_type, scene_type, location, time_of_day, i, len(beat_types)
            )
            
            beats.append(NarrativeBeat(
                start_percent=start_pct,
                end_percent=end_pct,
                text=text,
                beat_type=beat_type
            ))
        
        return beats
    
    def _get_travel_structure(self, num_beats: int) -> List[str]:
        if num_beats == 3:
            return ['setup', 'atmosphere', 'resolution']
        elif num_beats == 4:
            return ['setup', 'atmosphere', 'rising', 'resolution']
        elif num_beats == 5:
            return ['setup', 'atmosphere', 'rising', 'atmosphere', 'resolution']
        else:
            return ['setup', 'atmosphere', 'rising', 'atmosphere', 'rising', 'resolution']
    
    def _get_conversation_structure(self, num_beats: int) -> List[str]:
        if num_beats == 3:
            return ['setup', 'rising', 'resolution']
        elif num_beats == 4:
            return ['setup', 'rising', 'climax', 'resolution']
        else:
            return ['setup', 'atmosphere', 'rising', 'climax', 'resolution']
    
    def _get_action_structure(self, num_beats: int) -> List[str]:
        if num_beats == 3:
            return ['setup', 'climax', 'resolution']
        elif num_beats == 4:
            return ['setup', 'rising', 'climax', 'resolution']
        else:
            return ['setup', 'rising', 'climax', 'atmosphere', 'resolution']
    
    def _get_rest_structure(self, num_beats: int) -> List[str]:
        if num_beats == 3:
            return ['setup', 'atmosphere', 'resolution']
        elif num_beats == 4:
            return ['setup', 'rising', 'atmosphere', 'resolution']
        else:
            return ['setup', 'atmosphere', 'rising', 'atmosphere', 'resolution']
    
    def _generate_beat_text(self, beat_type: str, scene_type: str, location: str, 
                           time_of_day: str, beat_index: int, total_beats: int) -> str:
        """Generate text for a single beat."""
        import random
        
        # Location-based atmosphere
        location_lower = location.lower()
        
        # Determine environment details
        if 'hobbiton' in location_lower or 'shire' in location_lower:
            sights = ['round green doors', 'smoke from chimneys', 'well-tended gardens']
            sounds = ['birdsong', 'distant laughter', 'clinking of dishes']
            smells = ['pipe-weed', 'fresh bread', 'cut grass']
            terrain = 'gentle hills'
        elif 'rivendell' in location_lower:
            sights = ['white towers', 'waterfalls', 'elven lanterns']
            sounds = ['elvish singing', 'flowing water', 'harp music']
            smells = ['elanor flowers', 'clear water', 'old books']
            terrain = 'elf-roads'
        elif 'mirkwood' in location_lower:
            sights = ['dark trees', 'spider webs', 'dim light']
            sounds = ['rustling leaves', 'distant growls', 'creaking branches']
            smells = ['decay', 'stagnant water', 'pine resin']
            terrain = 'dark forest'
        elif 'misty' in location_lower or 'mountain' in location_lower:
            sights = ['sheer cliffs', 'snow peaks', 'goat paths']
            sounds = ['howling wind', 'falling rocks', 'distant thunder']
            smells = ['cold stone', 'thin air', 'snow']
            terrain = 'mountain paths'
        elif 'erebor' in location_lower or 'dragon' in location_lower:
            sights = ['golden halls', 'vast treasure', 'ancient statues']
            sounds = ['dripping water', 'echoes', 'shifting gold']
            smells = ['old stone', 'sulfur', 'dragon']
            terrain = 'dwarf-halls'
        elif 'lake' in location_lower or 'esgaroth' in location_lower:
            sights = ['wooden houses', 'fishing boats', 'the Mountain']
            sounds = ['water lapping', 'market chatter', 'fishmongers']
            smells = ['fish', 'woodsmoke', 'lake water']
            terrain = 'wooden walkways'
        else:
            sights = ['the open road', 'distant hills', 'passing clouds']
            sounds = ['wind', 'your footsteps', 'distant birds']
            smells = ['earth', 'grass', 'dust']
            terrain = 'winding paths'
        
        # Generate beat based on type
        if beat_type == 'setup':
            setups = [
                f"The journey begins. {random.choice(sights)} mark the way ahead.",
                f"You set out as {time_of_day.lower()} breaks over {location}.",
                f"The {terrain} stretch before you, {random.choice(smells)} on the air.",
                f"The road winds through {location}, {random.choice(sounds)} echoing."
            ]
            return random.choice(setups)
        
        elif beat_type == 'rising':
            risings = [
                f"Time passes. Your legs ache from the {terrain}.",
                f"The landscape shifts. {random.choice(sights)} appear in the distance.",
                f"Hours slip by. {random.choice(sounds)} make you wary.",
                f"The air changes - {random.choice(smells)} grows stronger.",
                f"Fatigue sets in as the {terrain} continue endlessly."
            ]
            return random.choice(risings)
        
        elif beat_type == 'climax':
            climaxes = [
                f"A sound freezes your blood - something {random.choice(sounds)} nearby!",
                f"The path vanishes! You are surrounded by {random.choice(sights)}.",
                f"You realize with horror: you are not alone in {location}.",
                f"The moment of crisis arrives. Heart pounding, you prepare."
            ]
            return random.choice(climaxes)
        
        elif beat_type == 'resolution':
            resolutions = [
                f"At last - {location} comes into view through {random.choice(sights)}.",
                f"You arrive, {random.choice(smells)} marking the end of this leg.",
                f"The journey segment ends. {random.choice(sounds)} welcome your arrival.",
                f"Safe for now. You rest among {random.choice(sights)}."
            ]
            return random.choice(resolutions)
        
        else:  # atmosphere
            atmospheres = [
                f"{random.choice(sights)} surround you. {random.choice(sounds)} fill the air.",
                f"The scent of {random.choice(smells)} drifts by on a gentle breeze.",
                f"You pause, taking in {random.choice(sights)} as {time_of_day.lower()} continues.",
                f"The {terrain} seem endless. {random.choice(sounds)} are your only company.",
                f"A moment of peace. {random.choice(smells)} reminds you of distant comforts."
            ]
            return random.choice(atmospheres)
    
    def generate_all_beats(self):
        """Generate beats for all scenes."""
        if not self.scenes:
            self.load_scenes()
        
        print("Generating narrative beats...")
        
        for i, scene in enumerate(self.scenes):
            scene_id = scene.get('id', f'scene_{i:03d}')
            beats = self.generate_beats(scene)
            
            self.beats[scene_id] = {
                'title': scene.get('title', 'Unknown'),
                'location': scene.get('location', 'Unknown'),
                'duration_hours': self.get_duration_hours(scene),
                'scene_type': self.determine_scene_type(scene),
                'beats': [
                    {
                        'start': b.start_percent,
                        'end': b.end_percent,
                        'text': b.text,
                        'type': b.beat_type
                    }
                    for b in beats
                ]
            }
            
            if (i + 1) % 50 == 0:
                print(f"  Generated {i + 1}/{len(self.scenes)} scenes...")
        
        self.save_beats()
        print(f"Generated beats for {len(self.beats)} scenes")
    
    def save_beats(self):
        """Save beats to JSON."""
        output = {
            'metadata': {
                'total_scenes': len(self.beats),
                'beat_types': ['setup', 'rising', 'climax', 'resolution', 'atmosphere'],
                'version': '1.0.0'
            },
            'scenes': self.beats
        }
        
        with open('../data/scene_beats.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print("Saved beats to scene_beats.json")
    
    def get_current_beat(self, scene_id: str, elapsed_percent: float) -> Dict:
        """Get the beat for a given elapsed time percentage."""
        if scene_id not in self.beats:
            return None
        
        scene_beats = self.beats[scene_id]['beats']
        
        for beat in scene_beats:
            if beat['start'] <= elapsed_percent < beat['end']:
                return beat
        
        return scene_beats[-1] if scene_beats else None


def main():
    """Generate all narrative beats."""
    generator = NarrativeBeatGenerator()
    generator.load_scenes()
    generator.generate_all_beats()
    
    # Show samples
    print("\n" + "="*60)
    print("SAMPLE BEATS")
    print("="*60)
    
    sample_ids = list(generator.beats.keys())[:3]
    for scene_id in sample_ids:
        scene_data = generator.beats[scene_id]
        print(f"\n{scene_data['title']}")
        print(f"Type: {scene_data['scene_type']} | Duration: {scene_data['duration_hours']:.1f}h")
        print("-" * 40)
        
        for beat in scene_data['beats']:
            print(f"[{beat['start']*100:>3.0f}%-{beat['end']*100:>3.0f}%] ({beat['type']:12}) {beat['text']}")


if __name__ == "__main__":
    main()
