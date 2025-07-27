"""Database models for email service."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class EmailRequest(Base):
    """Model for email delivery requests."""
    __tablename__ = 'email_requests'
    
    # Primary key
    email_request_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to avatar_requests
    avatar_request_id = Column(String(36), ForeignKey('avatar_requests.request_id'), nullable=False)
    
    # Recipient information
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(100), nullable=False)
    
    # Status tracking
    status = Column(String(20), default='pending', nullable=False)  
    # Status values: pending, sending, sent, failed, bounced
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Retry handling
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Email provider tracking
    smtp_message_id = Column(String(255), nullable=True)  # Brevo message ID
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_email_requests_status', 'status'),
        Index('idx_email_requests_avatar_id', 'avatar_request_id'),
        Index('idx_email_requests_pending', 'status', 'next_retry_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'email_request_id': self.email_request_id,
            'avatar_request_id': self.avatar_request_id,
            'recipient_email': self.recipient_email,
            'recipient_name': self.recipient_name,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'smtp_message_id': self.smtp_message_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def can_retry(self) -> bool:
        """Check if this request can be retried."""
        return (
            self.status in ['failed', 'pending'] and 
            self.retry_count < self.max_retries
        )
    
    def should_process_now(self) -> bool:
        """Check if this request should be processed now."""
        if self.status != 'pending':
            return False
        
        if self.next_retry_at is None:
            return True
            
        return datetime.utcnow() >= self.next_retry_at