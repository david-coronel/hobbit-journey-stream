#!/usr/bin/env python3
"""
The Hobbit Scene Generator - Final Version
Generates high-quality interstitial scenes with proper context.
"""

import json
import random
from datetime import datetime
from typing import List, Dict


class SceneGenerator:
    """Generates scenes that fit between canonical Hobbit events."""
    
    DIALOGUES = {
        'Bilbo': [
            "I do wish I was at home in my nice hole by the fire.",
            "We seem to be getting nowhere very fast, and my toes are quite numb.",
            "Is there no end to this wilderness? My stomach thinks my throat's been cut.",
            "I suppose we must keep going, though I don't fancy the look of that sky.",
            "This is not what I expected when I signed that contract.",
            "If only Gandalf were here, he would know what to do.",
            "I feel thin, sort of stretched, like butter scraped over too much bread.",
        ],
        'Thorin': [
            "We must press on. Every day matters, and the Mountain grows no closer.",
            "I remember when these lands were different, before the dragon came.",
            "We are Durin's folk. We do not falter while breath remains.",
            "Keep your spirits up, lads. We are near now. I feel it.",
            "Double the watch tonight. I trust nothing in these dark lands.",
        ],
        'Gandalf': [
            "All is not lost, my friends. Not while I am with you.",
            "There are older and fouler things than orcs in the deep places.",
            "Patience. The path reveals itself to those who wait.",
            "Trust your burglar. He has more in him than you know.",
        ],
        'Balin': [
            "In my youth, I heard tales of this place, though I never thought to see it.",
            "Thorin has the right of it, but mind your tempers. We are all weary.",
            "Best to rest while we can. Who knows what trials lie ahead.",
        ],
        'Bombur': [
            "My legs are aching something fierce. Could we not rest a little longer?",
            "Is it time to eat yet? My belly thinks my throat's been cut.",
            "I could sleep for a week, I swear it. Just one week.",
            "What I wouldn't give for a proper bed and a hot meal.",
        ],
        'Dori': [
            "Watch where you're putting those big feet, Bombur!",
            "Someone help the poor fellow up. Bombur's fallen again.",
            "I've had about enough of this journey.",
        ],
        'Kili': [
            "Fili and I can scout ahead. We'll spot any trouble.",
            "A bit of adventure never hurt anyone. Well, hardly anyone.",
        ],
        'Fili': [
            "Come on, brother. Let's see what's over that ridge.",
            "Race you to the top! Last one there's a rotten orc!",
        ],
        'Dwalin': [
            "I don't like this. I don't like this one bit.",
            "Keep your weapons ready. I've got a bad feeling.",
        ],
    }
    
    LOCATIONS = {
        'shire': {'name': 'the Shire', 'features': ['gentle hills', 'well-kept hedgerows', 'round green doors']},
        'trollshaws': {'name': 'the Trollshaws', 'features': ['twisted trees', 'rocky clearings', 'cold mists']},
        'rivendell': {'name': 'Rivendell', 'features': ['waterfalls', 'white towers', 'elm trees']},
        'misty_mountains': {'name': 'the Misty Mountains', 'features': ['jagged peaks', 'precarious paths', 'howling winds']},
        'mirkwood': {'name': 'Mirkwood', 'features': ['black branches', 'spider webs', 'dim green light']},
        'lake_town': {'name': 'Lake-town', 'features': ['wooden quays', 'slender bridges', 'tilting houses']},
        'erebor': {'name': 'the Lonely Mountain', 'features': ['black rock', 'the Desolation', 'ruins of Dale']},
        'dale': {'name': 'Dale', 'features': ['ruined towers', 'deserted streets', 'scorched earth']},
        'beorn': {'name': "Beorn's lands", 'features': ['flowering fields', 'bee gardens', 'the Carrock']},
        'wilderland': {'name': 'Wilderland', 'features': ['rolling grasslands', 'distant hills', 'wandering streams']},
    }
    
    def __init__(self):
        with open('../data/hobbit_narrative_analysis.json', 'r') as f:
            data = json.load(f)
        self.timeline = data.get('entries', [])
        self.gaps = self._find_gaps()
    
    def _find_gaps(self) -> List[Dict]:
        gaps = []
        for i in range(len(self.timeline) - 1):
            curr = self.timeline[i]
            nxt = self.timeline[i + 1]
            
            if curr.get('narrative_type') == 'scene' and nxt.get('narrative_type') == 'scene':
                try:
                    d1 = datetime.fromisoformat(curr['timestamp'])
                    d2 = datetime.fromisoformat(nxt['timestamp'])
                    days = (d2 - d1).days
                    if 1 <= days <= 30:
                        gaps.append({
                            'index': i,
                            'before': curr,
                            'after': nxt,
                            'days': days,
                            'chapter': curr.get('chapter', 'Unknown')
                        })
                except:
                    pass
        return gaps
    
    def _get_location(self, entry: Dict) -> str:
        text = entry.get('content', '').lower()
        for loc, keywords in [
            ('shire', ['shire', 'hobbiton']),
            ('trollshaws', ['troll']),
            ('rivendell', ['rivendell', 'elrond']),
            ('misty_mountains', ['misty mountain', 'goblin']),
            ('mirkwood', ['mirkwood', 'spider']),
            ('lake_town', ['lake-town', 'esgaroth']),
            ('erebor', ['lonely mountain', 'smaug']),
            ('beorn', ['beorn', 'carrock']),
        ]:
            if any(k in text for k in keywords):
                return loc
        return 'wilderland'
    
    def _get_chars(self, entry: Dict) -> List[str]:
        text = entry.get('content', '')
        found = [c for c in self.DIALOGUES if c in text or c.lower() in text.lower()]
        return found if found else ['Bilbo', 'Thorin']
    
    def generate(self, gap_idx: int = None) -> Dict:
        gap = self.gaps[gap_idx % len(self.gaps)] if gap_idx else random.choice(self.gaps)
        
        loc_key = self._get_location(gap['before'])
        chars = self._get_chars(gap['before']) or self._get_chars(gap['after']) or ['Bilbo', 'Thorin']
        
        loc = self.LOCATIONS[loc_key]
        time = random.choice(['Morning', 'Midday', 'Evening', 'Night'])
        
        # Build scene
        lines = []
        feat = random.choice(loc['features'])
        lines.append(f"{time} found them in {loc['name']}. {feat.capitalize()} {random.choice(['loomed ahead', 'lay behind', 'surrounded them'])}.")
        lines.append("")
        
        # Scene body based on type
        scene_type = random.choice(['conversation', 'observation', 'activity'])
        
        if scene_type == 'conversation' and len(chars) >= 2:
            c1, c2 = random.sample(chars, 2)
            lines.append(f"{c1} and {c2} {random.choice(['sat together', 'had paused to rest', 'gathered by a small fire'])}.")
            lines.append("")
            
            d1 = random.choice(self.DIALOGUES[c1])
            d2 = random.choice(self.DIALOGUES[c2])
            lines.append(f'"{d1}," said {c1}.')
            lines.append("")
            
            others = [c for c in chars if c != c1]
            if others:
                lines.append(f"{random.choice(others)} nodded thoughtfully.")
                lines.append("")
            
            lines.append(f'"{d2}," {c2} replied.')
            lines.append("")
            
        elif scene_type == 'observation':
            obs = random.choice(chars)
            lines.append(f"{obs} paused, {random.choice(['looking about', 'scanning the distance', 'sitting apart'])}.")
            lines.append("")
            lines.append(f"The {loc['name']} stretched out in all directions.")
            lines.append("")
            lines.append(f"How far they had come, and how far yet to go.")
            lines.append("")
            
        else:  # activity
            lines.append(f"The company was {random.choice(['making camp', 'tending gear', 'resting briefly'])}.")
            lines.append("")
            c = random.choice(chars)
            lines.append(f"{c} {random.choice(['mended a cloak', 'sharpened a blade', 'checked provisions'])}.")
            lines.append("")
        
        # Closing
        lines.append(f"Soon enough, it was time to {random.choice(['move on', 'resume their journey', 'continue'])}.")
        
        return {
            'text': '\n'.join(lines),
            'type': scene_type,
            'chapter': gap['chapter'],
            'days': gap['days'],
            'between': [gap['before'].get('date'), gap['after'].get('date')],
            'location': loc_key,
            'characters': chars
        }
    
    def generate_batch(self, count: int = 10) -> List[Dict]:
        return [self.generate() for _ in range(count)]
    
    def save(self, scenes: List[Dict], json_file: str = 'generated_scenes.json', 
             txt_file: str = 'generated_scenes.txt'):
        with open(json_file, 'w') as f:
            json.dump({'count': len(scenes), 'scenes': scenes}, f, indent=2)
        
        with open(txt_file, 'w') as f:
            f.write("# Generated Scenes for The Hobbit\n\n")
            for i, s in enumerate(scenes, 1):
                f.write(f"## Scene {i}: {s['chapter']}\n\n")
                f.write(f"**Gap:** {s['between'][0]} -> {s['between'][1]} ({s['days']} days)\n")
                f.write(f"**Location:** {s['location'].replace('_', ' ').title()}\n")
                f.write(f"**Characters:** {', '.join(s['characters'])}\n")
                f.write(f"**Type:** {s['type']}\n\n")
                f.write(s['text'])
                f.write("\n\n---\n\n")
        
        print(f"Saved {len(scenes)} scenes to {json_file} and {txt_file}")


def main():
    gen = SceneGenerator()
    print(f"Found {len(gen.gaps)} narrative gaps\n")
    
    scenes = gen.generate_batch(15)
    gen.save(scenes)
    
    print("\nSample scenes:\n")
    for s in scenes[:3]:
        print(f"--- {s['chapter']} ---")
        print(s['text'][:400] + "...\n")


if __name__ == '__main__':
    main()
