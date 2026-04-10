"""
Main Content Generation Engine

Orchestrates image, audio, and voice generation for the stream.
"""

import os
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
import time

from .config import GenerativeConfig


@dataclass
class GeneratedContent:
    """Result of a content generation request"""
    content_type: str  # image, audio, voice
    scene_id: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    status: str = "pending"  # pending, generating, completed, error
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_type": self.content_type,
            "scene_id": self.scene_id,
            "file_path": self.file_path,
            "url": self.url,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ContentGenerator:
    """
    Main engine for generating AI-powered content.
    
    Supports:
    - Image generation (DALL-E, Stable Diffusion)
    - Audio generation (ambient soundscapes, effects)
    - Voice generation (narration, dialogue)
    """
    
    def __init__(self, config: Optional[GenerativeConfig] = None):
        self.config = config or GenerativeConfig()
        self.cache: Dict[str, GeneratedContent] = {}
        self.queue: List[Dict[str, Any]] = []
        self.generation_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Callbacks for completion events
        self.on_image_complete: Optional[Callable] = None
        self.on_audio_complete: Optional[Callable] = None
        self.on_voice_complete: Optional[Callable] = None
        
        # Initialize providers if configured
        self._init_providers()
        
        # Start background processing
        self.start()
    
    def _init_providers(self):
        """Initialize AI provider clients"""
        self.openai_client = None
        self.elevenlabs_client = None
        
        # Initialize OpenAI if key available
        if self.config.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
                print(f"[Generative] OpenAI client initialized")
            except ImportError:
                print("[Generative] OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                print(f"[Generative] Failed to initialize OpenAI: {e}")
        
        # Initialize ElevenLabs if key available
        if self.config.elevenlabs_api_key:
            try:
                from elevenlabs import ElevenLabs
                self.elevenlabs_client = ElevenLabs(api_key=self.config.elevenlabs_api_key)
                print(f"[Generative] ElevenLabs client initialized")
            except ImportError:
                print("[Generative] ElevenLabs package not installed. Run: pip install elevenlabs")
            except Exception as e:
                print(f"[Generative] Failed to initialize ElevenLabs: {e}")
    
    def start(self):
        """Start background generation thread"""
        if not self.running:
            self.running = True
            self.generation_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.generation_thread.start()
            print("[Generative] Content generator started")
    
    def stop(self):
        """Stop background generation thread"""
        self.running = False
        if self.generation_thread:
            self.generation_thread.join(timeout=5)
        print("[Generative] Content generator stopped")
    
    def _process_queue(self):
        """Background thread to process generation queue"""
        while self.running:
            if self.queue:
                task = self.queue.pop(0)
                try:
                    self._generate_content(task)
                except Exception as e:
                    print(f"[Generative] Generation error: {e}")
                    task['result'].status = "error"
                    task['result'].error = str(e)
            time.sleep(0.1)
    
    def _generate_content(self, task: Dict[str, Any]):
        """Process a single generation task"""
        content_type = task['type']
        result = task['result']
        
        result.status = "generating"
        
        if content_type == "image":
            self._generate_image_task(task)
        elif content_type == "audio":
            self._generate_audio_task(task)
        elif content_type == "voice":
            self._generate_voice_task(task)
    
    # ==================== Image Generation ====================
    
    def generate_scene_image(self, scene_data: Dict[str, Any], 
                            force_regenerate: bool = False) -> GeneratedContent:
        """
        Generate an illustration for a scene.
        
        Args:
            scene_data: Scene information dict
            force_regenerate: Ignore cache and regenerate
        
        Returns:
            GeneratedContent with status and file path
        """
        scene_id = scene_data.get('id', 'unknown')
        
        # Check cache
        cache_key = f"image_{scene_id}"
        if not force_regenerate and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Create result object
        result = GeneratedContent(
            content_type="image",
            scene_id=scene_id,
            status="pending"
        )
        self.cache[cache_key] = result
        
        # Queue generation
        self.queue.append({
            'type': 'image',
            'scene': scene_data,
            'result': result
        })
        
        return result
    
    def _generate_image_task(self, task: Dict[str, Any]):
        """Generate scene image using configured provider"""
        scene = task['scene']
        result = task['result']
        
        if not self.config.images.enabled:
            result.status = "error"
            result.error = "Image generation disabled"
            return
        
        # Build prompt from template
        prompt = self._build_image_prompt(scene)
        
        # Generate using provider
        if self.config.images.provider == "openai" and self.openai_client:
            self._generate_dalle_image(prompt, result)
        else:
            # Placeholder for other providers or disabled
            result.status = "error"
            result.error = f"Provider {self.config.images.provider} not available"
    
    def _build_image_prompt(self, scene: Dict[str, Any]) -> str:
        """Build image generation prompt from scene data"""
        template = self.config.images.scene_prompt_template
        
        # Extract scene info
        title = scene.get('title', 'Unknown Scene')
        location = scene.get('location', 'Unknown Location')
        time_str = scene.get('time', 'Day')
        
        # Determine time of day and atmosphere
        time_lower = time_str.lower()
        if 'night' in time_lower or 'evening' in time_lower:
            time_of_day = "night"
            atmosphere = "dark, mysterious, moonlit"
        elif 'morning' in time_lower or 'dawn' in time_lower:
            time_of_day = "morning"
            atmosphere = "fresh, hopeful, golden light"
        elif 'afternoon' in time_lower:
            time_of_day = "afternoon"
            atmosphere = "warm, peaceful"
        else:
            time_of_day = "day"
            atmosphere = "natural daylight"
        
        # Get characters
        chars = scene.get('characters', [])
        if not chars and 'characters_present' in scene:
            chars = scene['characters_present']
        characters = ", ".join(chars) if chars else "None"
        
        # Get description
        description = scene.get('summary', scene.get('content', ''))[:200]
        
        return template.format(
            title=title,
            location=location,
            time_of_day=time_of_day,
            atmosphere=atmosphere,
            characters=characters,
            description=description
        )
    
    def _generate_dalle_image(self, prompt: str, result: GeneratedContent):
        """Generate image using DALL-E"""
        try:
            response = self.openai_client.images.generate(
                model=self.config.images.model,
                prompt=prompt,
                size=self.config.images.size,
                quality=self.config.images.quality,
                style=self.config.images.style,
                n=1
            )
            
            # Download and save image
            import urllib.request
            image_url = response.data[0].url
            
            # Create filename
            safe_name = "".join(c for c in result.scene_id if c.isalnum() or c in '_-')
            filename = f"{safe_name}_{int(time.time())}.png"
            filepath = os.path.join(self.config.images.cache_dir, filename)
            os.makedirs(self.config.images.cache_dir, exist_ok=True)
            
            # Download
            urllib.request.urlretrieve(image_url, filepath)
            
            result.file_path = filepath
            result.url = f"/media/images/{filename}"
            result.status = "completed"
            result.metadata['prompt'] = prompt
            result.metadata['provider'] = 'openai'
            
            if self.on_image_complete:
                self.on_image_complete(result)
                
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            print(f"[Generative] DALL-E generation failed: {e}")
    
    # ==================== Audio Generation ====================
    
    def generate_ambient_audio(self, scene_data: Dict[str, Any],
                               force_regenerate: bool = False) -> GeneratedContent:
        """Generate ambient soundscape for a scene"""
        scene_id = scene_data.get('id', 'unknown')
        
        cache_key = f"audio_{scene_id}"
        if not force_regenerate and cache_key in self.cache:
            return self.cache[cache_key]
        
        result = GeneratedContent(
            content_type="audio",
            scene_id=scene_id,
            status="pending"
        )
        self.cache[cache_key] = result
        
        self.queue.append({
            'type': 'audio',
            'scene': scene_data,
            'result': result
        })
        
        return result
    
    def _generate_audio_task(self, task: Dict[str, Any]):
        """Generate ambient audio"""
        scene = task['scene']
        result = task['result']
        
        if not self.config.audio.enabled:
            result.status = "error"
            result.error = "Audio generation disabled"
            return
        
        # For now, use placeholder/mock generation
        # In production, this would use AI audio generation APIs
        location = scene.get('location', '').lower()
        
        # Match location to ambient type
        ambient_type = "forest"  # default
        for loc_type, desc in self.config.audio.location_ambient.items():
            if loc_type in location:
                ambient_type = loc_type
                break
        
        # Create placeholder (in production, generate actual audio)
        result.status = "completed"
        result.metadata['ambient_type'] = ambient_type
        result.metadata['description'] = self.config.audio.location_ambient.get(ambient_type)
        result.url = f"/media/audio/ambient_{ambient_type}.mp3"
        
        if self.on_audio_complete:
            self.on_audio_complete(result)
    
    # ==================== Voice Generation ====================
    
    def generate_narration(self, text: str, voice_id: Optional[str] = None,
                          scene_id: str = "unknown",
                          force_regenerate: bool = False) -> GeneratedContent:
        """
        Generate voice narration for text.
        
        Args:
            text: Text to narrate
            voice_id: Voice ID to use (or None for default)
            scene_id: Associated scene ID
            force_regenerate: Ignore cache
        """
        # Create cache key from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        cache_key = f"voice_{scene_id}_{text_hash}"
        
        if not force_regenerate and cache_key in self.cache:
            return self.cache[cache_key]
        
        result = GeneratedContent(
            content_type="voice",
            scene_id=scene_id,
            status="pending"
        )
        self.cache[cache_key] = result
        
        self.queue.append({
            'type': 'voice',
            'text': text,
            'voice_id': voice_id or self.config.voice.default_voice,
            'result': result
        })
        
        return result
    
    def _generate_voice_task(self, task: Dict[str, Any]):
        """Generate voice narration using configured provider"""
        text = task['text']
        voice_id = task['voice_id']
        result = task['result']
        
        if not self.config.voice.enabled:
            result.status = "error"
            result.error = "Voice generation disabled"
            return
        
        provider = self.config.voice.provider
        
        if provider == "runpod_kokoro":
            self._generate_voice_runpod_kokoro(text, voice_id, result)
        elif provider == "modal_chatterbox":
            self._generate_voice_modal_chatterbox(text, voice_id, result)
        elif provider == "elevenlabs":
            self._generate_voice_elevenlabs(text, voice_id, result)
        else:
            result.status = "error"
            result.error = f"Unknown voice provider: {provider}"
    
    def _generate_voice_elevenlabs(self, text: str, voice_id: str, result):
        """Generate voice using ElevenLabs API"""
        if not self.elevenlabs_client:
            result.status = "error"
            result.error = "ElevenLabs not configured"
            return
        
        try:
            from elevenlabs import VoiceSettings
            
            # Generate audio
            audio = self.elevenlabs_client.generate(
                text=text,
                voice=voice_id,
                voice_settings=VoiceSettings(
                    stability=self.config.voice.stability,
                    similarity_boost=self.config.voice.similarity_boost,
                    style=self.config.voice.style
                )
            )
            
            # Save to file
            safe_name = "".join(c for c in result.scene_id if c.isalnum() or c in '_-')
            filename = f"{safe_name}_{int(time.time())}.mp3"
            filepath = os.path.join(self.config.voice.cache_dir, filename)
            os.makedirs(self.config.voice.cache_dir, exist_ok=True)
            
            # Save audio bytes
            if isinstance(audio, bytes):
                with open(filepath, 'wb') as f:
                    f.write(audio)
            else:
                # Handle generator
                with open(filepath, 'wb') as f:
                    for chunk in audio:
                        f.write(chunk)
            
            result.file_path = filepath
            result.url = f"/media/voice/{filename}"
            result.status = "completed"
            result.metadata['voice_id'] = voice_id
            result.metadata['provider'] = "elevenlabs"
            result.metadata['text_length'] = len(text)
            
            if self.on_voice_complete:
                self.on_voice_complete(result)
                
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            print(f"[Generative] ElevenLabs voice generation failed: {e}")
    
    def _generate_voice_runpod_kokoro(self, text: str, character: str, result):
        """Generate voice using RunPod Serverless Kokoro TTS"""
        import requests
        import base64
        
        endpoint = self.config.voice.runpod_endpoint
        api_key = self.config.voice.runpod_api_key
        
        if not endpoint:
            result.status = "error"
            result.error = "RunPod Kokoro endpoint not configured"
            return
        
        # Map character to Kokoro voice
        voice_mapping = self.config.voice.runpod_voice_mapping or {}
        kokoro_voice = voice_mapping.get(character, "af_sky")
        
        try:
            headers = {
                "Content-Type": "application/json",
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "input": {
                    "text": text,
                    "voice": kokoro_voice,
                    "speed": 1.0,
                    "format": "wav"
                }
            }
            
            print(f"[Generative] Calling RunPod Kokoro: voice={kokoro_voice}, chars={len(text)}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                result.status = "error"
                result.error = f"RunPod API error: {response.status_code}"
                print(f"[Generative] RunPod error: {response.text}")
                return
            
            response_data = response.json()
            
            # Handle RunPod's response format
            if "output" in response_data:
                output = response_data["output"]
            else:
                output = response_data
            
            if "error" in output:
                result.status = "error"
                result.error = output["error"]
                return
            
            # Decode audio
            audio_data = base64.b64decode(output["audio"])
            
            # Save to file
            safe_name = "".join(c for c in result.scene_id if c.isalnum() or c in '_-')
            filename = f"{safe_name}_{kokoro_voice}_{int(time.time())}.wav"
            filepath = os.path.join(self.config.voice.cache_dir, filename)
            os.makedirs(self.config.voice.cache_dir, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            result.file_path = filepath
            result.url = f"/media/voice/{filename}"
            result.status = "completed"
            result.metadata['voice_id'] = kokoro_voice
            result.metadata['character'] = character
            result.metadata['provider'] = "runpod_kokoro"
            result.metadata['duration'] = output.get("duration")
            result.metadata['text_length'] = len(text)
            
            print(f"[Generative] Generated: {output.get('duration', 0):.1f}s, {len(audio_data)} bytes")
            
            if self.on_voice_complete:
                self.on_voice_complete(result)
                
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            print(f"[Generative] RunPod Kokoro generation failed: {e}")
    
    def _generate_voice_modal_chatterbox(self, text: str, character: str, result):
        """Generate voice using Chatterbox TTS on Modal Labs"""
        import sys
        import os
        
        # Add parent directory to path for imports
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        try:
            from runpod_kokoro.chatterbox_client import ChatterboxClient
        except ImportError as e:
            result.status = "error"
            result.error = f"Chatterbox client not available: {e}"
            return
        
        endpoint = self.config.voice.runpod_endpoint  # Reuse same config field
        
        if not endpoint:
            result.status = "error"
            result.error = "Modal Chatterbox endpoint not configured (use voice.runpod_endpoint)"
            return
        
        # Map character to Kokoro voice
        voice_mapping = self.config.voice.runpod_voice_mapping or {}
        kokoro_voice = voice_mapping.get(character, "af_sky")
        
        try:
            print(f"[Generative] Calling Modal Chatterbox: voice={kokoro_voice}, chars={len(text)}")
            
            client = ChatterboxClient(endpoint)
            tts_result = client.generate(text=text, voice=kokoro_voice, speed=1.0, format="wav")
            
            # Save to file
            safe_name = "".join(c for c in result.scene_id if c.isalnum() or c in '_-')
            filename = f"{safe_name}_{kokoro_voice}_{int(time.time())}.wav"
            filepath = os.path.join(self.config.voice.cache_dir, filename)
            os.makedirs(self.config.voice.cache_dir, exist_ok=True)
            
            tts_result.save(filepath)
            
            result.file_path = filepath
            result.url = f"/media/voice/{filename}"
            result.status = "completed"
            result.metadata['voice_id'] = kokoro_voice
            result.metadata['character'] = character
            result.metadata['provider'] = "modal_chatterbox"
            result.metadata['duration'] = tts_result.duration
            result.metadata['text_length'] = len(text)
            
            print(f"[Generative] Generated: {tts_result.duration:.1f}s, {len(tts_result.audio_bytes)} bytes")
            
            if self.on_voice_complete:
                self.on_voice_complete(result)
                
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            print(f"[Generative] Modal Chatterbox generation failed: {e}")
    
    # ==================== Utility Methods ====================
    
    def get_status(self, scene_id: str = None) -> Dict[str, Any]:
        """Get generation status"""
        if scene_id:
            # Get status for specific scene
            scene_cache = {k: v for k, v in self.cache.items() if v.scene_id == scene_id}
            return {
                scene_id: {k: v.to_dict() for k, v in scene_cache.items()}
            }
        
        # Get all status
        return {
            "queue_length": len(self.queue),
            "cache_size": len(self.cache),
            "items": {k: v.to_dict() for k, v in list(self.cache.items())[:10]}  # Last 10
        }
    
    def clear_cache(self, scene_id: str = None):
        """Clear generation cache"""
        if scene_id:
            # Clear only specific scene
            keys_to_remove = [k for k, v in self.cache.items() if v.scene_id == scene_id]
            for k in keys_to_remove:
                del self.cache[k]
        else:
            self.cache.clear()
    
    def pregenerate_scene(self, scene_data: Dict[str, Any],
                         include_image: bool = True,
                         include_audio: bool = True,
                         include_voice: bool = False):
        """
        Pre-generate all content for a scene.
        
        Args:
            scene_data: Scene information
            include_image: Generate scene illustration
            include_audio: Generate ambient audio
            include_voice: Generate narration (requires beat text)
        """
        if include_image:
            self.generate_scene_image(scene_data)
        
        if include_audio:
            self.generate_ambient_audio(scene_data)
        
        if include_voice and 'beats' in scene_data:
            # Generate voice for first beat
            beats = scene_data['beats'].get('beats', [])
            if beats:
                self.generate_narration(
                    beats[0].get('text', ''),
                    scene_id=scene_data.get('id', 'unknown')
                )
