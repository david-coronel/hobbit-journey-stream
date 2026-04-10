#!/usr/bin/env python3
"""
Extract ALL text from The Hobbit and assign it to specific scenes.
Every paragraph of the book will be assigned to a scene.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Scene:
    chapter: str
    scene_number: int
    title: str
    text: str
    start_para: int
    end_para: int
    word_count: int
    location_hint: str = ""
    time_hint: str = ""


def load_epub(filepath: str) -> str:
    """Load and extract text from EPUB."""
    book = epub.read_epub(filepath)
    
    all_docs = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT and item.get_name().endswith('.htm'):
            content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            all_docs.append(text)
    
    return '\n'.join(all_docs)


def split_into_chapters(full_text: str) -> List[dict]:
    """Split full text into chapters."""
    chapter_titles = [
        'An Unexpected Party', 'Roast Mutton', 'A Short Rest', 
        'Over Hill and Under Hill', 'Riddles in the Dark',
        'Out of the Frying-Pan into the Fire', 'Queer Lodgings',
        'Flies and Spiders', 'Barrels Out of Bond', 'A Warm Welcome',
        'On the Doorstep', 'Inside Information', 'Not at Home',
        'Fire and Water', 'The Gathering of the Clouds',
        'A Thief in the Night', 'The Clouds Burst',
        'The Return Journey', 'The Last Stage'
    ]
    
    chapters = []
    for i, title in enumerate(chapter_titles):
        start = full_text.find(title)
        if start == -1:
            print(f"Warning: Could not find chapter '{title}'")
            continue
        
        # Find end (next chapter or end of text)
        if i + 1 < len(chapter_titles):
            end = full_text.find(chapter_titles[i + 1], start + 1)
        else:
            end = len(full_text)
        
        chapter_text = full_text[start:end].strip()
        chapters.append({
            'title': title,
            'text': chapter_text,
            'number': i + 1
        })
    
    return chapters


def split_chapter_into_paragraphs(chapter_text: str) -> List[str]:
    """Split chapter text into paragraphs."""
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', chapter_text)
    
    # Split by sentence-ending punctuation followed by space and capital letter
    # This preserves dialogue and narrative flow
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"])', text)
    
    # Group sentences into paragraphs (narrative units)
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Check if this starts a new paragraph (scene/location/time change)
        new_para_starters = [
            'When ', 'After ', 'Soon ', 'Later ', 'That ', 'The next', 'Next ',
            'At last', 'Meanwhile', 'By this', 'In the ', 'On the ', 'At the',
            'Morning ', 'Evening ', 'Night ', 'Day ', 'It was ', 'There ',
            'They ', 'He ', 'She ', 'Bilbo ', 'Thorin ', 'Gandalf ', 'But ',
            'And so', 'So ', 'Now ', 'Then '
        ]
        
        is_new_para = any(sentence.startswith(starter) for starter in new_para_starters)
        is_short = len(sentence) < 100
        
        # Also start new para if current is getting long
        current_length = sum(len(s) for s in current_para)
        
        if (is_new_para or current_length > 800) and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = [sentence]
        else:
            current_para.append(sentence)
    
    # Don't forget the last paragraph
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    # Filter out very short fragments and chapter headers
    filtered = []
    for para in paragraphs:
        para = para.strip()
        # Skip chapter title and very short fragments
        if len(para) > 50 and not any(para.startswith(title) for title in [
            'An Unexpected Party', 'Roast Mutton', 'A Short Rest'
        ]):
            filtered.append(para)
    
    return filtered


def identify_scene_boundaries(paragraphs: List[str], chapter_title: str) -> List[tuple]:
    """Identify where scenes start and end within chapter paragraphs."""
    
    # Scene definitions for each chapter with key phrases that mark scene starts
    scene_markers = {
        'An Unexpected Party': [
            ("In a hole in the ground", "The Unexpected Party Begins"),
            ("The door opened on to a tube-shaped hall", "Gandalf's Arrival"),
            ("Poor Bilbo couldn't believe it", "Thorin Arrives"),
            ("Then the bell rang again", "The Dwarves Arrive"),
            ("Far over the misty mountains cold", "The Feast and Song"),
            ("They talked for a long while", "The Contract and Morning After"),
            ("To the end of his days", "Bilbo Decides to Go")
        ],
        'Roast Mutton': [
            ("They were on the edge of the uplands", "Camping in the Trollshaws"),
            ("Bilbo never forgot the way he slunk to the ground", "Bilbo Tries to Pick a Pocket"),
            ("William never spoke for he stood turned to stone", "The Trolls' Argument"),
            ("It was just then that Gandalf came back", "Gandalf's Rescue")
        ],
        'A Short Rest': [
            ("The next day the travellers", "Journey to Rivendell"),
            ("The horses of Rivendell", "Welcome at Rivendell"),
            ("Elrond knew all about runes", "Elrond Examines the Swords and Map")
        ],
        'Over Hill and Under Hill': [
            ("There were many paths", "Climbing the Misty Mountains"),
            ("It was much larger", "Sheltering in the Cave"),
            ("The ponies were already there", "Captured by Goblins"),
            ("The Great Goblin gave a truly awful howl", "The Great Goblin's Interrogation"),
            ("All was well until one day they met a thunderstorm", "Gandalf Rescues Them")
        ],
        'Riddles in the Dark': [
            ("Deep down here by the dark water", "Bilbo Wakes Up Alone"),
            ("What has roots", "Finding the Ring and Meeting Gollum"),
            ("It couldn't be the last", "The Riddle Game"),
            ("Bilbo stood still a moment", "Escaping the Goblins")
        ],
        'Out of the Frying-Pan into the Fire': [
            ("Just at that moment the wolves trotted howling", "Hearing the Wargs"),
            ("The Wargs and the goblins often helped one another", "Trapped in the Trees"),
            ("The Lord of the Eagles of the Misty Mountains", "The Lord of the Eagles"),
            ("The eagle came again", "Rescued by the Eagles"),
            ("There stood a lone sentinel", "The Carrock")
        ],
        'Queer Lodgings': [
            ("They did not sing or tell stories that day", "Approaching Beorn's House"),
            ("There were horses", "Meeting Beorn"),
            ("At last Gandalf pushed away his plate", "Night at Beorn's"),
            ("The next morning they were wakened", "The Next Morning"),
            ("Beorn indeed became a great chief afterwards", "Beorn's Stories"),
            ("Mirkwood is a dangerous place", "Into Mirkwood")
        ],
        'Flies and Spiders': [
            ("It was dark and damp", "The Path Through Mirkwood"),
            ("They walked in a file", "Seeing the Lights"),
            ("The stream was right there", "Bombur Falls in the River"),
            ("Poor Bombur was heavy to carry", "Bombur's Dream"),
            ("They walked slowly and carefully", "Bilbo Climbs the Tree"),
            ("It was only a spider", "The Spiders Capture the Dwarves"),
            ("Quickly Bilbo slipped on his ring", "Bilbo Saves the Dwarves"),
            ("They had escaped the dungeons", "Escaping the Spiders"),
            ("Yes, yes!", "Captured by the Wood-elves")
        ],
        'Barrels Out of Bond': [
            ("The other Dwarves quite agreed", "Imprisoned in the Elvenking's Halls"),
            ("In another hall came Bilbo", "Bilbo Finds the Dwarves"),
            ("Bilbo wore his ring as usual", "The Escape Plan"),
            ("Quickly for last time they got the barrels ready", "Packing in Barrels"),
            ("Down the swift dark stream", "Floating Down the River"),
            ("There was a small town of Men", "Arrival at Lake-town")
        ],
        'A Warm Welcome': [
            ("They passed through a wood", "Welcome at Lake-town"),
            ("The Master was an able man", "The Master's Feast"),
            ("So one day", "Preparations for the Mountain")
        ],
        'On the Doorstep': [
            ("At the end of the third day", "The Desolation of Smaug"),
            ("Now they had to camp right out", "Camping on the Doorstep"),
            ("The sun had gone", "Searching for the Door"),
            ("Then Thorin stepped up", "The Thrush and the Keyhole"),
            ("Now the days passed slowly", "The Door Opens")
        ],
        'Inside Information': [
            ("Bilbo now found himself", "Bilbo Enters the Mountain"),
            ("Before he could do anything", "First Conversation with Smaug"),
            ("To say that Bilbo's breath was taken away", "The Theft of the Cup"),
            ("Bilbo had escaped the dragon's lair", "Second Conversation with Smaug"),
            ("My armour is like tenfold shields", "Smaug Suspects Lake-town"),
            ("And passing on and on", "Bilbo Learns of the Weak Spot")
        ],
        'Not at Home': [
            ("Now the days went on", "Smaug Attacks Lake-town"),
            ("The dragon was circling above", "The Dwarves Explore"),
            ("As a boy he used to wander", "Finding the Arkenstone"),
            ("It was on this errand", "Bilbo Takes the Arkenstone"),
            ("Suddenly a great light appeared", "Smaug's Death")
        ],
        'Fire and Water': [
            ("If you have never seen a dragon", "Smaug Attacks Lake-town"),
            ("Amid shrieks and wailing", "Bard Learns of the Weak Spot"),
            ("There was once a king", "The Black Arrow"),
            ("Then Bard drew his bow-string", "Smaug is Killed")
        ],
        'The Gathering of the Clouds': [
            ("Birds had begun to gather", "Birds Bring News"),
            ("Now Roac the raven", "Roac the Raven's Counsel"),
            ("They buried Thorin deep", "Thorin Fortifies the Mountain"),
            ("The Elvenking had received news", "Armies Approach"),
            ("The Elvenking had his host", "The Siege Begins")
        ],
        'A Thief in the Night': [
            ("As you have heard", "Bilbo Takes the Arkenstone to Bard"),
            ("Roaring he swept back", "Negotiations with Thorin"),
            ("It was not long before they heard", "Dain's Army Arrives"),
            ("The autumn sun shone upon the hill", "Battle of Five Armies Begins")
        ],
        'The Clouds Burst': [
            ("The Mountain trembled", "The Battle Rages"),
            ("The clouds burst", "The Eagles Arrive"),
            ("But even with the Eagles", "Beorn Arrives"),
            ("Victory had been assured", "Victory and Thorin's Death"),
            ("There is a sweet music", "Bilbo's Farewell to Thorin"),
            ("So ended the battle", "The Aftermath")
        ],
        'The Return Journey': [
            ("After the battle", "Dain Becomes King"),
            ("Then Bilbo farewell to the dwarves", "Bilbo Leaves"),
            ("So they went back to the Beorn's house", "Staying with Beorn Again"),
            ("It was on May the First", "Rivendell - The White Horses"),
            ("There is a land", "The Final Parting")
        ],
        'The Last Stage': [
            ("The journey home was uneventful", "Journey Back to the Shire"),
            ("Bag End itself was not unoccupied", "The Auction at Bag End"),
            ("And in the meanwhile", "Bilbo Returns Home")
        ]
    }
    
    markers = scene_markers.get(chapter_title, [])
    scenes = []
    
    if not markers:
        # No markers defined, treat as one scene
        return [(0, len(paragraphs), "Scene 1")]
    
    # Find paragraph indices for each marker
    scene_indices = []
    for marker, title in markers:
        for i, para in enumerate(paragraphs):
            if marker.lower() in para.lower()[:200]:  # Check beginning of paragraph
                scene_indices.append((i, title, marker))
                break
    
    # Sort by paragraph index
    scene_indices.sort(key=lambda x: x[0])
    
    # Create scene ranges
    for i, (start_idx, title, marker) in enumerate(scene_indices):
        if i + 1 < len(scene_indices):
            end_idx = scene_indices[i + 1][0]
        else:
            end_idx = len(paragraphs)
        scenes.append((start_idx, end_idx, title))
    
    # If first scene doesn't start at 0, add preamble
    if scenes and scenes[0][0] > 0:
        scenes.insert(0, (0, scenes[0][0], "Opening"))
    
    return scenes if scenes else [(0, len(paragraphs), "Full Chapter")]


def extract_scenes(chapter: dict) -> List[Scene]:
    """Extract all scenes from a chapter with their full text."""
    paragraphs = split_chapter_into_paragraphs(chapter['text'])
    boundaries = identify_scene_boundaries(paragraphs, chapter['title'])
    
    scenes = []
    for scene_num, (start, end, title) in enumerate(boundaries, 1):
        scene_paras = paragraphs[start:end]
        scene_text = '\n\n'.join(scene_paras)
        
        # Extract location/time hints from first paragraph
        location_hint = ""
        time_hint = ""
        if scene_paras:
            first = scene_paras[0].lower()
            location_words = ['shire', 'hobbiton', 'bag end', 'rivendell', 'mountain', 
                            'cave', 'forest', 'mirkwood', 'lake', 'town', 'erebor',
                            'beorn', 'house', 'hall', 'gate', 'door', 'road', 'path']
            for word in location_words:
                if word in first[:200]:
                    location_hint = word
                    break
            
            time_words = ['morning', 'evening', 'night', 'day', 'dawn', 'dusk', 'afternoon']
            for word in time_words:
                if word in first[:200]:
                    time_hint = word
                    break
        
        scenes.append(Scene(
            chapter=chapter['title'],
            scene_number=scene_num,
            title=title,
            text=scene_text,
            start_para=start,
            end_para=end,
            word_count=len(scene_text.split()),
            location_hint=location_hint,
            time_hint=time_hint
        ))
    
    return scenes


def main():
    print("Loading EPUB...")
    full_text = load_epub('The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub')
    print(f"Total text length: {len(full_text):,} characters")
    
    print("\nSplitting into chapters...")
    chapters = split_into_chapters(full_text)
    print(f"Found {len(chapters)} chapters")
    
    all_scenes = []
    total_words = 0
    
    for ch in chapters:
        print(f"\nProcessing: {ch['title']}...")
        scenes = extract_scenes(ch)
        
        ch_word_count = sum(s.word_count for s in scenes)
        total_words += ch_word_count
        
        print(f"  Split into {len(scenes)} scenes ({ch_word_count:,} words)")
        for s in scenes:
            print(f"    Scene {s.scene_number}: {s.title} ({s.word_count:,} words)")
        
        all_scenes.extend(scenes)
    
    # Convert to JSON-serializable format
    output = {
        'metadata': {
            'book': 'The Hobbit; Or There and Back Again',
            'author': 'J.R.R. Tolkien',
            'total_chapters': len(chapters),
            'total_scenes': len(all_scenes),
            'total_words': total_words,
            'extraction_date': '2024'
        },
        'scenes': [asdict(s) for s in all_scenes]
    }
    
    # Save to JSON
    output_file = 'hobbit_all_scenes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total chapters: {len(chapters)}")
    print(f"Total scenes: {len(all_scenes)}")
    print(f"Total words: {total_words:,}")
    print(f"Output file: {output_file}")
    
    # Also create a summary
    print(f"\n{'='*60}")
    print("SCENE SUMMARY BY CHAPTER")
    print(f"{'='*60}")
    
    current_chapter = None
    for scene in all_scenes:
        if scene.chapter != current_chapter:
            current_chapter = scene.chapter
            print(f"\n{current_chapter}:")
        print(f"  {scene.scene_number}. {scene.title} ({scene.word_count:,} words)")


if __name__ == "__main__":
    main()
