"""Databricks Claude integration for image quality scoring and commentary."""

import base64
import io
import json
import os
from typing import Dict, Optional, Tuple
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class DatabricksClaudeCommentator:
    """Generate fun commentary and quality scores using Databricks Claude endpoint."""
    
    def __init__(self):
        """Initialize the Databricks Claude client."""
        self.endpoint_url = os.getenv("DATABRICKS_CLAUDE_ENDPOINT", 
                                     "None")
        self.token = os.getenv("DATABRICKS_TOKEN")
        
        if not self.token:
            raise ValueError("DATABRICKS_TOKEN is required for Claude commentary")
            
    def analyze_avatar(self, 
                      image: Image.Image, 
                      superhero: str, 
                      color: str, 
                      car: str) -> Tuple[float, str, Dict]:
        """
        Analyze the generated avatar using Claude for quality and commentary.
        
        Args:
            image: Generated avatar image
            superhero: Selected superhero
            color: Selected color
            car: Selected car
            
        Returns:
            Tuple of (quality_score, commentary, full_analysis)
        """
        try:
            # Convert image to base64
            image_base64 = self._image_to_base64(image)
            
            # Create the prompt for Claude
            prompt = f"""You are a fun and enthusiastic comic book art critic reviewing superhero avatar transformations.

Analyze this generated avatar image and provide:
1. A quality score from 0 to 1 (where 1 is perfect cartoon consistency)
2. A short, fun, and encouraging commentary (2-3 sentences max)

Context:
- The person wanted to be transformed into a {superhero}-inspired character
- They chose {color} as their theme color
- Their favorite car is a {car}
- The setting should be a CarMax Innovation Garage

Please evaluate:
- How well the cartoon/comic book style is maintained throughout
- Whether the person's face is recognizable but stylized
- If the superhero theme comes through clearly
- Overall artistic cohesion and appeal

Respond in JSON format:
{{
  "quality_score": 0.85,
  "commentary": "Your commentary here!",
  "style_consistency": "excellent/good/fair",
  "superhero_likeness": "strong/moderate/weak",
  "fun_factor": "high/medium/low"
}}"""

            # Make the API call
            response = self._call_claude_endpoint(prompt, image_base64)
            
            if response:
                return self._parse_response(response)
            else:
                # Fallback to basic scoring
                return 0.75, "Looking super! Your avatar is ready to save the day!", {}
                
        except Exception as e:
            print(f"Claude analysis error: {e}")
            # Return default values on error
            return 0.75, "Awesome transformation! You look ready for action!", {}
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        # Resize if too large
        max_size = 1024
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    
    def _call_claude_endpoint(self, prompt: str, image_base64: str) -> Optional[Dict]:
        """Call the Databricks Claude endpoint."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Format request according to Databricks documentation
        # Using the correct format for vision models on Databricks
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Claude endpoint error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Claude endpoint request failed: {e}")
            return None
    
    def _parse_response(self, response: Dict) -> Tuple[float, str, Dict]:
        """Parse Claude's response from Databricks format."""
        try:
            # Databricks model serving returns in OpenAI-compatible format
            content = None
            
            # Extract content from response
            if "choices" in response and len(response["choices"]) > 0:
                # Standard OpenAI/Databricks format
                message = response["choices"][0].get("message", {})
                content = message.get("content", "")
            elif "predictions" in response:
                # Alternative Databricks format
                content = response["predictions"]
            elif "content" in response:
                # Direct content
                content = response["content"]
            else:
                # Fallback to string representation
                content = str(response)
            
            # Try to parse JSON from the content
            # Claude might wrap it in markdown code blocks
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON in the content
                import re
                json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = content
            
            analysis = json.loads(json_str)
            
            quality_score = float(analysis.get("quality_score", 0.75))
            commentary = analysis.get("commentary", "Amazing superhero transformation!")
            
            return quality_score, commentary, analysis
            
        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            print(f"Response structure: {response}")
            # Return defaults if parsing fails
            return 0.75, "Fantastic superhero avatar! Ready to save the day!", {}


def get_claude_commentary(image: Image.Image, superhero: str, color: str, car: str) -> Tuple[float, str]:
    """
    Get Claude's commentary on the generated avatar.
    
    Args:
        image: Generated avatar
        superhero: Selected superhero
        color: Theme color
        car: Selected car
        
    Returns:
        Tuple of (quality_score, commentary)
    """
    try:
        commentator = DatabricksClaudeCommentator()
        score, commentary, _ = commentator.analyze_avatar(image, superhero, color, car)
        return score, commentary
    except Exception as e:
        print(f"Claude commentary error: {e}")
        return 0.75, "Your superhero avatar looks amazing!"