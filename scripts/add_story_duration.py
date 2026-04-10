#!/usr/bin/env python3
"""
Add story duration (in-world time) to each scene.
This is how much time passes IN THE STORY, not reading time.
"""

import json
import re
from datetime import timedelta


def parse_duration_text(text):
    """Extract time duration mentions from text."""
    text_lower = text.lower()
    
    # Patterns for explicit time mentions
    patterns = [
        # Hours
        (r'for (an?|[0-9]+) hour', 'hours', 1),
        (r'([0-9]+) hours', 'hours', 1),
        (r'within (an?|[0-9]+) hour', 'hours', 1),
        (r'after (an?|[0-9]+) hour', 'hours', 1),
        (r'an hour later', 'hours', 1),
        (r'([0-9]+) hour later', 'hours', 1),
        (r'all (day|night) long', 'hours', 12),
        (r'all through the (day|night)', 'hours', 12),
        
        # Days
        (r'for (a|[0-9]+) day', 'days', 1),
        (r'([0-9]+) days', 'days', 1),
        (r'next day', 'days', 1),
        (r'the following day', 'days', 1),
        (r'a day later', 'days', 1),
        (r'([0-9]+) day later', 'days', 1),
        (r'after (a|[0-9]+) day', 'days', 1),
        (r'that day', 'days', 0.5),  # Rest of the day
        (r'all day', 'days', 0.5),
        
        # Weeks
        (r'for (a|[0-9]+) week', 'weeks', 1),
        (r'([0-9]+) weeks', 'weeks', 1),
        (r'week later', 'weeks', 1),
        (r'a week passed', 'weeks', 1),
        
        # Months
        (r'for (a|[0-9]+) month', 'months', 1),
        (r'([0-9]+) months', 'months', 1),
        (r'month later', 'months', 1),
        
        # Years
        (r'for (a|[0-9]+) year', 'years', 1),
        (r'([0-9]+) years', 'years', 1),
        (r'year later', 'years', 1),
        
        # Moments/instant
        (r'in a moment', 'minutes', 5),
        (r'for a moment', 'minutes', 5),
        (r'for moments', 'minutes', 10),
        (r'instantly', 'minutes', 1),
        
        # Minutes
        (r'for (a|[0-9]+) minute', 'minutes', 1),
        (r'([0-9]+) minutes', 'minutes', 1),
        (r'minute later', 'minutes', 1),
        
        # Specific time indicators
        (r'by morning', 'hours', 8),  # Overnight
        (r'by dawn', 'hours', 8),
        (r'by evening', 'hours', 8),
        (r'by night', 'hours', 8),
        (r'til morning', 'hours', 8),
        (r'til dawn', 'hours', 8),
        (r'til night', 'hours', 8),
        
        # Journey time patterns
        (r'journey of ([0-9]+) day', 'days', 1),
        (r'march of ([0-9]+) day', 'days', 1),
        (r'travelled for ([0-9]+) day', 'days', 1),
    ]
    
    explicit_mentions = []
    
    for pattern, unit, default_val in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match[0] else match[1] if len(match) > 1 else str(default_val)
            
            # Extract number
            if match in ['a', 'an']:
                num = 1
            else:
                try:
                    num = int(match)
                except:
                    num = default_val
            
            explicit_mentions.append((num, unit))
    
    return explicit_mentions


def estimate_scene_duration(scene, chapter_context):
    """Estimate story duration for a scene."""
    content = scene.get('content', '')
    title = scene.get('title', '')
    chapter = scene.get('chapter', '')
    is_canon = scene.get('is_canonical', True)
    word_count = scene.get('word_count', 0)
    
    # First, look for explicit time mentions
    explicit = parse_duration_text(content[:2000])  # Check first 2000 chars
    
    if explicit:
        # Take the largest explicit mention
        total_hours = 0
        for num, unit in explicit:
            if unit == 'minutes':
                total_hours += num / 60
            elif unit == 'hours':
                total_hours += num
            elif unit == 'days':
                total_hours += num * 24
            elif unit == 'weeks':
                total_hours += num * 24 * 7
            elif unit == 'months':
                total_hours += num * 24 * 30
            elif unit == 'years':
                total_hours += num * 24 * 365
        
        # Convert to appropriate unit
        if total_hours < 1:
            return {'duration': max(5, int(total_hours * 60)), 'unit': 'minutes', 'method': 'explicit'}
        elif total_hours < 24:
            return {'duration': round(total_hours, 1), 'unit': 'hours', 'method': 'explicit'}
        elif total_hours < 24 * 7:
            return {'duration': round(total_hours / 24, 1), 'unit': 'days', 'method': 'explicit'}
        elif total_hours < 24 * 30:
            return {'duration': round(total_hours / (24 * 7), 1), 'unit': 'weeks', 'method': 'explicit'}
        elif total_hours < 24 * 365:
            return {'duration': round(total_hours / (24 * 30), 1), 'unit': 'months', 'method': 'explicit'}
        else:
            return {'duration': round(total_hours / (24 * 365), 1), 'unit': 'years', 'method': 'explicit'}
    
    # No explicit mention - estimate based on content type and length
    method = 'estimated'
    
    # Check title patterns for clues
    title_lower = title.lower()
    
    # Very short scenes are moments
    if word_count < 100:
        return {'duration': 10, 'unit': 'minutes', 'method': method}
    
    # Action/combat scenes are typically short
    action_words = ['battle', 'fight', 'attack', 'rescue', 'escape', 'death', 'kill', 'combat']
    if any(w in title_lower for w in action_words):
        return {'duration': 30, 'unit': 'minutes', 'method': method}
    
    # Conversations/dialogues
    conv_words = ['conversation', 'talk', 'discussion', 'meeting', 'parley']
    if any(w in title_lower for w in conv_words):
        if word_count < 500:
            return {'duration': 15, 'unit': 'minutes', 'method': method}
        else:
            return {'duration': 1, 'unit': 'hours', 'method': method}
    
    # Meals/feasts
    meal_words = ['feast', 'dinner', 'breakfast', 'supper', 'meal', 'party']
    if any(w in title_lower for w in meal_words):
        return {'duration': 2, 'unit': 'hours', 'method': method}
    
    # Travel/journey scenes
    travel_words = ['journey', 'travel', 'march', 'walk', 'ride', 'road', 'path']
    if any(w in title_lower for w in travel_words):
        if word_count < 800:
            return {'duration': 4, 'unit': 'hours', 'method': method}
        else:
            return {'duration': 1, 'unit': 'days', 'method': method}
    
    # Rest/sleep scenes
    rest_words = ['rest', 'sleep', 'camp', 'night', 'dream', 'morning']
    if any(w in title_lower for w in rest_words):
        return {'duration': 8, 'unit': 'hours', 'method': method}
    
    # Planning/preparation
    plan_words = ['plan', 'prepare', 'counsel', 'advice', 'decision']
    if any(w in title_lower for w in plan_words):
        return {'duration': 2, 'unit': 'hours', 'method': method}
    
    # Exploration/searching
    explore_words = ['search', 'explore', 'find', 'look', 'climb', 'enter']
    if any(w in title_lower for w in explore_words):
        if word_count < 1000:
            return {'duration': 2, 'unit': 'hours', 'method': method}
        else:
            return {'duration': 6, 'unit': 'hours', 'method': method}
    
    # Default based on word count
    if word_count < 500:
        return {'duration': 30, 'unit': 'minutes', 'method': method}
    elif word_count < 1500:
        return {'duration': 2, 'unit': 'hours', 'method': method}
    elif word_count < 2500:
        return {'duration': 6, 'unit': 'hours', 'method': method}
    else:
        return {'duration': 1, 'unit': 'days', 'method': method}


