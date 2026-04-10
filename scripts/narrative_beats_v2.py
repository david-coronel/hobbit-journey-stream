#!/usr/bin/env python3
"""
Narrative Beat System v2 - Progressive Revelation
Generates consistent, entertaining beats that build over time.
"""

import json
import os
import re
from typing import List, Dict


class ProgressiveNarrativeGenerator:
    """Generates progressive narrative beats that build over time."""
    
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
    
    def split_text_into_beats(self, text: str, num_beats: int) -> List[str]:
        """Split text into roughly equal narrative chunks."""
        # Clean up text
        text = text.strip()
        if not text:
            return ["The scene unfolds..."] * num_beats
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < num_beats:
            # Pad with continuation phrases
            while len(sentences) < num_beats:
                sentences.append("The moment continues...")
        
        # Group sentences into beats
        beats = []
        chunk_size = len(sentences) // num_beats
        remainder = len(sentences) % num_beats
        
        start = 0
        for i in range(num_beats):
            size = chunk_size + (1 if i < remainder else 0)
            end = start + size
            beat_sentences = sentences[start:end]
            beats.append(' '.join(beat_sentences))
            start = end
        
        return beats
    
    def generate_canonical_beats(self, scene: Dict) -> List[Dict]:
        """Generate beats for canonical scenes using book text."""
        duration_hours = self.get_duration_hours(scene)
        content = scene.get('content', '')
        
        # Determine number of beats based on duration
        if duration_hours < 1:
            num_beats = 3
        elif duration_hours < 3:
            num_beats = 4
        elif duration_hours < 8:
            num_beats = 5
        else:
            num_beats = 6
        
        # Split content into beats
        beat_texts = self.split_text_into_beats(content, num_beats)
        
        beats = []
        for i, text in enumerate(beat_texts):
            start_pct = i / num_beats
            end_pct = (i + 1) / num_beats
            
            # Determine beat type based on position
            if i == 0:
                beat_type = 'opening'
            elif i == num_beats - 1:
                beat_type = 'conclusion'
            elif i < num_beats // 2:
                beat_type = 'development'
            else:
                beat_type = 'climax'
            
            beats.append({
                'start': start_pct,
                'end': end_pct,
                'text': text,
                'type': beat_type
            })
        
        return beats
    
    def generate_travel_narrative(self, scene: Dict, num_beats: int) -> List[str]:
        """Generate a continuous travel narrative with escalating detail."""
        location = scene.get('location', 'Unknown')
        duration = self.get_duration_hours(scene)
        characters = scene.get('characters', ['The Company'])
        main_char = characters[0] if characters else 'The traveler'
        
        # Create a continuous journey story
        narratives = []
        
        # Beat 1: Departure
        narratives.append(
            f"{main_char} sets out from {location}. The road ahead is uncertain, "
            f"but the journey of {duration:.0f} hours must be made."
        )
        
        # Middle beats: Progressive challenges
        middle_beats = num_beats - 2
        for i in range(middle_beats):
            progress = (i + 1) / (middle_beats + 1)
            hours_passed = duration * progress
            
            if progress < 0.3:
                # Early journey - establishing
                narratives.append(
                    f"An hour passes. Then another. {main_char} presses on, "
                    f"the landscape gradually shifting around them."
                )
            elif progress < 0.6:
                # Mid journey - fatigue sets in
                narratives.append(
                    f"After {hours_passed:.0f} hours, weariness creeps in. "
                    f"Each step feels heavier than the last, but stopping is not an option."
                )
            else:
                # Late journey - approaching destination
                narratives.append(
                    f"The end is near. With only {duration - hours_passed:.0f} hours remaining, "
                    f"{main_char} finds renewed strength in the approaching goal."
                )
        
        # Final beat: Arrival
        narratives.append(
            f"At last, after {duration:.0f} hours of travel, the destination is reached. "
            f"{main_char} collapses to rest, the journey complete for now."
        )
        
        return narratives
    
    def generate_wait_narrative(self, scene: Dict, num_beats: int) -> List[str]:
        """Generate waiting/recuperation narrative."""
        location = scene.get('location', 'Unknown')
        duration = self.get_duration_hours(scene)
        characters = scene.get('characters', ['The Company'])
        main_char = characters[0] if characters else 'The traveler'
        
        narratives = []
        
        # Beat 1: Settling in
        narratives.append(
            f"{main_char} makes camp at {location}. The {duration:.0f}-hour rest begins, "
            f"a welcome pause in the long journey."
        )
        
        # Middle beats: Time passing
        middle_beats = num_beats - 2
        for i in range(middle_beats):
            progress = (i + 1) / (middle_beats + 1)
            hours_passed = duration * progress
            
            if progress < 0.4:
                # Rest phase
                narratives.append(
                    f"Sleep comes slowly. {hours_passed:.0f} hours into the rest, "
                    f"exhaustion finally claims {main_char}."
                )
            elif progress < 0.7:
                # Dreams/waking
                narratives.append(
                    f"Hours later, {main_char} wakes with a start. Was that a dream, "
                    f"or something moving in the dark?"
                )
            else:
                # Preparing to depart
                narratives.append(
                    f"With only {duration - hours_passed:.0f} hours left, {main_char} "
                    f"rises and prepares for the road ahead."
                )
        
        # Final beat: Departure
        narratives.append(
            f"The {duration:.0f}-hour rest ends. {main_char} gathers their strength "
            f"and sets out once more, ready for what comes next."
        )
        
        return narratives
    
    def generate_generated_beats(self, scene: Dict) -> List[Dict]:
        """Generate beats for generated scenes with continuous narrative."""
        duration_hours = self.get_duration_hours(scene)
        content = scene.get('content', '')
        gap_type = scene.get('gap_type', 'travel')
        
        # Determine number of beats
        if duration_hours < 1:
            num_beats = 3
        elif duration_hours < 3:
            num_beats = 4
        elif duration_hours < 8:
            num_beats = 5
        else:
            num_beats = 6
        
        # Try to use existing content as a base
        if content and len(content) > 100:
            # Use content as base, split into beats
            beat_texts = self.split_text_into_beats(content, num_beats)
        else:
            # Generate based on gap type
            if gap_type == 'recuperation' or 'wait' in scene.get('title', '').lower():
                beat_texts = self.generate_wait_narrative(scene, num_beats)
            else:
                beat_texts = self.generate_travel_narrative(scene, num_beats)
        
        beats = []
        for i, text in enumerate(beat_texts):
            start_pct = i / num_beats
            end_pct = (i + 1) / num_beats
            
            if i == 0:
                beat_type = 'beginning'
            elif i == num_beats - 1:
                beat_type = 'end'
            else:
                beat_type = 'progress'
            
            beats.append({
                'start': start_pct,
                'end': end_pct,
                'text': text,
                'type': beat_type
            })
        
        return beats
    
    def is_canonical_scene(self, scene: Dict) -> bool:
        """Determine if a scene is canonical based on its fields."""
        # Canonical scenes have 'is_canonical' = True or don't have 'parent_gap_id'
        if 'is_canonical' in scene:
            return scene['is_canonical']
        # Generated scenes have parent_gap_id
        if 'parent_gap_id' in scene:
            return False
        return True
    
    def generate_beats(self, scene: Dict) -> List[Dict]:
        """Generate appropriate beats for any scene type."""
        is_canon = self.is_canonical_scene(scene)
        
        if is_canon:
            return self.generate_canonical_beats(scene)
        else:
            return self.generate_generated_beats(scene)
    
    def generate_all_beats(self):
        """Generate beats for all scenes."""
        if not self.scenes:
            self.load_scenes()
        
        print("Generating progressive narrative beats...")
        
        for i, scene in enumerate(self.scenes):
            scene_id = scene.get('id', f'scene_{i:03d}')
            beats = self.generate_beats(scene)
            
            self.beats[scene_id] = {
                'title': scene.get('title', 'Unknown'),
                'location': scene.get('location', 'Unknown'),
                'duration_hours': self.get_duration_hours(scene),
                'is_canonical': self.is_canonical_scene(scene),
                'beats': beats
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
                'note': 'Progressive revelation - beats build over time',
                'version': '2.0.0'
            },
            'scenes': self.beats
        }
        
        with open('../data/scene_beats.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print("Saved beats to scene_beats.json")


def main():
    """Generate all narrative beats."""
    generator = ProgressiveNarrativeGenerator()
    generator.load_scenes()
    generator.generate_all_beats()
    
    # Show samples
    print("\n" + "="*70)
    print("SAMPLE: Canonical Scene")
    print("="*70)
    
    # Find a canonical scene
    for scene_id, data in list(generator.beats.items())[:5]:
        if data['is_canonical']:
            print(f"\n{data['title']}")
            print(f"Duration: {data['duration_hours']:.1f}h | Beats: {len(data['beats'])}")
            print("-" * 50)
            for beat in data['beats']:
                text = beat['text'][:80] + "..." if len(beat['text']) > 80 else beat['text']
                print(f"[{beat['start']*100:>3.0f}%-{beat['end']*100:>3.0f}%] {text}")
            break
    
    print("\n" + "="*70)
    print("SAMPLE: Generated Scene")
    print("="*70)
    
    # Find a generated scene
    for scene_id, data in generator.beats.items():
        if not data['is_canonical']:
            print(f"\n{data['title']}")
            print(f"Duration: {data['duration_hours']:.1f}h | Beats: {len(data['beats'])}")
            print("-" * 50)
            for beat in data['beats']:
                text = beat['text'][:80] + "..." if len(beat['text']) > 80 else beat['text']
                print(f"[{beat['start']*100:>3.0f}%-{beat['end']*100:>3.0f}%] {text}")
            break


if __name__ == "__main__":
    main()
