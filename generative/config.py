"""
Configuration for generative content features
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ImageConfig:
    """Image generation settings"""
    enabled: bool = False
    provider: str = "openai"  # openai, stability, local
    model: str = "dall-e-3"
    size: str = "1024x1024"  # 1024x1024, 1792x1024, 1024x1792
    quality: str = "standard"  # standard, hd
    style: str = "vivid"  # vivid, natural
    cache_dir: str = "output/media/images"
    
    # Scene illustration prompts
    scene_prompt_template: str = """Fantasy illustration of a scene from The Hobbit by J.R.R. Tolkien.
Scene: {title}
Setting: {location}
Time: {time_of_day}
Atmosphere: {atmosphere}
Characters present: {characters}
Key moment: {description}

Style: Richly detailed fantasy art in the style of Alan Lee, atmospheric lighting, 
cinematic composition, watercolor and ink, Middle-earth aesthetic."""


@dataclass
class AudioConfig:
    """Audio/Sound generation settings"""
    enabled: bool = False
    provider: str = "elevenlabs"  # elevenlabs, openai, local
    
    # Ambient soundscapes
    ambient_enabled: bool = True
    ambient_volume: float = 0.3
    
    # Sound effects
    effects_enabled: bool = True
    effects_volume: float = 0.5
    
    # Cache settings
    cache_dir: str = "output/media/audio"
    
    # Location-based ambient templates
    location_ambient: Dict[str, str] = None
    
    def __post_init__(self):
        if self.location_ambient is None:
            self.location_ambient = {
                "forest": "Gentle forest ambience with rustling leaves, distant birdsong, peaceful woodland atmosphere",
                "mountain": "Windy mountain peaks howling gusts, rocky terrain, vast open skies",
                "cave": "Dark cave ambience with dripping water, echoing depths, mysterious underground",
                "hobbiton": "Peaceful countryside with birds chirping, gentle breeze, idyllic Shire atmosphere",
                "lake": "Calm lake waters lapping shore, gentle ripples, serene waterfront",
                "dungeon": "Dark dungeon with chains rattling, dripping water, ominous echoing",
                "battle": "Distant clashing swords, battle cries, dramatic tension",
                "dragon": "Heavy breathing, fire crackling, massive creature presence, gold coins shifting",
                "travel": "Walking on various terrain, backpack sounds, journey ambience"
            }


@dataclass
class VoiceConfig:
    """Voice/Narration generation settings"""
    enabled: bool = False
    provider: str = "elevenlabs"  # elevenlabs, openai, azure, runpod_kokoro, modal_chatterbox
    
    # Default narrator voice
    default_voice: str = "bilbo"
    
    # Voice mapping for characters
    character_voices: Dict[str, str] = None
    
    # Voice settings (for ElevenLabs)
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    
    # Cache settings
    cache_dir: str = "output/media/voice"
    
    # RunPod Kokoro settings
    runpod_endpoint: Optional[str] = None  # e.g., "https://api.runpod.ai/v2/xxxxx/run"
    runpod_api_key: Optional[str] = None
    runpod_voice_mapping: Dict[str, str] = None  # Map characters to Kokoro voices
    
    def __post_init__(self):
        if self.character_voices is None:
            self.character_voices = {
                "narrator": "XB0fDUnXU5powFXDhCwa",  # Default narrator
                "bilbo": "XB0fDUnXU5powFXDhCwa",      # Bilbo voice
                "gandalf": "TX3AEvVoIzMeN6YzH2bZ",    # Wise, older voice
                "thorin": "TxGEqnHWrfWFTfGW9XjX",     # Gruff, leadership voice
                "gollum": "XB0fDUnXU5powFXDhCwa",     # (Would use specific voice)
                "smaug": "XB0fDUnXU5powFXDhCwa",      # (Would use specific voice)
            }
        
        # Load RunPod/Modal API key and endpoint from environment
        if self.runpod_api_key is None:
            self.runpod_api_key = os.getenv("RUNPOD_API_KEY")
        if self.runpod_endpoint is None:
            self.runpod_endpoint = os.getenv("RUNPOD_KOKORO_ENDPOINT") or os.getenv("MODAL_CHATTERBOX_ENDPOINT")
        
        # Kokoro voice mapping for Hobbit characters
        if self.runpod_voice_mapping is None:
            self.runpod_voice_mapping = {
                "narrator": "af_sky",      # Light, storytelling voice
                "bilbo": "af_bella",        # Soft, gentle (hobbit-like)
                "gandalf": "am_echo",       # Deep, wise
                "thorin": "am_onyx",        # Authoritative
                "gollum": "am_puck",        # Playful but unsettling
                "smaug": "am_fenrir",       # Powerful, menacing
                "bard": "am_michael",       # Professional, clear
                "elrond": "am_liam",        # Warm, friendly
                "beorn": "am_fenrir",       # Strong
                "thranduil": "am_echo",     # Deep, regal
            }


@dataclass
class GenerativeConfig:
    """Main configuration for all generative features"""
    
    # API Keys (loaded from environment or .env file)
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    stability_api_key: Optional[str] = None
    
    # Feature toggles
    images: ImageConfig = None
    audio: AudioConfig = None
    voice: VoiceConfig = None
    
    # General settings
    auto_generate: bool = False  # Auto-generate on scene change
    cache_enabled: bool = True
    max_cache_size_mb: int = 1000
    
    def __post_init__(self):
        if self.images is None:
            self.images = ImageConfig()
        if self.audio is None:
            self.audio = AudioConfig()
        if self.voice is None:
            self.voice = VoiceConfig()
        
        # Load API keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", self.elevenlabs_api_key)
        self.stability_api_key = os.getenv("STABILITY_API_KEY", self.stability_api_key)
    
    @classmethod
    def from_file(cls, path: str = "generative/config.json"):
        """Load configuration from JSON file"""
        if not os.path.exists(path):
            return cls()
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls(
            openai_api_key=data.get('openai_api_key'),
            elevenlabs_api_key=data.get('elevenlabs_api_key'),
            stability_api_key=data.get('stability_api_key'),
            images=ImageConfig(**data.get('images', {})),
            audio=AudioConfig(**data.get('audio', {})),
            voice=VoiceConfig(**data.get('voice', {})),
            auto_generate=data.get('auto_generate', False),
            cache_enabled=data.get('cache_enabled', True),
            max_cache_size_mb=data.get('max_cache_size_mb', 1000)
        )
    
    def save(self, path: str = "generative/config.json"):
        """Save configuration to JSON file"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = asdict(self)
        # Remove API keys from saved file for security
        data.pop('openai_api_key', None)
        data.pop('elevenlabs_api_key', None)
        data.pop('stability_api_key', None)
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_ready(self, feature: str = None) -> bool:
        """Check if generative features are ready to use"""
        if feature == "images":
            return self.images.enabled and self.openai_api_key is not None
        elif feature == "audio":
            return self.audio.enabled  # Can use local generation
        elif feature == "voice":
            return self.voice.enabled and self.elevenlabs_api_key is not None
        else:
            # Check any feature is ready
            return (
                (self.images.enabled and self.openai_api_key is not None) or
                (self.audio.enabled) or
                (self.voice.enabled and self.elevenlabs_api_key is not None)
            )
