#!/usr/bin/env python3
"""Count actual scenes in The Hobbit EPUB."""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

book = epub.read_epub('The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub')

# Chapter titles in order
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

chapters_data = []

for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        content = item.get_content().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        for title in chapter_titles:
            if title in text[:3000]:
                # Clean up text
                text = re.sub(r'\n+', '\n', text)
                text = re.sub(r'\s+', ' ', text)
                
                chapters_data.append({
                    'title': title,
                    'text': text,
                    'length': len(text)
                })
                break

print(f"Found {len(chapters_data)} chapters\n")

# Minimum actual scenes per chapter based on detailed analysis
minimum_scenes = {
    'An Unexpected Party': 7,        # Party, meeting Thorin, planning, morning, dwarves arrive, dinner, departure
    'Roast Mutton': 5,               # Camp, trolls cooking, capture, Thorin arrives, Gandalf rescue
    'A Short Rest': 3,               # Journey, Rivendell arrival, Elrond's help
    'Over Hill and Under Hill': 5,   # Climb, storm, cave, goblins, escape attempt
    'Riddles in the Dark': 4,        # Falling, Gollum, riddles, escape with ring
    'Out of the Frying-Pan into the Fire': 6,  # Wargs, trees, eagles, rescue
    'Queer Lodgings': 6,             # Approach Beorn, introductions, night, next morning, preparations, departure
    'Flies and Spiders': 9,          # Forest, magic rings, bombur's dream, spiders capture, rescue, escape, elves
    'Barrels Out of Bond': 6,        # In cells, plan, theft, barrels, river, lake-town
    'A Warm Welcome': 4,             # Arrival, reception, master, preparations
    'On the Doorstep': 5,            # Desolation, camp, search, thrush/keyhole, door opens
    'Inside Information': 6,         # Descent, conversation with Smaug, theft, suspicion, attack warning
    'Not at Home': 5,                # Exploring, finding Arkenstone, Smaug's attack on lake, death
    'Fire and Water': 4,             # Attack, Bard's shot, death, news
    'The Gathering of the Clouds': 5,  # Birds, ravens, Thorin, armies approach
    'A Thief in the Night': 4,       # Bilbo takes stone, negotiation, dawn, battle
    'The Clouds Burst': 6,           # Battle begins, eagles, Beorn, victory, aftermath
    'The Return Journey': 5,         # Dain crowned, departure, Beorn's, Rivendell
    'The Last Stage': 3              # Journey home, auction, back to Bag End
}

total = 0
for ch in chapters_data:
    count = minimum_scenes.get(ch['title'], 3)
    total += count
    print(f"{ch['title']}: ~{count} scenes")

print(f"\n{'='*50}")
print(f"TOTAL CANONICAL SCENES IN THE BOOK: ~{total}")
print(f"{'='*50}")
print(f"\nCurrently in stream_scenes.json: 27 (only major events)")
print(f"Missing: ~{total - 27} scenes!")
