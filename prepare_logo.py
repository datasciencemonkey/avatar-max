"""Script to prepare the CarMax logo for use in the application."""

from pathlib import Path
from PIL import Image
from logo_overlay import create_placeholder_logo


def prepare_carmax_logo():
    """
    Instructions for preparing the CarMax logo.
    """
    logo_path = Path("assets/carmax_logo.png")
    
    print("=" * 60)
    print("CarMax Logo Setup Instructions")
    print("=" * 60)
    
    if logo_path.exists():
        print(f"✅ Logo found at: {logo_path}")
        
        # Check logo properties
        try:
            logo = Image.open(logo_path)
            print(f"   Format: {logo.format}")
            print(f"   Size: {logo.size}")
            print(f"   Mode: {logo.mode}")
            
            if logo.mode != 'RGBA':
                print("\n⚠️  Logo should be in RGBA mode for transparency")
                print("   Converting to RGBA...")
                logo = logo.convert('RGBA')
                logo.save(logo_path)
                print("   ✅ Converted to RGBA")
                
        except Exception as e:
            print(f"❌ Error reading logo: {e}")
    else:
        print(f"❌ Logo not found at: {logo_path}")
        print("\nTo add the CarMax logo:")
        print("1. Save the CarMax logo image as: assets/carmax_logo.png")
        print("2. Preferably use a PNG with transparent background")
        print("3. Recommended size: at least 400px wide")
        print("\nCreating a placeholder logo for testing...")
        create_placeholder_logo(logo_path)
    
    print("\n" + "=" * 60)
    print("Logo Requirements:")
    print("- Format: PNG (preferred) or JPEG")
    print("- Background: Transparent (preferred) or white")
    print("- Size: At least 400px wide for good quality")
    print("- Location: assets/carmax_logo.png")
    print("=" * 60)


if __name__ == "__main__":
    prepare_carmax_logo()