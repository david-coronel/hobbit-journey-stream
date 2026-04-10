#!/usr/bin/env python3
"""
Hobbit Journey Stream - Prototype GUI
A desktop interface for controlling and monitoring the narrative stream.
Updated for new stream_scenes.json format with full text content.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime


class HobbitStreamGUI:
    """Main application window for the Hobbit Journey Stream GUI."""
    
    # Default config
    DEFAULT_CONFIG = {
        "pacing_mode": {"value": "dramatic"},
        "pacing": {"value": 1.0},
        "base_delay": {"value": 10000},
        "word_count_factor": {"value": 0.02},
        "min_scene_duration": {"value": 3000},
        "max_scene_duration": {"value": 60000},
        "narrative": {"style": {"value": "immersive"}, "show_narrative": {"value": True}},
        "show_countdown": {"value": True}
    }
    
    # Pacing mode descriptions
    PACING_MODES = {
        "compressed": "Complete journey in 2-3 hours",
        "dramatic": "Important scenes linger longer",
        "synced": "Match story time to your time of day",
        "realtime": "1:1 experience (6 months)"
    }
    
    # Narrative styles
    NARRATIVE_STYLES = {
        "immersive": "You are there (second-person)",
        "cinematic": "Movie-like descriptions",
        "literary": "Tolkien-esque prose",
        "minimal": "Sparse and poetic",
        "character_pov": "Character's perspective"
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Hobbit Journey Stream - Control Panel")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a2e")
        
        # Data
        self.scenes = []
        self.current_index = 0
        self.auto_play = False
        self.auto_play_job = None
        self.countdown_job = None
        
        # Check emoji support
        self.emoji_supported = self._detect_emoji_support()
        
        # Find a font that supports emojis
        self.emoji_font = self._find_emoji_font()
        
        # Narratives and beats
        self.narratives = {}
        self.beats = {}
        self.current_beat_index = 0
        self.beat_start_time = 0
        self.typing_job = None
        self.typing_text = ""
        self.typing_index = 0
        self.load_narratives()
        self.load_beats()
        
        # Config
        self.config = self.load_config()
        
        # Pacing state
        self.pacing_mode = self.config.get('pacing_mode', {}).get('value', 'dramatic')
        self.narrative_style = self.config.get('narrative', {}).get('style', {}).get('value', 'immersive')
        
        # Countdown state
        self.countdown_ms = 0
        self.current_scene_delay = 0
        
        # Colors
        self.colors = {
            'bg': "#1a1a2e",
            'panel': "#16213e",
            'accent': "#d4af37",
            'text': "#f4e4bc",
            'muted': "#8b7355",
            'canon': "#4a9",
            'generated': "#a94"
        }
        
        # Font for emoji support
        self.emoji_font = self._find_emoji_font()
        
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def load_config(self):
        """Load configuration from stream_config.json."""
        config_path = 'data/stream_config.json'
        config = dict(self.DEFAULT_CONFIG)
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                # Merge loaded values with defaults
                for key in config:
                    if key in loaded and isinstance(loaded[key], dict) and 'value' in loaded[key]:
                        config[key]['value'] = loaded[key]['value']
                        
                print(f"Loaded config: mode={config.get('pacing_mode', {}).get('value', 'dramatic')}, pacing={config['pacing']['value']}x")
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        else:
            print(f"Config file not found, using defaults")
            self.save_config(config)
            
        return config
    
    def save_config(self, config=None):
        """Save configuration to stream_config.json."""
        if config is None:
            config = self.config
        
        try:
            # Build full config with metadata
            full_config = {
                "pacing_mode": {
                    "description": "Scene display pacing mode",
                    "value": config.get('pacing_mode', {}).get('value', self.pacing_mode),
                    "options": ["compressed", "dramatic", "synced", "realtime"]
                },
                "pacing": {
                    "description": "Speed multiplier (for compressed/dramatic modes)",
                    "value": config.get('pacing', {}).get('value', 1.0),
                    "min": 0.25,
                    "max": 3.0,
                    "unit": "multiplier"
                },
                "base_delay": {
                    "description": "Base delay per scene in milliseconds",
                    "value": config.get('base_delay', {}).get('value', 10000),
                    "min": 1000,
                    "max": 60000,
                    "unit": "milliseconds"
                },
                "word_count_factor": {
                    "description": "Additional delay per word",
                    "value": config.get('word_count_factor', {}).get('value', 0.02),
                    "min": 0,
                    "max": 0.1,
                    "unit": "ms/word"
                },
                "min_scene_duration": {
                    "description": "Minimum time to display a scene",
                    "value": config.get('min_scene_duration', {}).get('value', 3000),
                    "min": 1000,
                    "max": 10000,
                    "unit": "milliseconds"
                },
                "max_scene_duration": {
                    "description": "Maximum time to display a scene",
                    "value": config.get('max_scene_duration', {}).get('value', 60000),
                    "min": 10000,
                    "max": 300000,
                    "unit": "milliseconds"
                },
                "narrative": {
                    "description": "Narrative display settings",
                    "style": {
                        "description": "Narrative style for scene descriptions",
                        "value": config.get('narrative', {}).get('style', {}).get('value', self.narrative_style),
                        "options": list(self.NARRATIVE_STYLES.keys())
                    },
                    "show_narrative": {
                        "description": "Show narrative text instead of raw content",
                        "value": config.get('narrative', {}).get('show_narrative', {}).get('value', True)
                    }
                },
                "show_countdown": {
                    "description": "Whether to show countdown timer",
                    "value": config.get('show_countdown', {}).get('value', True)
                },
                "version": "2.0.0"
            }
            
            with open('data/stream_config.json', 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def calculate_scene_delay(self, scene):
        """Calculate display delay for a scene based on config."""
        pacing = self.config['pacing']['value']
        base_delay = self.config['base_delay']['value']
        word_factor = self.config['word_count_factor']['value']
        min_duration = self.config['min_scene_duration']['value']
        max_duration = self.config['max_scene_duration']['value']
        
        word_count = scene.get('word_count', 500)
        
        # Calculate delay: (base + word_count * factor) / pacing
        delay = (base_delay + word_count * word_factor * 1000) / pacing
        
        # Clamp to min/max
        delay = max(min_duration, min(max_duration, delay))
        
        return int(delay)
        
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Hobbit.TFrame", background=self.colors['panel'])
        style.configure("Hobbit.TLabel", 
                       background=self.colors['panel'],
                       foreground=self.colors['text'],
                       font=('Cormorant Garamond', 11))
        style.configure("Hobbit.TButton",
                       background=self.colors['accent'],
                       foreground="#1a1a2e",
                       font=('Cinzel', 10, 'bold'),
                       padding=10)
        style.map("Hobbit.TButton",
                 background=[('active', '#e5c04b'), ('pressed', '#b8942e')])
        
    def create_widgets(self):
        """Create all GUI widgets."""
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_header(main_frame)
        
        content = tk.Frame(main_frame, bg=self.colors['bg'])
        content.pack(fill=tk.BOTH, expand=True, pady=10)
        content.grid_columnconfigure(0, weight=4)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        self._create_scene_panel(content, 0, 0)
        self._create_sidebar(content, 0, 1)
        self._create_control_bar(main_frame)
        
    def _create_header(self, parent):
        """Create header with title."""
        header = tk.Frame(parent, bg=self.colors['panel'], height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        tk.Label(header, text="[The Hobbit Journey Stream]",
                bg=self.colors['panel'],
                fg=self.colors['accent'],
                font=('Cinzel', 20, 'bold')).pack(side=tk.LEFT, padx=20, pady=10)
        
        self.status_label = tk.Label(header, text=f"{self._get_symbol("●", "*")} Ready",
                                    bg=self.colors['panel'],
                                    fg=self.colors['canon'],
                                    font=('Cascadia Code', 10))
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
    def _create_scene_panel(self, parent, row, col):
        """Create main scene display panel."""
        panel = tk.Frame(parent, bg=self.colors['panel'], bd=2, relief=tk.RIDGE)
        panel.grid(row=row, column=col, sticky="nsew", padx=(0, 10))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        
        # Scene image/location header
        img_frame = tk.Frame(panel, bg="#2a3f2a", height=120)
        img_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        img_frame.pack_propagate(False)
        
        self.location_icon = tk.Label(img_frame, text="[*]",
                                     bg="#2a3f2a",
                                     fg=self.colors['text'],
                                     font=('Cascadia Code', 30, 'bold'))
        self.location_icon.pack(expand=True)
        
        self.location_name = tk.Label(img_frame, text="Loading...",
                                     bg="#2a3f2a",
                                     fg=self.colors['accent'],
                                     font=('Cinzel', 14))
        self.location_name.pack()
        
        # Scene content
        content_frame = tk.Frame(panel, bg=self.colors['panel'])
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Scene title
        title_frame = tk.Frame(content_frame, bg=self.colors['panel'])
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.scene_title = tk.Label(title_frame, text="Loading Journey...",
                                   bg=self.colors['panel'],
                                   fg=self.colors['accent'],
                                   font=('Cinzel', 16, 'bold'),
                                   wraplength=700)
        self.scene_title.pack(anchor=tk.W)
        
        self.scene_subtitle = tk.Label(title_frame, text="Initializing",
                                      bg=self.colors['panel'],
                                      fg=self.colors['muted'],
                                      font=('Cormorant Garamond', 11, 'italic'))
        self.scene_subtitle.pack(anchor=tk.W)
        
        # Scene text with scrollbar
        text_container = tk.Frame(content_frame, bg=self.colors['panel'])
        text_container.grid(row=1, column=0, sticky="nsew")
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        self.scene_text = scrolledtext.ScrolledText(
            text_container,
            wrap=tk.WORD,
            bg="#0f0f1a",
            fg=self.colors['text'],
            font=('Cormorant Garamond', 13),
            padx=20,
            pady=20,
            relief=tk.FLAT,
            state=tk.DISABLED,
            height=20
        )
        self.scene_text.grid(row=0, column=0, sticky="nsew")
        
        # Type indicator and chapter info
        info_frame = tk.Frame(content_frame, bg=self.colors['panel'])
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        self.type_indicator = tk.Label(info_frame, text="CANON",
                                      bg=self.colors['canon'],
                                      fg="white",
                                      font=('Cascadia Code', 9, 'bold'),
                                      padx=10,
                                      pady=3)
        self.type_indicator.pack(side=tk.LEFT)
        
        self.chapter_label = tk.Label(info_frame, text="",
                                     bg=self.colors['panel'],
                                     fg=self.colors['muted'],
                                     font=('Cinzel', 10))
        self.chapter_label.pack(side=tk.LEFT, padx=(15, 0))
        
        self.word_count_label = tk.Label(info_frame, text="",
                                        bg=self.colors['panel'],
                                        fg=self.colors['muted'],
                                        font=('Cascadia Code', 9))
        self.word_count_label.pack(side=tk.RIGHT)
        
        # Progress bars frame
        progress_frame = tk.Frame(content_frame, bg=self.colors['panel'])
        progress_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        
        # Scene progress bar
        scene_progress_label = tk.Label(progress_frame, text="Scene:",
                                       bg=self.colors['panel'],
                                       fg=self.colors['muted'],
                                       font=('Cascadia Code', 8))
        scene_progress_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.scene_progress = tk.Frame(progress_frame, bg=self.colors['panel'])
        self.scene_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.scene_progress_bar = tk.Canvas(self.scene_progress, 
                                           height=8, 
                                           bg=self.colors['bg'],
                                           highlightthickness=0)
        self.scene_progress_bar.pack(fill=tk.X, expand=True)
        
        # Beat progress bar
        beat_progress_label = tk.Label(progress_frame, text="Beat:",
                                      bg=self.colors['panel'],
                                      fg=self.colors['muted'],
                                      font=('Cascadia Code', 8))
        beat_progress_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.beat_progress = tk.Frame(progress_frame, bg=self.colors['panel'])
        self.beat_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.beat_progress_bar = tk.Canvas(self.beat_progress,
                                          height=8,
                                          bg=self.colors['bg'],
                                          highlightthickness=0)
        self.beat_progress_bar.pack(fill=tk.X, expand=True)
        
    def _create_sidebar(self, parent, row, col):
        """Create right sidebar with info panels - fixed width."""
        sidebar = tk.Frame(parent, bg=self.colors['bg'], width=280)
        sidebar.grid(row=row, column=col, sticky="ns")
        sidebar.grid_propagate(False)  # Prevent resizing
        sidebar.grid_rowconfigure(0, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)
        
        self._create_journey_info_panel(sidebar)
        self._create_characters_panel(sidebar)
        self._create_countdown_panel(sidebar)
        
    def _create_journey_info_panel(self, parent):
        """Create journey info panel."""
        # Use emoji font if available, otherwise Cinzel
        label_font = (self.emoji_font, 11) if self.emoji_font else ('Cinzel', 11)
        panel = tk.LabelFrame(parent, text=f" {self._get_symbol("📊", "[Stats]")} Journey Info ",
                             bg=self.colors['panel'],
                             fg=self.colors['accent'],
                             font=label_font,
                             padx=10, pady=10)
        panel.pack(fill=tk.X, pady=(0, 10))
        
        info_grid = tk.Frame(panel, bg=self.colors['panel'])
        info_grid.pack(fill=tk.X)
        
        labels = [
            ("Day:", "journey_day", "-"),
            ("Date:", "date", "-"),
            ("Time:", "time", "-"),
            ("Location:", "location", "-"),
            ("Duration:", "duration", "-"),
            ("Mode:", "mode", "-"),
            ("Style:", "style", "-")
        ]
        
        self.info_vars = {}
        for label, key, default in labels:
            row_frame = tk.Frame(info_grid, bg=self.colors['panel'])
            row_frame.pack(fill=tk.X, pady=3)
            
            tk.Label(row_frame, text=label,
                    bg=self.colors['panel'],
                    fg=self.colors['muted'],
                    font=('Cascadia Code', 9),
                    width=10,
                    anchor=tk.W).pack(side=tk.LEFT)
            
            var = tk.StringVar(value=default)
            self.info_vars[key] = var
            tk.Label(row_frame, textvariable=var,
                    bg=self.colors['panel'],
                    fg=self.colors['text'],
                    font=('Cinzel', 11),
                    wraplength=200).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
    def _create_characters_panel(self, parent):
        """Create characters panel."""
        label_font = (self.emoji_font, 11) if self.emoji_font else ('Cinzel', 11)
        panel = tk.LabelFrame(parent, text=f" {self._get_symbol("👥", "[Group]")} Present ",
                             bg=self.colors['panel'],
                             fg=self.colors['accent'],
                             font=label_font,
                             padx=10, pady=10)
        panel.pack(fill=tk.X, pady=(0, 10))
        
        self.characters_frame = tk.Frame(panel, bg=self.colors['panel'])
        self.characters_frame.pack(fill=tk.X)
        
        tk.Label(self.characters_frame, text="Loading...",
                bg=self.colors['panel'],
                fg=self.colors['muted'],
                font=('Cormorant Garamond', 11)).pack()
        
    def _create_countdown_panel(self, parent):
        """Create countdown panel."""
        label_font = (self.emoji_font, 11) if self.emoji_font else ('Cinzel', 11)
        panel = tk.LabelFrame(parent, text=f" {self._get_symbol("⏱️", "[T]")} Next Events ",
                             bg=self.colors['panel'],
                             fg=self.colors['accent'],
                             font=label_font,
                             padx=10, pady=10)
        panel.pack(fill=tk.X)
        
        self.countdown_text = tk.Label(panel, text="-",
                                      bg=self.colors['panel'],
                                      fg=self.colors['text'],
                                      font=('Cormorant Garamond', 11),
                                      wraplength=220,
                                      justify=tk.LEFT)
        self.countdown_text.pack(fill=tk.X, anchor=tk.W)
        
    def _create_control_bar(self, parent):
        """Create bottom control bar."""
        bar = tk.Frame(parent, bg=self.colors['panel'], height=90)
        bar.pack(fill=tk.X, pady=(10, 0))
        bar.pack_propagate(False)
        
        # HUD info
        hud_frame = tk.Frame(bar, bg=self.colors['panel'])
        hud_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.hud_items = {}
        hud_data = [
            (self._get_symbol("📅", "[Date]"), "In-Story Date", "hud_date", "April 26, 2941"),
            (self._get_symbol("🌄", "[Sun]"), "Time of Day", "hud_time", "Morning"),
            (self._get_symbol("📍", "[Loc]"), "Location", "hud_location", "Hobbiton"),
            (self._get_symbol("🎯", "[Target]"), "Next Event", "hud_next", "-")
        ]
        
        for icon, label, key, default in hud_data:
            item = tk.Frame(hud_frame, bg=self.colors['panel'])
            item.pack(side=tk.LEFT, padx=15)
            
            # Use emoji font for icon, fallback to default
            icon_font = (self.emoji_font, 18) if self.emoji_font else ('TkDefaultFont', 18)
            tk.Label(item, text=icon,
                    bg=self.colors['panel'],
                    fg=self.colors['text'],
                    font=icon_font).pack()
            
            text_frame = tk.Frame(item, bg=self.colors['panel'])
            text_frame.pack()
            
            tk.Label(text_frame, text=label,
                    bg=self.colors['panel'],
                    fg=self.colors['muted'],
                    font=('Cascadia Code', 8)).pack(anchor=tk.W)
            
            var = tk.StringVar(value=default)
            self.hud_items[key] = var
            tk.Label(text_frame, textvariable=var,
                    bg=self.colors['panel'],
                    fg=self.colors['text'],
                    font=('Cinzel', 10, 'bold'),
                    wraplength=150).pack(anchor=tk.W)
        
        # Control buttons
        btn_frame = tk.Frame(bar, bg=self.colors['panel'])
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Use emoji font for buttons with symbols
        btn_font = (self.emoji_font, 14, 'bold') if self.emoji_font else ('Cinzel', 14, 'bold')
        
        self.prev_btn = tk.Button(btn_frame, text=self._get_symbol("◀", "<"),
                                 bg=self.colors['panel'],
                                 fg=self.colors['accent'],
                                 font=btn_font,
                                 width=4,
                                 command=self.prev_scene,
                                 relief=tk.RIDGE,
                                 bd=2)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = tk.Button(btn_frame, text=self._get_symbol("▶", ">"),
                                 bg=self.colors['accent'],
                                 fg="#1a1a2e",
                                 font=btn_font,
                                 width=4,
                                 command=self.toggle_auto_play,
                                 relief=tk.RIDGE,
                                 bd=2)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(btn_frame, text=self._get_symbol("▶", ">"),
                                 bg=self.colors['panel'],
                                 fg=self.colors['accent'],
                                 font=btn_font,
                                 width=4,
                                 command=self.next_scene,
                                 relief=tk.RIDGE,
                                 bd=2)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Scene counter
        self.counter_label = tk.Label(bar, text="1 / 111",
                                     bg=self.colors['panel'],
                                     fg=self.colors['accent'],
                                     font=('Cascadia Code', 12))
        self.counter_label.pack(side=tk.RIGHT, padx=20)
        
        # Countdown timer (using ASCII for compatibility)
        self.countdown_label = tk.Label(bar, text="[--:--:--:--]",
                                       bg=self.colors['panel'],
                                       fg=self.colors['text'],
                                       font=('Cascadia Code', 14, 'bold'))
        self.countdown_label.pack(side=tk.RIGHT, padx=20)
        
        # Pacing control
        self._create_pacing_control(bar)
        
    def load_narratives(self):
        """Load pre-generated narrative content."""
        if os.path.exists('data/scene_narratives.json'):
            try:
                with open('data/scene_narratives.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.narratives = data.get('scenes', {})
                print(f"Loaded {len(self.narratives)} scene narratives")
            except Exception as e:
                print(f"Error loading narratives: {e}")
                self.narratives = {}
        else:
            print("No scene_narratives.json found")
            self.narratives = {}
    
    def load_beats(self):
        """Load narrative beats for progressive display."""
        if os.path.exists('data/scene_beats.json'):
            try:
                with open('data/scene_beats.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.beats = data.get('scenes', {})
                print(f"Loaded {len(self.beats)} scene beats")
            except Exception as e:
                print(f"Error loading beats: {e}")
                self.beats = {}
        else:
            print("No scene_beats.json found - beats disabled")
            self.beats = {}
    
    def get_scene_narrative(self, scene, style=None):
        """Get narrative text for a scene in the specified style."""
        if style is None:
            style = self.narrative_style
        
        scene_id = scene.get('id', '')
        
        # Try to get from pre-generated narratives
        if scene_id and scene_id in self.narratives:
            styles = self.narratives[scene_id].get('styles', {})
            if style in styles:
                return styles[style].get('text', scene.get('content', ''))
        
        # Fallback to original content
        return scene.get('content', scene.get('summary', 'No content'))
    
    def get_progressive_content(self, scene, scene_id):
        """Get content with progressive beat display.
        
        Shows the current beat based on elapsed time within the scene.
        """
        if not self.beats or scene_id not in self.beats:
            # Fallback to standard content if no beats
            return scene.get('content', scene.get('summary', 'No content'))
        
        scene_beats = self.beats[scene_id]
        beats = scene_beats.get('beats', [])
        
        if not beats:
            return scene.get('content', scene.get('summary', 'No content'))
        
        # Calculate elapsed percentage
        if self.auto_play and self.current_scene_delay > 0:
            elapsed = self.current_scene_delay - self.countdown_ms
            elapsed_pct = min(1.0, elapsed / self.current_scene_delay)
        else:
            elapsed_pct = 0.0
        
        # Find current beat
        current_beat = None
        beat_index = 0
        for i, beat in enumerate(beats):
            if beat['start'] <= elapsed_pct < beat['end']:
                current_beat = beat
                beat_index = i
                break
        
        if current_beat is None:
            current_beat = beats[-1]
            beat_index = len(beats) - 1
        
        # Build display
        is_canon = scene.get('is_canonical', not scene.get('parent_gap_id'))
        
        lines = []
        
        # Header showing progress
        beat_num = beat_index + 1
        total_beats = len(beats)
        elapsed_min = int(elapsed_pct * 100)
        
        lines.append(f"[BEAT {beat_num}/{total_beats}]")
        lines.append("")
        
        # Show revealed beats (current and previous)
        for i in range(beat_index + 1):
            beat = beats[i]
            prefix = ">>>" if i == beat_index else "   "
            lines.append(f"{prefix} {beat['text']}")
        
        # If not at end, hint at continuation
        if beat_index < total_beats - 1:
            lines.append("")
            lines.append(f"[{total_beats - beat_index - 1} more beats to reveal...]")
        
        return '\n'.join(lines)
    
    def update_beat_display(self, force=False):
        """Update display to show current beat during auto-play.
        
        Args:
            force: If True, update regardless of whether beat changed
        """
        if not self.scenes:
            return
        
        scene = self.scenes[self.current_index]
        scene_id = scene.get('id', f'scene_{self.current_index:03d}')
        
        if scene_id not in self.beats:
            return
        
        # Calculate current beat based on elapsed time
        scene_beats = self.beats[scene_id].get('beats', [])
        if not scene_beats:
            return
        
        if self.current_scene_delay > 0:
            elapsed = self.current_scene_delay - self.countdown_ms
            elapsed_pct = min(1.0, elapsed / self.current_scene_delay)
        else:
            elapsed_pct = 0.0
        
        # Find current beat index
        current_beat_idx = 0
        for i, beat in enumerate(scene_beats):
            if beat['start'] <= elapsed_pct < beat['end']:
                current_beat_idx = i
                break
            elif elapsed_pct >= beat['end']:
                current_beat_idx = i
        
        # Only update text if beat changed or forced
        if force or current_beat_idx != getattr(self, '_last_beat_idx', -1):
            self._last_beat_idx = current_beat_idx
            
            # Build content with typing animation for new beat
            self._start_typing_animation(scene, scene_id, current_beat_idx)
    
    def _start_typing_animation(self, scene, scene_id, current_beat_idx):
        """Start typing animation for the current beat.
        
        Shows previous beats instantly, types out the current beat.
        """
        # Cancel any existing typing animation
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
        
        scene_beats = self.beats[scene_id]['beats']
        beats = scene_beats
        total_beats = len(beats)
        
        # Calculate elapsed percentage for header
        if self.auto_play and self.current_scene_delay > 0:
            elapsed = self.current_scene_delay - self.countdown_ms
            elapsed_pct = min(1.0, elapsed / self.current_scene_delay)
        else:
            elapsed_pct = 0.0
        elapsed_min = int(elapsed_pct * 100)
        
        # Build the static part (header + previous beats)
        static_lines = []
        static_lines.append(f"[BEAT {current_beat_idx + 1}/{total_beats}]")
        static_lines.append("")
        
        # Add previous beats (fully visible)
        for i in range(current_beat_idx):
            beat = beats[i]
            static_lines.append(f"    {beat['text']}")
        
        self.typing_static_content = '\n'.join(static_lines)
        
        # Get the current beat text to type
        current_beat = beats[current_beat_idx]
        self.typing_beat_text = f">>> {current_beat['text']}"
        
        # Add continuation hint if not last beat
        if current_beat_idx < total_beats - 1:
            self.typing_suffix = f"\n\n[{total_beats - current_beat_idx - 1} more beats to reveal...]"
        else:
            self.typing_suffix = ""
        
        # Start typing animation
        self.typing_index = 0
        self._type_next_char()
    
    def _type_next_char(self):
        """Type the next character of the current beat.
        
        Typing speed: 20ms per character (~50 chars/sec)
        Fast enough to complete long beats within scene timing, still readable.
        """
        if not hasattr(self, 'typing_static_content') or not hasattr(self, 'typing_beat_text'):
            return
        
        # Build current display
        typed_portion = self.typing_beat_text[:self.typing_index]
        display_text = self.typing_static_content + '\n' + typed_portion + self.typing_suffix
        
        # Update text widget
        self.scene_text.config(state=tk.NORMAL)
        self.scene_text.delete(1.0, tk.END)
        self.scene_text.insert(1.0, display_text)
        self.scene_text.config(state=tk.DISABLED)
        
        # Continue typing if more characters remain
        if self.typing_index < len(self.typing_beat_text):
            self.typing_index += 1
            # 20ms per char = ~50 chars/sec
            self.typing_job = self.root.after(20, self._type_next_char)
        else:
            self.typing_job = None
    
    def calculate_scene_delay(self, scene):
        """Calculate display delay based on pacing mode and config."""
        mode = self.pacing_mode
        
        if mode == "realtime":
            # 1 hour story time = 1 hour real time
            # Get story duration in hours
            duration_hours = 1  # default
            if 'story_duration' in scene:
                sd = scene['story_duration']
                dur = sd.get('duration', 1)
                unit = sd.get('unit', 'hours')
                if unit == 'days':
                    duration_hours = dur * 24 * 60 * 60 * 1000  # Convert to ms
                elif unit == 'minutes':
                    duration_hours = dur * 60 * 1000
                else:
                    duration_hours = dur * 60 * 60 * 1000
            elif 'duration_hours' in scene:
                duration_hours = scene['duration_hours'] * 60 * 60 * 1000
            else:
                duration_hours = 60 * 60 * 1000  # 1 hour default
            return int(duration_hours)
            
        elif mode == "synced":
            # Calculate delay to sync story time with real-world time
            scene_date = scene.get('date', '')
            scene_time = scene.get('time', '')
            
            if scene_date and scene_time:
                target_datetime = self._parse_scene_datetime(scene_date, scene_time)
                if target_datetime:
                    now = datetime.now()
                    # Calculate difference to sync
                    diff_seconds = (target_datetime - now).total_seconds()
                    if diff_seconds > 0:
                        # Scale down significantly (6 months -> 24 hours)
                        scaled_ms = (diff_seconds / (180 * 24 * 3600)) * (24 * 3600 * 1000)
                        return max(5000, min(60000, int(scaled_ms)))
            
            # Fallback to dramatic mode
            return self._calculate_dramatic_delay(scene)
            
        elif mode == "dramatic":
            return self._calculate_dramatic_delay(scene)
            
        else:  # compressed (default)
            return self._calculate_compressed_delay(scene)
    
    def _parse_scene_datetime(self, date_str, time_str):
        """Parse scene date/time into datetime object for today."""
        try:
            # Extract time from time_str (e.g., "Late Morning" -> 10:00)
            time_map = {
                'dawn': 6, 'morning': 8, 'late morning': 10, 'noon': 12,
                'afternoon': 14, 'late afternoon': 16, 'evening': 18,
                'dusk': 19, 'night': 22, 'midnight': 0
            }
            
            hour = 12  # default
            time_lower = time_str.lower()
            for key, val in time_map.items():
                if key in time_lower:
                    hour = val
                    break
            
            # Return datetime for today with that hour
            now = datetime.now()
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)
        except:
            return None
    
    def _calculate_dramatic_delay(self, scene):
        """Calculate delay based on narrative importance (dramatic pacing)."""
        pacing = self.config['pacing']['value']
        base = self.config['base_delay']['value']
        word_factor = self.config['word_count_factor']['value']
        min_dur = self.config['min_scene_duration']['value']
        max_dur = self.config['max_scene_duration']['value']
        
        word_count = scene.get('word_count', 500)
        
        # Base delay
        delay = (base + word_count * word_factor * 1000) / pacing
        
        # Apply importance multipliers
        importance = self._calculate_importance(scene)
        delay = delay * (0.5 + importance)  # 0.5x to 1.5x based on importance
        
        # Gap type adjustments
        gap_type = scene.get('gap_type', '')
        if gap_type == 'travel':
            delay *= 0.6  # Travel scenes: faster
        elif gap_type == 'recuperation':
            delay *= 0.8  # Rest scenes: slightly faster
        
        return int(max(min_dur, min(max_dur, delay)))
    
    def _calculate_compressed_delay(self, scene):
        """Calculate delay for compressed mode (fastest)."""
        pacing = self.config['pacing']['value']
        base = self.config['base_delay']['value']
        word_factor = self.config['word_count_factor']['value']
        min_dur = self.config['min_scene_duration']['value']
        max_dur = self.config['max_scene_duration']['value']
        
        word_count = scene.get('word_count', 500)
        delay = (base + word_count * word_factor * 1000) / pacing
        
        return int(max(min_dur, min(max_dur, delay)))
    
    def _calculate_importance(self, scene):
        """Calculate narrative importance score (0-1)."""
        score = 0.5  # baseline
        
        # Canonical scenes are more important
        if scene.get('is_canonical'):
            score += 0.2
        
        # Title keywords indicate importance
        title = scene.get('title', '').lower()
        important_keywords = ['smaug', 'battle', 'death', 'escape', 'dragon', 
                            'gollum', 'eagles', 'treasure', 'arkenstone']
        for keyword in important_keywords:
            if keyword in title:
                score += 0.15
                break
        
        # Character density
        chars = scene.get('characters', [])
        if len(chars) >= 10:
            score += 0.1  # Large group scenes
        elif len(chars) <= 2:
            score += 0.05  # Intimate scenes
        
        # Dialogue indicator (rough heuristic)
        content = scene.get('content', '')
        if '"' in content or '"' in content:
            score += 0.1  # Has dialogue
        
        return min(1.0, score)
    
    def load_data(self):
        """Load scene data from stream_scenes.json and generated_gap_scenes.json."""
        canonical_scenes = []
        generated_scenes = []
        
        # Load canonical scenes
        if os.path.exists('data/stream_scenes.json'):
            try:
                with open('data/stream_scenes.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'scenes' in data:
                    canonical_scenes = data['scenes']
                    print(f"Loaded {len(canonical_scenes)} canonical scenes from stream_scenes.json")
                else:
                    canonical_scenes = data
                    print(f"Loaded {len(canonical_scenes)} scenes (legacy format)")
                    
            except Exception as e:
                print(f"Error loading stream_scenes.json: {e}")
                self.load_sample_data()
                return
        else:
            print("stream_scenes.json not found, using sample data")
            self.load_sample_data()
            return
        
        # Load generated gap scenes
        if os.path.exists('data/generated_gap_scenes.json'):
            try:
                with open('data/generated_gap_scenes.json', 'r', encoding='utf-8') as f:
                    gap_data = json.load(f)
                
                if 'generated_scenes' in gap_data:
                    generated_scenes = gap_data['generated_scenes']
                    print(f"Loaded {len(generated_scenes)} generated gap scenes")
                else:
                    print("No generated_scenes found in generated_gap_scenes.json")
                    
            except Exception as e:
                print(f"Error loading generated_gap_scenes.json: {e}")
        
        # Merge scenes in correct order
        self.scenes = self._merge_scenes(canonical_scenes, generated_scenes)
        print(f"Total scenes after merging: {len(self.scenes)}")
        
        if self.scenes:
            self.update_display()
    
    def _merge_scenes(self, canonical, generated):
        """Merge canonical and generated scenes in correct chronological order."""
        # Create a map of generated scenes by their parent gap
        generated_by_gap = {}
        for scene in generated:
            gap_id = scene.get('parent_gap_id', '')
            if gap_id not in generated_by_gap:
                generated_by_gap[gap_id] = []
            generated_by_gap[gap_id].append(scene)
        
        # Sort generated scenes within each gap by position (numerically)
        def parse_position(pos):
            """Parse position string like '1/10' into tuple (1, 10) for numeric sort."""
            if not pos:
                return (1, 1)
            try:
                parts = str(pos).split('/')
                return (int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                return (1, 1)
        
        for gap_id in generated_by_gap:
            generated_by_gap[gap_id].sort(
                key=lambda s: parse_position(s.get('position_in_gap', '1/1'))
            )
        
        # Build a map from canonical ID to index for gap lookup
        canon_id_to_index = {}
        for i, scene in enumerate(canonical):
            canon_id_to_index[scene.get('id', f'canon_{i+1:03d}')] = i
        
        # Also load gap metadata to find where each gap should be inserted
        gap_insert_positions = {}
        if os.path.exists('data/generated_gap_scenes.json'):
            try:
                with open('data/generated_gap_scenes.json', 'r', encoding='utf-8') as f:
                    gap_data = json.load(f)
                for gap in gap_data.get('gaps', []):
                    from_id = gap.get('from_scene', {}).get('id', '')
                    if from_id in canon_id_to_index:
                        gap_insert_positions[gap['gap_id']] = canon_id_to_index[from_id]
            except Exception:
                pass
        
        # Build merged list
        merged = []
        
        for i, canon_scene in enumerate(canonical):
            merged.append(canon_scene)
            
            # Find any gaps that should be inserted after this scene
            for gap_id, insert_pos in gap_insert_positions.items():
                if insert_pos == i and gap_id in generated_by_gap:
                    for gen_scene in generated_by_gap[gap_id]:
                        # Normalize generated scene to match canonical format
                        normalized = self._normalize_generated_scene(gen_scene)
                        merged.append(normalized)
        
        return merged
    
    def _normalize_generated_scene(self, scene):
        """Normalize generated scene to match canonical scene format."""
        normalized = dict(scene)  # Copy original
        
        # Mark as non-canonical
        normalized['is_canonical'] = False
        normalized['is_generated'] = True
        
        # Convert content/summary fields to match canonical format
        if 'summary' in scene and 'content' not in scene:
            normalized['content'] = scene['summary']
        
        # Ensure chapter field exists (use gap type as pseudo-chapter)
        if 'chapter' not in scene:
            gap_type = scene.get('gap_type', 'gap').title()
            normalized['chapter'] = f"Generated ({gap_type})"
        
        # Convert duration_hours to word_count estimate (roughly 150 words/hour)
        if 'duration_hours' in scene and 'word_count' not in scene:
            normalized['word_count'] = int(scene['duration_hours'] * 150)
        
        # Ensure time field exists
        if 'time' not in scene:
            normalized['time'] = 'Unknown'
        if 'time_icon' not in scene:
            normalized['time_icon'] = '*'
        
        # Ensure journey_day exists (extract from date if possible)
        if 'journey_day' not in scene and 'date' in scene:
            # Try to find journey_day from canonical scenes with same date
            normalized['journey_day'] = '-'
        
        # Add progress info
        normalized['progress'] = {
            'current': -1,  # Will be set after merge
            'total': -1
        }
        
        return normalized
    
    def _detect_emoji_support(self):
        """Detect if the system can display emojis properly.
        
        Returns:
            True if emojis are supported, False otherwise
        """
        try:
            # Create a hidden test label
            test = tk.Label(self.root, text="⏱️", font=('TkDefaultFont', 12))
            test.update_idletasks()
            
            # Check if text was set properly
            text = test.cget('text')
            test.destroy()
            
            # If we got the emoji back (not empty or garbled), it's supported
            return len(text) > 0 and ord(text[0]) > 127
        except Exception:
            return False
    
    def _find_emoji_font(self):
        """Find a font that supports emojis.
        
        Returns:
            Font family name or None
        """
        try:
            from tkinter import font as tkfont
            available = tkfont.families()
            
            # Priority order for emoji fonts
            emoji_fonts = [
                'Noto Color Emoji',     # Linux
                'Segoe UI Emoji',       # Windows 10+
                'Apple Color Emoji',    # macOS
                'EmojiOne',             # Open source
                'Twitter Color Emoji',  # Open source
                'Symbola',              # Fallback - black and white emoji
            ]
            
            for font_name in emoji_fonts:
                if font_name in available:
                    print(f"Found emoji font: {font_name}")
                    return font_name
            
            # Try 'standard symbols l' which might be Symbola
            if 'standard symbols l' in available:
                print("Found emoji font: standard symbols l")
                return 'standard symbols l'
            if 'symbol' in available:
                print("Found emoji font: symbol")
                return 'symbol'
            
            # Try generic sans-serif as fallback
            return 'sans-serif'
        except Exception as e:
            print(f"Font detection error: {e}")
            return None
    
    def _get_symbol(self, emoji, ascii_alt):
        """Get emoji or ASCII alternative based on system support.
        
        Args:
            emoji: The emoji character to use if supported
            ascii_alt: ASCII alternative if emojis not supported
        
        Returns:
            Emoji or ASCII string
        """
        return emoji if self.emoji_supported else ascii_alt
    
    def _emoji_to_ascii(self, emoji_text, default='?'):
        """Convert emoji to ASCII symbol, handling variation selectors.
        
        Args:
            emoji_text: The emoji string (may contain variation selectors)
            default: Default character if emoji not recognized
        
        Returns:
            ASCII character representing the emoji
        """
        if not emoji_text:
            return default
        
        # Remove variation selectors (U+FE0F) and other combining marks
        cleaned = emoji_text.strip()
        cleaned = cleaned.replace('\ufe0f', '')  # Remove variation selector-16
        
        # Mapping of emojis to ASCII symbols
        emoji_map = {
            # Time of day
            '~': '~', '~': '~',  # Late morning
            '*': '*', '*': '*',  # Noon/day
            'v': 'v',  # Late afternoon/sunset  
            self._get_symbol('🌄', '^'): '^',  # Morning
            'o': 'o',  # Night/crescent moon
            '@': '@',  # New moon
            'v': 'v',  # City at dusk
            '+': '+', '*': '*',
            'O': 'O',
            '!': '!', '#': '#', '~': '~',
            # Locations
            'T': 'T', 'T': 'T',  # Forest/trees
            'A': 'A',  # Lake-town
            'D': 'D', 'D': 'D',  # Dragon
            'X': 'X',  # Trolls
            '8': '8', '%': '%',  # Spiders
            'B': 'B',  # Beorn
            'E': 'E',  # Eagles
            'n': 'n', 'n': 'n',  # Houses
            'H': 'H',  # Rivendell
            'M': 'M', 'M': 'M',  # Mountains
            'S': 'S',  # Boats
            'd': 'd',  # Deer/animals
            '$': '$',  # Treasure
            'X': 'X', '/': '/',  # Weapons
            'O': 'O',  # Shield
            'm': 'm',  # Map
            'A': 'A',  # Camp
            'K': 'K',  # King
            'b': 'b', 'B': 'B',  # Birds/butterflies
        }
        
        # Try to match the cleaned emoji
        return emoji_map.get(cleaned, default)
    
    def _format_countdown(self, ms):
        """Format milliseconds as DD:HH:MM:SS."""
        total_seconds = ms // 1000
        
        days = total_seconds // 86400
        remaining = total_seconds % 86400
        
        hours = remaining // 3600
        remaining = remaining % 3600
        
        minutes = remaining // 60
        seconds = remaining % 60
        
        if days > 0:
            return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def load_sample_data(self):
        """Load sample scenes for testing."""
        self.scenes = [
            {
                "title": "The Unexpected Party Begins",
                "chapter": "An Unexpected Party",
                "content": "In a hole in the ground there lived a hobbit...",
                "location": "Hobbiton",
                "date": "April 26, 2941",
                "time": "Morning",
                "time_icon": "^",
                "journey_day": 1,
                "characters": ["Bilbo", "Gandalf"],
                "is_canonical": True,
                "word_count": 916,
                "progress": {"current": 1, "total": 111}
            }
        ]
        
    def update_display(self):
        """Update all display elements with current scene."""
        if not self.scenes:
            return
        
        # Initialize beat tracking if needed
        if not hasattr(self, '_last_beat_idx'):
            self._last_beat_idx = -1
            
        scene = self.scenes[self.current_index]
        
        # Get scene data with fallbacks
        title = scene.get('title', 'Untitled')
        chapter = scene.get('chapter', '')
        
        # Get scene metadata
        scene_id = scene.get('id', f'scene_{self.current_index:03d}')
        is_canon = scene.get('is_canonical', not scene.get('parent_gap_id'))
        location = scene.get('location', 'Unknown')
        date = scene.get('date', '-')
        time = scene.get('time', '-')
        time_icon = scene.get('time_icon', '*')
        journey_day = scene.get('journey_day', '-')
        word_count = scene.get('word_count', 0)
        gap_type = scene.get('gap_type', '')
        activity_type = scene.get('activity_type', '')
        canon_level = scene.get('canon_level', '')
        
        # Build display content using progressive beats
        content = self.get_progressive_content(scene, scene_id)
        
        # Update scene content
        self.scene_title.config(text=title)
        
        # Subtitle shows chapter or type
        if chapter:
            self.scene_subtitle.config(text=f"Chapter: {chapter}")
        else:
            scene_type = scene.get('scene_type', 'Generated')
            self.scene_subtitle.config(text=f"Type: {scene_type.title()}")
        
        # Update type indicator
        if is_canon:
            self.type_indicator.config(text="CANON", bg=self.colors['canon'])
            self.scene_subtitle.config(fg=self.colors['canon'])
        else:
            # Show canon level for generated scenes
            level_text = f" [{canon_level}]" if canon_level else ""
            self.type_indicator.config(text=f"GEN{level_text}", bg=self.colors['generated'])
            self.scene_subtitle.config(fg=self.colors['generated'])
            
        # Update text
        self.scene_text.config(state=tk.NORMAL)
        self.scene_text.delete(1.0, tk.END)
        self.scene_text.insert(1.0, content)
        self.scene_text.config(state=tk.DISABLED)
        self.scene_text.see(1.0)  # Scroll to top
        
        # Update progress bars
        self.update_progress_bars()
        
        # Update chapter and word count
        if is_canon:
            self.chapter_label.config(text=chapter if chapter else "Unknown")
        else:
            # For generated scenes, show gap type and activity
            display_chapter = chapter
            if activity_type:
                display_chapter = f"{chapter} - {activity_type}"
            self.chapter_label.config(text=display_chapter if display_chapter else "Generated Scene")
        
        self.word_count_label.config(text=f"{word_count:,} words")
        
        # Update location
        self.location_name.config(text=location)
        self.hud_items['hud_location'].set(location)
        
        # Update icon based on location
        loc_lower = location.lower()
        icon = 'm'
        for key, val in [
            ('shire', 'n'), ('hobbiton', 'n'), ('bag end', 'n'),
            ('rivendell', 'H'), ('elrond', 'H'),
            ('mountain', 'M'), ('misty', 'M'), ('goblin', 'O'),
            ('mirkwood', 'T'), ('forest', 'T'), ('wood', 'T'),
            ('lake', '~'), ('town', 'A'), ('esgaroth', 'A'),
            ('dale', 'H'), ('erebor', 'M'), ('dragon', 'D'),
            ('beorn', 'B'), ('troll', 'X'), ('spider', '8'),
        ]:
            if key in loc_lower:
                icon = val
                break
        self.location_icon.config(text=icon)
        
        # Update info panel
        self.info_vars['journey_day'].set(str(journey_day))
        self.info_vars['date'].set(date)
        self.info_vars['mode'].set(self.pacing_mode)
        self.info_vars['style'].set(self.narrative_style)
        # Convert emoji time_icon to ASCII symbol
        time_symbol = self._emoji_to_ascii(time_icon, '>')
        self.info_vars['time'].set(f"[{time_symbol}] {time}")
        self.info_vars['location'].set(location)
        
        # Update story duration
        duration_info = scene.get('story_duration', {})
        if duration_info:
            duration_display = scene.get('story_duration_display', 'Unknown')
            self.info_vars['duration'].set(duration_display)
        elif 'duration_hours' in scene:
            # For generated scenes with duration_hours
            hours = scene['duration_hours']
            self.info_vars['duration'].set(f"~{hours} hours")
        else:
            self.info_vars['duration'].set('~' + str(word_count // 500 + 1) + ' hours')
        
        # Update characters
        for widget in self.characters_frame.winfo_children():
            widget.destroy()
            
        chars = scene.get('characters', [])
        if chars:
            for char in chars[:12]:  # Limit display
                is_leader = char in ['Thorin', 'Gandalf', 'Bilbo']
                tag = tk.Label(self.characters_frame, text=char,
                              bg=self.colors['panel'],
                              fg=self.colors['accent'] if is_leader else self.colors['text'],
                              font=('Cinzel', 9, 'bold' if is_leader else 'normal'),
                              padx=8, pady=2,
                              relief=tk.RIDGE,
                              bd=1)
                tag.pack(side=tk.LEFT, padx=2, pady=2)
        else:
            tk.Label(self.characters_frame, text="None specified",
                    bg=self.colors['panel'],
                    fg=self.colors['muted'],
                    font=('Cormorant Garamond', 10, 'italic')).pack()
            
        # Update countdown / next events panel
        if is_canon:
            next_canon = scene.get('next_canonical')
            if next_canon:
                next_event = next_canon.get('next_event', 'Unknown')
                scenes_until = next_canon.get('scenes_until', 0)
                upcoming = next_canon.get('upcoming_events', [])
                
                # Add story time info
                duration_display = scene.get('story_duration_display', 'Unknown')
                method = scene.get('story_duration', {}).get('method', 'estimated')
                certainty = "OK" if method == 'explicit' else "~"
                
                text = f"[T] This scene: {certainty} {duration_display}\n\n"
                text += f"Next: {next_event}"
                if scenes_until > 1:
                    text += f"\n({scenes_until} scenes)"
                if len(upcoming) > 1:
                    text += f"\n\nUpcoming:\n" + "\n".join(f"* {e}" for e in upcoming[1:3])
                
                self.countdown_text.config(text=text)
                self.hud_items['hud_next'].set(next_event[:20])
            else:
                self.countdown_text.config(text="End of journey")
                self.hud_items['hud_next'].set("-")
        else:
            # For generated scenes - show canon basis and continuity info
            text = "[ Generated Scene ]\n\n"
            if canon_level:
                text += f"Canon Level: {canon_level}\n"
            if gap_type:
                text += f"Gap Type: {gap_type}\n"
            if 'validation_passed' in scene:
                status = "OK Passed" if scene['validation_passed'] else "! Issues"
                text += f"\nValidation: {status}"
            if 'continuity_checks' in scene:
                checks = scene['continuity_checks']
                issues = [k for k, v in checks.items() if 'FAIL' in str(v) or 'WARNING' in str(v)]
                if issues:
                    text += f"\n\nWarnings:\n" + "\n".join(f"* {i}" for i in issues[:3])
            
            self.countdown_text.config(text=text)
            
            # Find next canonical scene
            next_canon_title = "Unknown"
            for s in self.scenes[self.current_index+1:]:
                if s.get('is_canonical'):
                    next_canon_title = s.get('title', 'Unknown')
                    break
            self.hud_items['hud_next'].set(next_canon_title[:20])
            
        # Update HUD
        self.hud_items['hud_date'].set(date)
        time_symbol_hud = self._emoji_to_ascii(time_icon, '>')
        self.hud_items['hud_time'].set(f"[{time_symbol_hud}] {time}")
        
        # Update counter
        total = len(self.scenes)
        self.counter_label.config(text=f"{self.current_index + 1} / {total}")
        
        # Update button states
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < total - 1 else tk.DISABLED)
        
    def _cancel_typing(self):
        """Cancel any ongoing typing animation."""
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
    
    def next_scene(self):
        """Go to next scene."""
        if self.current_index < len(self.scenes) - 1:
            self._cancel_typing()
            self.current_index += 1
            self._last_beat_idx = -1  # Reset beat tracking
            
            # Reset and restart timer if auto-playing
            if self.auto_play:
                if self.auto_play_job:
                    self.root.after_cancel(self.auto_play_job)
                if self.countdown_job:
                    self.root.after_cancel(self.countdown_job)
                delay = self.calculate_scene_delay(self.scenes[self.current_index])
                self.start_countdown(delay)
                self.update_beat_display(force=True)
                self.auto_play_job = self.root.after(delay, self.auto_play_step)
            else:
                # Update countdown to show new scene duration
                delay = self.calculate_scene_delay(self.scenes[self.current_index])
                self.countdown_ms = delay
                self.current_scene_delay = delay
                # Format countdown
                self.countdown_label.config(text=f"[{self._format_countdown(delay)}]")
                self.update_progress_bars()
            
            self.update_display()
            
    def prev_scene(self):
        """Go to previous scene."""
        if self.current_index > 0:
            self._cancel_typing()
            self.current_index -= 1
            self._last_beat_idx = -1  # Reset beat tracking
            
            # Reset and restart timer if auto-playing
            if self.auto_play:
                if self.auto_play_job:
                    self.root.after_cancel(self.auto_play_job)
                if self.countdown_job:
                    self.root.after_cancel(self.countdown_job)
                delay = self.calculate_scene_delay(self.scenes[self.current_index])
                self.start_countdown(delay)
                self.update_beat_display(force=True)
                self.auto_play_job = self.root.after(delay, self.auto_play_step)
            else:
                # Update countdown to show new scene duration
                delay = self.calculate_scene_delay(self.scenes[self.current_index])
                self.countdown_ms = delay
                self.current_scene_delay = delay
                # Format countdown
                self.countdown_label.config(text=f"[{self._format_countdown(delay)}]")
                self.update_progress_bars()
            
            self.update_display()
            
    def _create_pacing_control(self, parent):
        """Create pacing control with mode selector and slider."""
        # Mode selector
        mode_frame = tk.Frame(parent, bg=self.colors['panel'])
        mode_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(mode_frame, text="Mode:",
                bg=self.colors['panel'],
                fg=self.colors['muted'],
                font=('Cascadia Code', 9)).pack(anchor=tk.W)
        
        self.mode_var = tk.StringVar(value=self.pacing_mode)
        self.mode_menu = tk.OptionMenu(mode_frame, self.mode_var, 
                                       *self.PACING_MODES.keys(),
                                       command=self.on_mode_changed)
        self.mode_menu.config(bg=self.colors['panel'],
                             fg=self.colors['text'],
                             font=('Cascadia Code', 9),
                             highlightthickness=0)
        self.mode_menu.pack(anchor=tk.W)
        
        # Style selector
        style_frame = tk.Frame(parent, bg=self.colors['panel'])
        style_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(style_frame, text="Style:",
                bg=self.colors['panel'],
                fg=self.colors['muted'],
                font=('Cascadia Code', 9)).pack(anchor=tk.W)
        
        self.style_var = tk.StringVar(value=self.narrative_style)
        self.style_menu = tk.OptionMenu(style_frame, self.style_var,
                                        *self.NARRATIVE_STYLES.keys(),
                                        command=self.on_style_changed)
        self.style_menu.config(bg=self.colors['panel'],
                              fg=self.colors['text'],
                              font=('Cascadia Code', 9),
                              highlightthickness=0)
        self.style_menu.pack(anchor=tk.W)
        
        # Speed slider
        frame = tk.Frame(parent, bg=self.colors['panel'])
        frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(frame, text="Speed:",
                bg=self.colors['panel'],
                fg=self.colors['muted'],
                font=('Cascadia Code', 9)).pack(anchor=tk.W)
        
        self.pacing_var = tk.DoubleVar(value=self.config['pacing']['value'])
        self.pacing_label = tk.Label(frame, text=f"{self.pacing_var.get():.2f}x",
                                     bg=self.colors['panel'],
                                     fg=self.colors['accent'],
                                     font=('Cascadia Code', 10, 'bold'),
                                     width=6)
        self.pacing_label.pack(anchor=tk.W)
        
        self.pacing_slider = tk.Scale(frame,
                                      from_=0.25,
                                      to=3.0,
                                      resolution=0.25,
                                      orient=tk.HORIZONTAL,
                                      bg=self.colors['panel'],
                                      fg=self.colors['text'],
                                      highlightthickness=0,
                                      troughcolor=self.colors['muted'],
                                      activebackground=self.colors['accent'],
                                      showvalue=False,
                                      length=100,
                                      variable=self.pacing_var,
                                      command=self.on_pacing_changed)
        self.pacing_slider.pack()
    
    def on_mode_changed(self, value):
        """Handle pacing mode change."""
        self.pacing_mode = value
        self.config['pacing_mode']['value'] = value
        self.save_config()
        print(f"Pacing mode changed to: {value}")
        
        # Update display if auto-playing to apply new timing
        if self.auto_play:
            # Restart countdown with new calculation
            self.countdown_job = None
            delay = self.calculate_scene_delay(self.scenes[self.current_index])
            self.start_countdown(delay)
    
    def on_style_changed(self, value):
        """Handle narrative style change."""
        self.narrative_style = value
        if 'narrative' not in self.config:
            self.config['narrative'] = {'style': {'value': value}}
        else:
            self.config['narrative']['style'] = {'value': value}
        self.save_config()
        print(f"Narrative style changed to: {value}")
        
        # Update current scene display
        self.update_display()
    
    def on_pacing_changed(self, value):
        """Handle pacing slider change."""
        pacing = float(value)
        self.config['pacing']['value'] = pacing
        self.pacing_label.config(text=f"{pacing:.2f}x")
        self.save_config()
        self.save_config()
        
        # Recalculate current countdown if auto-playing
        if self.auto_play and self.current_scene_delay > 0:
            # Adjust remaining time proportionally
            new_delay = self.calculate_scene_delay(self.scenes[self.current_index])
            elapsed = self.current_scene_delay - self.countdown_ms
            self.countdown_ms = max(0, new_delay - elapsed)
            self.current_scene_delay = new_delay
    
    def start_countdown(self, total_ms):
        """Start the countdown timer."""
        self.countdown_ms = total_ms
        self.current_scene_delay = total_ms
        self.update_countdown_display()
    
    def update_countdown_display(self):
        """Update countdown display and schedule next tick."""
        if not self.auto_play:
            self.countdown_label.config(text="[--:--:--:--]")
            return
        
        # Format as DD:HH:MM:SS (days:hours:minutes:seconds to next scene)
        time_str = self._format_countdown(self.countdown_ms)
        
        # Color based on remaining time
        if self.countdown_ms < 3000:
            color = "#e74c3c"  # Red when close to change
        elif self.countdown_ms < 10000:
            color = self.colors['accent']  # Yellow warning
        else:
            color = self.colors['text']  # Normal
            
        self.countdown_label.config(text=f"[{time_str}]", fg=color)
        
        # Update progress bars and beat display (synchronized)
        self.update_progress_bars()
        if self.auto_play:
            self.update_beat_display()
        
        # Schedule next update
        if self.countdown_ms > 0:
            self.countdown_ms -= 100  # Update every 100ms
            self.countdown_job = self.root.after(100, self.update_countdown_display)
    
    def update_progress_bars(self):
        """Update scene and beat progress bars."""
        if not self.scenes:
            return
        
        scene = self.scenes[self.current_index]
        scene_id = scene.get('id', f'scene_{self.current_index:03d}')
        
        # Update scene progress bar
        if self.current_scene_delay > 0:
            elapsed = self.current_scene_delay - self.countdown_ms
            scene_progress = min(1.0, elapsed / self.current_scene_delay)
        else:
            scene_progress = 0.0
        
        self._draw_progress_bar(self.scene_progress_bar, scene_progress, self.colors['accent'])
        
        # Update beat progress bar
        beat_progress = 0.0
        if self.beats and scene_id in self.beats:
            scene_beats = self.beats[scene_id].get('beats', [])
            if scene_beats and self.current_scene_delay > 0:
                elapsed = self.current_scene_delay - self.countdown_ms
                elapsed_pct = min(1.0, elapsed / self.current_scene_delay)
                
                # Find current beat
                for i, beat in enumerate(scene_beats):
                    if beat['start'] <= elapsed_pct < beat['end']:
                        # Progress within this beat
                        beat_range = beat['end'] - beat['start']
                        if beat_range > 0:
                            beat_progress = (elapsed_pct - beat['start']) / beat_range
                        else:
                            beat_progress = 1.0
                        break
                    elif elapsed_pct >= beat['end']:
                        beat_progress = 1.0
        
        self._draw_progress_bar(self.beat_progress_bar, beat_progress, self.colors['canon'])
    
    def _draw_progress_bar(self, canvas, progress, color):
        """Draw a progress bar on a canvas."""
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        if width < 10:  # Not ready yet
            width = 200  # Default
        
        # Draw background
        canvas.create_rectangle(0, 0, width, height, 
                               fill=self.colors['bg'], outline="")
        
        # Draw progress
        if progress > 0:
            fill_width = int(width * progress)
            canvas.create_rectangle(0, 0, fill_width, height,
                                   fill=color, outline="")
    
    def toggle_auto_play(self):
        """Toggle auto-play mode."""
        self.auto_play = not self.auto_play
        
        if self.auto_play:
            self.play_btn.config(text=self._get_symbol("⏸", "||"), bg="#e74c3c")
            self.status_label.config(text=f"{self._get_symbol("●", "*")} Auto-playing", fg="#e74c3c")
            # Start countdown for current scene
            delay = self.calculate_scene_delay(self.scenes[self.current_index])
            self.start_countdown(delay)
            # Start beat display updates (force initial update)
            self.update_beat_display(force=True)
            self.auto_play_job = self.root.after(delay, self.auto_play_step)
        else:
            self.play_btn.config(text=self._get_symbol("▶", ">"), bg=self.colors['accent'])
            self.status_label.config(text=f"{self._get_symbol("●", "*")} Paused", fg=self.colors['generated'])
            if self.auto_play_job:
                self.root.after_cancel(self.auto_play_job)
                self.auto_play_job = None
            if self.countdown_job:
                self.root.after_cancel(self.countdown_job)
                self.countdown_job = None
            self._cancel_typing()
            self.countdown_label.config(text="[--:--:--:--]")
                
    def auto_play_step(self):
        """Auto-play next scene after delay."""
        if not self.auto_play:
            return
            
        if self.current_index < len(self.scenes) - 1:
            self.next_scene()
            # Calculate delay for new scene
            delay = self.calculate_scene_delay(self.scenes[self.current_index])
            self.start_countdown(delay)
            self.auto_play_job = self.root.after(delay, self.auto_play_step)
        else:
            self.toggle_auto_play()  # Stop at end
            self.countdown_label.config(text="[00:00:00:00]")
            
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = HobbitStreamGUI(root)
    app.run()


if __name__ == "__main__":
    main()
