"""Email service module for sending superhero avatars via email."""

from .brevo_service import BrevoEmailService
from .models import EmailRequest

__all__ = ["BrevoEmailService", "EmailRequest"]