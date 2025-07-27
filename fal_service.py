"""Fal AI Image Generation service for Superhero Avatar Generator."""

import base64
import io
import os
import time
from typing import Optional, Tuple
import requests
from PIL import Image
import fal_client
from dotenv import load_dotenv

load_dotenv()


class FalImageGenerator:
    """Handles AI image generation using Fal AI."""
    
    def __init__(self):
        """Initialize the Fal image generator."""
        self.api_key = os.getenv("FAL_KEY")
        if not self.api_key:
            raise ValueError("FAL_KEY is required for Fal AI service")
        
        # Initialize Fal client
        fal_client.api_key = self.api_key
        
        # Import config
        from config import AppConfig
        
        # Get model name from config
        self.model_name = AppConfig.FAL_MODEL
    
    def generate_avatar(
        self,
        original_image: Image.Image,
        prompt: str,
        seed: int = -1
    ) -> Tuple[Optional[Image.Image], float, Optional[str]]:
        """Generate superhero avatar using Fal AI.
        
        Args:
            original_image: Original photo
            prompt: Generation prompt
            seed: Random seed (-1 for random)
            
        Returns:
            Tuple of (generated_image, generation_time, error_message)
        """
        start_time = time.time()
        
        try:
            # Convert image to base64
            image_data = self._image_to_base64(original_image)
            
            # Prepare input for Fal API
            input_data = {
                "prompt": prompt,
                "image_url": image_data,  # Fal accepts base64 data URLs
                "seed": seed if seed != -1 else None,
                "image_size": "square",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "enable_safety_checker": True,
                "safety_tolerance": 2
            }
            
            # Remove None values
            input_data = {k: v for k, v in input_data.items() if v is not None}
            
            
            # Run the model
            result = fal_client.run(
                self.model_name,
                arguments=input_data
            )
            
            # Extract the generated image URL
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                generated_image = self._download_image(image_url)
                generation_time = time.time() - start_time
                return generated_image, generation_time, None
            else:
                return None, 0, "No image generated from Fal AI"
                
        except Exception as e:
            generation_time = time.time() - start_time
            error_str = str(e)
            
            # Provide user-friendly error messages
            if "rate limit" in error_str.lower():
                error_message = "Service is busy. Please wait a moment and try again."
            elif "timeout" in error_str.lower():
                error_message = "Generation took too long. Please try again."
            elif "safety" in error_str.lower() or "flagged" in error_str.lower():
                error_message = "The image generation was blocked by content filters. Please try again with a different photo."
            else:
                error_message = f"Fal AI generation failed: {error_str}"
                
            return None, generation_time, error_message
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image
            
        Returns:
            Base64 encoded string with data URI prefix
        """
        # Resize if too large (Fal has limits)
        max_size = 1024
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        base64_encoded = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{base64_encoded}"
    
    def _download_image(self, url: str) -> Image.Image:
        """Download image from URL.
        
        Args:
            url: Image URL
            
        Returns:
            PIL Image object
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        image_data = io.BytesIO(response.content)
        image = Image.open(image_data)
        
        return image


def create_fal_generator() -> FalImageGenerator:
    """Create a Fal image generator for development.
    
    Returns:
        FalImageGenerator instance
    """
    return FalImageGenerator()