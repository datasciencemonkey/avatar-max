"""Tests for email service functionality."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

# Add parent directories to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from email_service.brevo_service import BrevoEmailService
from email_service.models import EmailRequest


class TestBrevoEmailService:
    """Test Brevo email service functionality."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("BREVO_SMTP_PASSWORD", "test-password")
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_FROM_NAME", "Test Sender")
    
    @pytest.fixture
    def temp_avatar(self):
        """Create a temporary avatar image."""
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (512, 512), color='blue')
            img.save(f.name)
            yield f.name
            os.unlink(f.name)
    
    def test_initialization(self, mock_env):
        """Test email service initialization."""
        service = BrevoEmailService()
        assert service.smtp_server == "smtp-relay.brevo.com"
        assert service.smtp_port == 587
        assert service.smtp_login == "93330f001@smtp-brevo.com"
        assert service.from_email == "test@example.com"
    
    def test_initialization_without_password(self, monkeypatch):
        """Test that initialization fails without password."""
        monkeypatch.delenv("BREVO_SMTP_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="BREVO_SMTP_PASSWORD"):
            BrevoEmailService()
    
    @patch('smtplib.SMTP')
    def test_send_avatar_email_success(self, mock_smtp, mock_env, temp_avatar):
        """Test successful email sending."""
        # Setup mock SMTP
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        service = BrevoEmailService()
        
        # Send email
        success, message_id, error = service.send_avatar_email(
            recipient_email="user@example.com",
            recipient_name="Test User",
            avatar_path=temp_avatar,
            superhero="Iron Man",
            color="Red",
            car="Tesla",
            request_id="test-123"
        )
        
        assert success is True
        assert message_id is not None
        assert error is None
        
        # Verify SMTP was called
        mock_smtp.assert_called_once_with("smtp-relay.brevo.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("93330f001@smtp-brevo.com", "test-password")
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_avatar_email_failure(self, mock_smtp, mock_env, temp_avatar):
        """Test email sending failure."""
        # Setup mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        service = BrevoEmailService()
        
        # Send email
        success, message_id, error = service.send_avatar_email(
            recipient_email="user@example.com",
            recipient_name="Test User",
            avatar_path=temp_avatar,
            superhero="Batman",
            color="Black",
            car="Batmobile",
            request_id="test-456"
        )
        
        assert success is False
        assert message_id is None
        assert "SMTP connection failed" in error
    
    def test_render_templates(self, mock_env):
        """Test template rendering."""
        service = BrevoEmailService()
        
        # Test HTML template
        html = service._render_html_template(
            name="John Doe",
            superhero="Spider-Man",
            color="Red and Blue",
            car="Web Shooter"
        )
        assert "John Doe" in html
        assert "Spider-Man" in html
        assert "Red and Blue" in html
        assert "Web Shooter" in html
        
        # Test text template
        text = service._render_text_template(
            name="Jane Doe",
            superhero="Wonder Woman",
            color="Gold",
            car="Invisible Jet"
        )
        assert "Jane Doe" in text
        assert "Wonder Woman" in text
        assert "Gold" in text
        assert "Invisible Jet" in text


class TestEmailRequest:
    """Test EmailRequest model."""
    
    def test_can_retry(self):
        """Test retry logic."""
        # Can retry - failed with retries left
        request = EmailRequest(
            status='failed',
            retry_count=1,
            max_retries=3
        )
        assert request.can_retry() is True
        
        # Cannot retry - max retries reached
        request.retry_count = 3
        assert request.can_retry() is False
        
        # Cannot retry - already sent
        request.status = 'sent'
        request.retry_count = 0
        assert request.can_retry() is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        request = EmailRequest(
            email_request_id="test-123",
            avatar_request_id="avatar-456",
            recipient_email="test@example.com",
            recipient_name="Test User",
            status="pending"
        )
        
        data = request.to_dict()
        assert data['email_request_id'] == "test-123"
        assert data['avatar_request_id'] == "avatar-456"
        assert data['recipient_email'] == "test@example.com"
        assert data['recipient_name'] == "Test User"
        assert data['status'] == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])