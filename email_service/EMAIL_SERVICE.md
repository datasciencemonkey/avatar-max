# Email Service - Technical Documentation

**Last Updated:** 2025-01-27 18:45:00 UTC

## How the Email Feature Works

This document provides a detailed technical explanation of the email delivery system for the Superhero Avatar Generator.

### 🎯 User Journey

1. **User Creates Avatar**
   - User completes the 5-step wizard
   - Avatar is generated and saved to storage (local or Databricks volume)
   - Database record created with avatar details and file paths

2. **User Clicks "Email My Avatar"**
   - Orange gradient button prominently displayed next to download button
   - When clicked, the system:
     ```python
     # Creates email request in database
     email_request_id = email_db_manager.create_email_request(
         avatar_request_id=st.session_state.request_id,
         recipient_email=email,
         recipient_name=name
     )
     ```
   - Shows immediate feedback: "✅ We'll email your avatar to **your@email.com** within 5 minutes!"
   - Additional info message: "💡 Check your inbox (and spam folder just in case)"

3. **Email Gets Queued**
   - New entry created in `email_requests` table with status='pending'
   - Links to the avatar request via foreign key relationship
   - Tracks recipient information and request timestamp

### ⚙️ Backend Processing

#### Database Architecture

The email system uses a dedicated table for tracking email requests:

```sql
CREATE TABLE email_requests (
    email_request_id VARCHAR(36) PRIMARY KEY,
    avatar_request_id VARCHAR(36) REFERENCES avatar_requests(request_id),
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP NULL,
    error_message TEXT NULL,
    error_code VARCHAR(50) NULL,
    smtp_message_id VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Databricks Job Processing

The email queue is processed by a scheduled Databricks job that runs every 5 minutes:

```python
# process_email_queue.py workflow
1. Query database for pending email requests
2. Fetch up to 50 requests per batch (configurable)
3. Include failed requests eligible for retry
4. For each request:
   - Load avatar image from storage path
   - Initialize Brevo SMTP connection
   - Compose and send email with avatar
   - Update status in database
   - Handle errors with retry logic
```

### 📧 Email Delivery Process

#### 1. **SMTP Configuration**

The system uses Brevo (formerly Sendinblue) as the SMTP provider:

```python
# Brevo SMTP Settings
SMTP Server: smtp-relay.brevo.com
Port: 587 (TLS encryption)
Login: 93330f001@smtp-brevo.com
Authentication: API Key (stored as BREVO_SMTP_PASSWORD)
```

#### 2. **Email Composition**

The system creates a multipart MIME email with:

- **HTML Version**: Responsive template with inline CSS
- **Plain Text Version**: Fallback for text-only clients
- **Image Attachments**:
  - Inline image (CID) for HTML display
  - File attachment for download

```python
# Email structure
MIMEMultipart('related')
├── MIMEMultipart('alternative')
│   ├── MIMEText(text_content, 'plain')
│   └── MIMEText(html_content, 'html')
├── MIMEImage(avatar_data) [Content-ID: avatar]
└── MIMEBase(avatar_data) [Attachment: superhero_avatar.png]
```

#### 3. **Template Processing**

Templates use placeholder substitution:

```html
<!-- HTML Template Placeholders -->
Hi {{NAME}}!

Your incredible {{SUPERHERO}}-inspired avatar is ready! 
We've transformed you into a superhero with your chosen {{COLOR}} theme, 
and yes, we included your favorite ride - the {{CAR}}!

<img src="cid:{{AVATAR_CID}}" alt="Your Superhero Avatar">
```

#### 4. **Sending Workflow**

```python
def send_avatar_email():
    # 1. Load and resize avatar image (max 800px width)
    with Image.open(avatar_path) as img:
        if img.width > 800:
            img = resize_image(img, max_width=800)
    
    # 2. Create MIME message structure
    msg = create_multipart_message()
    
    # 3. Render templates with user data
    html = render_html_template(name, superhero, color, car)
    text = render_text_template(name, superhero, color, car)
    
    # 4. Attach content and images
    attach_alternatives(msg, html, text)
    attach_avatar_images(msg, avatar_data)
    
    # 5. Send via SMTP with TLS
    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
```

### 🔄 Reliability Features

#### Retry Logic

The system implements exponential backoff for failed emails:

- **Maximum Retries**: 3 attempts
- **Backoff Schedule**: 
  - 1st retry: 5 minutes
  - 2nd retry: 10 minutes
  - 3rd retry: 20 minutes

```python
# Retry calculation
if email_failed and retry_count < max_retries:
    retry_count += 1
    backoff_minutes = 5 * (2 ** (retry_count - 1))
    next_retry_at = current_time + timedelta(minutes=backoff_minutes)
```

#### Status Flow

```
┌─────────┐     ┌──────────┐     ┌────────┐
│ pending │────▶│ sending  │────▶│  sent  │ ✓
└─────────┘     └──────────┘     └────────┘
                      │
                      ▼
                ┌──────────┐
                │  failed  │
                └──────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Retry Logic   │
              │ (up to 3x)    │
              └───────────────┘
                      │
                ┌─────┴─────┐
                ▼           ▼
           ┌────────┐  ┌─────────┐
           │  sent  │  │ failed  │
           └────────┘  └─────────┘
                       (max retries)
