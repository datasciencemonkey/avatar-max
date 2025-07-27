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
    """Save image to disk or Databricks volume.
    
    Args:
        image: PIL Image to save
        directory: Directory to save in
        filename: Filename to use
        
    Returns:
        Path to saved file
    """
    filepath = directory / filename
    
    # Check if we're writing to a Databricks volume
    if str(directory).startswith("/Volumes/"):
        try:
            # Check if we have Databricks credentials before trying to use SDK
            import os
            if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
                print("Databricks credentials not configured, falling back to local save")
                raise ValueError("Missing Databricks credentials")
            
            # Use Databricks SDK to upload to volume
            from databricks.sdk import WorkspaceClient
            from io import BytesIO
            
            print(f"Attempting to upload to Databricks volume: {filepath}")
            
            # Initialize Databricks client with timeout
            w = WorkspaceClient(host=os.getenv("DATABRICKS_HOST"), token=os.getenv("DATABRICKS_TOKEN"))
            
            # Convert PIL Image to bytes
            buffer = BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            
            # Upload to Databricks volume
            volume_file_path = str(filepath)
            w.files.upload(volume_file_path, buffer, overwrite=True)
            
            print(f"Successfully uploaded image to Databricks volume: {volume_file_path}")
        except Exception as e:
            error_msg = str(e)
            print(f"Error uploading to Databricks volume: {error_msg}")
            
            # Provide helpful error messages
            if "Invalid access token" in error_msg:
                print("❌ Authentication failed - check your DATABRICKS_TOKEN")
            elif "RESOURCE_DOES_NOT_EXIST" in error_msg:
                print("❌ Volume path does not exist - ensure volume is created in Databricks")
            elif "PERMISSION_DENIED" in error_msg:
                print("❌ Permission denied - check volume access permissions")
            
            # Fall back to local save if Databricks upload fails
            print("Falling back to local file system save")
            
            # Create local directory and save
            import os
            local_dir = Path("data") / directory.name
            local_dir.mkdir(exist_ok=True, parents=True)
            local_filepath = local_dir / filename
            
            # Save locally
            image.save(local_filepath, format="PNG", optimize=True)
            print(f"✅ Saved locally to: {local_filepath}")
            
            # Return the intended volume path for consistency
            return filepath
    else:
        # Local file system - use pathlib
        directory.mkdir(exist_ok=True, parents=True)
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
            "ai_model": f"{AppConfig.AI_PROVIDER} (configured)",
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