"""Utility functions for Superhero Avatar Generator."""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st
from PIL import Image
from email_validator import validate_email, EmailNotValidError

from config import AppConfig


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate user name input.
    
    Args:
        name: User's name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, None


def validate_email_address(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validated = validate_email(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_car_input(car: str) -> Tuple[bool, Optional[str]]:
    """Validate car input.
    
    Args:
        car: Car name/model
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not car or len(car.strip()) < 2:
        return False, "Please enter a car name (at least 2 characters)"
    
    if len(car) > 100:
        return False, "Car name must be less than 100 characters"
    
    return True, None


def validate_color_input(color: str) -> Tuple[bool, Optional[str]]:
    """Validate color input.
    
    Args:
        color: Color name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not color or len(color.strip()) < 2:
        return False, "Please enter a color name (at least 2 characters)"
    
    if len(color) > 50:
        return False, "Color name must be less than 50 characters"
    
    return True, None


def process_uploaded_image(image: Image.Image) -> Image.Image:
    """Process uploaded image for AI generation.
    
    Args:
        image: PIL Image object
        
    Returns:
        Processed PIL Image
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to optimal size while maintaining aspect ratio
    max_size = 1024
    width, height = image.size
    
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def generate_unique_filename(prefix: str = "avatar", extension: str = "png") -> str:
    """Generate a unique filename.
    
    Args:
        prefix: Filename prefix
        extension: File extension
        
    Returns:
        Unique filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"


def save_image(image: Image.Image, directory: Path, filename: str) -> Path:
    """Save image to disk.
    
    Args:
        image: PIL Image to save
        directory: Directory to save in
        filename: Filename to use
        
    Returns:
        Path to saved file
    """
    directory.mkdir(exist_ok=True, parents=True)
    filepath = directory / filename
    image.save(filepath, format="PNG", optimize=True)
    return filepath


def format_generation_time(seconds: float) -> str:
    """Format generation time for display.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    else:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"


def create_participant_record(
    name: str,
    email: str,
    superhero: str,
    car: str,
    color: str,
    original_image_path: Path,
    generated_image_path: Path,
    generation_time: float
) -> dict:
    """Create a participant record for storage.
    
    Args:
        name: Participant name
        email: Participant email
        superhero: Selected superhero
        car: Selected car
        color: Selected color
        original_image_path: Path to original photo
        generated_image_path: Path to generated avatar
        generation_time: Time taken to generate
        
    Returns:
        Dictionary with participant data
    """
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "email": email,
        "preferences": {
            "superhero": superhero,
            "car": car,
            "color": color
        },
        "images": {
            "original": str(original_image_path),
            "generated": str(generated_image_path)
        },
        "metadata": {
            "generation_time": generation_time,
            "ai_model": AppConfig.MODEL_NAME,
            "event": AppConfig.EVENT_NAME
        }
    }


def show_error(message: str) -> None:
    """Display error message in Streamlit.
    
    Args:
        message: Error message to display
    """
    st.error(f"❌ {message}")


def show_success(message: str) -> None:
    """Display success message in Streamlit.
    
    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")


def show_info(message: str) -> None:
    """Display info message in Streamlit.
    
    Args:
        message: Info message to display
    """
    st.info(f"ℹ️ {message}")


def reset_session_state() -> None:
    """Reset all session state variables."""
    keys_to_reset = [
        "name", "email", "superhero", "car", "color",
        "photo", "generated_avatar", "generation_time",
        "step", "form_submitted", "request_id"
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]