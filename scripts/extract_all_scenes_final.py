#!/usr/bin/env python3
"""
Extract ALL text from The Hobbit and assign it to specific scenes.
Final version - handles Chapter I/1/2 format properly.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass
from typing import List


@dataclass 
class Scene:
    chapter: str
    scene_number: int
    title: str
    text: str
    word_count: int


def extract_full_text_from_epub(filepath: str) -> str:
    """Extract all text content from EPUB."""
    book = epub.read_epub(filepath)
    
    all_texts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT and item.get_name().endswith('.htm'):
            content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav']):
                tag.decompose()
            
            text = soup.get_text()
            all_texts.append(text)
    
    return '\n'.join(all_texts)


def split_into_chapters(full_text: str) -> List[dict]:
    """Split full text into chapters."""
    chapter_titles = [
        ('Chapter I', 'An Unexpected Party'),
        ('Chapter 2', 'Roast Mutton'),
        ('Chapter 3', 'A Short Rest'),
        ('Chapter 4', 'Over Hill and Under Hill'),
        ('Chapter 5', 'Riddles in the Dark'),
        ('Chapter 6', 'Out of the Frying-Pan into the Fire'),
        ('Chapter 7', 'Queer Lodgings'),
        ('Chapter 8', 'Flies and Spiders'),
        ('Chapter 9', 'Barrels Out of Bond'),
        ('Chapter 10', 'A Warm Welcome'),
        ('Chapter 11', 'On the Doorstep'),
        ('Chapter 12', 'Inside Information'),
        ('Chapter 13', 'Not at Home'),
        ('Chapter 14', 'Fire and Water'),
        ('Chapter 15', 'The Gathering of the Clouds'),
        ('Chapter 16', 'A Thief in the Night'),
        ('Chapter 17', 'The Clouds Burst'),
        ('Chapter 18', 'The Return Journey'),
        ('Chapter 19', 'The Last Stage'),
    ]
    
    chapters = []
    
    for i, (chapter_marker, title) in enumerate(chapter_titles):
        start = full_text.find(chapter_marker)
        if start == -1:
            # Try alternate formats
            alt_marker = chapter_marker.replace('Chapter I', 'Chapter 1')
            start = full_text.find(alt_marker)
        
        if start == -1:
            print(f"Warning: Could not find {chapter_marker}")
            continue
        
        # Find end (next chapter or end of text)
        if i + 1 < len(chapter_titles):
            next_marker = chapter_titles[i + 1][0]
            end = full_text.find(next_marker, start + 1)
            if end == -1:
                end = len(full_text)
        else:
            end = len(full_text)
        
        chapter_text = full_text[start:end].strip()
        chapters.append({
            'title': title,
            'number': i + 1,
            'text': chapter_text
        })
    
    return chapters


def split_text_into_paragraphs(text: str) -> List[str]:
    """Split chapter text into paragraphs."""
    # Remove chapter header line
    lines = text.split('\n')
    content_lines = []
    header_found = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip chapter header lines
        if 'Chapter' in line and not header_found:
            header_found = True
            continue
        if line in ['An Unexpected Party', 'Roast Mutton', 'A Short Rest',
                   'Over Hill and Under Hill', 'Riddles in the Dark',
                   'Out of the Frying-Pan into the Fire', 'Queer Lodgings',
                   'Flies and Spiders', 'Barrels Out of Bond', 'A Warm Welcome',
                   'On the Doorstep', 'Inside Information', 'Not at Home',
                   'Fire and Water', 'The Gathering of the Clouds',
                   'A Thief in the Night', 'The Clouds Burst',
                   'The Return Journey', 'The Last Stage']:
            continue
        
        # Skip page numbers (standalone numbers)
        if re.match(r'^\d+$', line):
            continue
        
        content_lines.append(line)
    
    # Join and split by sentence endings
    content = ' '.join(content_lines)
    content = re.sub(r'\s+', ' ', content)
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', content)
    
    # Group into paragraphs
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        
        # New paragraph indicators
        new_para_starters = [
            'When ', 'After ', 'Soon ', 'Later ', 'That ', 'The next', 'Next ',
            'At last', 'Meanwhile', 'By this', 'In the ', 'On the ', 'At the',
            'Morning ', 'Evening ', 'Night ', 'Day ', 'It was ', 'There ',
            'They ', 'He ', 'She ', 'Bilbo ', 'Thorin ', 'Gandalf ', 'But ',
            'And so', 'So ', 'Now ', 'Then ', 'Suddenly ', 'All of a sudden',
            'However ', 'Nevertheless ', 'The ', 'At '
        ]
        
        is_new_para = any(sentence.startswith(starter) for starter in new_para_starters)
        current_length = sum(len(s) for s in current_para)
        
        if (is_new_para or current_length > 1500) and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = [sentence]
        else:
            current_para.append(sentence)
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return [p for p in paragraphs if len(p) > 50]


def split_chapter_into_scenes(chapter: dict) -> List[Scene]:
    """Split chapter into scenes."""
    title = chapter['title']
    paras = split_text_into_paragraphs(chapter['text'])
    
    # Scene definitions with paragraph count ratios
    scene_definitions = {
        'An Unexpected Party': [
            ("The Unexpected Party Begins", 0.00, 0.12),
            ("Gandalf's Visit", 0.12, 0.22),
            ("Thorin Arrives", 0.22, 0.30),
            ("The Dwarves Gather", 0.30, 0.42),
            ("The Feast and Song", 0.42, 0.52),
            ("Planning the Quest", 0.52, 0.65),
            ("Bilbo Decides to Go", 0.65, 1.00)
        ],
        'Roast Mutton': [
            ("Camping in the Trollshaws", 0.00, 0.22),
            ("Bilbo Tries to Steal", 0.22, 0.35),
            ("Captured by Trolls", 0.35, 0.50),
            ("Thorin's Arrival", 0.50, 0.65),
            ("Gandalf's Rescue", 0.65, 1.00)
        ],
        'A Short Rest': [
            ("Journey to Rivendell", 0.00, 0.25),
            ("The Last Homely House", 0.25, 0.50),
            ("Elrond's Counsel", 0.50, 1.00)
        ],
        'Over Hill and Under Hill': [
            ("Climbing the Mountains", 0.00, 0.20),
            ("The Storm and Cave", 0.20, 0.35),
            ("Captured by Goblins", 0.35, 0.50),
            ("The Great Goblin", 0.50, 0.65),
            ("Gandalf Rescues Them", 0.65, 1.00)
        ],
        'Riddles in the Dark': [
            ("Bilbo Wakes Alone", 0.00, 0.15),
            ("Finding the Ring", 0.15, 0.30),
            ("Meeting Gollum", 0.30, 0.45),
            ("The Riddle Game", 0.45, 0.70),
            ("Escaping the Goblins", 0.70, 1.00)
        ],
        'Out of the Frying-Pan into the Fire': [
            ("Reunion and Journey", 0.00, 0.15),
            ("The Wargs Attack", 0.15, 0.30),
            ("Trapped in Trees", 0.30, 0.50),
            ("The Lord of the Eagles", 0.50, 0.70),
            ("Rescue and the Carrock", 0.70, 1.00)
        ],
        'Queer Lodgings': [
            ("Approaching Beorn's House", 0.00, 0.15),
            ("Meeting Beorn", 0.15, 0.30),
            ("The Night", 0.30, 0.45),
            ("Beorn's Stories", 0.45, 0.65),
            ("Provisions and Departure", 0.65, 0.80),
            ("Into Mirkwood", 0.80, 1.00)
        ],
        'Flies and Spiders': [
            ("Entering Mirkwood", 0.00, 0.10),
            ("The Enchanted Lights", 0.10, 0.20),
            ("Bombur's Fall", 0.20, 0.30),
            ("Bombur's Dream", 0.30, 0.40),
            ("Starlight and Black Butterflies", 0.40, 0.50),
            ("Spiders Attack", 0.50, 0.65),
            ("Bilbo Rescues the Dwarves", 0.65, 0.80),
            ("Captured by Wood-elves", 0.80, 1.00)
        ],
        'Barrels Out of Bond': [
            ("Prisoner of the Elves", 0.00, 0.15),
            ("Bilbo Finds the Dwarves", 0.15, 0.30),
            ("The Escape Plan", 0.30, 0.45),
            ("The Water Gate", 0.45, 0.60),
            ("Floating Downriver", 0.60, 0.80),
            ("Lake-town", 0.80, 1.00)
        ],
        'A Warm Welcome': [
            ("Arrival at Lake-town", 0.00, 0.30),
            ("The Master's Feast", 0.30, 0.60),
            ("Departure for the Mountain", 0.60, 1.00)
        ],
        'On the Doorstep': [
            ("The Desolation of Smaug", 0.00, 0.15),
            ("Camping on the Mountain", 0.15, 0.35),
            ("Searching for the Door", 0.35, 0.55),
            ("The Thrush", 0.55, 0.70),
            ("The Secret Door Opens", 0.70, 1.00)
        ],
        'Inside Information': [
            ("Entering Erebor", 0.00, 0.12),
            ("Meeting Smaug", 0.12, 0.28),
            ("The Cup Theft", 0.28, 0.40),
            ("Conversation with Smaug", 0.40, 0.58),
            ("Smaug's Suspicion", 0.58, 0.75),
            ("The Weak Spot Revealed", 0.75, 1.00)
        ],
        'Not at Home': [
            ("Smaug Attacks Lake-town", 0.00, 0.20),
            ("Exploring the Mountain", 0.20, 0.40),
            ("Finding the Arkenstone", 0.40, 0.60),
            ("Bilbo Takes the Stone", 0.60, 0.80),
            ("Smaug's Death", 0.80, 1.00)
        ],
        'Fire and Water': [
            ("The Dragon's Attack", 0.00, 0.25),
            ("Bard Learns of the Weak Spot", 0.25, 0.50),
            ("The Black Arrow", 0.50, 0.70),
            ("Smaug is Killed", 0.70, 1.00)
        ],
        'The Gathering of the Clouds': [
            ("News of Smaug's Death", 0.00, 0.15),
            ("Roac the Raven", 0.15, 0.35),
            ("Thorin's Pride", 0.35, 0.50),
            ("Armies Gather", 0.50, 0.70),
            ("The Siege Begins", 0.70, 1.00)
        ],
        'A Thief in the Night': [
            ("Bilbo's Burden", 0.00, 0.15),
            ("Taking the Arkenstone", 0.15, 0.35),
            ("Parley with Bard", 0.35, 0.60),
            ("Dain Arrives", 0.60, 1.00)
        ],
        'The Clouds Burst': [
            ("Battle Joined", 0.00, 0.15),
            ("The Eagles Come", 0.15, 0.30),
            ("Beorn Arrives", 0.30, 0.45),
            ("Victory", 0.45, 0.60),
            ("Thorin's Death", 0.60, 0.80),
            ("Bilbo's Farewell", 0.80, 1.00)
        ],
        'The Return Journey': [
            ("Dain Becomes King", 0.00, 0.15),
            ("Leaving Erebor", 0.15, 0.35),
            ("Staying with Beorn", 0.35, 0.55),
            ("Rivendell Again", 0.55, 0.75),
            ("Homeward Bound", 0.75, 1.00)
        ],
        'The Last Stage': [
            ("The Road Home", 0.00, 0.30),
            ("The Auction", 0.30, 0.65),
            ("Home at Last", 0.65, 1.00)
        ]
    }
    
    scenes = []
    definitions = scene_definitions.get(title)
    
    if not definitions:
        chunk_size = max(1, len(paras) // 5)
        definitions = [(f"Scene {i+1}", i*chunk_size/len(paras), (i+1)*chunk_size/len(paras)) 
                       for i in range((len(paras) + chunk_size - 1) // chunk_size)]
    
    total_paras = len(paras)
    
    for i, (scene_title, start_frac, end_frac) in enumerate(definitions, 1):
        start_idx = int(start_frac * total_paras)
        end_idx = int(end_frac * total_paras) if end_frac < 1.0 else total_paras
        
        scene_paras = paras[start_idx:end_idx]
        scene_text = '\n\n'.join(scene_paras)
        
        scenes.append(Scene(
            chapter=title,
            scene_number=i,
            title=scene_title,
            text=scene_text,
            word_count=len(scene_text.split())
        ))
    
    return scenes


def main():
    print("Extracting full text from EPUB...")
    raw_text = extract_full_text_from_epub(
        'The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub'
    )
    print(f"Raw text: {len(raw_text):,} characters")
    
    print("\nSplitting into chapters...")
    chapters = split_into_chapters(raw_text)
    print(f"Found {len(chapters)} chapters")
    
    all_scenes = []
    total_words = 0
    
    for ch in chapters:
        scenes = split_chapter_into_scenes(ch)
        ch_words = sum(s.word_count for s in scenes)
        total_words += ch_words
        
        print(f"\n{ch['title']}: {len(scenes)} scenes ({ch_words:,} words)")
        for s in scenes:
            print(f"  {s.scene_number}. {s.title} ({s.word_count:,} words)")
        
        all_scenes.extend(scenes)
    
    # Create output
    output = {
        'metadata': {
            'book': 'The Hobbit; Or There and Back Again',
            'author': 'J.R.R. Tolkien',
            'total_chapters': len(chapters),
            'total_scenes': len(all_scenes),
            'total_words': total_words,
            'extraction_date': '2024'
        },
        'scenes': [
            {
                'id': f"ch{i//100:02d}_sc{(i%100):02d}" if i >= 100 else f"ch{i+1:02d}_sc01",
                'chapter': s.chapter,
                'scene_number': s.scene_number,
                'title': s.title,
                'text': s.text,
                'word_count': s.word_count
            }
            for i, s in enumerate(all_scenes)
        ]
    }
    
    # Fix IDs properly
    ch_counter = {}
    for s in output['scenes']:
        ch = s['chapter']
        if ch not in ch_counter:
            ch_counter[ch] = 0
        ch_counter[ch] += 1
        ch_num = list(ch_counter.keys()).index(ch) + 1
        s['id'] = f"ch{ch_num:02d}_sc{ch_counter[ch]:02d}"
    
    # Save
    with open('../data/hobbit_book_scenes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Index only
    output_index = {
        'metadata': output['metadata'],
        'scenes': [{k: v for k, v in s.items() if k != 'text'} for s in output['scenes']]
    }
    with open('hobbit_book_index.json', 'w', encoding='utf-8') as f:
        json.dump(output_index, f, indent=2)
    
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Chapters: {len(chapters)}")
    print(f"Total scenes: {len(all_scenes)}")
    print(f"Total words: {total_words:,}")
    print(f"\nFiles created:")
    print(f"  - hobbit_book_scenes.json")
    print(f"  - hobbit_book_index.json")
    
    if all_scenes:
        print(f"\n{'='*70}")
        print("Sample - First scene:")
        print(f"{'='*70}")
        s = all_scenes[0]
        print(f"Chapter: {s.chapter}")
        print(f"Scene: {s.title}")
        print(f"\n{s.text[:500]}...")


if __name__ == "__main__":
    main()
