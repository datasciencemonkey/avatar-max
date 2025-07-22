"""Configuration module for Superhero Avatar Generator."""

import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AppConfig:
    """Application configuration class."""
    
    # App Branding
    APP_TITLE = "🦸 Superhero Avatar Generator"
    APP_ICON = "🦸"
    PAGE_ICON = "🦸‍♀️"
    APP_DESCRIPTION = "Transform yourself into your favorite superhero!"
    
    # Theme Colors
    PRIMARY_COLOR = "#FF6B6B"
    SECONDARY_COLOR = "#4ECDC4"
    BACKGROUND_COLOR = "#1A1A2E"
    TEXT_COLOR = "#FFFFFF"
    
    # AI Model Settings
    AI_PROVIDER = "replicate"
    MODEL_NAME = "black-forest-labs/flux-kontext-pro"
    MODEL_VERSION = "latest"
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    
    # Image Settings
    IMAGE_SIZE = "1024x1024"
    IMAGE_FORMAT = "png"
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    
    # Superhero Options
    SUPERHERO_OPTIONS = [
        "Superman",
        "Batman", 
        "Wonder Woman",
        "Spider-Man",
        "Iron Man",
        "Black Panther",
        "Captain Marvel",
        "Thor",
        "The Flash",
        "Green Lantern",
        "Captain America",
        "Black Widow",
        "Hulk",
        "Doctor Strange",
        "Ant-Man"
    ]
    
    # Color Options (name, hex value)
    COLOR_OPTIONS = {
        "Red": "#FF0000",
        "Blue": "#0000FF",
        "Green": "#00FF00",
        "Purple": "#800080",
        "Gold": "#FFD700",
        "Silver": "#C0C0C0",
        "Black": "#000000",
        "Orange": "#FFA500",
        "Pink": "#FFC0CB",
        "Cyan": "#00FFFF"
    }
    
    # Prompt Template
    PROMPT_TEMPLATE = """Create a stunning superhero avatar transformation:

Subject: Person in the provided photo
Style: {superhero} superhero costume and powers
Color scheme: Primary color is {color}
Vehicle: {car} featured prominently in the scene
Setting: Epic superhero scene with dramatic lighting and effects

Requirements:
- Maintain the person's facial features and identity
- Professional photography quality
- Dramatic superhero pose
- Cinematic composition
- Ultra detailed, 8K resolution
- Photorealistic rendering"""

    # Event Configuration
    EVENT_NAME = os.getenv("EVENT_NAME", "Databricks @ Innovation Garage 2025")
    EVENT_THEME = os.getenv("EVENT_THEME", "futuristic city backdrop")
    
    # Storage Settings
    DATA_DIR = Path("data")
    AVATARS_DIR = DATA_DIR / "avatars"
    ORIGINALS_DIR = DATA_DIR / "originals"
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_RETRIES = 3
    GENERATION_TIMEOUT_SECONDS = 60
    
    # Feature Flags
    ENABLE_EMAIL_CAPTURE = True
    ENABLE_DOWNLOAD = True
    ENABLE_ANALYTICS = False
    REQUIRE_CONSENT = True
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required")
        
        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.AVATARS_DIR.mkdir(exist_ok=True)
        cls.ORIGINALS_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_prompt(cls, superhero: str, color: str, car: str) -> str:
        """Generate prompt with user selections."""
        return cls.PROMPT_TEMPLATE.format(
            superhero=superhero,
            color=color,
            car=car
        )