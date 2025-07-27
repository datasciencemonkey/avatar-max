# Email Service Module

This module handles email delivery of superhero avatars using Brevo SMTP service.

## Overview

The email service provides:
- Queue-based email delivery system
- Brevo SMTP integration
- HTML/text email templates
- Retry logic with exponential backoff
- Database tracking of email status
- Batch processing via Databricks jobs

## Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# Brevo SMTP Configuration
BREVO_SMTP_SERVER=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=93330f001@smtp-brevo.com
BREVO_SMTP_PASSWORD=your_brevo_smtp_api_key

# Email Settings
EMAIL_FROM_ADDRESS=avatars@yourdomain.com
EMAIL_FROM_NAME=Innovation Garage Superhero Creator
EMAIL_REPLY_TO=noreply@yourdomain.com
EMAIL_BATCH_SIZE=50
EMAIL_MAX_RETRIES=3
ENABLE_EMAIL_FEATURE=true
```

## Architecture

### Components

1. **models.py** - Database models for email_requests table
2. **db_manager.py** - Database operations for email queue
3. **brevo_service.py** - Brevo SMTP email sending implementation
4. **templates/** - HTML and text email templates
5. **jobs/** - Databricks job for processing email queue

### Database Schema

The `email_requests` table tracks:
- Email request ID and avatar request ID
- Recipient email and name
- Status (pending, sending, sent, failed, bounced)
- Timestamps and retry information
- SMTP message ID for tracking

### Email Flow

1. User clicks "Email My Avatar" button
2. Email request is created in database with status='pending'
3. Databricks job runs every 5 minutes to process queue
4. Job fetches pending requests and sends emails via Brevo
5. Status is updated based on send result
6. Failed emails are retried up to 3 times with exponential backoff

## Usage

### Manual Testing

Test the email service manually:

```bash
# Send test email with auto-generated avatar
python email_service/tests/test_email_manual.py --email your@email.com

# Send test email with specific avatar
python email_service/tests/test_email_manual.py --email your@email.com --avatar path/to/avatar.png
```

### Processing Email Queue

Run the email queue processor:

```bash
# Process email queue (normal mode)
python email_service/jobs/process_email_queue.py

# Dry run (no emails sent)
python email_service/jobs/process_email_queue.py --dry-run

# Custom batch size
python email_service/jobs/process_email_queue.py --batch-size 100
```

### Databricks Job Setup

1. Upload the code to your Databricks workspace
2. Create a new job using `email_job_config.json`
3. Configure cluster and credentials
4. Schedule runs every 5 minutes

## Templates

Email templates are located in `templates/`:
- `avatar_email.html` - Responsive HTML email template
- `avatar_email.txt` - Plain text fallback

Templates support placeholders:
- `{{NAME}}` - Recipient's name
- `{{SUPERHERO}}` - Selected superhero
- `{{COLOR}}` - Selected color
- `{{CAR}}` - Selected car
- `{{AVATAR_CID}}` - Avatar image content ID

## Testing

Run unit tests:

```bash
# Run email service tests
uv run pytest email_service/tests/test_email_service.py -v

# Run with coverage
uv run pytest email_service/tests/ --cov=email_service
```

## Monitoring

Monitor email delivery:
- Check `email_requests` table for status
- Review job logs in Databricks
- Monitor SMTP logs in Brevo dashboard

### Useful Queries

```sql
-- Get email statistics
SELECT 
    status, 
    COUNT(*) as count,
    AVG(retry_count) as avg_retries
FROM email_requests
GROUP BY status;

-- Find failed emails
SELECT * FROM email_requests
WHERE status = 'failed' 
AND retry_count >= max_retries
ORDER BY created_at DESC;

-- Recent email activity
SELECT 
    er.*, 
    ar.name, 
    ar.superhero
FROM email_requests er
JOIN avatar_requests ar ON er.avatar_request_id = ar.request_id
ORDER BY er.created_at DESC
LIMIT 50;
```

## Troubleshooting

### Common Issues

1. **SMTP Authentication Failed**
   - Verify BREVO_SMTP_PASSWORD is correct
   - Check Brevo account is active

2. **Emails Not Sending**
   - Check ENABLE_EMAIL_FEATURE=true
   - Verify Databricks job is running
   - Check database connectivity

3. **Emails in Spam**
   - Configure SPF/DKIM for your domain
   - Use proper FROM address
   - Check email content scoring

4. **Avatar Images Not Attaching**
   - Verify file paths are correct
   - Check file permissions
   - Ensure images exist in storage

## Security

- SMTP credentials stored as environment variables
- TLS encryption for SMTP connection
- No sensitive data in email content
- Rate limiting to prevent abuse

## Future Enhancements

- [ ] Add email open/click tracking
- [ ] Support multiple email providers
- [ ] Implement bounce handling
- [ ] Add email analytics dashboard
- [ ] Support batch email sending
- [ ] Add unsubscribe functionality