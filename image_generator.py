"""AI Image Generation module for Superhero Avatar Generator."""

import base64
import io
import time
from typing import Optional, Tuple

import replicate
import requests
from PIL import Image

from config import AppConfig
from utils import process_uploaded_image


class ImageGenerator:
    """Handles AI image generation using Replicate."""
    
    def __init__(self):
        """Initialize the image generator."""
        if not AppConfig.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN is required")
        
        # Initialize Replicate client
        self.client = replicate.Client(api_token=AppConfig.REPLICATE_API_TOKEN)
        self.model_name = AppConfig.MODEL_NAME
    
    def generate_avatar(
        self,
        original_image: Image.Image,
        superhero: str,
        color: str,
        car: str,
        max_retries: int = 3
    ) -> Tuple[Optional[Image.Image], float, Optional[str]]:
        """Generate superhero avatar using AI.
        
        Args:
            original_image: Original photo
            superhero: Selected superhero
            color: Selected color
            car: Selected car
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (generated_image, generation_time, error_message)
        """
        start_time = time.time()
        
        try:
            # Process the image
            processed_image = process_uploaded_image(original_image)
            
            # Convert image to base64
            image_data = self._image_to_base64(processed_image)
            
            # Generate prompt
            prompt = AppConfig.get_prompt(superhero, color, car)
            
            # Run the model with retries
            for attempt in range(max_retries):
                try:
                    output = self._run_model(image_data, prompt)
                    
                    if output:
                        # Download and return the generated image
                        generated_image = self._download_image(output)
                        generation_time = time.time() - start_time
                        return generated_image, generation_time, None
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise e
            
            return None, 0, "Failed to generate image after multiple attempts"
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_message = f"Generation failed: {str(e)}"
            return None, generation_time, error_message
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image
            
        Returns:
            Base64 encoded string with data URI prefix
        """
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        base64_encoded = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{base64_encoded}"
    
    def _run_model(self, image_data: str, prompt: str) -> Optional[str]:
        """Run the Replicate model.
        
        Args:
            image_data: Base64 encoded image data
            prompt: Generation prompt
            
        Returns:
            URL of generated image or None
        """
        # Run the FLUX Kontext Pro model
        output = self.client.run(
            self.model_name,
            input={
                "prompt": prompt,
                "image": image_data,
                "guidance_scale": 7.5,
                "num_inference_steps": 50,
                "strength": 0.8,  # How much to transform the original image
                # seed parameter omitted - Replicate will handle randomization
            }
        )
        
        # The output could be a URL or a list of URLs
        if isinstance(output, list) and len(output) > 0:
            return output[0]
        elif isinstance(output, str):
            return output
        else:
            return None
    
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


def create_test_generator() -> ImageGenerator:
    """Create a test image generator for development.
    
    Returns:
        ImageGenerator instance
    """
    return ImageGenerator()