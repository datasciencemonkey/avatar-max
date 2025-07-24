#!/usr/bin/env python3
"""
Standalone test script for Databricks volume write operations.
Tests writing to /Volumes/main/sgfs/sg-vol/avatarmax/ without app dependencies.
"""

import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_test_image(text: str, size=(400, 300), color='blue'):
    """Create a simple test image with text."""
    # Create image
    image = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(image)
    
    # Add text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except:
        font = ImageFont.load_default()
    
    # Center text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    return image


def test_credentials():
    """Test and display Databricks credentials."""
    print("=== Databricks Credentials Check ===")
    
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not host:
        print("❌ DATABRICKS_HOST not set")
        return False
    else:
        print(f"✅ DATABRICKS_HOST: {host}")
    
    if not token:
        print("❌ DATABRICKS_TOKEN not set")
        return False
    else:
        print(f"✅ DATABRICKS_TOKEN: {'*' * 8}{token[-4:]}")  # Show last 4 chars
    
    return True


def test_workspace_connection():
    """Test basic Databricks workspace connection."""
    print("\n=== Testing Workspace Connection ===")
    
    try:
        w = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN")
        )
        
        # Try to get current user to test authentication
        current_user = w.current_user.me()
        print(f"✅ Connected as: {current_user.user_name}")
        return w
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def test_volume_write(w: WorkspaceClient, folder: str, filename: str, image: Image.Image):
    """Test writing a single file to a volume folder."""
    volume_base = "/Volumes/main/sgfs/sg-vol/avatarmax"
    file_path = f"{volume_base}/{folder}/{filename}"
    
    print(f"\n=== Testing Write to {folder} ===")
    print(f"Target path: {file_path}")
    
    try:
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Upload to Databricks
        print("Uploading...")
        w.files.upload(file_path, buffer, overwrite=True)
        
        print(f"✅ Successfully uploaded to: {file_path}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Upload failed: {error_msg}")
        
        # Provide specific error guidance
        if "RESOURCE_DOES_NOT_EXIST" in error_msg:
            print("   → The volume or folder doesn't exist")
            print(f"   → Try creating the folder first: {volume_base}/{folder}")
        elif "PERMISSION_DENIED" in error_msg:
            print("   → You don't have write permissions to this volume")
        elif "Invalid access token" in error_msg:
            print("   → Your Databricks token is invalid or expired")
            
        return False


def test_folder_creation(w: WorkspaceClient, folder: str):
    """Test creating a folder in the volume."""
    volume_base = "/Volumes/main/sgfs/sg-vol/avatarmax"
    folder_path = f"{volume_base}/{folder}"
    
    print(f"\n=== Testing Folder Creation: {folder} ===")
    print(f"Target path: {folder_path}")
    
    try:
        # Try to create a dummy file to force folder creation
        dummy_content = io.BytesIO(b"test")
        dummy_path = f"{folder_path}/.test"
        
        w.files.upload(dummy_path, dummy_content, overwrite=True)
        print(f"✅ Folder created/verified: {folder_path}")
        
        # Try to delete the dummy file
        try:
            w.files.delete(dummy_path)
            print("✅ Cleaned up test file")
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ Folder creation failed: {e}")
        return False


def main():
    """Run all volume write tests."""
    print("=== Databricks Volume Write Test ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target volume: /Volumes/main/sgfs/sg-vol/avatarmax/\n")
    
    # Step 1: Check credentials
    if not test_credentials():
        print("\n❌ Missing credentials. Please set DATABRICKS_HOST and DATABRICKS_TOKEN in .env")
        return False
    
    # Step 2: Test connection
    w = test_workspace_connection()
    if not w:
        print("\n❌ Cannot connect to Databricks. Check your credentials.")
        return False
    
    # Step 3: Test folder creation
    folders_created = True
    for folder in ["avatars", "originals"]:
        if not test_folder_creation(w, folder):
            folders_created = False
    
    if not folders_created:
        print("\n⚠️  Folder creation failed. The volume might not exist or you lack permissions.")
        print("   Please ensure /Volumes/main/sgfs/sg-vol/avatarmax exists in your Databricks workspace.")
    
    # Step 4: Test file writes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test avatar write
    avatar_image = create_test_image("Test Avatar", color='purple')
    avatar_filename = f"test_avatar_{timestamp}.png"
    avatar_success = test_volume_write(w, "avatars", avatar_filename, avatar_image)
    
    # Test original write
    original_image = create_test_image("Test Original", color='green')
    original_filename = f"test_original_{timestamp}.png"
    original_success = test_volume_write(w, "originals", original_filename, original_image)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Connection: ✅ SUCCESS")
    print(f"Avatars folder: {'✅ SUCCESS' if avatar_success else '❌ FAILED'}")
    print(f"Originals folder: {'✅ SUCCESS' if original_success else '❌ FAILED'}")
    
    if avatar_success and original_success:
        print("\n✅ All tests passed! Volume writes are working correctly.")
        print("\nYou can verify the uploaded files in Databricks:")
        print(f"  - /Volumes/main/sgfs/sg-vol/avatarmax/avatars/{avatar_filename}")
        print(f"  - /Volumes/main/sgfs/sg-vol/avatarmax/originals/{original_filename}")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
    
    return avatar_success and original_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)