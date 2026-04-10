#!/usr/bin/env python3
"""
Extract ALL text from The Hobbit and assign it to specific scenes.
Version 3: Process the entire text as a whole, then split by chapter titles.
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
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
    word_count: int
    char_count: int


def extract_full_text_from_epub(filepath: str) -> str:
    """Extract all text content from EPUB."""
    book = epub.read_epub(filepath)
    
    all_texts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT and item.get_name().endswith('.htm'):
            content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script/style
            for tag in soup(['script', 'style', 'nav']):
                tag.decompose()
            
            text = soup.get_text()
            all_texts.append(text)
    
    return '\n'.join(all_texts)


def clean_text(text: str) -> str:
    """Clean up extracted text."""
    # Remove page numbers (standalone numbers)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Split by sentence endings followed by space and capital letter or quote
    pattern = r'(?<=[.!?])\s+(?=[A-Z"\'\(])'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def group_into_paragraphs(sentences: List[str]) -> List[str]:
    """Group sentences into paragraphs."""
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        # Special handling: standalone chapter numbers or titles
        stripped = sentence.strip()
        if re.match(r'^Chapter\s+\d+$', stripped):
            # Save current paragraph first
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            # Add chapter number as its own paragraph
            paragraphs.append(stripped)
            continue
        
        # Check for chapter titles (short standalone lines that match known titles)
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
        if stripped in chapter_titles:
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            paragraphs.append(stripped)
            continue
        
        # Start new paragraph indicators
        new_para_starters = [
            'When ', 'After ', 'Soon ', 'Later ', 'That ', 'The next', 'Next ',
            'At last', 'Meanwhile', 'By this', 'In the ', 'On the ', 'At the',
            'Morning ', 'Evening ', 'Night ', 'Day ', 'It was ', 'There ',
            'They ', 'He ', 'She ', 'Bilbo ', 'Thorin ', 'Gandalf ', 'But ',
            'And so', 'So ', 'Now ', 'Then ', 'Suddenly ', 'All of a sudden',
            'However ', 'Nevertheless '
        ]
        
        is_new_para = any(sentence.startswith(starter) for starter in new_para_starters)
        current_length = sum(len(s) for s in current_para)
        
        # Also start new para if current is getting long
        if (is_new_para or current_length > 1000) and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = [sentence]
        else:
            current_para.append(sentence)
    
    # Don't forget last paragraph
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return [p for p in paragraphs if len(p) > 30]


def split_into_chapters(paragraphs: List[str]) -> List[dict]:
    """Split paragraphs into chapters based on chapter titles."""
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
    
    # Find chapter boundaries
    chapters = []
    current_ch_title = None
    current_ch_paras = []
    ch_num = 0
    skip_next = False  # For skipping chapter number paragraph
    
    for i, para in enumerate(paragraphs):
        para_stripped = para.strip()
        
        if skip_next:
            skip_next = False
            continue
        
        # Check if this paragraph IS a chapter title
        found_chapter = None
        
        for title in chapter_titles:
            if para_stripped == title or para_stripped.startswith(title + ' '):
                found_chapter = title
                break
        
        if found_chapter:
            # Save previous chapter
            if current_ch_title and current_ch_paras:
                chapters.append({
                    'title': current_ch_title,
                    'number': ch_num,
                    'paragraphs': current_ch_paras
                })
            
            ch_num += 1
            current_ch_title = found_chapter
            current_ch_paras = []
            continue
        
        # Check if this is a "Chapter X" line - look for title in next paragraph
        if re.match(r'^Chapter\s+\d+$', para_stripped):
            if i + 1 < len(paragraphs):
                next_para = paragraphs[i + 1].strip()
                for title in chapter_titles:
                    if next_para == title or next_para.startswith(title):
                        # Save previous chapter
                        if current_ch_title and current_ch_paras:
                            chapters.append({
                                'title': current_ch_title,
                                'number': ch_num,
                                'paragraphs': current_ch_paras
                            })
                        
                        ch_num += 1
                        current_ch_title = title
                        current_ch_paras = []
                        skip_next = True  # Skip the title paragraph
                        break
            continue
        
        if current_ch_title:
            current_ch_paras.append(para)
    
    # Save last chapter
    if current_ch_title and current_ch_paras:
        chapters.append({
            'title': current_ch_title,
            'number': ch_num,
            'paragraphs': current_ch_paras
        })
    
    return chapters


def split_chapter_into_scenes(chapter: dict) -> List[Scene]:
    """Split chapter into scenes based on narrative breaks."""
    title = chapter['title']
    paras = chapter['paragraphs']
    
    # Scene definitions with estimated paragraph ranges based on word counts
    # Approx 90,000 words total / ~95 scenes = ~950 words per scene
    scene_definitions = {
        'An Unexpected Party': [
            ("The Unexpected Party", 0.00, 0.10),
            ("Gandalf's Visit", 0.10, 0.20),
            ("Thorin Arrives", 0.20, 0.30),
            ("The Dwarves Gather", 0.30, 0.45),
            ("Misty Mountains Song", 0.45, 0.55),
            ("Planning the Quest", 0.55, 0.70),
            ("Bilbo Decides to Go", 0.70, 1.00)
        ],
        'Roast Mutton': [
            ("Camping in the Trollshaws", 0.00, 0.20),
            ("Bilbo Tries to Steal", 0.20, 0.35),
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
        # Fallback: split into ~5 equal parts
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
            word_count=len(scene_text.split()),
            char_count=len(scene_text)
        ))
    
    return scenes


def main():
    print("Extracting full text from EPUB...")
    raw_text = extract_full_text_from_epub(
        'The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub'
    )
    print(f"Raw text: {len(raw_text):,} characters")
    
    print("\nCleaning text...")
    cleaned = clean_text(raw_text)
    print(f"Cleaned: {len(cleaned):,} characters")
    
    print("\nSplitting into sentences...")
    sentences = split_into_sentences(cleaned)
    print(f"Found {len(sentences):,} sentences")
    
    print("\nGrouping into paragraphs...")
    paragraphs = group_into_paragraphs(sentences)
    print(f"Found {len(paragraphs):,} paragraphs")
    
    print("\nSplitting into chapters...")
    chapters = split_into_chapters(paragraphs)
    print(f"Found {len(chapters)} chapters")
    
    if len(chapters) != 19:
        print(f"\nWARNING: Expected 19 chapters, found {len(chapters)}")
        print("Chapter titles found:")
        for ch in chapters[:5]:
            print(f"  - {ch['title']} ({len(ch['paragraphs'])} paras)")
    
    all_scenes = []
    total_words = 0
    total_chars = 0
    
    for ch in chapters:
        print(f"\nProcessing: {ch['title']} ({len(ch['paragraphs'])} paragraphs)")
        scenes = split_chapter_into_scenes(ch)
        
        ch_words = sum(s.word_count for s in scenes)
        ch_chars = sum(s.char_count for s in scenes)
        total_words += ch_words
        total_chars += ch_chars
        
        print(f"  → {len(scenes)} scenes ({ch_words:,} words)")
        for s in scenes:
            print(f"    {s.scene_number}. {s.title} ({s.word_count:,} words)")
        
        all_scenes.extend(scenes)
    
    # Create output
    output = {
        'metadata': {
            'book': 'The Hobbit; Or There and Back Again',
            'author': 'J.R.R. Tolkien',
            'total_chapters': len(chapters),
            'total_scenes': len(all_scenes),
            'total_words': total_words,
            'total_characters': total_chars
        },
        'scenes': [
            {
                'id': f"ch{list(set(s.chapter for s in all_scenes)).index(s.chapter) + 1:02d}_sc{s.scene_number:02d}",
                'chapter': s.chapter,
                'scene_number': s.scene_number,
                'title': s.title,
                'text': s.text,
                'word_count': s.word_count,
                'char_count': s.char_count
            }
            for s in all_scenes
        ]
    }
    
    # Save full version
    with open('hobbit_complete_scenes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Save index only (no text)
    output_index = {
        'metadata': output['metadata'],
        'scenes': [{k: v for k, v in s.items() if k != 'text'} for s in output['scenes']]
    }
    with open('hobbit_complete_index.json', 'w', encoding='utf-8') as f:
        json.dump(output_index, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Chapters: {len(chapters)}")
    print(f"Total scenes: {len(all_scenes)}")
    print(f"Total words: {total_words:,}")
    print(f"Total characters: {total_chars:,}")
    print(f"\nFiles created:")
    print(f"  - hobbit_complete_scenes.json ({total_chars/1024/1024:.1f} MB)")
    print(f"  - hobbit_complete_index.json")
    
    # Sample
    if all_scenes:
        print(f"\n{'='*70}")
        print("SAMPLE: First scene (first 400 chars)")
        print(f"{'='*70}")
        s = all_scenes[0]
        print(f"ID: ch01_sc01")
        print(f"Chapter: {s.chapter}")
        print(f"Title: {s.title}")
        print(f"\n{s.text[:400]}...")


if __name__ == "__main__":
    main()
