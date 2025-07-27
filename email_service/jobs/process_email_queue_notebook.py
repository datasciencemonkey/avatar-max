# Databricks notebook source
# MAGIC %md
# MAGIC # Email Queue Processor
# MAGIC 
# MAGIC This notebook processes pending email requests from the superhero avatar generator.
# MAGIC It runs as a scheduled job every 5 minutes.

# COMMAND ----------

# MAGIC %pip install sqlalchemy==2.0.36 psycopg2-binary==2.9.10 pillow==11.1.0 email-validator==2.2.0

# COMMAND ----------

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get parameters
dbutils.widgets.text("batch_size", "50", "Batch Size")
dbutils.widgets.text("dry_run", "false", "Dry Run Mode")

batch_size = int(dbutils.widgets.get("batch_size"))
dry_run = dbutils.widgets.get("dry_run").lower() == "true"

logger.info(f"Starting email queue processor - Batch size: {batch_size}, Dry run: {dry_run}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Services

# COMMAND ----------

# Import email service modules
from email_service.db_manager import EmailDatabaseManager
from email_service.brevo_service import BrevoEmailService
from email_service.models import EmailRequest

# Initialize services
email_db_manager = EmailDatabaseManager()
brevo_email_service = BrevoEmailService()

logger.info("Services initialized successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Process Email Queue

# COMMAND ----------

class EmailQueueProcessor:
    """Process pending email requests from the queue."""
    
    def __init__(self, batch_size: int = 50, dry_run: bool = False):
        """Initialize the email queue processor."""
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.processed_count = 0
        self.success_count = 0
        self.failure_count = 0
        
    def process_queue(self):
        """Process pending email requests."""
        logger.info(f"Starting email queue processing - Batch size: {self.batch_size}")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No emails will be sent")
        
        # Get pending email requests
        pending_requests = email_db_manager.get_pending_email_requests(limit=self.batch_size)
        
        if not pending_requests:
            logger.info("No pending email requests found")
            return
        
        logger.info(f"Found {len(pending_requests)} pending email requests")
        
        # Process each request
        for request in pending_requests:
            self.process_email_request(request)
        
        # Log summary
        logger.info(f"Processing complete - Total: {self.processed_count}, Success: {self.success_count}, Failed: {self.failure_count}")
        
        return {
            "processed": self.processed_count,
            "success": self.success_count,
            "failed": self.failure_count
        }
    
    def process_email_request(self, request: Dict[str, Any]):
        """Process a single email request."""
        request_id = request.get('email_request_id')
        avatar_request_id = request.get('avatar_request_id')
        
        logger.info(f"Processing email request: {request_id}")
        self.processed_count += 1
        
        try:
            # Update status to sending
            if not self.dry_run:
                email_db_manager.update_email_status(
                    email_request_id=request_id,
                    status='sending'
                )
            
            # Get avatar details
            avatar_details = self._get_avatar_details(avatar_request_id)
            if not avatar_details:
                raise Exception(f"Avatar request not found: {avatar_request_id}")
            
            # Determine avatar path
            avatar_path = self._get_avatar_path(avatar_details)
            if not avatar_path or not os.path.exists(avatar_path):
                raise Exception(f"Avatar file not found: {avatar_path}")
            
            # Send email
            if self.dry_run:
                logger.info(f"DRY RUN - Would send email to: {request.get('recipient_email')}")
                success = True
                message_id = "dry-run-message-id"
                error = None
            else:
                success, message_id, error = brevo_email_service.send_avatar_email(
                    recipient_email=request.get('recipient_email'),
                    recipient_name=request.get('recipient_name'),
                    avatar_path=avatar_path,
                    superhero=avatar_details.get('superhero'),
                    color=avatar_details.get('color'),
                    car=avatar_details.get('car'),
                    request_id=avatar_request_id
                )
            
            if success:
                # Update status to sent
                if not self.dry_run:
                    email_db_manager.update_email_status(
                        email_request_id=request_id,
                        status='sent',
                        smtp_message_id=message_id
                    )
                logger.info(f"Email sent successfully: {request_id} (Message ID: {message_id})")
                self.success_count += 1
            else:
                # Update status to failed
                if not self.dry_run:
                    email_db_manager.update_email_status(
                        email_request_id=request_id,
                        status='failed',
                        error_message=error,
                        error_code='SMTP_SEND_FAILED'
                    )
                logger.error(f"Failed to send email: {request_id} - {error}")
                self.failure_count += 1
                
        except Exception as e:
            # Update status to failed
            if not self.dry_run:
                email_db_manager.update_email_status(
                    email_request_id=request_id,
                    status='failed',
                    error_message=str(e),
                    error_code='PROCESSING_ERROR'
                )
            logger.error(f"Error processing email request {request_id}: {e}")
            self.failure_count += 1
    
    def _get_avatar_details(self, avatar_request_id: str) -> Dict[str, Any]:
        """Get avatar details from database."""
        # This would normally query the avatar_requests table
        # For now, using the email_db_manager to get basic details
        conn = email_db_manager.engine.connect()
        try:
            result = conn.execute(
                """
                SELECT name, email, superhero, color, car, local_path, databricks_path
                FROM avatar_requests
                WHERE request_id = %s
                """,
                (avatar_request_id,)
            ).fetchone()
            
            if result:
                return {
                    'name': result[0],
                    'email': result[1],
                    'superhero': result[2],
                    'color': result[3],
                    'car': result[4],
                    'local_path': result[5],
                    'databricks_path': result[6]
                }
        finally:
            conn.close()
        
        return None
    
    def _get_avatar_path(self, avatar_details: Dict[str, Any]) -> str:
        """Determine the correct avatar file path."""
        # Check Databricks volume first
        if avatar_details.get('databricks_path'):
            databricks_volume = os.getenv('DATABRICKS_VOLUME', '/Volumes/main/sgfs/sg-vol/avatarmax')
            databricks_path = os.path.join(databricks_volume, avatar_details['databricks_path'])
            if os.path.exists(databricks_path):
                return databricks_path
        
        # Fall back to local path
        if avatar_details.get('local_path'):
            return avatar_details['local_path']
        
        return None

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run the Processor

# COMMAND ----------

# Create processor instance
processor = EmailQueueProcessor(batch_size=batch_size, dry_run=dry_run)

# Process the queue
results = processor.process_queue()

# Display results
print(f"\n{'='*60}")
print("EMAIL QUEUE PROCESSING RESULTS")
print(f"{'='*60}")
print(f"Total Processed: {results['processed']}")
print(f"Successful: {results['success']}")
print(f"Failed: {results['failed']}")
print(f"{'='*60}\n")

# Return results for job monitoring
dbutils.notebook.exit(results)