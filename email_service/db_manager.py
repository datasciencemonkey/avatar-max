"""Database manager extensions for email service."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import DatabaseManager, AvatarRequest
from .models import EmailRequest


class EmailDatabaseManager(DatabaseManager):
    """Extended database manager with email-specific functionality."""
    
    def __init__(self):
        """Initialize email database manager."""
        super().__init__()
        # Ensure email tables are created
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
    
    def create_email_request(
        self,
        avatar_request_id: str,
        recipient_email: str,
        recipient_name: str
    ) -> str:
        """Create a new email request.
        
        Args:
            avatar_request_id: ID of the avatar request
            recipient_email: Email address to send to
            recipient_name: Name of the recipient
            
        Returns:
            email_request_id of the created record
        """
        with self.get_session() as session:
            email_request = EmailRequest(
                avatar_request_id=avatar_request_id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                status='pending'
            )
            session.add(email_request)
            session.flush()
            return email_request.email_request_id
    
    def get_pending_email_requests(
        self, 
        batch_size: int = 50,
        include_retries: bool = True
    ) -> List[Dict[str, Any]]:
        """Get pending email requests for processing.
        
        Args:
            batch_size: Maximum number of requests to return
            include_retries: Whether to include failed requests that can be retried
            
        Returns:
            List of email request dictionaries with avatar request data
        """
        with self.get_session() as session:
            query = session.query(EmailRequest, AvatarRequest).join(
                AvatarRequest,
                EmailRequest.avatar_request_id == AvatarRequest.request_id
            )
            
            # Build conditions for pending requests
            conditions = [EmailRequest.status == 'pending']
            
            if include_retries:
                # Include failed requests that can be retried
                retry_condition = and_(
                    EmailRequest.status == 'failed',
                    EmailRequest.retry_count < EmailRequest.max_retries,
                    or_(
                        EmailRequest.next_retry_at.is_(None),
                        EmailRequest.next_retry_at <= datetime.utcnow()
                    )
                )
                conditions.append(retry_condition)
            
            # Apply conditions
            query = query.filter(or_(*conditions))
            
            # Order by creation time (oldest first)
            query = query.order_by(EmailRequest.created_at.asc())
            
            # Limit batch size
            query = query.limit(batch_size)
            
            # Execute and format results
            results = []
            for email_req, avatar_req in query.all():
                result = email_req.to_dict()
                result['avatar_data'] = avatar_req.to_dict()
                results.append(result)
            
            return results
    
    def update_email_status(
        self,
        email_request_id: str,
        status: str,
        smtp_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        """Update the status of an email request.
        
        Args:
            email_request_id: ID of the email request
            status: New status (sending, sent, failed, bounced)
            smtp_message_id: Message ID from SMTP server
            error_message: Error message if failed
            error_code: Error code if failed
        """
        with self.get_session() as session:
            email_req = session.query(EmailRequest).filter_by(
                email_request_id=email_request_id
            ).first()
            
            if email_req:
                email_req.status = status
                email_req.updated_at = datetime.utcnow()
                
                if status == 'sent':
                    email_req.sent_at = datetime.utcnow()
                    if smtp_message_id:
                        email_req.smtp_message_id = smtp_message_id
                
                elif status == 'failed':
                    email_req.retry_count += 1
                    if error_message:
                        email_req.error_message = error_message
                    if error_code:
                        email_req.error_code = error_code
                    
                    # Set next retry time with exponential backoff
                    if email_req.retry_count < email_req.max_retries:
                        backoff_minutes = 5 * (2 ** (email_req.retry_count - 1))
                        email_req.next_retry_at = datetime.utcnow() + timedelta(
                            minutes=backoff_minutes
                        )
    
    def mark_email_requested(self, avatar_request_id: str):
        """Mark an avatar request as having email requested.
        
        Args:
            avatar_request_id: ID of the avatar request
        """
        with self.get_session() as session:
            avatar_req = session.query(AvatarRequest).filter_by(
                request_id=avatar_request_id
            ).first()
            
            if avatar_req:
                # Add email_requested field to AvatarRequest if not exists
                if hasattr(avatar_req, 'email_requested'):
                    avatar_req.email_requested = True
                if hasattr(avatar_req, 'email_request_time'):
                    avatar_req.email_request_time = datetime.utcnow()
    
    def get_email_request_status(self, email_request_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an email request.
        
        Args:
            email_request_id: ID of the email request
            
        Returns:
            Email request data or None if not found
        """
        with self.get_session() as session:
            email_req = session.query(EmailRequest).filter_by(
                email_request_id=email_request_id
            ).first()
            
            return email_req.to_dict() if email_req else None
    
    def get_email_statistics(self) -> Dict[str, Any]:
        """Get email delivery statistics.
        
        Returns:
            Dictionary with email statistics
        """
        with self.get_session() as session:
            total = session.query(EmailRequest).count()
            pending = session.query(EmailRequest).filter_by(status='pending').count()
            sent = session.query(EmailRequest).filter_by(status='sent').count()
            failed = session.query(EmailRequest).filter_by(status='failed').count()
            
            # Get retry statistics
            retrying = session.query(EmailRequest).filter(
                and_(
                    EmailRequest.status == 'failed',
                    EmailRequest.retry_count < EmailRequest.max_retries
                )
            ).count()
            
            return {
                'total_requests': total,
                'pending': pending,
                'sent': sent,
                'failed': failed,
                'retrying': retrying,
                'success_rate': (sent / total * 100) if total > 0 else 0
            }


# Create global email database manager instance
email_db_manager = EmailDatabaseManager()