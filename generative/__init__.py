"""
Generative Content Module for The Hobbit Journey Stream

Provides AI-powered generation of:
- Images: Scene illustrations, character portraits, location art
- Audio: Ambient soundscapes, sound effects
- Voice: Narration, character dialogue

Usage:
    from generative import ContentGenerator
    
    generator = ContentGenerator()
    
    # Generate scene illustration
    image_path = generator.generate_scene_image(scene_data)
    
    # Generate ambient audio
    audio_path = generator.generate_ambient_audio(scene_data)
    
    # Generate narration
    voice_path = generator.generate_narration(text, voice_id="bilbo")
"""

from .engine import ContentGenerator
from .config import GenerativeConfig

__version__ = "1.0.0"
__all__ = ["ContentGenerator", "GenerativeConfig"]
