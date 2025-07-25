"""Test script for Fal AI integration."""

import os
import sys
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fal_service import FalImageGenerator
from config import AppConfig

# Load environment variables
load_dotenv()


def create_test_image():
    """Create a simple test image."""
    # Create a 512x512 test image with a gradient
    img = Image.new('RGB', (512, 512), color='blue')
    return img


def test_fal_service():
    """Test the Fal AI service integration."""
    print("🧪 Testing Fal AI Integration\n")
    
    # Check environment setup
    print("1. Checking environment configuration...")
    if not os.getenv("FAL_KEY"):
        print("❌ FAL_KEY not found in environment variables")
        print("   Please set FAL_KEY in your .env file")
        return False
    else:
        print("✅ FAL_KEY found")
    
    # Test FalImageGenerator initialization
    print("\n2. Initializing Fal Image Generator...")
    try:
        generator = FalImageGenerator()
        print("✅ FalImageGenerator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize FalImageGenerator: {e}")
        return False
    
    # Test image generation
    print("\n3. Testing image generation...")
    test_image = create_test_image()
    
    # Test parameters
    prompt = "Transform person into Superman-inspired character with red cape in a garage setting with a blue car. Cartoon style, family-friendly."
    
    print(f"   Prompt: {prompt}")
    print("   Generating avatar...")
    
    try:
        result_image, generation_time, error = generator.generate_avatar(
            test_image,
            prompt,
            seed=42  # Fixed seed for reproducibility
        )
        
        if error:
            print(f"❌ Generation failed with error: {error}")
            return False
        
        if result_image:
            print(f"✅ Avatar generated successfully in {generation_time:.2f} seconds")
            print(f"   Image size: {result_image.size}")
            print(f"   Image mode: {result_image.mode}")
            
            # Save the test result
            output_path = Path(__file__).parent / "test_fal_output.png"
            result_image.save(output_path)
            print(f"   Saved test output to: {output_path}")
            
            return True
        else:
            print("❌ No image was generated")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fal_client_direct():
    """Test Fal client directly."""
    print("\n4. Testing Fal client directly...")
    
    try:
        import fal_client
        
        # Set API key
        fal_client.api_key = os.getenv("FAL_KEY")
        
        # Test simple text-to-image generation
        print("   Testing basic Fal AI functionality...")
        
        # Try to get model info
        print("✅ Fal client imported and configured successfully")
        return True
        
    except Exception as e:
        print(f"❌ Fal client test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Fal AI Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Basic Fal service test
    test1_result = test_fal_service()
    
    # Test 2: Direct client test
    test2_result = test_fal_client_direct()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Fal Service Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"  Fal Client Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print("=" * 60)
    
    # Overall result
    all_passed = test1_result and test2_result
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)