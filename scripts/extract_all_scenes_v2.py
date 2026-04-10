#!/usr/bin/env python3
"""
Extract ALL text from The Hobbit and assign it to specific scenes.
Parse the actual EPUB HTML structure.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Tuple


@dataclass
class Scene:
    chapter: str
    scene_number: int
    title: str
    text: str
    paragraphs: List[str]
    word_count: int
    char_count: int


def get_all_paragraphs_from_epub(filepath: str) -> List[Tuple[str, str]]:
    """Extract all paragraphs from EPUB with their document source."""
    book = epub.read_epub(filepath)
    
    all_paras = []
    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        
        content = item.get_content().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style
        for tag in soup(['script', 'style', 'nav']):
            tag.decompose()
        
        # Find all paragraph elements
        for p in soup.find_all(['p', 'div']):
            text = p.get_text(strip=True)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 20:  # Skip very short lines
                all_paras.append((item.get_name(), text))
    
    return all_paras


def identify_chapters(paragraphs: List[Tuple[str, str]]) -> List[dict]:
    """Identify chapter boundaries in paragraph list."""
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
    current_chapter = None
    current_paras = []
    ch_num = 0
    
    for doc_name, para in paragraphs:
        # Check if this paragraph starts a chapter
        for title in chapter_titles:
            if para.startswith(title) or para.startswith(f"Chapter") and title in para[:50]:
                # Save previous chapter
                if current_chapter and current_paras:
                    chapters.append({
                        'title': current_chapter,
                        'number': ch_num,
                        'paragraphs': current_paras
                    })
                
                ch_num += 1
                current_chapter = title
                current_paras = []
                break
        
        if current_chapter:
            current_paras.append(para)
    
    # Don't forget last chapter
    if current_chapter and current_paras:
        chapters.append({
            'title': current_chapter,
            'number': ch_num,
            'paragraphs': current_paras
        })
    
    return chapters


def split_into_scenes(chapter: dict) -> List[Scene]:
    """Split chapter paragraphs into scenes."""
    title = chapter['title']
    paras = chapter['paragraphs']
    
    # Scene definitions with detailed paragraph ranges
    # Based on narrative structure analysis
    scene_definitions = {
        'An Unexpected Party': [
            ("The Unexpected Party", 0, 30),
            ("Gandalf's Visit", 30, 60),
            ("Thorin Arrives", 60, 90),
            ("The Dwarves Gather", 90, 130),
            ("The Feast and Song", 130, 170),
            ("Planning the Quest", 170, 210),
            ("Bilbo Joins", 210, None)
        ],
        'Roast Mutton': [
            ("Camping in the Trollshaws", 0, 50),
            ("Bilbo Tries to Steal", 50, 80),
            ("Captured by Trolls", 80, 110),
            ("Thorin's Arrival", 110, 130),
            ("Gandalf's Rescue", 130, None)
        ],
        'A Short Rest': [
            ("Journey to Rivendell", 0, 30),
            ("The Last Homely House", 30, 60),
            ("Elrond's Counsel", 60, None)
        ],
        'Over Hill and Under Hill': [
            ("Climbing the Mountains", 0, 30),
            ("The Storm and Cave", 30, 60),
            ("Captured by Goblins", 60, 90),
            ("The Great Goblin", 90, 120),
            ("Gandalf Rescues", 120, None)
        ],
        'Riddles in the Dark': [
            ("Bilbo Wakes Alone", 0, 20),
            ("Finding the Ring", 20, 50),
            ("Meeting Gollum", 50, 90),
            ("The Riddle Game", 90, 150),
            ("Escaping", 150, None)
        ],
        'Out of the Frying-Pan into the Fire': [
            ("Reunion and Journey", 0, 30),
            ("The Wargs Attack", 30, 60),
            ("Trapped in Trees", 60, 100),
            ("The Eagles", 100, 130),
            ("Rescue", 130, None)
        ],
        'Queer Lodgings': [
            ("Approaching Beorn's", 0, 30),
            ("Meeting Beorn", 30, 70),
            ("The Night", 70, 100),
            ("Stories and Provisions", 100, 140),
            ("Into Mirkwood", 140, None)
        ],
        'Flies and Spiders': [
            ("Entering Mirkwood", 0, 30),
            ("The Enchanted Lights", 30, 60),
            ("Bombur's Fall", 60, 90),
            ("The Dream", 90, 120),
            ("Starlight and Black Butterflies", 120, 150),
            ("Spiders Attack", 150, 190),
            ("Bilbo Rescues the Dwarves", 190, 230),
            ("Captured by Elves", 230, None)
        ],
        'Barrels Out of Bond': [
            ("Prisoner of the Elves", 0, 30),
            ("Bilbo Finds the Dwarves", 30, 60),
            ("The Escape Plan", 60, 90),
            ("The Water Gate", 90, 130),
            ("Floating Downriver", 130, 170),
            ("Lake-town", 170, None)
        ],
        'A Warm Welcome': [
            ("Arrival at Lake-town", 0, 30),
            ("The Master's Feast", 30, 60),
            ("Departure for the Mountain", 60, None)
        ],
        'On the Doorstep': [
            ("The Desolation of Smaug", 0, 20),
            ("Camping on the Mountain", 20, 50),
            ("Searching for the Door", 50, 80),
            ("The Thrush", 80, 100),
            ("The Secret Door Opens", 100, None)
        ],
        'Inside Information': [
            ("Entering Erebor", 0, 25),
            ("Meeting Smaug", 25, 60),
            ("The Cup Theft", 60, 90),
            ("Conversation with Smaug", 90, 130),
            ("Smaug's Suspicion", 130, 160),
            ("The Weak Spot", 160, None)
        ],
        'Not at Home': [
            ("Smaug Attacks Lake-town", 0, 30),
            ("Exploring the Mountain", 30, 60),
            ("Finding the Arkenstone", 60, 90),
            ("Bilbo Takes the Stone", 90, 110),
            ("Smaug's Death", 110, None)
        ],
        'Fire and Water': [
            ("The Dragon's Attack", 0, 25),
            ("The Black Arrow", 25, 50),
            ("Bard's Shot", 50, 70),
            ("Smaug Falls", 70, None)
        ],
        'The Gathering of the Clouds': [
            ("News of Smaug's Death", 0, 25),
            ("Roac the Raven", 25, 50),
            ("Thorin's Pride", 50, 75),
            ("Armies Gather", 75, 100),
            ("The Siege Begins", 100, None)
        ],
        'A Thief in the Night': [
            ("Bilbo's Burden", 0, 25),
            ("Taking the Arkenstone", 25, 50),
            ("Parley with Bard", 50, 80),
            ("Dain Arrives", 80, None)
        ],
        'The Clouds Burst': [
            ("Battle Joined", 0, 25),
            ("The Eagles Come", 25, 50),
            ("Beorn's Arrival", 50, 70),
            ("Victory", 70, 100),
            ("Thorin's Death", 100, 130),
            ("Farewell", 130, None)
        ],
        'The Return Journey': [
            ("Dain King Under the Mountain", 0, 20),
            ("Leaving Erebor", 20, 50),
            ("Beorn's Hospitality", 50, 70),
            ("Rivendell Again", 70, 90),
            ("Homeward Bound", 90, None)
        ],
        'The Last Stage': [
            ("The Road Home", 0, 20),
            ("The Auction", 20, 45),
            ("Home at Last", 45, None)
        ]
    }
    
    scenes = []
    definitions = scene_definitions.get(title, [(f"Scene {i+1}", i*20, (i+1)*20) for i in range(len(paras)//20 + 1)])
    
    for i, (scene_title, start, end) in enumerate(definitions, 1):
        if end is None:
            end = len(paras)
        
        scene_paras = paras[start:end]
        scene_text = '\n\n'.join(scene_paras)
        
        scenes.append(Scene(
            chapter=title,
            scene_number=i,
            title=scene_title,
            text=scene_text,
            paragraphs=scene_paras,
            word_count=len(scene_text.split()),
            char_count=len(scene_text)
        ))
    
    return scenes


def main():
    print("Extracting all paragraphs from EPUB...")
    all_paras = get_all_paragraphs_from_epub(
        'The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub'
    )
    print(f"Found {len(all_paras)} paragraphs")
    
    print("\nIdentifying chapters...")
    chapters = identify_chapters(all_paras)
    print(f"Found {len(chapters)} chapters")
    
    all_scenes = []
    total_words = 0
    total_chars = 0
    
    for ch in chapters:
        print(f"\nProcessing: {ch['title']} ({len(ch['paragraphs'])} paragraphs)")
        scenes = split_into_scenes(ch)
        
        ch_words = sum(s.word_count for s in scenes)
        ch_chars = sum(s.char_count for s in scenes)
        total_words += ch_words
        total_chars += ch_chars
        
        print(f"  Split into {len(scenes)} scenes ({ch_words:,} words)")
        for s in scenes:
            print(f"    {s.scene_number}. {s.title} ({s.word_count:,} words, {len(s.paragraphs)} paras)")
        
        all_scenes.extend(scenes)
    
    # Create output with full text
    output = {
        'metadata': {
            'book': 'The Hobbit; Or There and Back Again',
            'author': 'J.R.R. Tolkien',
            'total_chapters': len(chapters),
            'total_scenes': len(all_scenes),
            'total_words': total_words,
            'total_characters': total_chars,
            'extraction_method': 'EPUB paragraph-based with manual scene boundaries'
        },
        'scenes': [
            {
                'id': f"{s.chapter.lower().replace(' ', '_')}_scene_{s.scene_number}",
                'chapter': s.chapter,
                'scene_number': s.scene_number,
                'title': s.title,
                'text': s.text,
                'paragraph_count': len(s.paragraphs),
                'word_count': s.word_count,
                'char_count': s.char_count
            }
            for s in all_scenes
        ]
    }
    
    # Save full version with text
    with open('hobbit_all_scenes_full.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Save version without text (just metadata)
    output_no_text = {
        'metadata': output['metadata'],
        'scenes': [
            {k: v for k, v in s.items() if k != 'text'}
            for s in output['scenes']
        ]
    }
    
    with open('hobbit_all_scenes_index.json', 'w', encoding='utf-8') as f:
        json.dump(output_no_text, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total chapters: {len(chapters)}")
    print(f"Total scenes: {len(all_scenes)}")
    print(f"Total words: {total_words:,}")
    print(f"Total characters: {total_chars:,}")
    print(f"\nOutput files:")
    print(f"  - hobbit_all_scenes_full.json (with full text)")
    print(f"  - hobbit_all_scenes_index.json (metadata only)")
    
    # Sample scene text
    print(f"\n{'='*70}")
    print("SAMPLE: First scene text (first 500 chars)")
    print(f"{'='*70}")
    first_scene = all_scenes[0]
    print(f"Chapter: {first_scene.chapter}")
    print(f"Scene: {first_scene.title}")
    print(f"\n{first_scene.text[:500]}...")


if __name__ == "__main__":
    main()
