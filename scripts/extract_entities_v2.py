#!/usr/bin/env python3
"""
Extract characters and places from The Hobbit narrative analysis.
Version 2: Improved filtering and classification.
"""

import json
import re
from collections import Counter, defaultdict

def load_narrative_data(filepath="hobbit_narrative_analysis.json"):
    """Load the narrative analysis data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('entries', data.get('timeline', []))

def extract_capitalized_phrases(text):
    """Extract capitalized words and phrases from text."""
    # Multi-word capitalized phrases (e.g., "The Shire", "Lake Town")
    # Match "The X Y" or "A X Y" patterns
    multi_word = re.findall(r'\b(?:The|A|An)?\s*[A-Z][a-z]+(?:\s+(?:of|the|in|on|at|under|over|upon|and)?\s*[A-Z][a-z]+)+\b', text)
    
    # Single capitalized words
    single_word = re.findall(r'\b[A-Z][a-z]{1,15}\b', text)
    
    return multi_word + single_word

# Common words that get capitalized but are NOT names
FALSE_POSITIVE_WORDS = {
    # Sentence-starting verbs
    'said', 'asked', 'answered', 'replied', 'cried', 'shouted', 'called', 'cried',
    'thought', 'felt', 'saw', 'looked', 'went', 'came', 'stood', 'sat', 'went',
    'began', 'started', 'stopped', 'continued', 'turned', 'walked', 'ran', 'moved',
    'heard', 'found', 'took', 'gave', 'put', 'set', 'left', 'right', 'made',
    'added', 'agreed', 'allowed', 'asked', 'brought', 'built', 'burned',
    'carried', 'caught', 'changed', 'closed', 'opened', 'followed', 'forgot',
    'remembered', 'returned', 'sent', 'showed', 'spoke', 'told', 'tried', 'used',
    'waited', 'wanted', 'watched', 'worked', 'wrapped',
    
    # Modal/auxiliary verbs
    'not', 'let', 'don', 'won', 'can', 'could', 'would', 'should', 'might', 'must',
    'had', 'has', 'was', 'were', 'been', 'being', 'did', 'does', 'doing',
    'got', 'get', 'getting', 'are', 'were', 'is', 'be', 'am',
    
    # Common adverbs/adjectives at sentence start
    'now', 'then', 'soon', 'later', 'before', 'after', 'again', 'once', 'back',
    'away', 'down', 'up', 'out', 'in', 'off', 'over', 'under', 'here', 'there',
    'thus', 'hence', 'yes', 'no', 'well', 'just', 'only', 'even', 'also', 'still',
    'already', 'perhaps', 'indeed', 'however', 'suddenly', 'finally', 'at',
    
    # Sentence-starting nouns that aren't proper names
    'day', 'night', 'morning', 'evening', 'time', 'way', 'man', 'men', 'hand',
    'head', 'face', 'eye', 'eyes', 'door', 'room', 'hill', 'side', 'end', 'top',
    'water', 'fire', 'sun', 'moon', 'wind', 'rain', 'snow', 'ground', 'earth',
    'stone', 'rock', 'wood', 'tree', 'grass', 'gold', 'silver', 'iron', 'light',
    'dark', 'shadow', 'path', 'road', 'bridge', 'camp', 'wall', 'floor', 'roof',
    'song', 'story', 'voice', 'sound', 'noise', 'word', 'name', 'question', 'answer',
    'thing', 'nothing', 'something', 'everything', 'anything', 'part', 'rest',
    'front', 'back', 'middle', 'centre', 'center', 'edge', 'corner', 'place',
    'moment', 'minute', 'hour', 'year', 'week', 'month', 'today', 'tomorrow',
    
    # Numbers/ordinals
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'first', 'second', 'third', 'fourth', 'fifth', 'last', 'next', 'other', 'another',
    
    # Directions
    'north', 'south', 'east', 'west',
    
    # Colors
    'red', 'blue', 'green', 'yellow', 'white', 'black', 'brown', 'grey', 'gray', 'gold',
    
    # Pronouns and determiners
    'he', 'she', 'it', 'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us',
    'his', 'its', 'their', 'our', 'your', 'my', 'this', 'that', 'these', 'those',
    'each', 'every', 'all', 'both', 'either', 'neither', 'some', 'any', 'many',
    'much', 'more', 'most', 'few', 'several', 'various', 'such', 'same', 'different',
    'own', 'very', 'own', 'own', 'whole', 'half', 'quarter', 'double', 'single',
    
    # Interjections
    'oh', 'ah', 'ha', 'ho', 'hey', 'why', 'what', 'when', 'where', 'who', 'how',
    
    # Dialect/slang
    'yer', 'ye', 'em',
    
    # Cooking/food words that appear capitalized
    'roast', 'boiled', 'baked', 'fried', 'stew', 'toast', 'tea', 'ale', 'wine',
    
    # Miscellaneous false positives
    'ugh', 'pound', 'past', 'turn', 'clouds', 'lullaby', 'roads', 'standing',
    'running', 'take', 'get', 'give', 'make', 'put', 'cut', 'sit', 'try', 'fly',
    'did', 'was', 'were', 'map', 'bag', 'tea', 'foe', 'lob', 'bid', 'ere',
    'than', 'tra', 'azog',  # Azog is a character but barely mentioned
}

def is_likely_name(phrase, count):
    """Determine if a capitalized phrase is likely a proper name."""
    phrase = phrase.strip()
    phrase_lower = phrase.lower()
    
    # Exclude common false positives
    if phrase_lower in FALSE_POSITIVE_WORDS:
        return False
    
    # Exclude very short words (unless they are known Tolkien names)
    known_short_names = {'be', 'ma', 'um', 'azog', 'ori', 'oin', 'ui', 'ui'}
    if len(phrase) < 3 and phrase_lower not in known_short_names:
        return False
    
    # Require at least 2 occurrences
    if count < 2:
        return False
    
    # Exclude roman numerals
    if re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', phrase):
        return False
    
    return True

# Known Middle-earth entities for better classification
KNOWN_CHARACTERS = {
    # Main characters
    'bilbo', 'bilbo baggins', 'baggins',
    'gandalf', 'gandalf the grey', 'mithrandir', 'the wizard', 'wizard',
    'thorin', 'thorin oakenshield', 'oakenshield',
    'smaug', 'the dragon', 'dragon',
    'gollum', 'smeagol',
    'beorn', 'the skin-changer', 'skin-changer', 'the beorning',
    'bard', 'bard the bowman', 'the bowman',
    'elrond', 'the master of rivendell',
    'the necromancer', 'necromancer',
    'the lord of the eagles', 'the eagle king', 'great eagle',
    
    # Dwarves
    'balin', 'dwalin', 'fili', 'kili', 'dori', 'nori', 'ori',
    'oin', 'gloin', 'bifur', 'bofur', 'bombur', 
    'thrain', 'thror', 'the father of thorin',
    
    # Elves
    'thranduil', 'the elvenking', 'elvenking', 'the king of the elves', 'the elf king',
    'galion', 'the butler',
    
    # Humans
    'the master', 'master of lake-town', 'the master of esgaroth',
    'the captain', 'the raft-men',
    'girion', 'lord of dale',
    
    # Goblins
    'the great goblin', 'great goblin', 'the goblin king', 'goblin king',
    
    # Trolls
    'bert', 'tom', 'tom troll', 'bert troll', 'william', 'william troll', 'the trolls',
    
    # Wolves/Wargs
    'the wargs', 'wargs', 'the wolf', 'wolf', 'the wolves',
    
    # Eagles
    'gwaihir', 'the great eagle',
    
    # Spiders
    'the spiders', 'the great spider',
    
    # Other
    'the ferryman', 'the boatman', 'old tommy', 'old tommy troll',
}

KNOWN_PLACES = {
    # Shire region
    'the shire', 'shire', 'hobbiton', 'bywater', 'the water', 'bag end', 'bag-end',
    'the hill', 'the green dragon', 'the ivy bush', 'tookland', 'great smials',
    
    # Eriador
    'trollshaws', 'troll shaws', 'the trollshaws', 'the trolls camp',
    'rivendell', 'the last homely house', 'the house of elrond',
    'the ford of bruinen',
    
    # Misty Mountains
    'misty mountains', 'the misty mountains', 'the high pass', 'high pass',
    'the goblin gate', 'goblin gate', 'the front porch',
    'the goblin tunnels', 'the tunnels', 'the underground halls',
    'gollums lake', 'the underground lake', 'the inky pool',
    'the back door', 'the little back door',
    
    # Anduin Vale
    'the anduin', 'anduin', 'the great river', 'the river', 'forest river',
    'the carrock', 'carrock', 'the eagle eyrie',
    'beorns hall', 'beorns house', 'beorns clearing', 'beorns lands',
    'beorns house', 'beorns keep',
    
    # Mirkwood
    'mirkwood', 'the forest', 'the dark forest', 'the wood', 'the black forest',
    'the enchanted stream', 'the black river', 'the stream', 'the magic stream',
    'the elf path', 'the elf road', 'the elven path',
    'the elvenking halls', 'the kings palace', 'the kings cellar', 'the cellar',
    'the dungeon', 'the wood elves cave', 'the caves', 'the elven halls',
    'the bridge', 'the elven bridge',
    
    # Erebor and Dale
    'lonely mountain', 'the lonely mountain', 'erebor', 'the mountain', 'the mount',
    'the desolation of smaug', 'the desolation',
    'dale', 'the town of dale', 'the city of dale',
    'ravenhill', 'the guardroom', 'the treasure chamber', 'the great hall',
    'the front gate', 'the gate', 'the secret door', 'the hidden door',
    'the bottom of the hill', 'the dragons lair', 'lair', 'the chamber',
    'the arkenstone chamber',
    
    # Lake-town
    'esgaroth', 'lake-town', 'lake town', 'the lake', 'the long lake', 'long lake',
    'the master house', 'the masters house', 'the town hall',
    'the bridge town', 'the market place',
    
    # Iron Hills
    'the iron hills', 'iron hills',
    
    # Wider world
    'wilderland', 'the wild', 'the wild lands', 'the east',
    'gundabad', 'mount gundabad',
    'moria', 'khazad-dum', 'the black land', 'the black chasm',
    'the grey mountains', 'the withered heath',
    'the blue mountains', 'the ered luin',
    'the northern wastes', 'the waste',
    'rhun', 'the east lands', 'the south',
    'the end of the world',
    
    # Camps and battlefields
    'the camp', 'the camp of the men', 'the camp of the elves', 'the camp of the dwarves',
    'the battlefield', 'the plain', 'the valley', 'the slopes',
    'the wall', 'the fortified wall',
}

def classify_entity(phrase, context_examples):
    """Classify an entity as character or place."""
    phrase_lower = phrase.lower().strip()
    
    # Direct matches in known lists
    if phrase_lower in KNOWN_CHARACTERS:
        return 'character'
    if phrase_lower in KNOWN_PLACES:
        return 'place'
    
    # Pattern-based classification
    
    # Place suffixes (geographic features)
    place_suffixes = [
        'town', 'ville', 'ton', 'ham', 'by', 'thorpe', 'wick', 'wich', 'stead', 'stede',
        'hill', 'mount', 'mountain', 'mont', 'berg', 'tor', 'fell', 'down', 'downs',
        'wood', 'woods', 'forest', 'weald', 'holt', 'shaw', 'thicket',
        'river', 'rill', 'brook', 'beck', 'burn', 'bourne', 'water', 'ford', 'ford',
        'lake', 'loch', 'lough', 'mere', 'tarn', 'pool', 'pond', 'waters',
        'dale', 'valley', 'vale', 'glen', 'dale', 'cwm',
        'cave', 'cavern', 'hole', 'hollow',
        'gate', 'door', 'portal', 'entry', 'entrance', 'way', 'path', 'road', 'track', 'trail',
        'hall', 'house', 'home', 'stead', 'hold', 'court', 'garth', 'yard',
        'camp', 'clearing', 'mead', 'field', 'plain', 'heath', 'moor', 'waste',
        'wall', 'bridge', 'cross', 'crossing', 'pass', 'gap', 'notch', 'col',
        'rock', 'stone', 'cliff', 'crag', 'scar', 'edge', 'brink',
        'land', 'lands', 'realm', 'kingdom', 'domain', 'country', 'region', 'shire',
        'chamber', 'room', 'cellar', 'dungeon', 'pit', 'shaft', 'mine',
        'lair', 'den', 'nest', 'eyrie',
        'slope', 'side', 'face', 'flank', 'shoulder', 'brow',
        'eyrie', 'aerie',
    ]
    
    for suffix in place_suffixes:
        if phrase_lower.endswith(' ' + suffix) or phrase_lower == suffix:
            # But check if it's "the [something]" which could be a character title
            if re.match(r'^the\s+\w+$', phrase_lower):
                return 'unknown'
            return 'place'
    
    # Character titles
    character_indicators = [
        'king', 'queen', 'lord', 'lady', 'master', 'mistress', 'sir', 'madam',
        'captain', 'chief', 'head', 'leader', 'prince', 'princess',
        'wizard', 'witch', 'mage', 'sorcerer', 'necromancer',
        'elf', 'elves', 'dwarf', 'dwarves', 'goblin', 'goblins', 'orc', 'orcs',
        'troll', 'trolls', 'giant', 'giants', 'dragon', 'eagle', 'eagles',
        'man', 'men', 'woman', 'women', 'child', 'children',
        'rider', 'riders', 'warrior', 'warriors', 'guard', 'guards', 'sentry', 'sentries',
        'bowman', 'archer', 'spearman', 'swordsman', 'fighter', 'champion',
        'butler', 'servant', 'slave', 'prisoner', 'captive',
        'ferryman', 'boatman', 'sailor', 'mariner', 'captain',
        'father', 'mother', 'brother', 'sister', 'son', 'daughter', 'uncle', 'aunt', 'cousin',
        'friend', 'foe', 'enemy', 'ally', 'companion', 'comrade',
        'skin-changer', 'skin-changers', 'werewolf', 'werebear',
        'spider', 'spiders', 'wolf', 'wolves', 'wargs', 'warg',
        'raven', 'ravens', 'thrush', 'thrushes', 'bird', 'birds',
    ]
    
    # Check if phrase contains character indicators
    for indicator in character_indicators:
        if indicator in phrase_lower:
            # Check if it's "the [indicator]" pattern
            if re.search(r'\bthe\s+' + indicator + r'\b', phrase_lower):
                return 'character'
            # Or just the indicator at the end
            if phrase_lower.endswith(' ' + indicator) or phrase_lower == indicator:
                return 'character'
    
    # Analyze contexts
    character_context_clues = 0
    place_context_clues = 0
    
    for context in context_examples[:5]:
        context_lower = context.lower()
        
        # Character action verbs (subject position)
        char_verbs = ['said', 'asked', 'answered', 'replied', 'cried', 'shouted', 'called',
                      'thought', 'felt', 'knew', 'saw', 'looked', 'went', 'came']
        for verb in char_verbs:
            # Pattern: "Name said/verb" or "The X said/verb"
            if re.search(r'\b' + re.escape(phrase_lower) + r'\s+' + verb + r'\b', context_lower):
                character_context_clues += 1
        
        # Place prepositions
        place_preps = ['in', 'at', 'to', 'from', 'through', 'over', 'under', 'near', 
                       'towards', 'upon', 'inside', 'outside', 'beyond', 'above', 'below']
        for prep in place_preps:
            # Pattern: "prep Name" or "prep the Name"
            if re.search(r'\b' + prep + r'\s+(?:the\s+)?' + re.escape(phrase_lower) + r'\b', context_lower):
                place_context_clues += 1
    
    if character_context_clues > place_context_clues:
        return 'character'
    elif place_context_clues > character_context_clues:
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
        
        for phrase in phrases:
            if len(phrase_contexts[phrase]) < 10:
                phrase_contexts[phrase].append(content)
    
    phrase_counts = Counter(all_phrases)
    print(f"Found {len(phrase_counts)} unique capitalized phrases")
    
    # Filter to likely names
    print("Filtering to likely names...")
    likely_names = {}
    for phrase, count in phrase_counts.items():
        if is_likely_name(phrase, count):
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
            'contexts': info['contexts'][:3]
        }
        
        if classification == 'character':
            characters[phrase] = entity_info
        elif classification == 'place':
            places[phrase] = entity_info
        else:
            unknown[phrase] = entity_info
    
    print(f"Classified: {len(characters)} characters, {len(places)} places, {len(unknown)} unknown")
    
    # Sort by mention count
    characters_sorted = dict(sorted(characters.items(), key=lambda x: x[1]['mentions'], reverse=True))
    places_sorted = dict(sorted(places.items(), key=lambda x: x[1]['mentions'], reverse=True))
    unknown_sorted = dict(sorted(unknown.items(), key=lambda x: x[1]['mentions'], reverse=True))
    
    # Save to JSON
    with open('../data/hobbit_characters.json', 'w', encoding='utf-8') as f:
        json.dump({'count': len(characters_sorted), 'characters': characters_sorted}, f, indent=2, ensure_ascii=False)
    
    with open('../data/hobbit_places.json', 'w', encoding='utf-8') as f:
        json.dump({'count': len(places_sorted), 'places': places_sorted}, f, indent=2, ensure_ascii=False)
    
    with open('../data/hobbit_entities_unknown.json', 'w', encoding='utf-8') as f:
        json.dump({'count': len(unknown_sorted), 'entities': unknown_sorted}, f, indent=2, ensure_ascii=False)
    
    # Create readable text files
    with open('hobbit_characters.txt', 'w', encoding='utf-8') as f:
        f.write("# Characters in The Hobbit\n\n")
        f.write(f"Total: {len(characters_sorted)} characters\n\n")
        f.write("| # | Character | Mentions | Sample Context |\n")
        f.write("|---|-----------|----------|----------------|\n")
        for i, (name, info) in enumerate(characters_sorted.items(), 1):
            context = info['contexts'][0][:70] + '...' if len(info['contexts'][0]) > 70 else info['contexts'][0]
            f.write(f"| {i} | {name} | {info['mentions']} | {context} |\n")
    
    with open('hobbit_places.txt', 'w', encoding='utf-8') as f:
        f.write("# Places in The Hobbit\n\n")
        f.write(f"Total: {len(places_sorted)} places\n\n")
        f.write("| # | Place | Mentions | Sample Context |\n")
        f.write("|---|-------|----------|----------------|\n")
        for i, (name, info) in enumerate(places_sorted.items(), 1):
            context = info['contexts'][0][:70] + '...' if len(info['contexts'][0]) > 70 else info['contexts'][0]
            f.write(f"| {i} | {name} | {info['mentions']} | {context} |\n")
    
    # Summary
    print("\n✅ Output files created:")
    print("  - hobbit_characters.json")
    print("  - hobbit_places.json")
    print("  - hobbit_characters.txt")
    print("  - hobbit_places.txt")
    print("  - hobbit_entities_unknown.json")
    
    print("\n" + "="*60)
    print("TOP 25 CHARACTERS:")
    print("="*60)
    for i, (name, info) in enumerate(list(characters_sorted.items())[:25], 1):
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    print("\n" + "="*60)
    print("TOP 25 PLACES:")
    print("="*60)
    for i, (name, info) in enumerate(list(places_sorted.items())[:25], 1):
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    if unknown_sorted:
        print("\n" + "="*60)
        print("UNKNOWN ENTITIES (need manual review):")
        print("="*60)
        for i, (name, info) in enumerate(list(unknown_sorted.items())[:15], 1):
            print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    return characters_sorted, places_sorted, unknown_sorted

if __name__ == '__main__':
    extract_entities()
