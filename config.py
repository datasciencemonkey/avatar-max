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
    AI_PROVIDER = os.getenv("AI_PROVIDER", "replicate")  # Options: "fal" or "replicate"
    
    # Replicate settings
    REPLICATE_MODEL = os.getenv("AI_MODEL", "black-forest-labs/flux-kontext-pro")
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    
    # Fal AI settings
    FAL_MODEL = os.getenv("AI_MODEL", "fal-ai/flux-pro/kontext")
    FAL_API_KEY = os.getenv("FAL_KEY")
    
    MODEL_VERSION = "latest"

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
        "Ant-Man",
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
        "Cyan": "#00FFFF",
    }

    # Prompt Template
    PROMPT_TEMPLATE = """move the person to a showroom garage, dressed like {superhero}, retain facial features. Show a {color} {car} in the background. Let them raise their thumbs up. Make it 90s cartoon style or anime style. family friendly."""

    # Event Configuration
    EVENT_NAME = os.getenv("EVENT_NAME", "Databricks @ Innovation Garage 2025")
    EVENT_THEME = os.getenv("EVENT_THEME", "futuristic city backdrop")

    # Storage Settings
    # Use Databricks volume if available, otherwise local storage
    DATABRICKS_VOLUME = os.getenv(
        "DATABRICKS_VOLUME", "/Volumes/main/sgfs/sg-vol/avatarmax"
    )

    # Check if we're in Databricks environment
    # In Databricks, volumes are always accessible at /Volumes/
    IS_DATABRICKS = (
        os.getenv("DATABRICKS_RUNTIME_VERSION") is not None
        or (os.path.exists("/Volumes/") and os.path.exists(DATABRICKS_VOLUME))
    )
    USE_DATABRICKS_VOLUME = IS_DATABRICKS and os.path.exists(DATABRICKS_VOLUME)
    
    # Debug logging (uncomment for troubleshooting)
    # print(f"DEBUG Config - DATABRICKS_RUNTIME_VERSION: {os.getenv('DATABRICKS_RUNTIME_VERSION')}")
    # print(f"DEBUG Config - /Volumes/ exists: {os.path.exists('/Volumes/')}")
    # print(f"DEBUG Config - DATABRICKS_VOLUME: {DATABRICKS_VOLUME}")
    # print(f"DEBUG Config - DATABRICKS_VOLUME exists: {os.path.exists(DATABRICKS_VOLUME)}")
    # print(f"DEBUG Config - IS_DATABRICKS: {IS_DATABRICKS}")
    # print(f"DEBUG Config - USE_DATABRICKS_VOLUME: {USE_DATABRICKS_VOLUME}")

    if USE_DATABRICKS_VOLUME:
        DATA_DIR = Path(DATABRICKS_VOLUME)
    else:
        DATA_DIR = Path("data")

    AVATARS_DIR = DATA_DIR / "avatars"
    ORIGINALS_DIR = DATA_DIR / "originals"
    
    # Static Assets Path
    # When using Databricks volumes, assets are stored in the volume
    # Otherwise, use local assets folder
    if USE_DATABRICKS_VOLUME:
        ASSETS_DIR = Path(DATABRICKS_VOLUME)
    else:
        ASSETS_DIR = Path("assets")

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
        if cls.AI_PROVIDER == "replicate" and not cls.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required for Replicate provider")
        elif cls.AI_PROVIDER == "fal" and not cls.FAL_API_KEY:
            raise ValueError("FAL_KEY environment variable is required for Fal provider")
        elif cls.AI_PROVIDER not in ["replicate", "fal"]:
            raise ValueError(f"Invalid AI_PROVIDER: {cls.AI_PROVIDER}. Must be 'replicate' or 'fal'")

        # Create directories if they don't exist
        # For Databricks volumes, directories will be created when saving files
        if not str(cls.DATA_DIR).startswith("/Volumes/"):
            # Only create directories for local file system
            cls.DATA_DIR.mkdir(exist_ok=True)
            cls.AVATARS_DIR.mkdir(exist_ok=True)
            cls.ORIGINALS_DIR.mkdir(exist_ok=True)
        else:
            # For Databricks volumes, just log that we'll create on write
            print(f"Using Databricks volume: {cls.DATA_DIR}")
            print("Directories will be created when saving files")

        return True

    @classmethod
    def get_prompt(cls, superhero: str, color: str, car: str) -> str:
        """Generate prompt with user selections."""
        return cls.PROMPT_TEMPLATE.format(superhero=superhero, color=color, car=car)