```

### 🏗️ System Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Streamlit UI  │────────▶│   PostgreSQL    │
│                 │         │   Database      │
│ [Email Button]  │         │                 │
└─────────────────┘         │ - avatar_requests│
                            │ - email_requests │
                            └─────────────────┘
                                     ▲
                                     │
                            ┌────────┴────────┐
                            │ Databricks Job  │
                            │                 │
                            │ Runs every      │
                            │ 5 minutes       │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ Email Processor │
                            │                 │
                            │ - Load avatars  │
                            │ - Send emails   │
                            │ - Update status │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Brevo SMTP     │
                            │                 │
                            │ TLS Port 587    │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  User Inbox     │
                            │                 │
                            │ 📧 Avatar Email │
                            └─────────────────┘
```

### 🔍 Key Components Explained

#### 1. **`models.py`** - Data Models
- Defines `EmailRequest` SQLAlchemy model
- Includes methods for retry eligibility
- Tracks all email metadata

#### 2. **`db_manager.py`** - Database Operations
- `create_email_request()` - Queue new email
- `get_pending_email_requests()` - Fetch batch for processing
- `update_email_status()` - Track delivery status
- `get_email_statistics()` - Monitor performance

#### 3. **`brevo_service.py`** - SMTP Integration
- Handles SMTP connection with TLS
- Composes multipart MIME messages
- Manages image attachments
- Renders email templates

#### 4. **`process_email_queue.py`** - Job Processor
- Batch processes email queue
- Implements retry logic
- Handles errors gracefully
- Supports dry-run mode for testing

### 📊 Monitoring & Operations

#### Check Email Queue Status

```sql
-- View pending emails
SELECT er.*, ar.name, ar.superhero 
FROM email_requests er
JOIN avatar_requests ar ON er.avatar_request_id = ar.request_id
WHERE er.status = 'pending'
ORDER BY er.created_at;

-- Check failed emails
SELECT * FROM email_requests 
WHERE status = 'failed' 
AND retry_count >= max_retries
ORDER BY created_at DESC;

-- Email delivery statistics
SELECT 
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries,
    MAX(updated_at) as last_activity
FROM email_requests
GROUP BY status;
```

#### Manual Operations

```bash
# Process queue manually
python email_service/jobs/process_email_queue.py

# Dry run to test without sending
python email_service/jobs/process_email_queue.py --dry-run

# Process larger batch
python email_service/jobs/process_email_queue.py --batch-size 100

# Send test email
python email_service/tests/test_email_manual.py --email test@example.com
```

### 🚀 Design Decisions & Benefits

#### Why Queue-Based Architecture?

1. **Decoupling**: UI remains responsive, no blocking operations
2. **Scalability**: Can process thousands of emails in batches
3. **Reliability**: Failed emails don't affect user experience
4. **Monitoring**: Complete visibility into email delivery status

#### Why Brevo SMTP?

1. **Deliverability**: Professional email service with high inbox rates
2. **Reliability**: 99.9% uptime SLA
3. **Features**: Built-in tracking, analytics, and bounce handling
4. **Cost-Effective**: Generous free tier and competitive pricing

#### Why 5-Minute Processing Interval?

1. **User Expectations**: Fast enough for "real-time" feel
2. **Resource Efficiency**: Batching reduces database/SMTP connections
3. **Rate Limiting**: Avoids overwhelming SMTP server
4. **Cost Optimization**: Minimizes Databricks compute costs

### 🔧 Configuration Reference

#### Required Environment Variables

```bash
# Brevo SMTP Configuration
BREVO_SMTP_SERVER=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=93330f001@smtp-brevo.com
BREVO_SMTP_PASSWORD=<your-api-key>

# Email Settings
EMAIL_FROM_ADDRESS=avatars@innovationgarage.com
EMAIL_FROM_NAME=Innovation Garage Superhero Creator
EMAIL_REPLY_TO=noreply@innovationgarage.com
EMAIL_BATCH_SIZE=50
EMAIL_MAX_RETRIES=3
ENABLE_EMAIL_FEATURE=true

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### 📈 Performance Considerations

- **Batch Size**: 50 emails per job run (configurable)
- **Processing Time**: ~2-3 seconds per email
- **Image Optimization**: Avatars resized to max 800px for email
- **Database Indexes**: Optimized queries with status and timestamp indexes
- **Connection Pooling**: Disabled for serverless compatibility

### 🛡️ Security Measures

1. **Credentials**: SMTP password stored as environment variable
2. **TLS Encryption**: All SMTP connections use TLS
3. **Input Validation**: Email addresses validated before queuing
4. **Rate Limiting**: Batch processing prevents abuse
5. **Error Sanitization**: Sensitive data removed from logs

### 🔮 Future Enhancements

- [ ] Add email open/click tracking
- [ ] Implement bounce handling webhook
- [ ] Add email preference management
- [ ] Create analytics dashboard
- [ ] Add email templating engine

---

This documentation reflects the current implementation of the email service. For operational procedures and troubleshooting, refer to the [README.md](./README.md) file.