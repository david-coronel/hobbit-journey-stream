#!/usr/bin/env python3
"""
The Hobbit Scene Generation Engine v2
Generates high-quality scenes that fit between canonical events.
"""

import json
import random
from datetime import datetime
from typing import List, Dict


class HobbitSceneGenerator:
    """Generates plausible interstitial scenes for The Hobbit."""
    
    # Richer dialogue by character
    DIALOGUES = {
        'Bilbo': [
            "I do wish I was at home in my nice hole by the fire, with the kettle just beginning to sing.",
            "We seem to be getting nowhere very fast, and my toes are quite numb.",
            "Is there no end to this wilderness? My stomach thinks my throat's been cut.",
            "I suppose we must keep going, though I don't like the look of that sky.",
            "This is not what I expected when I signed that contract, not at all.",
            "If only Gandalf were here, he'd know what to do.",
            "I feel thin, sort of stretched, like butter scraped over too much bread.",
            "My dear fellow, I am quite ready to entertain any suggestions you might have.",
        ],
        'Thorin': [
            "We must press on. Every day matters, and the Mountain grows no closer while we linger.",
            "I remember when these lands were different... before the dragon came.",
            "We are Durin's folk. We do not falter, not while breath remains in our bodies.",
            "Keep your spirits up, lads. We are near now. I feel it in my bones.",
            "Double the watch tonight. I trust nothing in these dark lands.",
            "The treasure calls to us, as it called to our fathers before us.",
            "We shall reclaim what was ours, or die in the attempt.",
        ],
        'Gandalf': [
            "All is not lost, my friends. Not while I am with you.",
            "There are older and fouler things than orcs in the deep places of the world.",
            "Patience. The path reveals itself to those who wait and watch.",
            "I have business elsewhere, but I shall return when you have most need of me.",
            "Trust your burglar. He has more in him than you know, and more than he knows himself.",
            "The dawn will come, as it always does. Until then, we endure.",
        ],
        'Balin': [
            "In my youth, I remember tales of this place, though I never thought to see it.",
            "Thorin has the right of it, but mind your tempers. We are all tired and hungry.",
            "The old maps show a path through here, if we can but find it.",
            "Best to rest while we can. Who knows what trials lie ahead.",
            "I have seen worse winters than this, and darker days. We shall endure.",
        ],
        'Bombur': [
            "My legs are aching something fierce. Could we not rest just a little longer?",
            "Is it time to eat yet? My belly thinks my throat's been cut days ago.",
            "I could sleep for a week, I swear it. Just a week, that's all I ask.",
            "Couldn't we have taken the path around? My feet are killing me.",
            "What I wouldn't give for a proper bed and a hot meal. Just one hot meal.",
        ],
        'Dori': [
            "Watch where you're putting those big feet, Bombur! That's my toe you've mashed.",
            "Someone help the poor fellow up. Bombur's fallen again, surprise surprise.",
            "I've had about enough of this journey. When do we reach proper civilization?",
            "Mark my words, this path leads nowhere good. I have a feeling about these things.",
        ],
        'Kili': [
            "Fili and I can scout ahead. We'll spot any trouble before it spots us.",
            "A bit of adventure never hurt anyone. Well, hardly anyone.",
            "I bet I could hit that target from here. Want to wager on it?",
            "The old stories speak of this place. Listen, and I'll tell you what I know.",
        ],
        'Fili': [
            "Come on, brother. Let's see what's over that ridge before the others catch up.",
            "These old bones are still good for something, even if I do say so myself.",
            "Race you to the top! Last one there's a rotten orc!",
            "Kili, keep your voice down. Do you want every enemy within miles to hear us?",
        ],
        'Gloin': [
            "My beard's full of twigs and my temper's shorter than a goblin's patience.",
            "If we don't find shelter soon, I'll be icicles by morning.",
            "In the Iron Hills, we had proper winters. This is just uncomfortable.",
        ],
        'Oin': [
            "Does anyone have any ointment? My ears are acting up in this damp.",
            "I heard a sound, I swear it. Something moving in the dark.",
            "My hearing may be fading, but my nose works fine. Something's coming.",
        ],
        'Dwalin': [
            "I don't like this. I don't like this one bit. Something's watching us.",
            "Keep your weapons ready. I've got a bad feeling about this place.",
            "In the old days, we'd have cleared this land of filth. The world grows soft.",
        ],
        'Bofur': [
            "Anyone fancy a song? I've got one about a troll and a farmer's daughter...",
            "This reminds me of the time in the Blue Mountains when the goats got loose.",
            "Cheer up, lads! It could be worse. We could be back in the goblin tunnels.",
        ],
        'Ori': [
            "Should I be recording this? Someone should be recording this for posterity.",
            "I have paper and ink, if anyone wants to dictate their thoughts.",
            "The book says there should be a landmark here. I don't see any landmark.",
        ],
        'Nori': [
            "I found some mushrooms. Don't ask where. They're edible, probably.",
            "There's a path to the left that looks less traveled. Or more trapped.",
            "Keep your valuables close. There are light fingers in these parts.",
        ],
    }
    
    # Location descriptions
    LOCATIONS = {
        'shire': {
            'name': 'the Shire',
            'features': ['gentle hills', 'well-kept hedgerows', 'round green doors', 'pleasant gardens'],
            'mood': 'peaceful, green, comfortable',
        },
        'trollshaws': {
            'name': 'the Trollshaws',
            'features': ['twisted trees', 'rocky clearings', 'troll footprints', 'cold mists'],
            'mood': 'uneasy, damp, threatening',
        },
        'rivendell': {
            'name': 'Rivendell',
            'features': ['waterfalls', 'white towers', 'elm trees', 'the sound of harps'],
            'mood': 'peaceful, magical, safe',
        },
        'misty_mountains': {
            'name': 'the Misty Mountains',
            'features': ['jagged peaks', 'precarious paths', 'howling winds', 'snow fields'],
            'mood': 'dangerous, cold, imposing',
        },
        'mirkwood': {
            'name': 'Mirkwood',
            'features': ['black branches', 'spider webs', 'dim green light', 'strange noises'],
            'mood': 'oppressive, gloomy, treacherous',
        },
        'lake_town': {
            'name': 'Lake-town',
            'features': ['wooden quays', 'slender bridges', 'tilting houses', 'the Long Lake'],
            'mood': 'damp, busy, precarious',
        },
        'erebor': {
            'name': 'the Lonely Mountain',
            'features': ['black rock', 'the Desolation', 'ruins of Dale', 'the Front Gate'],
            'mood': 'desolate, awe-inspiring, dangerous',
        },
        'dale': {
            'name': 'Dale',
            'features': ['ruined towers', 'deserted streets', 'scorched earth', 'silent bells'],
            'mood': 'haunted, sad, empty',
        },
        'beorn': {
            'name': "Beorn's lands",
            'features': ['flowering fields', 'bee gardens', 'the Carrock', 'rich grass'],
            'mood': 'wild, abundant, strange',
        },
        'wilderland': {
            'name': 'Wilderland',
            'features': ['rolling grasslands', 'distant hills', 'wandering streams', 'open sky'],
            'mood': 'vast, uncertain, free',
        }
    }
    
    def __init__(self, timeline_path="hobbit_narrative_analysis.json"):
        with open(timeline_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.timeline = data.get('entries', [])
        self.gaps = self._identify_gaps()
    
    def _identify_gaps(self) -> List[Dict]:
        """Find gaps between scene entries."""
        gaps = []
        
        for i in range(len(self.timeline) - 1):
            current = self.timeline[i]
            next_entry = self.timeline[i + 1]
            
            if current.get('narrative_type') == 'scene' and next_entry.get('narrative_type') == 'scene':
                try:
                    current_date = datetime.fromisoformat(current['timestamp'])
                    next_date = datetime.fromisoformat(next_entry['timestamp'])
                    gap_days = (next_date - current_date).days
                    
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
    
    def _detect_location(self, entry: Dict) -> str:
        """Detect location from entry content."""
        content = entry.get('content', '').lower()
        
        checks = [
            ('shire', ['shire', 'hobbiton', 'bag end']),
            ('trollshaws', ['troll']),
            ('rivendell', ['rivendell', 'elrond', 'last homely house']),
            ('misty_mountains', ['misty mountain', 'goblin', 'mountain path']),
            ('mirkwood', ['mirkwood', 'forest', 'spider']),
            ('lake_town', ['lake-town', 'esgaroth', 'bard']),
            ('erebor', ['lonely mountain', 'erebor', 'smaug', 'dragon']),
            ('dale', ['dale', 'desolation']),
            ('beorn', ['beorn', 'carrock']),
        ]
        
        for loc, keywords in checks:
            if any(kw in content for kw in keywords):
                return loc
        
        return 'wilderland'
    
    def _detect_characters(self, entry: Dict) -> List[str]:
        """Detect characters in entry."""
        content = entry.get('content', '')
        chars = []
        
        for char in self.DIALOGUES.keys():
            if char in content or char.lower() in content.lower():
                chars.append(char)
        
        return chars if chars else ['Bilbo', 'Thorin']
    
    def _format_characters(self, chars: List[str]) -> str:
        """Format character list nicely."""
        if len(chars) == 1:
            return chars[0]
        elif len(chars) == 2:
            return f"{chars[0]} and {chars[1]}"
        else:
            return ", ".join(chars[:-1]) + f", and {chars[-1]}"
    
    def _generate_conversation(self, chars: List[str], location: str, time: str) -> str:
        """Generate a conversation scene."""
        loc = self.LOCATIONS.get(location, self.LOCATIONS['wilderland'])
        
        lines = []
        
        # Opening setting
        feat = random.choice(loc['features'])
        feat_cap = feat[0].upper() + feat[1:] if feat else feat
        lines.append(f"{time.capitalize()} found them in {loc['name']}. "
                    f"{feat_cap} "
                    f"{random.choice(['loomed ahead', 'lay behind', 'surrounded them'])}.")
        lines.append("")
        
        # Characters and activity
        char_str = self._format_characters(chars)
        activity = random.choice([
            'had paused to rest',
            'were making a brief halt',
            'sat together in silence',
            'gathered around a small fire'
        ])
        lines.append(f"{char_str} {activity}.")
        lines.append("")
        
        # Dialogue
        if len(chars) >= 2:
            s1, s2 = random.sample(chars, 2)
            d1 = random.choice(self.DIALOGUES.get(s1, ["..."]))
            d2 = random.choice(self.DIALOGUES.get(s2, ["..."]))
            
            manner = random.choice(['', ' softly', ' with a sigh', ' after a moment', ' at last'])
            lines.append(f'"{d1}," said {s1}{manner}.')
            lines.append("")
            
            # Reaction (from someone other than speaker)
            other_chars = [c for c in chars if c != s1]
            reactions = [
                f"{random.choice(other_chars if other_chars else chars)} nodded thoughtfully.",
                f"A {random.choice(['long', 'brief', 'weighted'])} silence followed.",
                f"The {random.choice(['wind', 'silence', 'darkness'])} seemed to deepen.",
                ""
            ]
            reaction = random.choice(reactions)
            if reaction:
                lines.append(reaction)
                lines.append("")
            
            manner2 = random.choice(['', ' quietly', ' at length', ' with a shrug'])
            lines.append(f'"{d2}," {s2} replied{manner2}.')
            lines.append("")
        
        # Closing
        endings = [
            f"They rested a while longer, then {random.choice(['pressed on', 'resumed their journey'])}.",
            f"No more was said, but {random.choice(['all felt the weight of the words', 'the mood had shifted'])}.",
            f"Soon enough, it was time to {random.choice(['move on', 'break camp', 'continue'])}.",
        ]
        lines.append(random.choice(endings))
        
        return "\n".join(lines)
    
    def _generate_observation(self, chars: List[str], location: str, time: str) -> str:
        """Generate an observation scene."""
        loc = self.LOCATIONS.get(location, self.LOCATIONS['wilderland'])
        observer = random.choice(chars)
        
        lines = []
        feat = random.choice(loc['features'])
        feat_cap = feat[0].upper() + feat[1:] if feat else feat
        lines.append(f"{time.capitalize()} light spread across {loc['name']}. "
                    f"{feat_cap} "
                    f"{random.choice(['gleamed', 'stood silent', 'marked the horizon'])}.")
        lines.append("")
        
        action = random.choice([
            'looking about carefully',
            'scanning the distance',
            'turning slowly in place',
            'sitting apart from the others'
        ])
        lines.append(f"{observer} paused, {action}. "
                    f"The {loc['name']} stretched out in all directions, "
                    f"{random.choice(loc['features'])} marking the landscape.")
        lines.append("")
        
        reflection = random.choice([
            f"{observer} thought of {random.choice(['home', 'better days', 'the journey ahead'])}, "
            f"and {random.choice(['smiled', 'frowned', 'sighed'])}.",
            f"There was beauty here, of a sort, but also {random.choice(['danger', 'melancholy'])}.",
            "How far they had come, and how far yet to go.",
        ])
        lines.append(reflection)
        lines.append("")
        
        lines.append(f"After a time, {observer} rejoined the company, "
                    f"saying nothing of what had passed through their mind.")
        
        return "\n".join(lines)
    
    def _generate_activity(self, chars: List[str], location: str, time: str) -> str:
        """Generate an activity scene."""
        loc = self.LOCATIONS.get(location, self.LOCATIONS['wilderland'])
        
        lines = []
        time_phrase = random.choice([
            f"{time.capitalize()} in {loc['name']}",
            f"{time.capitalize()} found them in {loc['name']}",
            f"It was {time} in {loc['name']}"
        ])
        lines.append(f"{time_phrase}. {random.choice(loc['features'])} "
                    f"{random.choice(['provided some shelter', 'were visible nearby', 'marked their surroundings'])}.")
        lines.append("")
        
        activities = [
            'occupied with various tasks',
            'making the best of a poor camp',
            'tending to their gear and provisions'
        ]
        char_str = self._format_characters(chars)
        lines.append(f"The company was {random.choice(activities)}.")
        lines.append("")
        
        # Specific activity
        if len(chars) >= 2:
            c1, c2 = random.sample(chars, 2)
            specifics = [
                f"{c1} {random.choice(['mended a torn cloak', 'sharpened a blade', 'counted remaining provisions'])}.",
                f"{c1} and {c2} {random.choice(['argued quietly about the route', 'shared what little food remained'])}.",
                f"Someone {random.choice(['hummed a traveling song', 'cursed under their breath'])}.",
            ]
        else:
            specifics = [
                f"{chars[0]} {random.choice(['mended a torn cloak', 'sharpened a blade'])}.",
                f"Someone {random.choice(['hummed a traveling song', 'cursed under their breath'])}.",
            ]
        lines.append(random.choice(specifics))
        lines.append("")
        
        lines.append(f"It was {random.choice(['uneventful', 'tedious', 'necessary'])} work, but it passed the time. "
                    f"When all was ready, they {random.choice(['moved on', 'prepared for what might come'])}.")
        
        return "\n".join(lines)
    
    def generate_scene(self, gap_index: int = None) -> Dict:
        """Generate a complete scene."""
        if gap_index is None:
            gap = random.choice(self.gaps)
        else:
            gap = self.gaps[gap_index % len(self.gaps)]
        
        before = gap['before']
        after = gap['after']
        
        location = self._detect_location(before)
        characters = self._detect_characters(before) or self._detect_characters(after)
        if not characters:
            characters = ['Bilbo', 'Thorin', 'Balin']
        
        time = random.choice(['morning', 'midday', 'evening', 'night'])
        scene_type = random.choice(['conversation', 'observation', 'activity'])
        
        if scene_type == 'conversation':
            text = self._generate_conversation(characters, location, time)
        elif scene_type == 'observation':
            text = self._generate_observation(characters, location, time)
        else:
            text = self._generate_activity(characters, location, time)
        
        return {
            'type': 'generated_scene',
            'scene_type': scene_type,
            'text': text,
            'gap': {
                'chapter': gap['chapter'],
                'gap_days': gap['gap_days'],
                'before_date': before.get('date'),
                'after_date': after.get('date'),
                'characters': characters,
                'location': location
            }
        }
    
    def generate_for_chapter(self, chapter: str, count: int = 2) -> List[Dict]:
        """Generate scenes for a specific chapter."""
        chapter_gaps = [g for g in self.gaps if g['chapter'] == chapter]
        if not chapter_gaps:
            return []
        
        scenes = []
        for i in range(min(count, len(chapter_gaps))):
            idx = self.gaps.index(chapter_gaps[i % len(chapter_gaps)])
            scenes.append(self.generate_scene(idx))
        return scenes
    
    def export_scenes(self, scenes: List[Dict], json_path: str = "generated_scenes_v2.json", 
                     txt_path: str = "generated_scenes_v2.txt"):
        """Export scenes to files."""
        # JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({'count': len(scenes), 'scenes': scenes}, f, indent=2, ensure_ascii=False)
        
        # Readable text
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# Generated Scenes for The Hobbit\n\n")
            f.write("*AI-generated scenes to fill narrative gaps between canonical events.*\n\n")
            
            for i, scene in enumerate(scenes, 1):
                gap = scene['gap']
                f.write(f"## Scene {i}: {gap['chapter']}\n\n")
                f.write(f"**Between:** {gap['before_date']} -> {gap['after_date']} ({gap['gap_days']} days)\n")
                f.write(f"**Location:** {gap['location'].replace('_', ' ').title()}\n")
                f.write(f"**Characters:** {', '.join(gap['characters'])}\n")
                f.write(f"**Type:** {scene['scene_type']}\n\n")
                f.write(scene['text'])
                f.write("\n\n---\n\n")
        
        print(f"Exported {len(scenes)} scenes to {json_path} and {txt_path}")


def main():
    """Generate sample scenes."""
    print("="*70)
    print("THE HOBBIT SCENE GENERATOR v2")
    print("="*70)
    
    gen = HobbitSceneGenerator()
    print(f"\nFound {len(gen.gaps)} narrative gaps suitable for generation\n")
    
    scenes = []
    test_chapters = ['Chapter II', 'Chapter IV', 'Chapter VIII', 'Chapter XI', 'Chapter XV']
    
    for chapter in test_chapters:
        chapter_scenes = gen.generate_for_chapter(chapter, count=1)
        scenes.extend(chapter_scenes)
        
        if chapter_scenes:
            print(f"--- {chapter} ---")
            print(chapter_scenes[0]['text'][:500])
            print("\n")
    
    gen.export_scenes(scenes)
    print(f"\nTotal scenes generated: {len(scenes)}")


if __name__ == '__main__':
    main()