def format_duration(duration_info):
    """Format duration for display."""
    duration = duration_info['duration']
    unit = duration_info['unit']
    method = duration_info['method']
    
    # Pluralize
    if duration == 1:
        if unit == 'minutes':
            unit_str = 'minute'
        elif unit == 'hours':
            unit_str = 'hour'
        elif unit == 'days':
            unit_str = 'day'
        elif unit == 'weeks':
            unit_str = 'week'
        elif unit == 'months':
            unit_str = 'month'
        elif unit == 'years':
            unit_str = 'year'
    else:
        unit_str = unit
    
    # Format number
    if isinstance(duration, float):
        if duration == int(duration):
            num_str = str(int(duration))
        else:
            num_str = f"{duration:.1f}"
    else:
        num_str = str(duration)
    
    prefix = "~" if method == 'estimated' else ""
    return f"{prefix}{num_str} {unit_str}"


def main():
    print("Loading stream_scenes.json...")
    with open('../data/stream_scenes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scenes = data['scenes']
    
    print(f"Processing {len(scenes)} scenes...")
    
    explicit_count = 0
    estimated_count = 0
    
    for scene in scenes:
        duration_info = estimate_scene_duration(scene, None)
        scene['story_duration'] = duration_info
        scene['story_duration_display'] = format_duration(duration_info)
        
        if duration_info['method'] == 'explicit':
            explicit_count += 1
        else:
            estimated_count += 1
    
    # Update metadata
    data['metadata']['has_story_durations'] = True
    data['metadata']['explicit_durations'] = explicit_count
    data['metadata']['estimated_durations'] = estimated_count
    
    # Save
    with open('../data/stream_scenes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("STORY DURATIONS ADDED")
    print(f"{'='*60}")
    print(f"Total scenes: {len(scenes)}")
    print(f"Explicit durations: {explicit_count}")
    print(f"Estimated durations: {estimated_count}")
    
    # Show examples
    print(f"\n{'='*60}")
    print("EXAMPLES")
    print(f"{'='*60}")
    
    # Show a mix of explicit and estimated
    shown = 0
    for scene in scenes[:20]:
        icon = "✓" if scene['story_duration']['method'] == 'explicit' else "~"
        print(f"{icon} {scene['id']}: {scene['title'][:40]:<40} → {scene['story_duration_display']}")
        if scene['story_duration']['method'] == 'explicit':
            shown += 1
        if shown >= 3:
            break
    
    print("\n...")
    
    # Show total story time
    total_hours = 0
    for scene in scenes:
        d = scene['story_duration']
        val = d['duration']
        unit = d['unit']
        
        if unit == 'minutes':
            total_hours += val / 60
        elif unit == 'hours':
            total_hours += val
        elif unit == 'days':
            total_hours += val * 24
        elif unit == 'weeks':
            total_hours += val * 24 * 7
        elif unit == 'months':
            total_hours += val * 24 * 30
        elif unit == 'years':
            total_hours += val * 24 * 365
    
    total_days = total_hours / 24
    total_weeks = total_days / 7
    
    print(f"\n{'='*60}")
    print("TOTAL STORY TIME")
    print(f"{'='*60}")
    print(f"In-world time covered: {total_hours:.0f} hours")
    print(f"                      = {total_days:.1f} days")
    print(f"                      = {total_weeks:.1f} weeks")
    print(f"                      (~{total_days/365:.1f} years)")
    
    print("\nFile updated: stream_scenes.json")


if __name__ == "__main__":
    main()
