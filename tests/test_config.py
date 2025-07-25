"""Tests for configuration module."""

import os
import pytest
from pathlib import Path

from config import AppConfig


def test_app_config_basics():
    """Test basic configuration values."""
    assert AppConfig.APP_TITLE == "🦸 Superhero Avatar Generator"
    assert AppConfig.AI_PROVIDER in ["replicate", "fal"]
    assert AppConfig.REPLICATE_MODEL_NAME == "black-forest-labs/flux-kontext-dev"
    assert AppConfig.FAL_MODEL_NAME == "fal-ai/flux-pro/kontext"
    assert AppConfig.IMAGE_SIZE == "1024x1024"


def test_superhero_options():
    """Test superhero options are available."""
    assert len(AppConfig.SUPERHERO_OPTIONS) > 0
    assert "Superman" in AppConfig.SUPERHERO_OPTIONS
    assert "Batman" in AppConfig.SUPERHERO_OPTIONS
    assert "Wonder Woman" in AppConfig.SUPERHERO_OPTIONS


def test_color_options():
    """Test color options are properly formatted."""
    assert len(AppConfig.COLOR_OPTIONS) > 0
    assert "Red" in AppConfig.COLOR_OPTIONS
    assert AppConfig.COLOR_OPTIONS["Red"] == "#FF0000"
    assert AppConfig.COLOR_OPTIONS["Blue"] == "#0000FF"


def test_prompt_generation():
    """Test prompt template generation."""
    prompt = AppConfig.get_prompt(
        superhero="Iron Man",
        color="Red",
        car="Tesla Model S"
    )
    assert "Iron Man" in prompt
    assert "Red" in prompt
    assert "Tesla Model S" in prompt
    assert "Carmax Innovation Garage" in prompt


def test_directory_creation():
    """Test that directories are created during validation."""
    # Clean up first if they exist
    if AppConfig.AVATARS_DIR.exists():
        AppConfig.AVATARS_DIR.rmdir()
    if AppConfig.ORIGINALS_DIR.exists():
        AppConfig.ORIGINALS_DIR.rmdir()
    if AppConfig.DATA_DIR.exists():
        AppConfig.DATA_DIR.rmdir()
    
    # Set a dummy token for validation
    os.environ["REPLICATE_API_TOKEN"] = "test_token"
    
    # Reload config to pick up the token
    from importlib import reload
    import config
    reload(config)
    
    # Validate should create directories
    assert config.AppConfig.validate() == True
    
    # Check directories were created
    assert config.AppConfig.DATA_DIR.exists()
    assert config.AppConfig.AVATARS_DIR.exists()
    assert config.AppConfig.ORIGINALS_DIR.exists()


def test_validation_fails_without_token():
    """Test validation fails without API token."""
    # Remove tokens if they exist
    if "REPLICATE_API_TOKEN" in os.environ:
        del os.environ["REPLICATE_API_TOKEN"]
    if "FAL_KEY" in os.environ:
        del os.environ["FAL_KEY"]
    
    # Reload config to pick up missing token
    from importlib import reload
    import config
    reload(config)
    
    # Should fail for the configured provider
    with pytest.raises(ValueError):
        config.AppConfig.validate()