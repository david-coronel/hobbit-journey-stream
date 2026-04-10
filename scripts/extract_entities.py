#!/usr/bin/env python3
"""
Extract characters and places from The Hobbit narrative analysis.
Uses pattern matching and heuristics to identify proper nouns.
"""

import json
import re
from collections import Counter, defaultdict

def load_narrative_data(filepath="hobbit_narrative_analysis.json"):
    """Load the narrative analysis data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Return the entries list
    return data.get('entries', data.get('timeline', []))

def extract_capitalized_phrases(text):
    """
    Extract capitalized words and phrases from text.
    Returns list of potential proper nouns.
    """
    # Multi-word capitalized phrases (e.g., "The Shire", "Lake Town")
    multi_word = re.findall(r'\b(?:The|A|An)?\s*[A-Z][a-z]+(?:\s+(?:of|the|in|on|at|under|over|upon)?\s*[A-Z][a-z]+)+\b', text)
    
    # Single capitalized words (but not sentence starters unless followed by lowercase)
    single_word = re.findall(r'\b[A-Z][a-z]{1,15}\b', text)
    
    return multi_word + single_word

def is_likely_name(phrase, count, all_phrases):
    """
    Determine if a capitalized phrase is likely a proper name.
    Filters out common words and requires multiple occurrences.
    """
    phrase = phrase.strip()
    
    # Common words to exclude (non-names that get capitalized)
    common_words = {
        'the', 'and', 'but', 'or', 'yet', 'so', 'for', 'nor',
        'he', 'she', 'it', 'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us',
        'his', 'her', 'its', 'their', 'our', 'your', 'my',
        'this', 'that', 'these', 'those',
        'there', 'here', 'where', 'when', 'what', 'who', 'why', 'how',
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'first', 'second', 'third', 'last', 'next', 'other', 'another',
        'good', 'great', 'little', 'old', 'new', 'long', 'small', 'big', 'high', 'low',
        'dark', 'light', 'hot', 'cold', 'far', 'near', 'deep', 'wide',
        'suddenly', 'perhaps', 'indeed', 'however', 'although', 'though',
        'very', 'much', 'many', 'more', 'most', 'some', 'any', 'all', 'none',
        'now', 'then', 'soon', 'later', 'before', 'after', 'again', 'once',
        'well', 'just', 'only', 'even', 'also', 'still', 'already',
        'back', 'away', 'down', 'up', 'out', 'in', 'off', 'on', 'over', 'under',
        'right', 'left', 'straight', 'round', 'about',
        'such', 'same', 'different', 'own', 'last', 'few', 'several',
        'may', 'might', 'must', 'shall', 'should', 'will', 'would', 'could', 'can',
        'said', 'say', 'says', 'came', 'come', 'went', 'go', 'goes', 'going',
        'look', 'looked', 'looking', 'see', 'saw', 'seen', 'seem', 'seemed',
        'know', 'knew', 'known', 'think', 'thought', 'find', 'found',
        'day', 'night', 'morning', 'evening', 'time', 'way', 'man', 'men', 'hand',
        'head', 'face', 'eye', 'eyes', 'door', 'room', 'hill', 'mountain', 'forest',
        'water', 'fire', 'sun', 'moon', 'wind', 'rain', 'snow', 'ground', 'earth',
        'stone', 'rock', 'wood', 'tree', 'grass', 'gold', 'silver', 'iron',
        'sword', 'bow', 'arrow', 'knife', 'staff', 'ring', 'key', 'door', 'gate',
        'cave', 'hall', 'house', 'home', 'path', 'road', 'bridge', 'river', 'lake',
        'son', 'daughter', 'father', 'mother', 'brother', 'sister', 'friend',
        'king', 'queen', 'lord', 'master', 'sir', 'mr', 'mrs', 'ms',
        'answer', 'question', 'thing', 'nothing', 'something', 'everything',
        'end', 'beginning', 'middle', 'side', 'top', 'bottom', 'edge', 'center',
        'name', 'story', 'song', 'word', 'voice', 'sound', 'noise', 'music',
        'north', 'south', 'east', 'west',
        'hobbit', 'dwarf', 'dwarves', 'elf', 'elves', 'goblin', 'goblins', 'orc', 'orcs',
        'troll', 'trolls', 'dragon', 'wizard', 'eagle', 'eagles', 'raven', 'ravens',
        'pony', 'ponies', 'horse', 'horses', 'dog', 'dogs', 'wolf', 'wolves',
        'giant', 'giants', 'spider', 'spiders', 'butterfly', 'butterflies',
        'bread', 'meat', 'cheese', 'ale', 'wine', 'food', 'meal', 'breakfast', 'dinner',
        'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    }
    
    # Exclude if it's just a common word
    if phrase.lower() in common_words:
        return False
    
    # Require at least 2 occurrences (filter out rare false positives)
    if count < 2:
        return False
    
    # Exclude very short words (likely not names)
    if len(phrase) < 3:
        return False
    
    # Exclude roman numerals
    if re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', phrase):
        return False
    
    return True

def classify_entity(phrase, context_examples):
    """
    Classify an entity as character or place based on patterns and context.
    Returns: 'character', 'place', or 'unknown'
    """
    phrase_lower = phrase.lower()
    
    # Known Middle-earth characters (major and minor)
    known_characters = {
        # Main characters
        'bilbo', 'bilbo baggins', 'baggins',
        'gandalf', 'gandalf the grey', 'the wizard',
        'thorin', 'thorin oakenshield', 'oakenshield',
        'smaug', 'the dragon',
        'gollum',
        'beorn', 'the skin-changer', 'skin-changer',
        'bard', 'bard the bowman', 'the bowman',
        'elrond',
        'the necromancer',
        'the lord of the eagles', 'great eagle',
        
        # Dwarves
        'balin', 'dwalin', 'fili', 'kili', 'dori', 'nori', 'ori',
        'oin', 'gloin', 'bifur', 'bofur', 'bombur', 'thrain', 'thror',
        
        # Elves
        'thranduil', 'the elvenking', 'elvenking', 'the king of the elves',
        'galion',
        
        # Humans
        'bard', 'master of lake-town', 'master', 'the master',
        'the captain', 'the raft-men', 'the men of the lake',
        
        # Goblins
        'the great goblin', 'great goblin', 'the goblin king', 'goblin king',
        
        # Trolls
        'bert', 'tom', 'william', 'the trolls',
        
        # Spiders
        'the spiders',
        
        # Wolves/Wargs
        'the wargs', 'wargs',
        
        # Eagles
        'gwaihir', 
        
        # Others
        'the ferryman', 'the boatman',
    }
    
    # Known Middle-earth places
    known_places = {
        # Regions
        'the shire', 'shire', 'hobbiton', 'bywater', 'the water',
        'trollshaws', 'troll shaws',
        'rivendell', 'the last homely house',
        'misty mountains', 'the misty mountains',
        'mirkwood', 'the forest', 'the dark forest', 'the wood',
        'lonely mountain', 'the lonely mountain', 'erebor', 'the mountain',
        'dale', 'esgaroth', 'lake-town', 'lake town', 'the lake',
        'the iron hills',
        'the anduin', 'the great river', 'forest river',
        'wilderland', 'the wild',
        'gundabad', 'mount gundabad',
        'moria', 'the black land',
        'the grey mountains',
        'the blue mountains',
        
        # Specific locations
        'bag end', 'the hill', 'the green dragon', 'the ivy bush',
        'the trolls camp', 'the trolls clearing',
        'the high pass', 'high pass',
        'the goblin gate', 'goblin gate',
        'the goblin tunnels', 'the tunnels',
        'gollums lake', 'the underground lake',
        'the carrock', 'carrock',
        'beorns hall', 'beorns house', 'beorns clearing',
        'the enchanted stream', 'the black river',
        'the elvenking halls', 'the kings palace', 'the cellar',
        'the bottom of the hill', 'the dragons lair', 'the great hall',
        'ravenhill', 'the front gate', 'the back door', 'the secret door',
        'the guardroom', 'the treasure chamber',
        'the camp', 'the camp of the men', 'the camp of the elves',
        'the battlefield',
    }
    
    # Check known lists
    if phrase_lower in known_characters:
        return 'character'
    if phrase_lower in known_places:
        return 'place'
    
    # Pattern-based classification
    
    # Place indicators in the name itself
    place_suffixes = ['town', 'hill', 'mountain', 'wood', 'forest', 'river', 'lake', 'water', 
                      'dale', 'gate', 'door', 'cave', 'hall', 'pass', 'clearing', 'stream',
                      'path', 'road', 'bridge', 'camp', 'land', 'country', 'region',
                      'cellar', 'chamber', 'room', 'palace', 'house', 'lair', 'tunnels']
    place_prefixes = ['mount', 'lake', 'river', 'forest', 'green', 'lonely', 'mistry', 'misty',
                      'dark', 'high', 'low', 'great', 'little', 'long']
    
    for suffix in place_suffixes:
        if phrase_lower.endswith(' ' + suffix) or phrase_lower == suffix:
            return 'place'
    
    # Character indicators
    character_titles = ['king', 'queen', 'lord', 'master', 'captain', 'elf', 'dwarf', 'goblin',
                        'troll', 'wizard', 'dragon', 'skin-changer', 'bowman', 'ferryman', 'boatman',
                        'necromancer', 'eagle', 'spider']
    
    for title in character_titles:
        if title in phrase_lower:
            # Check if it's "the [title]" pattern (more likely character)
            if re.search(r'\bthe\s+' + title + r'\b', phrase_lower):
                return 'character'
    
    # Check context for clues
    for context in context_examples[:5]:  # Check first 5 examples
        context_lower = context.lower()
        
        # Character context clues
        character_clues = ['said', 'asked', 'answered', 'replied', 'cried', 'shouted', 'whispered',
                          'thought', 'felt', 'saw', 'looked', 'went', 'came', 'stood', 'sat',
                          'he', 'she', 'him', 'her', 'his']
        for clue in character_clues:
            if ' ' + clue + ' ' in context_lower or context_lower.startswith(clue + ' '):
                return 'character'
        
        # Place context clues  
        place_clues = ['in', 'at', 'to', 'from', 'through', 'over', 'under', 'near', 'towards',
                       'upon', 'inside', 'outside', 'beyond', 'above', 'below']
        for clue in place_clues:
            if ' ' + clue + ' the ' + phrase_lower in context_lower or \
               ' ' + clue + ' ' + phrase_lower in context_lower:
                return 'place'
    
    return 'unknown'

def extract_entities():
    """Main function to extract and classify entities."""
    print("Loading narrative data...")
    entries = load_narrative_data()
    
    print("Extracting capitalized phrases...")
    all_phrases = []
    phrase_contexts = defaultdict(list)
    
    for entry in entries:
        content = entry['content']
        phrases = extract_capitalized_phrases(content)
        all_phrases.extend(phrases)
        
        # Store context for each phrase
        for phrase in phrases:
            if len(phrase_contexts[phrase]) < 10:  # Keep up to 10 examples
                phrase_contexts[phrase].append(content)
    
    # Count occurrences
    phrase_counts = Counter(all_phrases)
    
    print(f"Found {len(phrase_counts)} unique capitalized phrases")
    
    # Filter to likely names
    print("Filtering to likely names...")
    likely_names = {}
    for phrase, count in phrase_counts.items():
        if is_likely_name(phrase, count, phrase_counts):
            likely_names[phrase] = {
                'count': count,
                'contexts': phrase_contexts[phrase]
            }
    
    print(f"Found {len(likely_names)} likely names")
    
    # Classify entities
    print("Classifying entities...")
    characters = {}
    places = {}
    unknown = {}
    
    for phrase, info in likely_names.items():
        classification = classify_entity(phrase, info['contexts'])
        
        entity_info = {
            'name': phrase,
            'mentions': info['count'],
            'contexts': info['contexts'][:3]  # Store first 3 context examples
        }
        
        if classification == 'character':
            characters[phrase] = entity_info
        elif classification == 'place':
            places[phrase] = entity_info
        else:
            unknown[phrase] = entity_info
    
    print(f"Classified: {len(characters)} characters, {len(places)} places, {len(unknown)} unknown")
    
    # Save results
    # Sort by mention count
    characters_sorted = dict(sorted(characters.items(), key=lambda x: x[1]['mentions'], reverse=True))
    places_sorted = dict(sorted(places.items(), key=lambda x: x[1]['mentions'], reverse=True))
    unknown_sorted = dict(sorted(unknown.items(), key=lambda x: x[1]['mentions'], reverse=True))
    
    # Save to JSON
    with open('../data/hobbit_characters.json', 'w', encoding='utf-8') as f:
        json.dump({
            'count': len(characters_sorted),
            'characters': characters_sorted
        }, f, indent=2, ensure_ascii=False)
    
    with open('../data/hobbit_places.json', 'w', encoding='utf-8') as f:
        json.dump({
            'count': len(places_sorted),
            'places': places_sorted
        }, f, indent=2, ensure_ascii=False)
    
    with open('../data/hobbit_entities_unknown.json', 'w', encoding='utf-8') as f:
        json.dump({
            'count': len(unknown_sorted),
            'entities': unknown_sorted
        }, f, indent=2, ensure_ascii=False)
    
    # Also create readable text files
    with open('hobbit_characters.txt', 'w', encoding='utf-8') as f:
        f.write("# Characters in The Hobbit\n\n")
        f.write(f"Total: {len(characters_sorted)} characters\n\n")
        f.write("| Character | Mentions | Sample Contexts |\n")
        f.write("|-----------|----------|------------------|\n")
        for name, info in list(characters_sorted.items())[:100]:  # Top 100
            contexts = info['contexts'][0][:80] + '...' if len(info['contexts'][0]) > 80 else info['contexts'][0]
            f.write(f"| {name} | {info['mentions']} | {contexts} |\n")
    
    with open('hobbit_places.txt', 'w', encoding='utf-8') as f:
        f.write("# Places in The Hobbit\n\n")
        f.write(f"Total: {len(places_sorted)} places\n\n")
        f.write("| Place | Mentions | Sample Contexts |\n")
        f.write("|-------|----------|------------------|\n")
        for name, info in list(places_sorted.items())[:100]:  # Top 100
            contexts = info['contexts'][0][:80] + '...' if len(info['contexts'][0]) > 80 else info['contexts'][0]
            f.write(f"| {name} | {info['mentions']} | {contexts} |\n")
    
    print("\n✅ Output files created:")
    print("  - hobbit_characters.json")
    print("  - hobbit_places.json")
    print("  - hobbit_characters.txt")
    print("  - hobbit_places.txt")
    print("  - hobbit_entities_unknown.json (for manual review)")
    
    # Print top entities
    print("\n" + "="*60)
    print("TOP 20 CHARACTERS:")
    print("="*60)
    for i, (name, info) in enumerate(list(characters_sorted.items())[:20], 1):
        print(f"{i:2d}. {name:<25} ({info['mentions']} mentions)")
    
    print("\n" + "="*60)
    print("TOP 20 PLACES:")
    print("="*60)
    for i, (name, info) in enumerate(list(places_sorted.items())[:20], 1):
        print(f"{i:2d}. {name:<25} ({info['mentions']} mentions)")
    
    return characters_sorted, places_sorted, unknown_sorted

if __name__ == '__main__':
    extract_entities()
