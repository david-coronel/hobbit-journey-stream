#!/usr/bin/env python3
"""
Extract characters and places from The Hobbit.
Final version with proper merging and cleaning.
"""

import json
import re
from collections import Counter, defaultdict

def load_narrative_data(filepath="hobbit_narrative_analysis.json"):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('entries', data.get('timeline', []))

def extract_capitalized_phrases(text):
    """Extract all capitalized phrases from text."""
    entities = []
    
    # Pattern 1: "The/A/An X Y" phrases
    pattern1 = re.compile(r'\b(The|the|A|a|An|an)\s+([A-Z][a-zA-Z]*(?:\s+(?:of|the|in|on|at|under|over|upon|and)?\s*[A-Z][a-zA-Z]*)*)\b')
    for match in pattern1.finditer(text):
        entities.append(match.group(0))
    
    # Pattern 2: "X Y" multi-word proper nouns
    pattern2 = re.compile(r'\b([A-Z][a-zA-Z]+)\s+([A-Z][a-zA-Z]+(?:\s+(?:of|the|in|on|at|under|over|upon|and)?\s*[A-Z][a-zA-Z]+)*)\b')
    for match in pattern2.finditer(text):
        entities.append(match.group(0))
    
    # Pattern 3: Single capitalized words (mid-sentence is more reliable)
    pattern3 = re.compile(r'(?:^|[.!?;:,"]\s+)([A-Z][a-zA-Z]{2,})\b')
    for match in pattern3.finditer(text):
        entities.append(match.group(1))
    
    # Pattern 4: Mid-sentence capitalized words
    pattern4 = re.compile(r'\s+([A-Z][a-zA-Z]{2,})\b')
    for match in pattern4.finditer(text):
        entities.append(match.group(1))
    
    return entities

# Words to exclude (false positives)
EXCLUDE_WORDS = {
    # Question words
    'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whom', 'whose',
    
    # Pronouns
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
    'this', 'that', 'these', 'those', 'all', 'any', 'both', 'each', 'every', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'none', 'one', 'ones', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'only', 'even', 'also', 'still', 'yet', 'already',
    
    # Common sentence starters / verbs
    'said', 'asked', 'answered', 'replied', 'cried', 'shouted', 'called', 'answered',
    'thought', 'felt', 'saw', 'looked', 'went', 'came', 'stood', 'sat', 'lay', 'laying',
    'began', 'started', 'stopped', 'turned', 'walked', 'ran', 'moved', 'got', 'getting',
    'heard', 'found', 'took', 'gave', 'put', 'set', 'left', 'made', 'brought', 'saw',
    'did', 'done', 'doing', 'had', 'has', 'have', 'having', 'was', 'were', 'been', 'being',
    'is', 'are', 'am', 'be', 'will', 'would', 'shall', 'should', 'may', 'might', 'can', 'could',
    'come', 'coming', 'go', 'going', 'gone', 'get', 'getting', 'take', 'taking', 'took', 'taken',
    'make', 'making', 'run', 'running', 'ran', 'know', 'knew', 'known', 'knowing',
    'think', 'thinking', 'thought', 'tell', 'telling', 'told', 'see', 'seeing', 'seen',
    'say', 'saying', 'give', 'giving', 'gave', 'given', 'find', 'finding', 'found',
    'not', 'let', 'don', 'won', 'aren', 'wasn', 'weren', 'haven', 'hasn', 'hadn',
    
    # Adverbs
    'then', 'than', 'thus', 'there', 'here', 'now', 'quite', 'indeed', 'perhaps',
    'suddenly', 'finally', 'soon', 'later', 'before', 'after', 'again', 'once',
    'back', 'away', 'down', 'up', 'out', 'off', 'over', 'under', 'upon', 'across',
    'yes', 'no', 'oh', 'ah', 'ha', 'ho', 'hey', 'alas', 'lo', 'behold',
    'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 'otherwise',
    
    # Prepositions/Conjunctions (standalone)
    'and', 'but', 'for', 'nor', 'yet', 'so', 'or', 'if', 'while', 'when', 'where',
    'because', 'since', 'until', 'unless', 'although', 'though', 'whether', 'either',
    
    # Articles/Determiners
    'the', 'a', 'an', 'another', 'every', 'each', 'either', 'neither', 'such',
    
    # Adjectives (standalone are not entities)
    'good', 'great', 'little', 'old', 'new', 'long', 'small', 'big', 'high', 'low',
    'young', 'large', 'few', 'own', 'same', 'right', 'left', 'last', 'late', 'early',
    'dark', 'light', 'deep', 'far', 'near', 'full', 'empty', 'true', 'open', 'closed',
    'red', 'blue', 'green', 'yellow', 'white', 'black', 'brown', 'grey', 'gray', 'gold',
    'golden', 'poor', 'rich', 'sudden', 'fell', 'keen', 'wild', 'tame', 'fair',
    'first', 'second', 'third', 'last', 'next', 'other', 'another', 'one', 'two',
    'north', 'south', 'east', 'west', 'northern', 'southern', 'eastern', 'western',
    'main', 'chief', 'principal', 'general', 'particular', 'special',
    'whole', 'half', 'quarter', 'double', 'single', 'second', 'third',
    
    # Common nouns (not proper)
    'day', 'night', 'morning', 'evening', 'time', 'way', 'man', 'men', 'hand', 'hands',
    'head', 'face', 'eye', 'eyes', 'foot', 'feet', 'back', 'side', 'end', 'top', 'bottom',
    'door', 'room', 'wall', 'floor', 'roof', 'window', 'fire', 'water', 'sun', 'moon',
    'wind', 'rain', 'snow', 'ground', 'earth', 'stone', 'rock', 'wood', 'tree', 'grass',
    'path', 'road', 'hill', 'gate', 'cave', 'hall', 'house', 'home', 'place', 'spot',
    'song', 'voice', 'sound', 'word', 'thing', 'part', 'name', 'number', 'sort', 'kind',
    'edge', 'point', 'tip', 'line', 'middle', 'center', 'corner', 'side',
    'front', 'rear', 'back', 'top', 'bottom', 'inside', 'outside',
    
    # Meta
    'chapter', 'note', 'end', 'beginning', 'part', 'page', 'line',
    
    # Months/days
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    
    # Common capitalized in text
    'his', 'her', 'their', 'your', 'our', 'my',
    'you', 'all', 'some', 'many', 'much', 'more', 'most', 'several', 'various',
    'come', 'after', 'before', 'during', 'within', 'without',
}

