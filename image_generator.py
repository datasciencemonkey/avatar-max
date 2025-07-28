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
from databricks_claude import get_claude_commentary
from logo_overlay import add_logo_to_image


class ReplicateImageGenerator:
    """Handles AI image generation using Replicate."""
    
    def __init__(self):
        """Initialize the Replicate generator."""
        if not AppConfig.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN is required")
        
        # Initialize Replicate client
        self.client = replicate.Client(api_token=AppConfig.REPLICATE_API_TOKEN)
        self.model_name = AppConfig.REPLICATE_MODEL
    
    def generate(self, image_data: str, prompt: str, seed: int = -1) -> Optional[str]:
        """Run the Replicate model.
        
        Args:
            image_data: Base64 encoded image data
            prompt: Generation prompt
            seed: Random seed (-1 for random)
            
        Returns:
            URL of generated image or None
        """
        
        # Standard Flux model parameters
        input_params = {
            "prompt": prompt,
            "input_image": image_data,
            "seed": seed,
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "safety_tolerance": 2,
            "prompt_upsampling": True,
            "num_outputs": 1,
            "disable_safety_check": False
        }
        
        # Run the model
        output = self.client.run(
            self.model_name,
            input=input_params
        )
        
        # Handle different Replicate API response formats
        if output is None:
            return None
        elif isinstance(output, str):
            # Direct URL string
            return output
        elif hasattr(output, 'url'):
            # File object with url method
            if callable(getattr(output, 'url')):
                return output.url()
            else:
                return output.url
        elif isinstance(output, list) and len(output) > 0:
            # List of URLs or objects - get the first one
            first_item = output[0]
            if isinstance(first_item, str):
                return first_item
            elif hasattr(first_item, 'url'):
                if callable(getattr(first_item, 'url')):
                    return first_item.url()
                else:
                    return first_item.url
        
        return None


class ImageGenerator:
    """Unified image generator that supports multiple providers."""
    
    def __init__(self):
        """Initialize the image generator with configured provider."""
        self.provider = AppConfig.AI_PROVIDER
        
        if self.provider == "replicate":
            self.generator = ReplicateImageGenerator()
        elif self.provider == "fal":
            from fal_service import FalImageGenerator
            self.generator = FalImageGenerator()
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
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
            
            # Generate prompt
            prompt = AppConfig.get_prompt(superhero, color, car)
            
            # Use provider-specific generation
            generated_image = None
            
            if self.provider == "fal":
                # Fal has its own generate_avatar method
                generated_image, gen_time, error = self.generator.generate_avatar(
                    processed_image, prompt, seed=-1
                )
                if error:
                    return None, gen_time, error
            else:
                # Replicate flow
                image_data = self._image_to_base64(processed_image)
                
                # Run the model with retries
                for attempt in range(max_retries):
                    try:
                        output = self.generator.generate(image_data, prompt)
                        
                        if output:
                            # Download and process the generated image
                            generated_image = self._download_image(output)
                            break
                            
                    except Exception as e:
                        error_str = str(e)
                        # Check for sensitivity error
                        if "E005" in error_str or "flagged as sensitive" in error_str:
                            # Try with modified prompt on sensitivity errors
                            if attempt < max_retries - 1:
                                # Simplify prompt for retry
                                prompt = f"Professional portrait of person as {superhero} character with {car} and {color} theme. Family-friendly superhero costume."
                                time.sleep(2 ** attempt)
                                continue
                        elif attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise e
                else:
                    return None, 0, "Failed to generate image after multiple attempts"
            
            # Now apply post-processing to the generated image from either provider
            
            # Get Claude commentary and quality score
            claude_score = None
            commentary = None
            try:
                claude_score, commentary = get_claude_commentary(
                    generated_image, superhero, color, car
                )
                print(f"Claude quality score: {claude_score:.2f}")
                print(f"Commentary: {commentary}")
                
            except Exception as e:
                print(f"Claude commentary error: {e}")
                # Fallback when Claude is unavailable
                claude_score = None
                commentary = "Your superhero avatar is ready!"
            
            # Add CarMax logo overlay
            try:
                generated_image = add_logo_to_image(
                    generated_image,
                    position="bottom-right",
                    size_ratio=0.12,  # 12% of image width
                    padding=15,
                    opacity=0.85
                )
                print("Added CarMax logo overlay")
            except Exception as e:
                print(f"Warning: Could not add logo overlay: {e}")
            
            # Add Databricks logo overlay
            try:
                databricks_logo_path = AppConfig.ASSETS_DIR / "Databricks-Logo.png"
                generated_image = add_logo_to_image(
                    generated_image,
                    logo_path=databricks_logo_path,
                    position="bottom-left",
                    size_ratio=0.15,  # 15% of image width
                    padding=20,
                    opacity=0.9
                )
                print("Added Databricks logo overlay")
            except Exception as e:
                print(f"Warning: Could not add Databricks logo overlay: {e}")
            
            # Add Innovation Garage logo overlay
            try:
                innovation_garage_logo_path = AppConfig.ASSETS_DIR / "innovation_garage.png"
                generated_image = add_logo_to_image(
                    generated_image,
                    logo_path=innovation_garage_logo_path,
                    position="top-right",
                    size_ratio=0.18,  # 18% of image width
                    padding=20,
                    opacity=0.85
                )
                print("Added Innovation Garage logo overlay")
            except Exception as e:
                print(f"Warning: Could not add Innovation Garage logo overlay: {e}")
            
            generation_time = time.time() - start_time
            
            # Re-attach the Claude analysis to the final image after logo overlays
            if claude_score is not None:
                setattr(generated_image, 'style_score', claude_score)
            if commentary is not None:
                setattr(generated_image, 'commentary', commentary)
                
            return generated_image, generation_time, None
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_str = str(e)
            
            # Provide user-friendly error messages
            if "E005" in error_str or "flagged as sensitive" in error_str:
                error_message = "The image generation was blocked by content filters. Please try again with a different photo or contact support if this persists."
            elif "rate limit" in error_str.lower():
                error_message = "Service is busy. Please wait a moment and try again."
            elif "timeout" in error_str.lower():
                error_message = "Generation took too long. Please try again."
            else:
                error_message = f"Generation failed: {error_str}"
                
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