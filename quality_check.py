"""Quality check module for ensuring consistent cartoon style in generated images."""

import numpy as np
from PIL import Image
from typing import Tuple, Optional
import cv2


class StyleConsistencyChecker:
    """Check if generated images have consistent cartoon/animation style throughout."""
    
    def __init__(self):
        """Initialize the style consistency checker."""
        self.min_cartoon_score = 0.7  # Minimum score to pass quality check
        
    def check_image_style(self, image: Image.Image) -> Tuple[bool, float, Optional[str]]:
        """
        Check if the entire image maintains consistent cartoon style.
        
        Args:
            image: PIL Image to check
            
        Returns:
            Tuple of (passes_check, style_score, error_message)
        """
        try:
            # Convert PIL to numpy array
            img_array = np.array(image)
            
            # Run multiple style checks
            edge_score = self._check_edge_consistency(img_array)
            color_score = self._check_color_saturation(img_array)
            gradient_score = self._check_gradient_smoothness(img_array)
            texture_score = self._check_texture_uniformity(img_array)
            
            # Combine scores (weighted average)
            style_score = (
                edge_score * 0.3 +
                color_score * 0.3 +
                gradient_score * 0.2 +
                texture_score * 0.2
            )
            
            # Determine if image passes quality check
            passes = style_score >= self.min_cartoon_score
            
            error_msg = None
            if not passes:
                if edge_score < 0.6:
                    error_msg = "Image contains mixed realistic and cartoon elements"
                elif color_score < 0.6:
                    error_msg = "Color saturation is inconsistent across the image"
                elif gradient_score < 0.6:
                    error_msg = "Some areas have photorealistic gradients"
                else:
                    error_msg = "Image style is not uniformly cartoon-like"
                    
            return passes, style_score, error_msg
            
        except Exception as e:
            return False, 0.0, f"Quality check failed: {str(e)}"
    
    def _check_edge_consistency(self, img_array: np.ndarray) -> float:
        """
        Check if edges are consistently cartoon-like (bold and simplified).
        
        Cartoon images typically have:
        - Bold, defined edges
        - Fewer edge details than photos
        - Consistent edge thickness
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density (cartoon images have lower edge density)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Cartoon images typically have edge density between 0.02 and 0.15
        if 0.02 <= edge_density <= 0.15:
            score = 1.0
        elif edge_density < 0.02:
            score = edge_density / 0.02
        else:
            score = max(0, 1 - (edge_density - 0.15) / 0.15)
            
        return score
    
    def _check_color_saturation(self, img_array: np.ndarray) -> float:
        """
        Check if colors are consistently saturated (cartoon-like).
        
        Cartoon images typically have:
        - High color saturation
        - Consistent saturation across regions
        - Limited color palette
        """
        # Convert to HSV
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = hsv[:, :, 1]
        
        # Calculate average saturation
        avg_saturation = np.mean(saturation)
        
        # Calculate saturation variance (should be low for consistent style)
        saturation_std = np.std(saturation)
        
        # Score based on high saturation and low variance
        sat_score = min(1.0, avg_saturation / 200)  # Higher saturation is better
        consistency_score = max(0, 1 - saturation_std / 50)  # Lower variance is better
        
        return (sat_score + consistency_score) / 2
    
    def _check_gradient_smoothness(self, img_array: np.ndarray) -> float:
        """
        Check if gradients are smooth and cartoon-like.
        
        Cartoon images typically have:
        - Smooth color transitions
        - Cel-shading effects
        - Minimal texture detail
        """
        # Calculate gradient magnitude
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Cartoon images have distinct but smooth gradients
        gradient_variance = np.var(gradient_mag)
        
        # Lower variance indicates smoother, more cartoon-like gradients
        if gradient_variance < 500:
            score = 1.0
        elif gradient_variance > 2000:
            score = 0.0
        else:
            score = 1 - (gradient_variance - 500) / 1500
            
        return score
    
    def _check_texture_uniformity(self, img_array: np.ndarray) -> float:
        """
        Check if textures are uniform and simplified (cartoon-like).
        
        Cartoon images typically have:
        - Large areas of uniform color
        - Minimal texture detail
        - Simplified surfaces
        """
        # Divide image into regions and check color uniformity
        h, w = img_array.shape[:2]
        region_size = 32
        uniformity_scores = []
        
        for i in range(0, h - region_size, region_size):
            for j in range(0, w - region_size, region_size):
                region = img_array[i:i+region_size, j:j+region_size]
                
                # Calculate color variance in region
                region_variance = np.var(region, axis=(0, 1))
                avg_variance = np.mean(region_variance)
                
                # Lower variance means more uniform (cartoon-like)
                if avg_variance < 100:
                    uniformity_scores.append(1.0)
                elif avg_variance > 1000:
                    uniformity_scores.append(0.0)
                else:
                    uniformity_scores.append(1 - (avg_variance - 100) / 900)
        
        return np.mean(uniformity_scores) if uniformity_scores else 0.5


def analyze_style_consistency(image: Image.Image) -> dict:
    """
    Analyze an image for style consistency and return detailed metrics.
    
    Args:
        image: PIL Image to analyze
        
    Returns:
        Dictionary with analysis results
    """
    checker = StyleConsistencyChecker()
    passes, score, error = checker.check_image_style(image)
    
    return {
        "passes_quality_check": passes,
        "style_consistency_score": round(score, 3),
        "error_message": error,
        "recommendation": "Image has consistent cartoon style" if passes else "Regenerate with stronger cartoon style emphasis"
    }