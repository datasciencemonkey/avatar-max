"""Brevo SMTP email service implementation."""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from PIL import Image
import io

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class BrevoEmailService:
    """Email service using Brevo SMTP."""
    
    def __init__(self):
        """Initialize Brevo email service."""
        # SMTP Configuration
        self.smtp_server = os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com")
        self.smtp_port = int(os.getenv("BREVO_SMTP_PORT", "587"))
        self.smtp_login = os.getenv("BREVO_SMTP_LOGIN", "93330f001@smtp-brevo.com")
        self.smtp_password = os.getenv("BREVO_SMTP_PASSWORD")
        
        if not self.smtp_password:
            raise ValueError("BREVO_SMTP_PASSWORD environment variable is required")
        
        # Email settings
        self.from_email = os.getenv("EMAIL_FROM_ADDRESS", "avatars@innovationgarage.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Innovation Garage Superhero Creator")
        self.reply_to = os.getenv("EMAIL_REPLY_TO", self.from_email)
        
        # Template paths
        self.template_dir = Path(__file__).parent / "templates"
        
    def send_avatar_email(
        self,
        recipient_email: str,
        recipient_name: str,
        avatar_path: str,
        superhero: str,
        color: str,
        car: str,
        request_id: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send avatar email to recipient.
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Name of recipient
            avatar_path: Path to avatar image file
            superhero: Selected superhero
            color: Selected color
            car: Selected car
            request_id: Avatar request ID for tracking
            
        Returns:
            Tuple of (success, message_id, error_message)
        """
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = f"Your {superhero} Avatar is Ready! 🦸"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = recipient_email
            msg['Reply-To'] = self.reply_to
            
            # Add custom headers for tracking
            msg['X-Avatar-Request-ID'] = request_id
            msg['X-Mailer'] = "Innovation Garage Avatar Generator"
            
            # Create the HTML and text parts
            html_content = self._render_html_template(
                recipient_name, superhero, color, car
            )
            text_content = self._render_text_template(
                recipient_name, superhero, color, car
            )
            
            # Create alternative container for HTML/text
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Attach text and HTML parts
            msg_alternative.attach(MIMEText(text_content, 'plain'))
            msg_alternative.attach(MIMEText(html_content, 'html'))
            
            # Attach avatar image
            avatar_cid = self._attach_avatar_image(msg, avatar_path)
            
            # Update HTML content with image CID
            html_content = html_content.replace("{{AVATAR_CID}}", avatar_cid)
            
            # Re-attach updated HTML
            msg_alternative.get_payload()[1] = MIMEText(html_content, 'html')
            
            # Send email
            message_id = self._send_smtp_email(msg)
            
            logger.info(f"Email sent successfully to {recipient_email} with message ID: {message_id}")
            return True, message_id, None
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(f"Email send error for {recipient_email}: {error_msg}")
            return False, None, error_msg
    
    def _render_html_template(
        self,
        name: str,
        superhero: str,
        color: str,
        car: str
    ) -> str:
        """Render HTML email template."""
        template_path = self.template_dir / "avatar_email.html"
        
        # Default template if file doesn't exist
        if not template_path.exists():
            return self._get_default_html_template(name, superhero, color, car)
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        replacements = {
            "{{NAME}}": name,
            "{{SUPERHERO}}": superhero,
            "{{COLOR}}": color,
            "{{CAR}}": car,
            "{{YEAR}}": str(datetime.now().year),
            "{{AVATAR_CID}}": "avatar"  # Will be replaced with actual CID
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        return template
    
    def _render_text_template(
        self,
        name: str,
        superhero: str,
        color: str,
        car: str
    ) -> str:
        """Render text email template."""
        template_path = self.template_dir / "avatar_email.txt"
        
        # Default template if file doesn't exist
        if not template_path.exists():
            return self._get_default_text_template(name, superhero, color, car)
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        replacements = {
            "{{NAME}}": name,
            "{{SUPERHERO}}": superhero,
            "{{COLOR}}": color,
            "{{CAR}}": car,
            "{{YEAR}}": str(datetime.now().year)
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        return template
    
    def _attach_avatar_image(self, msg: MIMEMultipart, avatar_path: str) -> str:
        """Attach avatar image to email and return CID."""
        # Load and resize image for email
        with Image.open(avatar_path) as img:
            # Resize to max 800px width for email
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
        
        # Create image attachment
        img_attachment = MIMEImage(img_data, 'png')
        img_attachment.add_header('Content-ID', '<avatar>')
        img_attachment.add_header('Content-Disposition', 'inline', filename='superhero_avatar.png')
        msg.attach(img_attachment)
        
        # Also attach as downloadable attachment
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(img_data)
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            'attachment; filename="superhero_avatar.png"'
        )
        msg.attach(attachment)
        
        return "avatar"
    
    def _send_smtp_email(self, msg: MIMEMultipart) -> str:
        """Send email via SMTP and return message ID."""
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect to SMTP server
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.smtp_login, self.smtp_password)
            
            # Send email
            response = server.send_message(msg)
            
            # Get message ID from response or generate one
            message_id = msg.get('Message-ID', f"avatar-{datetime.now().timestamp()}")
            
            return message_id
    
    def _get_default_html_template(self, name: str, superhero: str, color: str, car: str) -> str:
        """Get default HTML template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Superhero Avatar is Ready!</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Your Superhero Avatar is Ready! 🦸</h1>
                </div>
                
                <div style="padding: 30px;">
                    <p style="font-size: 18px; color: #333;">Hi {name}!</p>
                    
                    <p style="font-size: 16px; color: #666; line-height: 1.6;">
                        Your amazing {superhero}-inspired avatar with {color} theme and your favorite {car} is ready!
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <img src="cid:{{{{AVATAR_CID}}}}" alt="Your Superhero Avatar" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                    </div>
                    
                    <p style="font-size: 16px; color: #666; line-height: 1.6;">
                        Your avatar is attached to this email. Feel free to download it and share your superhero transformation with friends!
                    </p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="font-size: 14px; color: #999;">
                            Created with ❤️ at Innovation Garage<br>
                            Powered by Databricks & CarMax
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_default_text_template(self, name: str, superhero: str, color: str, car: str) -> str:
        """Get default text template."""
        return f"""
Hi {name}!

Your Superhero Avatar is Ready! 🦸

Your amazing {superhero}-inspired avatar with {color} theme and your favorite {car} is ready!

Your avatar image is attached to this email. Feel free to download it and share your superhero transformation with friends!

---
Created with ❤️ at Innovation Garage
Powered by Databricks & CarMax
        """.strip()


# Create global email service instance
brevo_email_service = BrevoEmailService()