# Databricks Job Deployment Guide

This guide walks you through deploying the email queue processing job to Databricks.

## Prerequisites

1. **Databricks Workspace Access**
   - Admin or job creation permissions
   - Personal Access Token (PAT)

2. **Environment Variables Set**
   ```bash
   export DATABRICKS_HOST=https://your-workspace.databricks.com
   export DATABRICKS_TOKEN=your-personal-access-token
   export DATABASE_URL=postgresql://user:pass@host:5432/superhero_avatars
   export BREVO_SMTP_PASSWORD=your-brevo-smtp-password
   ```

3. **Required Secrets**
   - Brevo SMTP credentials
   - Database connection string
   - Email configuration values

## Deployment Methods

### Method 1: Automated Setup Script

The easiest way to deploy is using the provided setup script:

```bash
# Run from the project root
cd email_service/jobs
python databricks_job_setup.py
```

This script will:
1. Create secrets scopes for credentials
2. Upload all required secrets
3. Upload the email processing code
4. Create the scheduled job
5. Optionally run a test execution

### Method 2: Manual Databricks UI Setup

#### Step 1: Create Secrets Scope

1. Go to Databricks workspace
2. Navigate to **Settings > Admin Console > Secret Scopes**
3. Create two scopes:
   - `email-service` - For email credentials
   - `superhero-app` - For app credentials

#### Step 2: Add Secrets

Using Databricks CLI:

```bash
# Install Databricks CLI if needed
pip install databricks-cli

# Configure CLI
databricks configure --token

# Add email service secrets
databricks secrets put --scope email-service --key brevo-smtp-server --string-value "smtp-relay.brevo.com"
databricks secrets put --scope email-service --key brevo-smtp-port --string-value "587"
databricks secrets put --scope email-service --key brevo-smtp-login --string-value "93330f001@smtp-brevo.com"
databricks secrets put --scope email-service --key brevo-smtp-password --string-value "your-password"
databricks secrets put --scope email-service --key email-from-address --string-value "avatars@yourdomain.com"
databricks secrets put --scope email-service --key email-from-name --string-value "Innovation Garage Superhero Creator"
databricks secrets put --scope email-service --key email-reply-to --string-value "noreply@yourdomain.com"

# Add app secrets
databricks secrets put --scope superhero-app --key database-url --string-value "postgresql://..."
databricks secrets put --scope superhero-app --key databricks-volume --string-value "/Volumes/main/sgfs/sg-vol/avatarmax"
```

#### Step 3: Upload Code to Workspace

1. In Databricks workspace, navigate to **Workspace > Users > your-email**
2. Create folder: `superhero-email-service`
3. Upload files:
   - `process_email_queue_notebook.py` (as a Python notebook)
   - Create `email_service` folder and upload all module files

#### Step 4: Create the Job

1. Go to **Workflows > Jobs**
2. Click **Create Job**
3. Configure:
   - **Name**: `process-superhero-email-queue`
   - **Task name**: `process_email_queue`
   - **Type**: Notebook
   - **Source**: Select the uploaded notebook
   - **Parameters**: 
     - `batch_size`: `50`
     - `dry_run`: `false`

4. **Cluster Configuration**:
   - **Cluster mode**: Single Node
   - **Node type**: `i3.xlarge` (or your preference)
   - **Databricks Runtime**: 14.3 LTS
   - **Spark Config**:
     ```
     spark.databricks.cluster.profile singleNode
     spark.master local[*]
     ```

5. **Environment Variables** (under Advanced options):
   ```
   BREVO_SMTP_SERVER={{secrets/email-service/brevo-smtp-server}}
   BREVO_SMTP_PORT={{secrets/email-service/brevo-smtp-port}}
   BREVO_SMTP_LOGIN={{secrets/email-service/brevo-smtp-login}}
   BREVO_SMTP_PASSWORD={{secrets/email-service/brevo-smtp-password}}
   EMAIL_FROM_ADDRESS={{secrets/email-service/email-from-address}}
   EMAIL_FROM_NAME={{secrets/email-service/email-from-name}}
   EMAIL_REPLY_TO={{secrets/email-service/email-reply-to}}
   DATABASE_URL={{secrets/superhero-app/database-url}}
   DATABRICKS_VOLUME={{secrets/superhero-app/databricks-volume}}
   ```

