"""
Scene Manager - Orchestrates canonical events and generated scenes for display.
Creates a unified timeline mixing real narrative with generated filler scenes.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


class SceneManager:
    """Manages the flow between canonical events and generated scenes."""
    
    def __init__(self, timeline_path="hobbit_realistic_timeline.json",
                 scenes_path="generated_scenes.json",
                 characters_path="hobbit_characters.json",
                 places_path="hobbit_places.json"):
        with open(timeline_path) as f:
            self.timeline = json.load(f)
        
        with open(scenes_path) as f:
            self.generated_scenes = json.load(f)
        
        with open(characters_path) as f:
            self.characters = json.load(f)
            
        with open(places_path) as f:
            self.places = json.load(f)
        
        # Build unified scene list
        self.all_scenes = []
        self.current_index = 0
        self._build_unified_timeline()
    
    def _build_unified_timeline(self):
        """Merge canonical events and generated scenes into ordered list."""
        # Get canonical scene-type entries
        timeline_data = self.timeline.get('entries', self.timeline) if isinstance(self.timeline, dict) else self.timeline
        canonical = [e for e in timeline_data if e.get('type') == 'scene']
        
        # Get generated scenes
        generated = self.generated_scenes.get('scenes', [])
        
        # Create unified list with source tracking
        all_entries = []
        
        for entry in canonical:
            all_entries.append({
                'source': 'canonical',
                'date': entry.get('date'),
                'time': entry.get('time'),
                'location': entry.get('location'),
                'title': entry.get('title'),
                'summary': entry.get('summary'),
                'chapter': entry.get('chapter'),
                'characters': entry.get('characters', []),
                'type': 'canonical'
            })
        
        for scene in generated:
            # Extract time from text if not present (e.g., "Morning found them...")
            text = scene.get('text', '')
            time = scene.get('time_of_day')
            if not time and text:
                time_words = ['morning', 'midday', 'noon', 'afternoon', 'evening', 'night', 'dawn']
                for tw in time_words:
                    if text.lower().startswith(tw):
                        time = tw
                        break
            
            # Get date from 'between' array
            date = scene.get('date')
            if not date and 'between' in scene:
                date = scene['between'][0] if scene['between'] else None
            
            # Create title from type and location
            loc = scene.get('location', 'Unknown').title()
            scene_type = scene.get('type', 'scene')
            title = f"{scene_type.title()} in {loc}"
            
            all_entries.append({
                'source': 'generated',
                'date': date,
                'time': time,
                'location': loc,
                'title': title,
                'content': text,
                'characters_present': scene.get('characters', []),
                'scene_type': scene_type,
                'type': 'generated'
            })
        
        # Sort by date, then by time of day
        time_order = {'dawn': 0, 'morning': 1, 'noon': 2, 'afternoon': 3, 
                      'evening': 4, 'night': 5}
        
        def sort_key(entry):
            if not entry:
                return ('2941-04-01', 3)
            date = entry.get('date') or '2941-04-01'
            time = (entry.get('time') or '').lower()
            time_val = time_order.get(time, 3)
            return (date, time_val)
        
        all_entries.sort(key=sort_key)
        self.all_scenes = all_entries
        print(f"Built unified timeline: {len(self.all_scenes)} total scenes")
        print(f"  - Canonical: {len([s for s in self.all_scenes if s['type'] == 'canonical'])}")
        print(f"  - Generated: {len([s for s in self.all_scenes if s['type'] == 'generated'])}")
    
    def get_current_scene(self):
        """Get the current scene."""
        if 0 <= self.current_index < len(self.all_scenes):
            return self.all_scenes[self.current_index]
        return None
    
    def next_scene(self):
        """Advance to next scene."""
        if self.current_index < len(self.all_scenes) - 1:
            self.current_index += 1
        return self.get_current_scene()
    
    def previous_scene(self):
        """Go back to previous scene."""
        if self.current_index > 0:
            self.current_index -= 1
        return self.get_current_scene()
    
    def jump_to_date(self, date_str):
        """Jump to scenes on a specific date."""
        for i, scene in enumerate(self.all_scenes):
            if scene.get('date') == date_str:
                self.current_index = i
                return scene
        return None
    
    def get_time_until_next_canonical(self):
        """Calculate time remaining until next canonical event."""
        current = self.get_current_scene()
        if not current:
            return None
        
        current_date = current.get('date')
        current_idx = self.current_index
        
        # Find next canonical event
        for i in range(current_idx + 1, len(self.all_scenes)):
            if self.all_scenes[i]['type'] == 'canonical':
                next_canon = self.all_scenes[i]
                return {
                    'next_event': next_canon.get('title'),
                    'next_date': next_canon.get('date'),
                    'current_date': current_date,
                    'scenes_until': i - current_idx
                }
        return None
    
    def get_display_state(self):
        """Get complete state for display rendering."""
        scene = self.get_current_scene()
        if not scene:
            return None
        
        # Determine time of day icon
        time = (scene.get('time') or 'afternoon').lower()
        time_icons = {
            'dawn': '🌅', 'morning': '🌄', 'noon': '☀️',
            'afternoon': '🌤️', 'evening': '🌆', 'night': '🌙'
        }
        time_icon = time_icons.get(time, '☀️')
        
        # Calculate journey day number
        start_date = datetime(2941, 4, 26)
        try:
            scene_date = datetime.strptime(scene.get('date', '2941-04-26'), '%Y-%m-%d')
            journey_day = (scene_date - start_date).days + 1
        except:
            journey_day = 1
        
        # Get next canonical info
        next_canonical = self.get_time_until_next_canonical()
        
        # Get location display name
        location = scene.get('location', 'Unknown Location')
        
        # Format content based on scene type
        if scene['type'] == 'canonical':
            content = scene.get('summary', '')
            chapter = scene.get('chapter', '')
            subtitle = f"Chapter: {chapter}" if chapter else "Canonical Event"
        else:
            content = scene.get('content', '')
            scene_type = scene.get('scene_type') or 'scene'
            subtitle = f"Generated {scene_type.title()}"
        
        # Get characters
        chars = scene.get('characters', []) or scene.get('characters_present', [])
        
        return {
            'title': scene.get('title', 'Untitled Scene'),
            'subtitle': subtitle,
            'content': content,
            'location': location,
            'date': scene.get('date', 'Unknown'),
            'time': time,
            'time_icon': time_icon,
            'journey_day': journey_day,
            'characters': chars,
            'is_canonical': scene['type'] == 'canonical',
            'scene_type': scene.get('scene_type', 'canonical'),
            'next_canonical': next_canonical,
            'progress': {
                'current': self.current_index + 1,
                'total': len(self.all_scenes)
            }
        }


if __name__ == "__main__":
    manager = SceneManager()
    
    # Test: show first few scenes
    print("\n" + "="*60)
    print("SCENE MANAGER TEST - First 5 scenes")
    print("="*60)
    
    for i in range(min(5, len(manager.all_scenes))):
        state = manager.get_display_state()
        print(f"\n[{state['progress']['current']}/{state['progress']['total']}] "
              f"{'📖' if state['is_canonical'] else '✨'} {state['title']}")
        print(f"    📅 {state['date']} {state['time_icon']} {state['time'].title()}")
        print(f"    📍 {state['location']}")
        print(f"    👥 {', '.join(state['characters'][:5])}")
        if state['next_canonical']:
            nc = state['next_canonical']
            print(f"    [T]  {nc['scenes_until']} scenes until: {nc['next_event']}")
        manager.next_scene()
