#!/usr/bin/env python3
"""
Update stream_scenes.json with all canonical scenes from the book.
Merge with existing generated scenes using date-based insertion.
"""

import json
from datetime import datetime, timedelta


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_date(date_str):
    """Parse date string in various formats."""
    if not date_str or date_str == '-':
        return None
    try:
        return datetime.strptime(date_str, '%B %d, %Y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None


def format_date_shire(dt):
    """Format date in Shire Reckoning."""
    if not dt:
        return "Unknown Date"
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    return f"{month_names[dt.month]} {dt.day}, {dt.year}"


def get_location_for_scene(chapter_title, scene_title):
    """Determine location based on chapter and scene context."""
    locations = {
        'An Unexpected Party': {'default': 'Hobbiton'},
        'Roast Mutton': {'default': 'Trollshaws'},
        'A Short Rest': {'default': 'Rivendell'},
        'Over Hill and Under Hill': {'default': 'Misty Mountains'},
        'Riddles in the Dark': {'default': 'Goblin Tunnels'},
        'Out of the Frying-Pan into the Fire': {'default': 'The Carrock'},
        'Queer Lodgings': {'default': "Beorn's Hall"},
        'Flies and Spiders': {'default': 'Mirkwood'},
        'Barrels Out of Bond': {'default': 'Lake-town'},
        'A Warm Welcome': {'default': 'Lake-town'},
        'On the Doorstep': {'default': 'The Lonely Mountain'},
        'Inside Information': {'default': 'Erebor'},
        'Not at Home': {'default': 'Erebor'},
        'Fire and Water': {'default': 'Lake-town'},
        'The Gathering of the Clouds': {'default': 'Erebor'},
        'A Thief in the Night': {'default': 'Ravenhill'},
        'The Clouds Burst': {'default': 'The Mountain'},
        'The Return Journey': {'default': 'The Road East'},
        'The Last Stage': {'default': 'The Shire'},
    }
    return locations.get(chapter_title, {}).get('default', 'Wilderland')


def get_time_of_day(scene_number, total_scenes):
    """Estimate time of day based on scene position."""
    times = [
        ('Morning', '🌄'), ('Late Morning', '🌤️'), ('Noon', '☀️'),
        ('Afternoon', '🌤️'), ('Late Afternoon', '🌅'),
        ('Evening', '🌆'), ('Night', '🌙'), ('Late Night', '🌑')
    ]
    ratio = scene_number / max(total_scenes, 1)
    idx = min(int(ratio * len(times)), len(times) - 1)
    return times[idx]


def get_journey_day(chapter_num, scene_num, total_scenes_in_ch):
    """Calculate journey day number."""
    # Outward journey (April 26 - December 2941)
    outward_base = {
        1: 1, 2: 3, 3: 6, 4: 10, 5: 12, 6: 13, 7: 16,
        8: 20, 9: 35, 10: 40, 11: 43, 12: 46, 13: 50,
        14: 51, 15: 53, 16: 60, 17: 60
    }
    # Return journey starts in May 2942
    return_base = {
        18: 380,  # ~May 2942
        19: 390   # ~June 2942
    }
    
    if chapter_num in return_base:
        base = return_base[chapter_num]
    else:
        base = outward_base.get(chapter_num, chapter_num * 3)
    
    offset = int((scene_num - 1) / max(total_scenes_in_ch, 1) * 2)
    return base + offset


def get_characters_for_scene(chapter_title):
    """Get characters present in a chapter."""
    company = ["Thorin", "Gandalf", "Bilbo", "Balin", "Dwalin", "Fili", "Kili", 
               "Oin", "Gloin", "Dori", "Nori", "Ori", "Bifur", "Bofur", "Bombur"]
    
    character_map = {
        'An Unexpected Party': ["Bilbo", "Gandalf", "Thorin"],
        'Riddles in the Dark': ["Bilbo", "Gollum"],
        'Inside Information': ["Bilbo", "Smaug"],
        'Fire and Water': ["Bard", "Smaug"],
        'A Thief in the Night': ["Bilbo", "Bard", "Elvenking"],
        'The Last Stage': ["Bilbo"],
    }
    return character_map.get(chapter_title, company)


def merge_scenes():
    """Merge canonical book scenes with generated scenes using date-based insertion."""
    print("Loading data...")
    
    # Load book scenes
    book_data = load_json('../data/hobbit_book_scenes.json')
    book_scenes = book_data['scenes']
    print(f"Found {len(book_scenes)} canonical scenes")
    
    # Load generated scenes
    try:
        gen_data = load_json('generated_scenes.json')
        generated_scenes = gen_data.get('scenes', []) if isinstance(gen_data, dict) else gen_data
        print(f"Found {len(generated_scenes)} generated scenes")
    except FileNotFoundError:
        generated_scenes = []
    
    # Build chapter order
    chapter_order = [
        'An Unexpected Party', 'Roast Mutton', 'A Short Rest',
        'Over Hill and Under Hill', 'Riddles in the Dark',
        'Out of the Frying-Pan into the Fire', 'Queer Lodgings',
        'Flies and Spiders', 'Barrels Out of Bond', 'A Warm Welcome',
        'On the Doorstep', 'Inside Information', 'Not at Home',
        'Fire and Water', 'The Gathering of the Clouds',
        'A Thief in the Night', 'The Clouds Burst',
        'The Return Journey', 'The Last Stage'
    ]
    
    # Group book scenes by chapter
    by_chapter = {}
    for s in book_scenes:
        ch = s['chapter']
        if ch not in by_chapter:
            by_chapter[ch] = []
        by_chapter[ch].append(s)
    
    # Build canonical scene list
    canonical_scenes = []
    scene_counter = 0
    
    for ch_num, chapter_title in enumerate(chapter_order, 1):
        if chapter_title not in by_chapter:
            continue
        
        ch_scenes = sorted(by_chapter[chapter_title], key=lambda x: x['scene_number'])
        
        for scene in ch_scenes:
            scene_counter += 1
            time_name, time_icon = get_time_of_day(scene['scene_number'], len(ch_scenes))
            location = get_location_for_scene(chapter_title, scene['title'])
            journey_day = get_journey_day(ch_num, scene['scene_number'], len(ch_scenes))
            start_date = datetime(2941, 4, 26)
            scene_date = start_date + timedelta(days=journey_day - 1)
            date_str = format_date_shire(scene_date)
            characters = get_characters_for_scene(chapter_title)
            
            canonical_scenes.append({
                'id': f"canon_{scene_counter:03d}",
                'title': scene['title'],
                'chapter': chapter_title,
                'content': scene['text'],
                'summary': scene['text'][:300] + '...' if len(scene['text']) > 300 else scene['text'],
                'location': location,
                'date': date_str,
                'date_iso': scene_date.strftime('%Y-%m-%d'),
                'time': time_name,
                'time_icon': time_icon,
                'journey_day': journey_day,
                'characters': characters,
                'is_canonical': True,
                'word_count': scene['word_count'],
                'progress': {'current': scene_counter, 'total': 0}
            })
    
    # Process generated scenes with their dates
    processed_generated = []
    for gen in generated_scenes:
        between = gen.get('between', [])
        if between:
            try:
                gen_date = datetime.strptime(between[0], '%Y-%m-%d')
                date_str = format_date_shire(gen_date)
            except:
                gen_date = None
                date_str = "Unknown"
        else:
            gen_date = None
            date_str = "Unknown"
        
        scene_type = gen.get('type', 'Scene').title()
        loc = gen.get('location', 'Unknown').replace('_', ' ').title()
        
        processed_generated.append({
            'id': None,  # Will be assigned later
            'title': f"{scene_type} in {loc}",
            'content': gen.get('text', ''),
            'summary': gen.get('text', '')[:200] + '...' if len(gen.get('text', '')) > 200 else gen.get('text', ''),
            'location': loc,
            'date': date_str,
            'date_iso': gen_date.strftime('%Y-%m-%d') if gen_date else None,
            'time': 'Various',
            'time_icon': '🌤️',
            'journey_day': (gen_date - datetime(2941, 4, 26)).days + 1 if gen_date else 0,
            'characters': gen.get('characters', []),
            'is_canonical': False,
            'scene_type': gen.get('type'),
            'word_count': len(gen.get('text', '').split()),
            'progress': {'current': 0, 'total': 0},
            'gen_date': gen_date
        })
    
    # Merge by date
    all_scenes = []
    
    # Sort canonical by date
    canonical_scenes.sort(key=lambda x: (x.get('journey_day', 0), x.get('scene_number', 0)))
    
    # Insert generated scenes at appropriate points
    used_generated = set()
    
    for canon in canonical_scenes:
        all_scenes.append(canon)
        
        # Find generated scenes that belong after this canonical scene
        # (but before the next one)
        canon_date = parse_date(canon['date'])
        
        for i, gen in enumerate(processed_generated):
            if i in used_generated:
                continue
            
            gen_date = gen.get('gen_date')
            if gen_date and canon_date:
                # Insert if generated date is close to canonical date
                day_diff = abs((gen_date - canon_date).days)
                if day_diff <= 2:
                    all_scenes.append(gen)
                    used_generated.add(i)
    
    # Add remaining generated scenes at the end
    for i, gen in enumerate(processed_generated):
        if i not in used_generated:
            all_scenes.append(gen)
    
    # Update IDs and progress for all scenes
    total = len(all_scenes)
    for i, scene in enumerate(all_scenes, 1):
        scene['progress']['current'] = i
        scene['progress']['total'] = total
        if scene.get('is_canonical'):
            scene['id'] = f"canon_{i:03d}"
        else:
            scene['id'] = f"gen_{i:03d}"
        # Remove temporary gen_date
        if 'gen_date' in scene:
            del scene['gen_date']
    
    # Add next_canonical info
    for i, scene in enumerate(all_scenes):
        upcoming = []
        for j in range(i + 1, min(i + 5, len(all_scenes))):
            if all_scenes[j].get('is_canonical'):
                upcoming.append(all_scenes[j]['title'])
                if len(upcoming) >= 3:
                    break
        
        if upcoming:
            scene['next_canonical'] = {
                'next_event': upcoming[0],
                'scenes_until': 1,
                'upcoming_events': upcoming
            }
    
    # Create output
    output = {
        'metadata': {
            'title': 'The Hobbit Journey Stream',
            'total_scenes': len(all_scenes),
            'canonical_scenes': len([s for s in all_scenes if s.get('is_canonical')]),
            'generated_scenes': len([s for s in all_scenes if not s.get('is_canonical')]),
            'total_word_count': sum(s.get('word_count', 0) for s in all_scenes),
            'created': datetime.now().isoformat(),
            'source': 'hobbit_book_scenes.json + generated_scenes.json'
        },
        'scenes': all_scenes
    }
    
    # Save
    save_json(output, '../data/stream_scenes.json')
    
    # Print summary
    print(f"\n{'='*70}")
    print("STREAM SCENES UPDATED")
    print(f"{'='*70}")
    print(f"Total scenes: {output['metadata']['total_scenes']}")
    print(f"  - Canonical: {output['metadata']['canonical_scenes']}")
    print(f"  - Generated: {output['metadata']['generated_scenes']}")
    print(f"  - Total words: {output['metadata']['total_word_count']:,}")
    
    print(f"\nFirst 5 scenes:")
    for s in all_scenes[:5]:
        canon = "📖" if s.get('is_canonical') else "✨"
        title = s.get('title', 'Untitled')[:45]
        chapter = s.get('chapter', s.get('location', 'Generated'))[:15]
        print(f"  {canon} {s['id']}: {title} ({chapter})")
    
    print(f"\nLast 5 scenes:")
    for s in all_scenes[-5:]:
        canon = "📖" if s.get('is_canonical') else "✨"
        title = s.get('title', 'Untitled')[:45]
        chapter = s.get('chapter', s.get('location', 'Generated'))[:15]
        print(f"  {canon} {s['id']}: {title} ({chapter})")


if __name__ == "__main__":
    merge_scenes()