# Known Middle-earth entities
CHARACTERS = {
    # Main
    'bilbo', 'baggins', 'bilbo baggins',
    'gandalf', 'the wizard', 'gandalf the grey',
    'thorin', 'thorin oakenshield', 'oakenshield',
    'smaug', 'the dragon',
    'gollum', 'smeagol',
    'beorn', 'the skin-changer', 'skin-changer',
    'bard', 'bard the bowman', 'the bowman',
    'elrond',
    'the necromancer',
    'the lord of the eagles',
    
    # Dwarves
    'balin', 'dwalin', 'fili', 'kili', 'dori', 'nori', 'ori',
    'oin', 'gloin', 'bifur', 'bofur', 'bombur',
    'thrain', 'thror', 'dain', 'dain ironfoot',
    
    # Elves
    'thranduil', 'the elvenking', 'elvenking', 'the elf king',
    'galion',
    
    # Men
    'the master', 'master of lake-town', 'girion',
    'the captain', 'the bowman',
    
    # Goblins
    'the great goblin', 'goblin king', 'the goblin king',
    
    # Trolls
    'tom', 'bert', 'william',
    
    # Groups
    'the goblins', 'goblins', 'the goblines',
    'the dwarves', 'dwarves', 'the dwarfs',
    'the elves', 'elves',
    'the trolls', 'trolls',
    'the wargs', 'wargs', 'the wolves',
    'the eagles', 'eagles',
    'the spiders', 'spiders',
    'the ravens', 'ravens', 'roac',
    'the thrushes', 'thrushes', 'the thrush',
    'the ponies', 'ponies',
    
    # Titles as characters
    'king', 'the king', 'lord', 'the lord',
    
    # Objects/artifacts
    'the arkenstone', 'arkenstone',
}

PLACES = {
    # Shire
    'the shire', 'shire', 'hobbiton', 'bywater', 'the water',
    'bag end', 'the hill', 'the green dragon', 'the ivy bush',
    
    # Eriador
    'the trollshaws', 'trollshaws', 'troll shaws',
    'rivendell', 'the last homely house', 'the ford of bruinen',
    
    # Misty Mountains
    'the misty mountains', 'misty mountains',
    'the high pass', 'the goblin gate', 'the front porch',
    'the goblin tunnels', 'the tunnels', 'gollums lake',
    
    # Anduin Vale
    'the anduin', 'the great river', 'forest river',
    'the carrock', 'carrock',
    'beorns hall', 'beorns house', 'beorns clearing',
    
    # Mirkwood
    'mirkwood', 'the forest', 'the dark forest', 'the wood',
    'the enchanted stream', 'the elvenking halls',
    'the kings palace', 'the cellar', 'the dungeon',
    
    # Erebor
    'the lonely mountain', 'lonely mountain', 'erebor', 'the mountain',
    'the desolation', 'dale',
    'the front gate', 'the secret door', 'the back door',
    'ravenhill', 'the guardroom', 'the treasure chamber',
    'the bottom of the hill', 'the dragons lair',
    
    # Lake-town
    'esgaroth', 'lake-town', 'lake town',
    'the long lake', 'the lake',
    
    # Other
    'the iron hills', 'iron hills',
    'wilderland', 'the wild',
    'gundabad', 'mount gundabad',
    'moria', 'the grey mountains', 'the withered heath',
    'the camp', 'the battlefield',
    'the edge', 'the brink', 'the lip',
}

