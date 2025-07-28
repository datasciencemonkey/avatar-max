# QR Code Feature Setup

## Overview
Replaced email functionality with QR code generation that uploads avatars to Google Cloud Storage (GCS) and generates shareable QR codes.

## Required Packages
Add these to your `pyproject.toml` or install with uv:

```bash
uv add google-cloud-storage qrcode[pil]
```

## GCS Setup
1. Create a GCS bucket named `innovation_garage01` (or update the bucket name in `qr_service/gcs_uploader.py`)
2. Set up GCS authentication:
   - Either set `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account JSON file
   - Or use Application Default Credentials (ADC) if running on GCP

## Environment Variables
No additional environment variables required if using default GCS authentication methods.

## How It Works
1. User generates their superhero avatar
2. Clicks "Generate QR Code" button
3. Avatar is uploaded to GCS with a unique filename
4. QR code is generated linking to the public GCS URL
5. QR code is displayed in the app along with the direct link

## File Structure
```
qr_service/
├── __init__.py         # Package initialization
├── gcs_uploader.py     # Handles GCS uploads
└── qr_generator.py     # Generates QR codes
```

## Changes Made
- Removed email button and replaced with QR code button
- Kept email field for user data collection
- Added QR code display in a popup with the generated image
- Updated button styling to match the new functionality