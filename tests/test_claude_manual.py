#!/usr/bin/env python3
"""
Manual test script for Claude quality checking.

This script can be run from the command line to verify Claude integration is working.

Usage:
    uv run python tests/test_claude_manual.py
    
    Or with a specific image:
    uv run python tests/test_claude_manual.py path/to/image.png
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from databricks_claude import get_claude_commentary, DatabricksClaudeCommentator


def create_test_image():
    """Create a test superhero-style image."""
    # Create a colorful test image
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple superhero-style background
    # Top half - sky blue
    draw.rectangle([0, 0, 512, 256], fill=(135, 206, 235))
    # Bottom half - city gray
    draw.rectangle([0, 256, 512, 512], fill=(105, 105, 105))
    
    # Add some "buildings"
    for i in range(0, 512, 80):
        height = 150 + (i % 100)
        draw.rectangle([i, 512-height, i+60, 512], fill=(70, 70, 70))
    
    # Add a circle for a "person"
    draw.ellipse([206, 150, 306, 250], fill=(255, 220, 177))  # Face
    
    # Add "cape"
    draw.polygon([(256, 250), (180, 400), (332, 400)], fill=(255, 0, 0))
    
    # Add text
    try:
        draw.text((256, 50), "SUPERHERO TEST", fill=(255, 255, 0), anchor="mm")
    except:
        # If font fails, just continue
        pass
    
    return img


def test_claude_quality(image_path=None):
    """Test Claude quality checking functionality."""
    print("\n" + "="*70)
    print("CLAUDE QUALITY CHECKING - MANUAL TEST")
    print("="*70)
    
    # Check for token
    token = os.getenv("DATABRICKS_TOKEN")
    if not token:
        print("\n❌ ERROR: DATABRICKS_TOKEN environment variable not set!")
        print("Please set your Databricks token to run this test.")
        print("Example: export DATABRICKS_TOKEN='your-token-here'")
        return False
    
    print(f"\n✅ DATABRICKS_TOKEN found")
    endpoint = os.getenv('DATABRICKS_CLAUDE_ENDPOINT', 'default endpoint')
    print(f"📍 Endpoint: {endpoint}")
    
    # Check if endpoint is properly set
    if endpoint == "None" or endpoint == "default endpoint":
        print("\n⚠️  WARNING: DATABRICKS_CLAUDE_ENDPOINT may not be properly configured!")
        print("The endpoint URL should be a valid HTTPS URL.")
        print("Example: export DATABRICKS_CLAUDE_ENDPOINT='https://your-workspace.databricks.com/serving-endpoints/...'")
        
        # Ask if user wants to continue
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Load or create test image
    if image_path and Path(image_path).exists():
        print(f"\n📷 Loading image from: {image_path}")
        test_image = Image.open(image_path)
    else:
        print("\n🎨 Creating test superhero image...")
        test_image = create_test_image()
        # Save it for inspection
        test_image.save("test_superhero.png")
        print("💾 Test image saved as: test_superhero.png")
    
    # Test parameters
    superhero = "Iron Man"
    color = "red and gold"
    car = "Audi R8"
    
    print(f"\n🦸 Test Parameters:")
    print(f"   Superhero: {superhero}")
    print(f"   Color: {color}")
    print(f"   Car: {car}")
    
    print("\n🔄 Calling Claude API...")
    
    try:
        # Test 1: Using the simple function
        print("\n--- Test 1: get_claude_commentary() ---")
        score, commentary = get_claude_commentary(test_image, superhero, color, car)
        
        print(f"✅ Success!")
        print(f"📊 Quality Score: {score:.2f}/1.00")
        print(f"💬 Commentary: {commentary}")
        
        # Test 2: Using the class directly for more details
        print("\n--- Test 2: DatabricksClaudeCommentator (detailed) ---")
        commentator = DatabricksClaudeCommentator()
        score2, commentary2, analysis = commentator.analyze_avatar(
            test_image, 
            "Captain America", 
            "blue and silver", 
            "Harley Davidson"
        )
        
        print(f"✅ Success!")
        print(f"📊 Quality Score: {score2:.2f}/1.00")
        print(f"💬 Commentary: {commentary2}")
        
        if analysis:
            print(f"\n📋 Full Analysis:")
            for key, value in analysis.items():
                print(f"   {key}: {value}")
        
        print("\n✅ ALL TESTS PASSED! Claude integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        print("\nPossible issues:")
        print("1. Check your DATABRICKS_TOKEN is valid")
        print("2. Verify the Claude endpoint URL is correct")
        print("3. Ensure you have network connectivity")
        print("4. Check if the Databricks workspace is accessible")
        return False
    
    finally:
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    # Check if an image path was provided
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run the test
    success = test_claude_quality(image_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()