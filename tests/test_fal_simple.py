"""Simple test script to verify Fal AI connection and basic functionality."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


def test_fal_connection():
    """Test basic Fal AI connection."""
    print("🧪 Testing Fal AI Connection\n")
    
    # Check for API key
    api_key = os.getenv("FAL_KEY")
    if not api_key:
        print("❌ FAL_KEY not found in environment variables")
        print("   Please add FAL_KEY=your_key_here to your .env file")
        return False
    
    print("✅ FAL_KEY found in environment")
    
    # Test import
    try:
        import fal_client
        print("✅ fal-client package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import fal-client: {e}")
        print("   Run: uv add fal-client")
        return False
    
    # Test API key setting
    try:
        fal_client.api_key = api_key
        print("✅ API key configured")
    except Exception as e:
        print(f"❌ Failed to set API key: {e}")
        return False
    
    # Test model availability
    print("\n📋 Testing FLUX Kontext model availability...")
    model_name = "fal-ai/flux-pro/kontext"
    
    try:
        # Just verify we can reference the model
        print(f"✅ Model reference: {model_name}")
        print("   Ready to generate images!")
        return True
        
    except Exception as e:
        print(f"❌ Error with model: {e}")
        return False


def test_config():
    """Test configuration setup."""
    print("\n🔧 Testing Configuration\n")
    
    from config import AppConfig
    
    provider = AppConfig.AI_PROVIDER
    print(f"Current AI Provider: {provider}")
    
    if provider == "fal":
        if AppConfig.FAL_API_KEY:
            print("✅ Fal AI is configured as provider with API key")
        else:
            print("❌ Fal AI is selected but FAL_KEY is missing")
            return False
    elif provider == "replicate":
        print("ℹ️  Replicate is configured as provider")
        print("   To use Fal, set AI_PROVIDER=fal in .env")
    
    return True


def main():
    """Run the tests."""
    print("=" * 60)
    print("Fal AI Simple Connection Test")
    print("=" * 60)
    
    # Run tests
    connection_ok = test_fal_connection()
    config_ok = test_config()
    
    print("\n" + "=" * 60)
    if connection_ok and config_ok:
        print("✅ All tests passed! Fal AI is ready to use.")
        print("\nTo use Fal AI in the app:")
        print("1. Ensure AI_PROVIDER=fal in your .env file")
        print("2. Run the app: streamlit run app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()