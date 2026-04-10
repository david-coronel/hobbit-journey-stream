"""
Export Stream Data - Converts scenes to JSON format for the web display.
Run this to generate stream_scenes.json from the scene manager data.
"""

import json
from scene_manager import SceneManager


def export_stream_data(output_path="stream_scenes.json"):
    """Export all scenes to a JSON file for the web display."""
    
    manager = SceneManager()
    
    stream_scenes = []
    
    # Process all scenes
    manager.current_index = 0
    
    num_scenes = len(manager.all_scenes)
    
    for idx in range(num_scenes):
        manager.current_index = idx
        state = manager.get_display_state()
        if not state:
            continue
        
        # Build next_canonical info
        next_canon = state.get('next_canonical')
        next_canonical_data = None
        if next_canon:
            next_canonical_data = {
                'next_event': next_canon['next_event'],
                'scenes_until': next_canon['scenes_until']
            }
        
        stream_scene = {
            'title': state['title'],
            'subtitle': f"Chapter: {state.get('chapter', '')}" if state['is_canonical'] else f"Generated {(state.get('scene_type') or 'Scene').title()}",
            'content': state['content'],
            'location': state['location'],
            'date': state['date'],
            'time': state['time'].title() if state['time'] else 'Afternoon',
            'time_icon': state['time_icon'],
            'journey_day': state['journey_day'],
            'characters': state['characters'],
            'is_canonical': state['is_canonical'],
            'scene_type': state.get('scene_type'),
            'next_canonical': next_canonical_data,
            'progress': state['progress']
        }
        
        stream_scenes.append(stream_scene)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(stream_scenes, f, indent=2)
    
    print(f"Exported {len(stream_scenes)} scenes to {output_path}")
    
    # Print summary
    canonical = [s for s in stream_scenes if s['is_canonical']]
    generated = [s for s in stream_scenes if not s['is_canonical']]
    
    print(f"\nBreakdown:")
    print(f"  - Canonical scenes: {len(canonical)}")
    print(f"  - Generated scenes: {len(generated)}")
    
    # Show first few examples
    print(f"\nFirst 5 scenes:")
    for i, scene in enumerate(stream_scenes[:5]):
        icon = '📖' if scene['is_canonical'] else '✨'
        print(f"  {i+1}. {icon} {scene['title']} ({scene['date']} {scene['time_icon']})")
    
    return stream_scenes


if __name__ == "__main__":
    export_stream_data()