# Place suffixes
PLACE_SUFFIXES = [
    'town', 'ton', 'ham', 'by', 'thorpe', 'wick', 'stead',
    'hill', 'mount', 'mountain', 'berg', 'fell', 'down', 'moor', 'heath',
    'wood', 'forest', 'grove', 'shaw', 'dale', 'vale', 'glen',
    'river', 'rill', 'brook', 'burn', 'water', 'ford',
    'lake', 'mere', 'pool', 'sea',
    'cave', 'hole', 'pit', 'mine',
    'gate', 'door', 'path', 'road', 'way', 'pass',
    'hall', 'house', 'home', 'court', 'yard',
    'camp', 'field', 'plain', 'land', 'realm', 'kingdom',
    'chamber', 'room', 'cellar', 'dungeon',
    'wall', 'bridge', 'crossing', 'pass',
    'rock', 'cliff', 'edge', 'rim', 'slope', 'ridge',
    'tower', 'fort', 'castle', 'keep',
]

def normalize_entity(name):
    """Normalize entity name for deduplication."""
    name = name.strip()
    name_lower = name.lower()
    
    # Remove leading article for matching
    if name_lower.startswith('the '):
        return name_lower[4:]
    if name_lower.startswith('a ') or name_lower.startswith('an '):
        return name_lower[2:]
    return name_lower

def is_valid_entity(name, count):
    """Check if entity is valid."""
    name_lower = name.lower().strip()
    
    if count < 2:
        return False
    
    if name_lower in EXCLUDE_WORDS:
        return False
    
    # Check normalized form
    normalized = normalize_entity(name)
    if normalized in EXCLUDE_WORDS:
        return False
    
    # Exclude single letters and roman numerals
    if len(name) < 2:
        return False
    if re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', name, re.I):
        return False
    
    return True

def classify_entity(name):
    """Classify entity as character, place, or unknown."""
    name_lower = name.lower().strip()
    normalized = normalize_entity(name)
    
    # Direct matches
    if name_lower in CHARACTERS or normalized in CHARACTERS:
        return 'character'
    if name_lower in PLACES or normalized in PLACES:
        return 'place'
    
    # Place suffix check
    for suffix in PLACE_SUFFIXES:
        if normalized.endswith(' ' + suffix) or normalized == suffix:
            return 'place'
    
    # Character title check
    character_titles = ['king', 'queen', 'lord', 'master', 'captain', 
                       'wizard', 'elf', 'dwarf', 'goblin', 'troll', 
                       'dragon', 'eagle', 'bowman']
    for title in character_titles:
        if title in normalized:
            # Check for "the X" pattern
            if name_lower.startswith('the ') and title in name_lower:
                return 'character'
    
    return 'unknown'

def merge_duplicates(entities):
    """Merge duplicate entities (e.g., 'the Mountain' and 'Mountain')."""
    merged = defaultdict(lambda: {'count': 0, 'contexts': [], 'forms': set()})
    
    for name, info in entities.items():
        normalized = normalize_entity(name)
        
        # Prefer longer/more specific forms
        merged[normalized]['count'] += info['count']
        merged[normalized]['contexts'].extend(info['contexts'])
        merged[normalized]['forms'].add(name)
        
        # Choose best display name
        if not merged[normalized].get('display'):
            merged[normalized]['display'] = name
        else:
            current = merged[normalized]['display']
            # Prefer forms with "the" if they appear more often
            name_lower = name.lower()
            if name_lower.startswith('the ') and not current.lower().startswith('the '):
                if info['count'] > entities.get(current, {}).get('count', 0) * 0.5:
                    merged[normalized]['display'] = name
    
    # Convert back
    result = {}
    for normalized, data in merged.items():
        display = data['display']
        result[display] = {
            'count': data['count'],
            'contexts': data['contexts'][:5],
            'all_forms': list(data['forms'])
        }
    
    return result

