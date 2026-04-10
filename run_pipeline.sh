#!/bin/bash
# Hobbit Journey Stream - Full Processing Pipeline
# Processes the EPUB from scratch to generate all necessary data files

set -e  # Exit on error

echo "=================================="
echo "Hobbit Journey Stream Pipeline"
echo "=================================="
echo ""

# Check for EPUB
if [ ! -f "The Hobbit Or There and Back Again -- Tolkien, John Ronald Reuel.epub" ]; then
    echo "Error: EPUB file not found!"
    exit 1
fi

echo "Step 1/8: Extracting scenes from EPUB..."
cd scripts
python3 extract_all_scenes_final.py

echo "Step 2/8: Extracting entities (characters, places, objects)..."
python3 extract_entities_final.py

echo "Step 3/8: Adding story duration estimates..."
python3 add_story_duration.py

echo "Step 4/8: Adding summaries..."
python3 add_summaries.py

echo "Step 5/8: Generating gap content (this may take a while)..."
if [ -f "../data/.env" ]; then
    python3 gap_content_generator.py
else
    echo "  Skipping gap generation (no .env file with API keys)"
fi

echo "Step 6/8: Updating stream scenes..."
python3 update_stream_scenes.py

cd ..

echo "Step 7/8: Generating narrative styles..."
python3 scripts/narrative_generator.py

echo "Step 8/8: Generating progressive beats..."
python3 scripts/narrative_beats_v2.py

echo ""
echo "=================================="
echo "Pipeline complete!"
echo "=================================="
echo ""
echo "To launch the GUI, run:"
echo "  python3 gui_prototype.py"
echo ""
