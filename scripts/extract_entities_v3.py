#!/usr/bin/env python3
"""
Extract characters and places from The Hobbit narrative analysis.
Version 3: Better multi-word phrase handling and filtering.
"""

import json
import re
from collections import Counter, defaultdict

def load_narrative_data(filepath="hobbit_narrative_analysis.json"):
    """Load the narrative analysis data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('entries', data.get('timeline', []))

def extract_entities_from_text(text):
    """
    Extract potential entity names from text.
    Returns list of (entity, context) tuples.
    """
    entities = []
    
    # Pattern 1: Multi-word proper nouns with "The/A/An" (The Shire, The Hill)
    pattern1 = re.compile(r'\b(The|the|A|a|An|an)\s+([A-Z][a-z]+(?:\s+(?:of|the|in|on|at|under|over|upon|and)?\s*[A-Z][a-z]+)*)\b')
    for match in pattern1.finditer(text):
        full_match = match.group(0)
        # Keep full match including article
        if len(full_match) > 5:  # Avoid just "The X" where X is short
            entities.append((full_match, text))
    
    # Pattern 2: Multi-word proper nouns without article (River Running, Lonely Mountain)
    pattern2 = re.compile(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+(?:of|the|in|on|at|under|over|upon|and)?\s*[A-Z][a-z]+)*)\b')
    for match in pattern2.finditer(text):
        # Avoid sentence starts unless both words are capitalized
        start_pos = match.start()
        if start_pos > 0:
            prev_char = text[start_pos-1]
            # If preceded by sentence end or start, check if second word is also capitalized
            if prev_char in '.!?"\n':
                pass  # Likely sentence start, but both words capitalized so keep
            elif prev_char == ' ' and start_pos > 1:
                # Check if previous word ends sentence
                pass
        entities.append((match.group(0), text))
    
    # Pattern 3: Single capitalized words (names like Bilbo, Gandalf)
    # But avoid sentence starters by checking context
    pattern3 = re.compile(r'(?:^|[.!?;:]\s+|"\s*)([A-Z][a-z]{2,15})\b')
    for match in pattern3.finditer(text):
        # Only include if it looks like a name (not a common word)
        word = match.group(1)
        entities.append((word, text))
    
    # Pattern 4: Capitalized words mid-sentence (strong indicator of proper noun)
    pattern4 = re.compile(r'\s+([A-Z][a-z]{2,15})\b')
    for match in pattern4.finditer(text):
        word = match.group(1)
        entities.append((word, text))
    
    return entities

# Common words to exclude (not proper names)
COMMON_WORDS = {
    # Pronouns/determiners
    'the', 'a', 'an', 'this', 'that', 'these', 'those', 'some', 'any', 'all', 'each', 'every',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'first', 'second', 'third', 'last', 'next', 'other', 'another',
    'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    
    # Common adjectives
    'good', 'great', 'little', 'old', 'new', 'long', 'small', 'big', 'high', 'low',
    'young', 'large', 'few', 'own', 'same', 'right', 'left', 'last', 'late', 'early',
    'dark', 'light', 'heavy', 'hot', 'cold', 'far', 'near', 'deep', 'wide', 'full', 'empty',
    'whole', 'half', 'sure', 'certain', 'true', 'clear', 'open', 'closed', 'dead', 'alive',
    'red', 'blue', 'green', 'yellow', 'white', 'black', 'brown', 'grey', 'gray', 'gold', 'golden',
    'silent', 'quiet', 'loud', 'quick', 'slow', 'hard', 'soft', 'sharp', 'dull',
    'strong', 'weak', 'brave', 'fierce', 'wild', 'tame', 'fell', 'keen',
    
    # Common nouns
    'day', 'night', 'morning', 'evening', 'time', 'way', 'man', 'men', 'hand', 'hands',
    'head', 'face', 'eye', 'eyes', 'foot', 'feet', 'back', 'side', 'end', 'top', 'bottom',
    'door', 'room', 'wall', 'floor', 'roof', 'window', 'fire', 'water', 'sun', 'moon',
    'wind', 'rain', 'snow', 'ground', 'earth', 'stone', 'rock', 'wood', 'tree', 'grass',
    'path', 'road', 'bridge', 'river', 'lake', 'hill', 'mountain', 'valley', 'wood', 'forest',
    'camp', 'wall', 'gate', 'cave', 'hall', 'house', 'home', 'place', 'spot', 'point',
    'sound', 'noise', 'voice', 'song', 'word', 'story', 'question', 'answer', 'thing',
    'part', 'piece', 'bit', 'lot', 'deal', 'kind', 'sort', 'name', 'number',
    'north', 'south', 'east', 'west',
    
    # Verbs (common at sentence start)
    'said', 'asked', 'answered', 'replied', 'cried', 'shouted', 'called', 'cried', 'answered',
    'thought', 'felt', 'saw', 'looked', 'went', 'came', 'stood', 'sat', 'went', 'got',
    'began', 'started', 'stopped', 'continued', 'turned', 'walked', 'ran', 'moved', 'came',
    'heard', 'found', 'took', 'gave', 'put', 'set', 'left', 'made', 'brought', 'saw',
    'added', 'agreed', 'allowed', 'asked', 'burned', 'carried', 'caught', 'changed',
    'closed', 'opened', 'followed', 'forgot', 'remembered', 'returned', 'sent', 'showed',
    'spoke', 'told', 'tried', 'used', 'waited', 'wanted', 'watched', 'worked', 'wrapped',
    'did', 'done', 'doing', 'had', 'has', 'have', 'having', 'was', 'were', 'been', 'being',
    'is', 'are', 'am', 'be', 'will', 'would', 'shall', 'should', 'may', 'might', 'can', 'could',
    'come', 'coming', 'go', 'going', 'gone', 'went', 'get', 'getting', 'got', 'gotten',
    'take', 'taking', 'took', 'taken', 'make', 'making', 'made', 'run', 'running', 'ran',
    'know', 'knew', 'known', 'knowing', 'think', 'thinking', 'thought', 'tell', 'told',
    'see', 'seeing', 'seen', 'saw', 'say', 'saying', 'give', 'giving', 'gave', 'given',
    'find', 'finding', 'found', 'eat', 'eating', 'ate', 'eaten', 'drink', 'drinking', 'drank', 'drunk',
    'not', 'let', 'don', 'won', 'aren', 'wasn', 'weren', 'haven', 'hasn', 'hadn',
    
    # Adverbs
    'now', 'then', 'soon', 'later', 'before', 'after', 'again', 'once', 'back', 'away',
    'down', 'up', 'out', 'in', 'off', 'over', 'under', 'here', 'there', 'thus', 'hence',
    'yes', 'no', 'well', 'just', 'only', 'even', 'also', 'still', 'already', 'perhaps',
    'indeed', 'however', 'suddenly', 'finally', 'at', 'yet', 'but', 'and', 'or', 'nor',
    'very', 'quite', 'rather', 'too', 'so', 'as', 'how', 'when', 'where', 'why', 'what',
    'almost', 'nearly', 'hardly', 'scarcely', 'barely', 'just', 'only', 'merely',
    'quickly', 'slowly', 'carefully', 'suddenly', 'immediately', 'finally', 'eventually',
    
    # Prepositions (when standalone)
    'for', 'from', 'with', 'into', 'onto', 'upon', 'within', 'without', 'through', 'throughout',
    'between', 'among', 'amid', 'amidst', 'beside', 'besides', 'beyond', 'except', 'save',
    'till', 'until', 'unto', 'toward', 'towards', 'against', 'across', 'along', 'around',
    'behind', 'below', 'beneath', 'beside', 'inside', 'outside', 'past', 'since', 'than',
    'though', 'although', 'because', 'while', 'whilst', 'whereas', 'whether',
    
    # Conjunctions
    'and', 'but', 'or', 'nor', 'for', 'so', 'yet', 'either', 'neither', 'both',
    'whether', 'either', 'neither', 'both', 'not', 'only', 'also', 'too',
    
    # Numbers/quantifiers
    'much', 'many', 'more', 'most', 'some', 'any', 'all', 'none', 'nothing', 'something',
    'everything', 'anything', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten', 'eleven', 'twelve', 'first', 'second', 'third', 'fourth',
    
    # Time words
    'today', 'tomorrow', 'yesterday', 'morning', 'evening', 'night', 'day', 'week',
    'month', 'year', 'hour', 'minute', 'moment', 'while', 'time', 'spring', 'summer',
    'autumn', 'fall', 'winter',
    
    # Dialect/slang
    'yer', 'ye', 'em', 'um', 'uh', 'eh', 'ah', 'oh', 'ho', 'ha',
    
    # Meta
    'chapter', 'note', 'end', 'beginning', 'middle', 'part', 'section', 'book',
    
    # Months/days (capitalized)
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
}

# Known Tolkien entities
KNOWN_CHARACTERS = {
    # Main characters
    'bilbo', 'bilbo baggins', 'baggins',
    'gandalf', 'gandalf the grey', 'mithrandir', 'the grey wizard', 'the wizard',
    'thorin', 'thorin oakenshield', 'oakenshield',
    'smaug', 'the dragon', 'the worm',
    'gollum', 'smeagol',
    'beorn', 'the skin-changer', 'skin-changer', 'the beorning',
    'bard', 'bard the bowman', 'the bowman', 'bard of esgaroth',
    'elrond', 'the master of rivendell', 'half-elven',
    'the necromancer', 'necromancer',
    'the lord of the eagles', 'the great eagle', 'the eagle king',
    
    # Dwarves - Thorin and company
    'balin', 'dwalin', 'fili', 'kili', 'dori', 'nori', 'ori',
    'oin', 'gloin', 'bifur', 'bofur', 'bombur', 
    'thrain', 'thror', 'the father of thorin',
    
    # Dwarves - others
    'dain', 'dain ironfoot', 'ironfoot',
    'nain', 'funder', 'gror', 'borin',
    
    # Elves
    'thranduil', 'the elvenking', 'elvenking', 'the king of the elves', 'the elf king',
    'galion', 'the butler', 'the elven butler',
    'the elf guard', 'the elf captain', 'the chief guard',
    
    # Men
    'the master', 'master of lake-town', 'the master of esgaroth', 'the coward',
    'the captain', 'the raft-men', 'the bargemen',
    'girion', 'lord of dale', 'the lord of dale',
    'the men of esgaroth', 'the men of the lake', 'the lake men',
    'the bowman', 'the archer',
    
    # Goblins
    'the great goblin', 'great goblin', 'the goblin king', 'goblin king', 'the king under the mountain',
    'goblin soldiers', 'the goblins', 'the orcs',
    
    # Trolls
    'tom', 'bert', 'william', 'tom troll', 'bert troll', 'william troll',
    'the trolls', 'the three trolls', 'old tommy', 'old tommy troll',
    
    # Wargs/Wolves
    'the wargs', 'wargs', 'the wolves', 'the wolf', 'the great wolf',
    
    # Eagles
    'gwaihir', 'the windlord',
    
    # Spiders
    'the spiders', 'the great spider', 'the forest spiders',
    
    # Thrushes/Ravens
    'roac', 'roac the raven', 'the old raven', 'the raven', 'the ravens',
    'the thrush', 'the old thrush', 'the thrushes',
    
    # Ponies
    'the ponies', 'the pony', 'myrtle', 'minty', 'grip', 'wolf', 'whitey',
    'the last pony',
    
    # Other beings
    'the stone-giants', 'the giants', 'the mountain giants',
    'the enchanted deer', 'the deer',
    'the flies', 'the butterflies', 'the bees',
    'the thrush', 'the blackbird', 'the old thrush',
    
    # Minor characters
    'the ferryman', 'the boatman', 'the raftman', 'old tolly',
    'the gate guard', 'the porter', 'the doorward',
    'the cellarman', 'the butler',
    'the minstrel', 'the harpist', 'the singer',
}

KNOWN_PLACES = {
    # The Shire
    'the shire', 'shire', 'hobbiton', 'hobbiton hill', 'bywater', 'the water',
    'bag end', 'bag-end', 'bag end house',
    'the hill', 'the hobbiton hill', 'the shire hill',
    'the green dragon', 'the ivy bush', 'the bird and baby',
    'tookland', 'the tookland', 'great smials', 'the great smials',
    'the michel delving', 'michel delving',
    'the east road', 'the great east road',
    'the borders of the shire', 'the shire borders',
    
    # Eriador
    'trollshaws', 'troll shaws', 'the trollshaws',
    'the trolls camp', 'the clearing', 'the trolls clearing',
    'rivendell', 'the last homely house', 'the house of elrond',
    'the ford of bruinen', 'the bruinen', 'the loudwater',
    'the hidden valley', 'the valley of rivendell',
    
    # Misty Mountains
    'misty mountains', 'the misty mountains', 'the misty mountain',
    'the high pass', 'high pass', 'the pass',
    'the goblin gate', 'goblin gate', 'the front porch', 'the cave mouth',
    'the goblin tunnels', 'the tunnels', 'the underground halls', 'the goblin halls',
    'gollums lake', 'the underground lake', 'the inky pool', 'the dark lake',
    'the back door', 'the little back door', 'the secret door', 'the hidden door',
    'the crack', 'the slit', 'the narrow place',
    
    # Anduin Vale
    'the anduin', 'anduin', 'the great river', 'the river', 'the long river',
    'forest river', 'the forest river',
    'the carrock', 'carrock', 'the great rock',
    'the eagle eyrie', 'the eyrie',
    'beorns hall', 'beorns house', 'beorns clearing', 'beorns lands', 'beorns keep',
    'beorns house', 'beorns garden', 'the beorning lands',
    'the vale', 'the anduin vale',
    
    # Mirkwood
    'mirkwood', 'the forest', 'the dark forest', 'the wood', 'the black forest',
    'the forest road', 'the elf path', 'the elven path', 'the old road',
    'the enchanted stream', 'the black river', 'the stream', 'the magic stream',
    'the elvenking halls', 'the kings palace', 'the kings cellar', 'the cellar',
    'the dungeon', 'the wood elves cave', 'the caves', 'the elven halls',
    'the bridge', 'the elven bridge', 'the gate', 'the cave gate',
    'the clearing', 'the spider clearing', 'the glade',
    'the darkness', 'the blackness', 'the gloom',
    
    # Erebor region
    'lonely mountain', 'the lonely mountain', 'erebor', 'the mountain', 'the mount',
    'the desolation of smaug', 'the desolation', 'the wastes',
    'dale', 'the town of dale', 'the city of dale',
    'ravenhill', 'the guardroom', 'the treasure chamber', 'the great hall',
    'the front gate', 'the gate', 'the main gate', 'the door', 'the front door',
    'the secret door', 'the hidden door', 'the side door',
    'the bottom of the hill', 'the base of the mountain', 'the mountains foot',
    'the dragons lair', 'lair', 'the chamber', 'the arkenstone chamber',
    'the great chamber', 'the lowest cellar', 'the lowest dungeon',
    'the watchtower', 'the look-out post', 'ravenhill', 'raven hill',
    
    # Lake-town/Esgaroth
    'esgaroth', 'lake-town', 'lake town', 'the lake', 'the long lake',
    'the town', 'the town hall', 'the masters house',
    'the bridge', 'the market place', 'the market', 'the quays', 'the quay',
    'the shore', 'the lake shore', 'the water side', 'the waters edge',
    
    # Iron Hills
    'the iron hills', 'iron hills',
    
    # Wider geography
    'wilderland', 'the wild', 'the wild lands', 'the wilderness', 'the east',
    'gundabad', 'mount gundabad', 'gundabad mountain', 'the goblin mountain',
    'moria', 'khazad-dum', 'the black chasm', 'the black land',
    'the grey mountains', 'the withered heath',
    'the blue mountains', 'the ered luin', 'belegost', 'nogrod',
    'the northern wastes', 'the waste', 'the frozen north',
    'rhun', 'the east lands', 'the south', 'the far south',
    'the end of the world', 'the worlds end',
    'the dark land', 'the southern land',
    
    # Camps and battlefields
    'the camp', 'the camp of the men', 'the camp of the elves', 'the camp of the dwarves',
    'the siege', 'the siege works',
    'the battlefield', 'the plain', 'the valley', 'the slopes', 'the ridge',
    'the wall', 'the fortified wall', 'the wall of the mountain',
    'the front', 'the line', 'the vanguard', 'the rear guard',
}

# Place indicator words
PLACE_INDICATORS = [
    'town', 'ville', 'ton', 'ham', 'by', 'thorpe', 'wick', 'wich', 'stead', 'stede',
    'hill', 'mount', 'mountain', 'mont', 'berg', 'tor', 'fell', 'down', 'downs', 'moor', 'heath',
    'wood', 'woods', 'forest', 'weald', 'holt', 'shaw', 'thicket', 'grove', 'glen', 'dale', 'vale',
    'river', 'rill', 'brook', 'beck', 'burn', 'bourne', 'water', 'ford',
    'lake', 'loch', 'lough', 'mere', 'tarn', 'pool', 'pond', 'waters', 'sea', 'ocean',
    'cave', 'cavern', 'hole', 'hollow', 'pit', 'shaft', 'mine', 'tunnel', 'passage',
    'gate', 'door', 'portal', 'entry', 'entrance', 'way', 'path', 'road', 'track', 'trail',
    'hall', 'house', 'home', 'stead', 'hold', 'court', 'garth', 'yard', 'court', 'porch',
    'camp', 'clearing', 'mead', 'field', 'plain', 'heath', 'moor', 'waste', 'wild',
    'land', 'lands', 'realm', 'kingdom', 'domain', 'country', 'region', 'shire', 'province',
    'chamber', 'room', 'cellar', 'dungeon', 'crypt', 'tomb',
    'lair', 'den', 'nest', 'eyrie', 'aerie', 'roost',
    'wall', 'bridge', 'cross', 'crossing', 'pass', 'gap', 'notch', 'col',
    'rock', 'stone', 'cliff', 'crag', 'scar', 'edge', 'brink', 'rim', 'lip',
    'slope', 'side', 'face', 'flank', 'shoulder', 'brow', 'crest', 'ridge', 'spur',
    'tower', 'fort', 'fortress', 'castle', 'keep', 'stronghold', 'fastness',
]

# Character indicator words
CHARACTER_INDICATORS = [
    'king', 'queen', 'lord', 'lady', 'master', 'mistress', 'sir', 'madam', 'sire',
    'captain', 'chief', 'head', 'leader', 'prince', 'princess', 'steward', 'warden',
    'wizard', 'witch', 'mage', 'sorcerer', 'necromancer', 'enchanter', 'warlock',
    'elf', 'elves', 'elfin', 'dwarf', 'dwarves', 'goblin', 'goblins', 'orc', 'orcs',
    'troll', 'trolls', 'giant', 'giants', 'dragon', 'eagle', 'eagles', 'raven', 'ravens',
    'man', 'men', 'woman', 'women', 'child', 'children', 'folk', 'people',
    'rider', 'riders', 'warrior', 'warriors', 'guard', 'guards', 'sentry', 'sentries',
    'bowman', 'archer', 'spearman', 'swordsman', 'fighter', 'champion', 'hero', 'chieftain',
    'butler', 'servant', 'slave', 'prisoner', 'captive', 'hostage',
    'ferryman', 'boatman', 'sailor', 'mariner', 'captain', 'boatsman',
    'father', 'mother', 'brother', 'sister', 'son', 'daughter', 'uncle', 'aunt', 'cousin',
    'friend', 'foe', 'enemy', 'ally', 'companion', 'comrade', 'fellow', 'neighbor',
    'skin-changer', 'skin-changers', 'werebear', 'beorning',
    'spider', 'spiders', 'wolf', 'wolves', 'wargs', 'warg', 'were-wolf',
    'thrush', 'thrushes', 'bird', 'birds', 'fowl', 'beast', 'beasts', 'creature', 'creatures',
]

def is_likely_name(phrase, count):
    """Filter out non-names."""
    phrase = phrase.strip()
    phrase_lower = phrase.lower()
    
    # Must have at least 2 mentions
    if count < 2:
        return False
    
    # Exclude common words
    if phrase_lower in COMMON_WORDS:
        return False
    
    # Exclude standalone articles/prepositions
    if phrase_lower in ('the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'from', 'by', 'with'):
        return False
    
    # Exclude very short unless known
    known_short = {'ui', 'ma', 'azog'}
    if len(phrase) < 3 and phrase_lower not in known_short:
        return False
    
    # Exclude roman numerals
    if re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', phrase, re.I):
        return False
    
    # Exclude date/month words
    if phrase_lower in ('january', 'february', 'march', 'april', 'may', 'june', 
                        'july', 'august', 'september', 'october', 'november', 'december',
                        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
        return False
    
    return True

def classify_entity(phrase, contexts):
    """Classify as character, place, or unknown."""
    phrase_lower = phrase.lower().strip()
    
    # Direct matches
    if phrase_lower in KNOWN_CHARACTERS:
        return 'character'
    if phrase_lower in KNOWN_PLACES:
        return 'place'
    
    # Check for place suffixes
    for suffix in PLACE_INDICATORS:
        if phrase_lower.endswith(' ' + suffix) or phrase_lower == suffix:
            return 'place'
    
    # Check for character indicators
    for indicator in CHARACTER_INDICATORS:
        if indicator in phrase_lower:
            # Must be a title pattern like "the king" or "king something"
            if re.search(r'\bthe\s+' + indicator + r'\b', phrase_lower):
                return 'character'
            if re.search(r'\b' + indicator + r'\s+[A-Z]', phrase, re.I):
                return 'character'
    
    # Context-based classification
    char_clues = 0
    place_clues = 0
    
    for ctx in contexts[:5]:
        ctx_lower = ctx.lower()
        
        # Character action clues
        if re.search(r'\b' + re.escape(phrase_lower) + r'\s+(said|asked|answered|replied|cried|thought|felt|went|came)', ctx_lower):
            char_clues += 1
        
        # Place preposition clues
        if re.search(r'\b(in|at|to|from|through|over|under|near|towards|upon)\s+(the\s+)?' + re.escape(phrase_lower) + r'\b', ctx_lower):
            place_clues += 1
    
    if char_clues > place_clues:
        return 'character'
    elif place_clues > char_clues:
        return 'place'
    
    return 'unknown'

def clean_entity_name(phrase):
    """Clean up entity name - fix spacing, normalize case."""
    # Fix multiple spaces
    phrase = re.sub(r'\s+', ' ', phrase).strip()
    # Normalize "The/A/An" to lowercase unless it's part of a name
    phrase = re.sub(r'^(The|the|A|a|An|an)\s+', lambda m: m.group(1).lower() + ' ', phrase)
    return phrase

def extract_entities():
    """Main extraction function."""
    print("Loading narrative data...")
    entries = load_narrative_data()
    
    print("Extracting entities...")
    all_entities = []
    entity_contexts = defaultdict(list)
    
    for entry in entries:
        content = entry['content']
        entities = extract_entities_from_text(content)
        
        for entity, context in entities:
            entity = clean_entity_name(entity)
            all_entities.append(entity)
            if len(entity_contexts[entity]) < 5:
                entity_contexts[entity].append(context)
    
    entity_counts = Counter(all_entities)
    print(f"Found {len(entity_counts)} unique entities")
    
    # Filter
    print("Filtering...")
    valid_entities = {}
    for entity, count in entity_counts.items():
        if is_likely_name(entity, count):
            valid_entities[entity] = {
                'count': count,
                'contexts': entity_contexts[entity]
            }
    print(f"Found {len(valid_entities)} valid entities")
    
    # Classify
    print("Classifying...")
    characters = {}
    places = {}
    unknown = {}
    objects = {}  # For things like Arkenstone
    
    for entity, info in valid_entities.items():
        classification = classify_entity(entity, info['contexts'])
        
        # Special case: Arkenstone is an object, not a place
        if 'arkenstone' in entity.lower():
            objects[entity] = {
                'name': entity,
                'mentions': info['count'],
                'contexts': info['contexts'][:3]
            }
            continue
        
        data = {
            'name': entity,
            'mentions': info['count'],
            'contexts': info['contexts'][:3]
        }
        
        if classification == 'character':
            characters[entity] = data
        elif classification == 'place':
            places[entity] = data
        else:
            unknown[entity] = data
    
    print(f"Classified: {len(characters)} characters, {len(places)} places, {len(objects)} objects, {len(unknown)} unknown")
    
    # Sort
    chars_sorted = dict(sorted(characters.items(), key=lambda x: x[1]['mentions'], reverse=True))
    places_sorted = dict(sorted(places.items(), key=lambda x: x[1]['mentions'], reverse=True))
    objects_sorted = dict(sorted(objects.items(), key=lambda x: x[1]['mentions'], reverse=True))
    unknown_sorted = dict(sorted(unknown.items(), key=lambda x: x[1]['mentions'], reverse=True))
    
    # Save JSON
    for fname, data in [
        ('../data/hobbit_characters.json', {'count': len(chars_sorted), 'characters': chars_sorted}),
        ('../data/hobbit_places.json', {'count': len(places_sorted), 'places': places_sorted}),
        ('hobbit_objects.json', {'count': len(objects_sorted), 'objects': objects_sorted}),
        ('../data/hobbit_entities_unknown.json', {'count': len(unknown_sorted), 'entities': unknown_sorted}),
    ]:
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Create markdown files
    with open('hobbit_characters.txt', 'w', encoding='utf-8') as f:
        f.write("# Characters in The Hobbit\n\n")
        f.write(f"Total: {len(chars_sorted)} characters\n\n")
        for i, (name, info) in enumerate(chars_sorted.items(), 1):
            f.write(f"{i:3d}. **{name}** ({info['mentions']} mentions)\n")
            if info['contexts']:
                ctx = info['contexts'][0][:100]
                f.write(f"     > \"{ctx}...\"\n")
        f.write("\n")
    
    with open('hobbit_places.txt', 'w', encoding='utf-8') as f:
        f.write("# Places in The Hobbit\n\n")
        f.write(f"Total: {len(places_sorted)} places\n\n")
        for i, (name, info) in enumerate(places_sorted.items(), 1):
            f.write(f"{i:3d}. **{name}** ({info['mentions']} mentions)\n")
            if info['contexts']:
                ctx = info['contexts'][0][:100]
                f.write(f"     > \"{ctx}...\"\n")
        f.write("\n")
    
    # Print summary
    print("\n" + "="*60)
    print("TOP 20 CHARACTERS")
    print("="*60)
    for i, (name, info) in enumerate(list(chars_sorted.items())[:20], 1):
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    print("\n" + "="*60)
    print("TOP 20 PLACES")
    print("="*60)
    for i, (name, info) in enumerate(list(places_sorted.items())[:20], 1):
        print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    if objects_sorted:
        print("\n" + "="*60)
        print("OBJECTS")
        print("="*60)
        for name, info in objects_sorted.items():
            print(f"    {name:<30} ({info['mentions']} mentions)")
    
    if unknown_sorted:
        print("\n" + "="*60)
        print("UNKNOWN (Top 10)")
        print("="*60)
        for i, (name, info) in enumerate(list(unknown_sorted.items())[:10], 1):
            print(f"{i:2d}. {name:<30} ({info['mentions']} mentions)")
    
    print("\n✅ Created files:")
    print("  - hobbit_characters.json")
    print("  - hobbit_places.json")
    print("  - hobbit_characters.txt")
    print("  - hobbit_places.txt")
    print("  - hobbit_objects.json")
    print("  - hobbit_entities_unknown.json")

if __name__ == '__main__':
    extract_entities()
