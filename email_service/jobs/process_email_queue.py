#!/usr/bin/env python3
"""
Email queue processor job for Databricks.

This job runs periodically to process pending email requests and send avatar emails.

Usage:
    python process_email_queue.py [--batch-size=50] [--dry-run]
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from email_service.db_manager import email_db_manager
from email_service.brevo_service import brevo_email_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailQueueProcessor:
    """Process pending email requests from the queue."""
    
    def __init__(self, batch_size: int = 50, dry_run: bool = False):
        """Initialize the email queue processor.
        
        Args:
            batch_size: Number of emails to process in one run
            dry_run: If True, don't actually send emails
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.processed_count = 0
        self.success_count = 0
        self.failure_count = 0
        
    def process_queue(self):
        """Process pending email requests."""
        logger.info(f"Starting email queue processing (batch_size={self.batch_size}, dry_run={self.dry_run})")
        
        try:
            # Get pending requests
            pending_requests = email_db_manager.get_pending_email_requests(
                batch_size=self.batch_size,
                include_retries=True
            )
            
            if not pending_requests:
                logger.info("No pending email requests to process")
                return
            
            logger.info(f"Found {len(pending_requests)} pending email requests")
            
            # Process each request
            for request in pending_requests:
                self._process_single_request(request)
            
            # Log summary
            logger.info(
                f"Email queue processing completed. "
                f"Processed: {self.processed_count}, "
                f"Success: {self.success_count}, "
                f"Failed: {self.failure_count}"
            )
            
        except Exception as e:
            logger.error(f"Error processing email queue: {e}", exc_info=True)
            raise
    
    def _process_single_request(self, request: Dict[str, Any]):
        """Process a single email request.
        
        Args:
            request: Email request data with avatar information
        """
        email_request_id = request['email_request_id']
        recipient_email = request['recipient_email']
        
        logger.info(f"Processing email request {email_request_id} for {recipient_email}")
        
        try:
            self.processed_count += 1
            
            # Update status to sending
            if not self.dry_run:
                email_db_manager.update_email_status(
                    email_request_id, 
                    status='sending'
                )
            
            # Get avatar data
            avatar_data = request.get('avatar_data', {})
            avatar_path = avatar_data.get('generated_image_path')
            
            if not avatar_path:
                raise ValueError("No avatar image path found")
            
            # Check if file exists
            if not os.path.exists(avatar_path):
                raise FileNotFoundError(f"Avatar image not found at {avatar_path}")
            
            # Send email
            if self.dry_run:
                logger.info(f"DRY RUN: Would send email to {recipient_email}")
                success = True
                message_id = "dry-run-message-id"
                error_message = None
            else:
                success, message_id, error_message = brevo_email_service.send_avatar_email(
                    recipient_email=recipient_email,
                    recipient_name=request['recipient_name'],
                    avatar_path=avatar_path,
                    superhero=avatar_data.get('superhero', 'Unknown'),
                    color=avatar_data.get('color', 'Unknown'),
                    car=avatar_data.get('car', 'Unknown'),
                    request_id=request['avatar_request_id']
                )
            
            # Update status based on result
            if success:
                self.success_count += 1
                if not self.dry_run:
                    email_db_manager.update_email_status(
                        email_request_id,
                        status='sent',
                        smtp_message_id=message_id
                    )
                logger.info(f"Successfully sent email to {recipient_email}")
            else:
                self.failure_count += 1
                if not self.dry_run:
                    email_db_manager.update_email_status(
                        email_request_id,
                        status='failed',
                        error_message=error_message
                    )
                logger.error(f"Failed to send email to {recipient_email}: {error_message}")
                
        except Exception as e:
            self.failure_count += 1
            error_message = str(e)
            logger.error(f"Error processing request {email_request_id}: {error_message}", exc_info=True)
            
            if not self.dry_run:
                email_db_manager.update_email_status(
                    email_request_id,
                    status='failed',
                    error_message=error_message
                )


def main():
    """Main entry point for the email queue processor."""
    parser = argparse.ArgumentParser(description='Process email queue for avatar delivery')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=int(os.getenv('EMAIL_BATCH_SIZE', '50')),
        help='Number of emails to process in one batch'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually sending emails'
    )
    
    args = parser.parse_args()
    
    # Check if email feature is enabled
    if os.getenv('ENABLE_EMAIL_FEATURE', 'true').lower() != 'true':
        logger.info("Email feature is disabled. Exiting.")
        return
    
    # Create and run processor
    processor = EmailQueueProcessor(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    processor.process_queue()
    
    # Exit with appropriate code
    sys.exit(0 if processor.failure_count == 0 else 1)


if __name__ == '__main__':
    main()