6. **Libraries**:
   - `sqlalchemy==2.0.36`
   - `psycopg2-binary==2.9.10`
   - `pillow==11.1.0`
   - `email-validator==2.2.0`

7. **Schedule**:
   - **Type**: Scheduled
   - **Schedule**: `0 0/5 * * * ?` (every 5 minutes)
   - **Timezone**: Your timezone

8. **Notifications** (optional):
   - On failure: admin@yourdomain.com

### Method 3: Using Databricks CLI

```bash
# Create job from JSON config
databricks jobs create --json-file databricks_job_config.json

# Or create with inline configuration
databricks jobs create --json '{
  "name": "process-superhero-email-queue",
  "tasks": [{
    "task_key": "process_email_queue",
    "notebook_task": {
      "notebook_path": "/Users/your-email/superhero-email-service/process_email_queue_notebook",
      "base_parameters": {
        "batch_size": "50",
        "dry_run": "false"
      }
    },
    "new_cluster": {
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 0
    }
  }],
  "schedule": {
    "quartz_cron_expression": "0 0/5 * * * ?",
    "timezone_id": "America/New_York"
  }
}'
```

## Testing the Deployment

### 1. Manual Test Run

```bash
# Trigger a test run
databricks jobs run-now --job-id <job-id>

# With dry-run mode
databricks jobs run-now --job-id <job-id> --notebook-params '{"dry_run": "true"}'
```

### 2. Monitor Job Execution

- Go to **Workflows > Job Runs**
- Click on your job run
- Check:
  - Cluster startup time
  - Notebook execution logs
  - Output results

### 3. Verify Email Delivery

1. Create a test avatar request
2. Click "Email My Avatar" in the app
3. Wait up to 5 minutes
4. Check recipient inbox
5. Verify database status:

```sql
SELECT * FROM email_requests 
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;
```

## Monitoring & Maintenance

### Job Health Monitoring

The job includes health rules:
- Alert if runtime > 5 minutes
- Alert on failures
- Email notifications to admin

### Performance Tuning

1. **Batch Size**: Adjust based on volume
   - Low volume: 25-50 emails
   - High volume: 100-200 emails

2. **Cluster Size**: 
   - Single node sufficient for < 1000 emails/hour
   - Scale to 2-4 workers for higher volumes

3. **Schedule Frequency**:
   - Every 5 minutes: Standard
   - Every 2 minutes: High priority events
   - Every 10 minutes: Low volume periods

### Troubleshooting

#### Job Fails to Start
- Check cluster permissions
- Verify secrets are accessible
- Check notebook path is correct

#### Emails Not Sending
- Verify SMTP credentials in secrets
- Check database connectivity
- Review job logs for errors
- Test with dry-run mode

#### Performance Issues
- Increase cluster size
- Reduce batch size
- Check database query performance
- Monitor SMTP rate limits

## Security Best Practices

1. **Secrets Management**
   - Never hardcode credentials
   - Use secret scopes for all sensitive data
   - Rotate SMTP passwords regularly

2. **Access Control**
   - Limit job edit permissions
   - Use service principals for production
   - Enable audit logging

3. **Data Protection**
   - Ensure TLS for SMTP connections
   - Don't log email addresses in plain text
   - Implement data retention policies

## Cost Optimization

1. **Cluster Configuration**
   - Use spot instances for non-critical runs
   - Enable auto-termination (10 minutes)
   - Right-size cluster for workload

2. **Schedule Optimization**
   - Reduce frequency during low-usage hours
   - Pause job during maintenance windows
   - Monitor actual email volume patterns

3. **Resource Usage**
   - Track DBU consumption
   - Set budget alerts
   - Review job metrics monthly

## Rollback Procedure

If issues occur:

1. **Immediate Actions**
   - Pause the job schedule
   - Set dry_run=true for debugging
   - Check recent code changes

2. **Rollback Steps**
   ```bash
   # Revert to previous notebook version
   databricks workspace export /path/to/notebook -f PYTHON > backup.py
   databricks workspace import backup.py /path/to/notebook -l PYTHON -o
   
   # Or restore from version control
   git checkout <previous-commit> -- process_email_queue_notebook.py
   databricks workspace import process_email_queue_notebook.py /path/to/notebook -l PYTHON -o
   ```

3. **Verification**
   - Run test with small batch
   - Monitor for 1-2 cycles
   - Check email delivery status

---

For additional support or questions, contact the Innovation Garage team.