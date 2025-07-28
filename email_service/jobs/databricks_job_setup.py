#!/usr/bin/env python3
"""
Databricks job setup script for email queue processing.

This script creates a Databricks job that runs every 5 minutes to process
pending email requests from the superhero avatar generator.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
from databricks.sdk.service.workspace import ImportFormat

load_dotenv()

def upload_secrets(client: WorkspaceClient, scope_name: str = "sgscope"):
    """Upload email service secrets to Databricks."""
    print("\nUploading secrets...")
    
    # Define required secrets
    secrets = {
        "brevo-smtp-server": os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com"),
        "brevo-smtp-port": os.getenv("BREVO_SMTP_PORT", "587"),
        "brevo-smtp-login": os.getenv("BREVO_SMTP_LOGIN", "93330f001@smtp-brevo.com"),
        "brevo-smtp-password": os.getenv("BREVO_SMTP_PASSWORD"),
        "email-from-address": os.getenv("EMAIL_FROM_ADDRESS"),
        "email-from-name": os.getenv("EMAIL_FROM_NAME", "Databricks Innovation Garage Superhero"),
        "email-reply-to": os.getenv("EMAIL_REPLY_TO", "noreply@innovationgarage.com")
    }
    
    # Also need the main app secrets
    app_scope = "sgscope"
    
    app_secrets = {
        "database-url": os.getenv("DATABASE_URL"),
        "databricks-volume": os.getenv("DATABRICKS_VOLUME", "/Volumes/main/sgfs/sg-vol/avatarmax")
    }
    
    # Upload email service secrets
    for key, value in secrets.items():
        if value:
            try:
                client.secrets.put_secret(
                    scope=scope_name,
                    key=key,
                    string_value=value
                )
                print(f"✅ Uploaded secret: {scope_name}/{key}")
            except Exception as e:
                print(f"❌ Failed to upload secret {key}: {e}")
    
    # Upload app secrets
    for key, value in app_secrets.items():
        if value:
            try:
                client.secrets.put_secret(
                    scope=app_scope,
                    key=key,
                    string_value=value
                )
                print(f"✅ Uploaded secret: {app_scope}/{key}")
            except Exception as e:
                print(f"❌ Failed to upload secret {key}: {e}")

def upload_job_code(client: WorkspaceClient, workspace_path: str = "/Workspace/Users/sathish.gangichetty@databricks.com/superhero-email-service"):
    """Upload the email processing code to Databricks workspace."""
    print(f"\nUploading code to workspace: {workspace_path}")
    
    # Create workspace directory
    try:
        client.workspace.mkdirs(workspace_path)
        print(f"✅ Created workspace directory: {workspace_path}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Workspace directory already exists: {workspace_path}")
    
    # Upload process_email_queue_notebook.py as a notebook
    local_file = Path(__file__).parent / "process_email_queue_notebook.py"
    remote_file = f"{workspace_path}/process_email_queue.py"
    
    try:
        with open(local_file, "rb") as f:
            client.workspace.upload(
                path=remote_file,
                content=f.read(),
                format=ImportFormat.AUTO,
                overwrite=True
            )
        print(f"✅ Uploaded: {remote_file}")
    except Exception as e:
        print(f"❌ Failed to upload file: {e}")
    
    # Upload email service modules
    email_service_path = Path(__file__).parent.parent
    modules = ["__init__.py", "models.py", "db_manager.py", "brevo_service.py"]
    
    # Create email_service directory
    email_module_path = f"{workspace_path}/email_service"
    try:
        client.workspace.mkdirs(email_module_path)
    except:
        pass
    
    for module in modules:
        local_module = email_service_path / module
        if local_module.exists():
            remote_module = f"{email_module_path}/{module}"
            try:
                with open(local_module, "rb") as f:
                    client.workspace.upload(
                        path=remote_module,
                        content=f.read(),
                        overwrite=True
                    )
                print(f"✅ Uploaded: {remote_module}")
            except Exception as e:
                print(f"❌ Failed to upload {module}: {e}")
    
    # Upload templates
    templates_path = f"{email_module_path}/templates"
    try:
        client.workspace.mkdirs(templates_path)
    except:
        pass
    
    for template in ["avatar_email.html", "avatar_email.txt"]:
        local_template = email_service_path / "templates" / template
        if local_template.exists():
            remote_template = f"{templates_path}/{template}"
            try:
                with open(local_template, "r") as f:
                    content = f.read()
                    # Upload as a file with explicit format
                    client.workspace.upload(
                        path=remote_template,
                        content=content.encode('utf-8'),
                        format=ImportFormat.AUTO,
                        overwrite=True
                    )
                print(f"✅ Uploaded: {remote_template}")
            except Exception as e:
                print(f"❌ Failed to upload template {template}: {e}")

def create_job(client: WorkspaceClient, job_config_path: str, workspace_path: str = "/Workspace/Users/sathish.gangichetty@databricks.com/superhero-email-service"):
    """Create the Databricks job for email processing."""
    print("\nCreating Databricks job...")
    
    # Load job configuration
    with open(job_config_path, "r") as f:
        job_config = json.load(f)
    
    # Update the task to use notebook instead of wheel
    job_config["tasks"][0] = {
        "task_key": "process_email_queue",
        "description": "Process pending superhero avatar emails from the queue",
        "run_if": "ALL_SUCCESS",
        "notebook_task": {
            "notebook_path": f"{workspace_path}/process_email_queue.py",
            "base_parameters": {
                "batch_size": "50",
                "dry_run": "false"
            }
        },
        "existing_cluster_id": "0118-165440-l8erfx3g",
        "timeout_seconds": 600,
        "retry_on_timeout": True,
        "max_retries": 2,
        "min_retry_interval_millis": 60000
    }
    
    # Create the job
    try:
        # Create job using the SDK's expected format - simplified to avoid enum issues
        job = client.jobs.create(
            name=job_config["name"],
            tasks=job_config["tasks"],
            schedule=job_config.get("schedule"),
            max_concurrent_runs=job_config.get("max_concurrent_runs", 1),
            timeout_seconds=job_config.get("timeout_seconds", 0),
            tags=job_config.get("tags", {})
        )
        print(f"✅ Created job: {job.job_id}")
        print(f"Name: {job_config['name']}")
        print(f"Schedule: Every 5 minutes")
        return job.job_id
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        
        # Try to find existing job
        jobs_list = client.jobs.list()
        for existing_job in jobs_list:
            if existing_job.settings.name == job_config["name"]:
                print(f"⚠️  Job already exists with ID: {existing_job.job_id}")
                return existing_job.job_id
        
        raise

def test_job(client: WorkspaceClient, job_id: int):
    """Run a test execution of the job."""
    print(f"\nTesting job {job_id}...")
    
    try:
        run = client.jobs.run_now(job_id=job_id)
        print(f"✅ Started test run: {run.run_id}")
        print("   Monitor at: https://<your-workspace>.databricks.com/#job/{job_id}/run/{run_id}")
        return run.run_id
    except Exception as e:
        print(f"❌ Failed to start test run: {e}")

def main():
    """Main setup function."""
    print("="*60)
    print("DATABRICKS EMAIL JOB SETUP")
    print("="*60)
    
    # Check for required environment variables
    if not os.getenv("DATABRICKS_HOST"):
        print("❌ ERROR: DATABRICKS_HOST not set!")
        print("   Set your Databricks workspace URL")
        sys.exit(1)
    
    if not os.getenv("DATABRICKS_TOKEN"):
        print("❌ ERROR: DATABRICKS_TOKEN not set!")
        print("   Set your Databricks personal access token")
        sys.exit(1)
    
    if not os.getenv("DATABASE_URL"):
        print("❌ ERROR: DATABASE_URL not set!")
        print("   Set your PostgreSQL connection string")
        sys.exit(1)
    
    if not os.getenv("BREVO_SMTP_PASSWORD"):
        print("❌ ERROR: BREVO_SMTP_PASSWORD not set!")
        print("   Set your Brevo SMTP password")
        sys.exit(1)
    
    # Initialize Databricks client
    print("\nConnecting to Databricks...")
    client = WorkspaceClient()
    print("✅ Connected to Databricks")
    
    # Setup steps
    try:
        
        # 1. Upload secrets
        upload_secrets(client)
        
        # 2. Upload code
        upload_job_code(client)
        
        # 4. Create job
        job_config_path = Path(__file__).parent / "databricks_job_config.json"
        job_id = create_job(client, job_config_path)
        
        # 5. Test job (optional)
        if input("\n🧪 Run test execution? (y/n): ").lower() == "y":
            test_job(client, job_id)
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print(f"   Job ID: {job_id}")
        print("   Schedule: Every 5 minutes")
        print("   Status: Active")
        print("\n📊 Monitor your job at:")
        print(f"   https://<your-workspace>.databricks.com/#job/{job_id}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()