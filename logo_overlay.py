"""Logo overlay functionality for generated images."""

from PIL import Image, ImageDraw
from pathlib import Path
from typing import Optional, Tuple
from config import AppConfig


def add_logo_to_image(
    image: Image.Image,
    logo_path: Path = None,
    position: str = "bottom-right",
    size_ratio: float = 0.15,
    padding: int = 20,
    opacity: float = 0.9
) -> Image.Image:
    """
    Add a logo overlay to an image.
    
    Args:
        image: The main image to add logo to
        logo_path: Path to the logo file
        position: Position of logo ("bottom-right", "bottom-left", "top-right", "top-left")
        size_ratio: Logo size as ratio of image width (0.15 = 15% of width)
        padding: Padding from edges in pixels
        opacity: Logo opacity (0.0 to 1.0)
    
    Returns:
        Image with logo overlay
    """
    try:
        # Use default CarMax logo if no path specified
        if logo_path is None:
            logo_path = AppConfig.ASSETS_DIR / "carmax_logo.png"
            
        # Load logo with comprehensive fallback strategy
        print(f"Attempting to load logo from: {logo_path}")
        
        # List of paths to try in order
        paths_to_try = [
            logo_path,  # Primary path (volume or configured path)
            Path("assets") / logo_path.name,  # Local assets folder
            Path(__file__).parent / "assets" / logo_path.name,  # Assets relative to this file
            Path.cwd() / "assets" / logo_path.name,  # Assets from current working directory
        ]
        
        logo_found = False
        for i, path_to_try in enumerate(paths_to_try):
            print(f"  Trying path {i+1}: {path_to_try}")
            if path_to_try.exists():
                print(f"  ✓ Found logo at: {path_to_try}")
                logo_path = path_to_try
                logo_found = True
                break
            else:
                print(f"  ✗ Not found at: {path_to_try}")
        
        if not logo_found:
            print(f"Logo '{logo_path.name}' not found in any of the attempted paths")
            print(f"Current working directory: {Path.cwd()}")
            print(f"Script directory: {Path(__file__).parent}")
            print(f"Available files in current directory:")
            try:
                for file in Path.cwd().iterdir():
                    if file.is_file():
                        print(f"  - {file.name}")
            except Exception as e:
                print(f"  - Error listing current directory: {e}")
            return image
            
        logo = Image.open(logo_path)
        
        # Convert to RGBA if needed
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Make a copy of the main image
        result = image.copy()
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        # Calculate logo size maintaining aspect ratio
        logo_width = int(result.width * size_ratio)
        logo_height = int(logo.height * (logo_width / logo.width))
        
        # Resize logo
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Apply opacity to logo
        if opacity < 1.0:
            logo = apply_opacity(logo, opacity)
        
        # Calculate position
        if position == "bottom-right":
            x = result.width - logo_width - padding
            y = result.height - logo_height - padding
        elif position == "bottom-left":
            x = padding
            y = result.height - logo_height - padding
        elif position == "top-right":
            x = result.width - logo_width - padding
            y = padding
        elif position == "top-left":
            x = padding
            y = padding
        else:
            # Default to bottom-right
            x = result.width - logo_width - padding
            y = result.height - logo_height - padding
        
        # Paste logo onto image
        result.paste(logo, (x, y), logo)
        
        # Convert back to RGB if original was RGB
        if image.mode == 'RGB':
            result = result.convert('RGB')
        
        return result
        
    except Exception as e:
        print(f"Error adding logo: {e}")
        return image


def apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
    """
    Apply opacity to an image.
    
    Args:
        image: Image to modify
        opacity: Opacity value (0.0 to 1.0)
    
    Returns:
        Image with applied opacity
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get image data
    data = image.getdata()
    
    # Apply opacity
    new_data = []
    for item in data:
        # Change opacity of each pixel
        new_data.append((item[0], item[1], item[2], int(item[3] * opacity)))
    
    # Update image data
    image.putdata(new_data)
    
    return image


def create_placeholder_logo(path: Path) -> None:
    """
    Create a placeholder CarMax logo for testing.
    This should be replaced with the actual logo.
    """
    # Create a simple text-based placeholder
    width, height = 400, 100
    logo = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(logo)
    
    # Draw CarMax text (placeholder)
    # Note: In production, use the actual CarMax logo image
    draw.rectangle([0, 0, width, height], fill=(0, 20, 100, 255))
    draw.text((20, 30), "CARMAX", fill=(255, 255, 255, 255))
    
    # Save placeholder
    path.parent.mkdir(parents=True, exist_ok=True)
    logo.save(path)
    print(f"Created placeholder logo at {path}")
    print("Please replace with actual CarMax logo!")