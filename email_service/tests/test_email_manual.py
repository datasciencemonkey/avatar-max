#!/usr/bin/env python3
"""
Manual test script for email service.

Usage:
    python test_email_manual.py --email your@email.com [--avatar path/to/avatar.png]
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from email_service.brevo_service import BrevoEmailService


def create_test_avatar():
    """Create a test superhero avatar image."""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw superhero-style background
    draw.rectangle([0, 0, 512, 256], fill=(135, 206, 235))  # Sky
    draw.rectangle([0, 256, 512, 512], fill=(34, 139, 34))  # Ground
    
    # Draw a simple superhero figure
    # Body
    draw.rectangle([206, 200, 306, 350], fill=(255, 0, 0))  # Red suit
    
    # Head
    draw.ellipse([226, 150, 286, 210], fill=(255, 220, 177))  # Face
    
    # Cape
    draw.polygon([(206, 220), (160, 380), (352, 380), (306, 220)], fill=(139, 0, 0))
    
    # Add "S" logo
    draw.text((246, 250), "S", fill=(255, 255, 0))
    
    # Save to temp file
    temp_path = Path("/tmp/test_superhero_avatar.png")
    img.save(temp_path)
    
    return str(temp_path)


def test_email_send(email_address: str, avatar_path: str = None):
    """Test sending an email with avatar."""
    print("\n" + "="*60)
    print("EMAIL SERVICE MANUAL TEST")
    print("="*60)
    
    # Check for SMTP password
    if not os.getenv("BREVO_SMTP_PASSWORD"):
        print("\n❌ ERROR: BREVO_SMTP_PASSWORD not set!")
        print("Please set your Brevo SMTP password in .env file")
        return False
    
    print(f"\n📧 Testing email to: {email_address}")
    
    # Create test avatar if not provided
    if not avatar_path:
        print("🎨 Creating test avatar...")
        avatar_path = create_test_avatar()
        print(f"✅ Test avatar created: {avatar_path}")
    else:
        print(f"📷 Using provided avatar: {avatar_path}")
    
    # Initialize email service
    try:
        print("\n🔧 Initializing email service...")
        service = BrevoEmailService()
        print("✅ Email service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize email service: {e}")
        return False
    
    # Send test email
    print("\n📤 Sending test email...")
    try:
        success, message_id, error = service.send_avatar_email(
            recipient_email=email_address,
            recipient_name="Test User",
            avatar_path=avatar_path,
            superhero="Test Hero",
            color="Rainbow",
            car="Test Mobile",
            request_id="test-manual-001"
        )
        
        if success:
            print(f"✅ Email sent successfully!")
            print(f"📬 Message ID: {message_id}")
            print(f"\n🎉 Check your inbox at {email_address}")
            print("💡 Also check spam folder just in case")
            return True
        else:
            print(f"❌ Failed to send email: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
    
    finally:
        print("\n" + "="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test email service manually')
    parser.add_argument(
        '--email',
        required=True,
        help='Email address to send test email to'
    )
    parser.add_argument(
        '--avatar',
        help='Path to avatar image (optional, will create test image if not provided)'
    )
    
    args = parser.parse_args()
    
    # Validate email
    from email_validator import validate_email, EmailNotValidError
    try:
        validate_email(args.email)
    except EmailNotValidError:
        print(f"❌ Invalid email address: {args.email}")
        sys.exit(1)
    
    # Run test
    success = test_email_send(args.email, args.avatar)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()