def extract_all():
    """Main extraction function."""
    print("Loading data...")
    entries = load_narrative_data()
    
    print("Extracting entities...")
    all_entities = []
    entity_contexts = defaultdict(list)
    
    for entry in entries:
        content = entry['content']
        phrases = extract_capitalized_phrases(content)
        
        for phrase in phrases:
            phrase = phrase.strip()
            if phrase:
                all_entities.append(phrase)
                if len(entity_contexts[phrase]) < 5:
                    entity_contexts[phrase].append(content)
    
    counts = Counter(all_entities)
    print(f"Found {len(counts)} unique raw entities")
    
    # Filter
    valid = {}
    for name, count in counts.items():
        if is_valid_entity(name, count):
            valid[name] = {
                'count': count,
                'contexts': entity_contexts[name]
            }
    print(f"Found {len(valid)} valid entities")
    
    # Merge duplicates
    merged = merge_duplicates(valid)
    print(f"After merging: {len(merged)} entities")
    
    # Classify
    characters = {}
    places = {}
    unknown = {}
    
    for name, info in merged.items():
        classification = classify_entity(name)
        
        data = {
            'name': name,
            'mentions': info['count'],
            'contexts': info['contexts'][:3],
            'forms': info.get('all_forms', [name])
        }
        
        if classification == 'character':
            characters[name] = data
        elif classification == 'place':
            places[name] = data
        else:
            unknown[name] = data
    
    print(f"Classified: {len(characters)} characters, {len(places)} places, {len(unknown)} unknown")
    
    # Sort
    chars_sorted = dict(sorted(characters.items(), key=lambda x: x[1]['mentions'], reverse=True))
    places_sorted = dict(sorted(places.items(), key=lambda x: x[1]['mentions'], reverse=True))
    unknown_sorted = dict(sorted(unknown.items(), key=lambda x: x[1]['mentions'], reverse=True))
    
    # Save
    for fname, key, data in [
        ('../data/hobbit_characters.json', 'characters', chars_sorted),
        ('../data/hobbit_places.json', 'places', places_sorted),
        ('../data/hobbit_entities_unknown.json', 'entities', unknown_sorted),
    ]:
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump({'count': len(data), key: data}, f, indent=2, ensure_ascii=False)
    
    # Create markdown
    with open('hobbit_characters.txt', 'w', encoding='utf-8') as f:
        f.write("# Characters in The Hobbit\n\n")
        f.write(f"**Total: {len(chars_sorted)} characters**\n\n")
        f.write("| # | Character | Mentions |\n")
        f.write("|---|-----------|----------|\n")
        for i, (name, info) in enumerate(chars_sorted.items(), 1):
            f.write(f"| {i} | **{name}** | {info['mentions']} |\n")
            if info.get('forms') and len(info['forms']) > 1:
                f.write(f"| | *Also: {', '.join(info['forms'])}* | |\n")
    
    with open('hobbit_places.txt', 'w', encoding='utf-8') as f:
        f.write("# Places in The Hobbit\n\n")
        f.write(f"**Total: {len(places_sorted)} places**\n\n")
        f.write("| # | Place | Mentions |\n")
        f.write("|---|-------|----------|\n")
        for i, (name, info) in enumerate(places_sorted.items(), 1):
            f.write(f"| {i} | **{name}** | {info['mentions']} |\n")
            if info.get('forms') and len(info['forms']) > 1:
                f.write(f"| | *Also: {', '.join(info['forms'])}* | |\n")
    
    # Print summary
    print("\n" + "="*60)
    print("TOP 20 CHARACTERS")
    print("="*60)
    for i, (name, info) in enumerate(list(chars_sorted.items())[:20], 1):
        forms = f" [{', '.join(info['forms'])}]" if len(info.get('forms', [])) > 1 else ''
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions){forms}")
    
    print("\n" + "="*60)
    print("TOP 20 PLACES")
    print("="*60)
    for i, (name, info) in enumerate(list(places_sorted.items())[:20], 1):
        forms = f" [{', '.join(info['forms'])}]" if len(info.get('forms', [])) > 1 else ''
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions){forms}")
    
    if unknown_sorted:
        print("\n" + "="*60)
        print("TOP 10 UNKNOWN")
        print("="*60)
        for i, (name, info) in enumerate(list(unknown_sorted.items())[:10], 1):
            print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    print("\n✅ Created:")
    print("  - hobbit_characters.json / .txt")
    print("  - hobbit_places.json / .txt")
    print("  - hobbit_entities_unknown.json")

if __name__ == '__main__':
    extract_all()
