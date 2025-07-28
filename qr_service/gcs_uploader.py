"""Simple GCS uploader for superhero avatars."""

import os
import uuid
import json
from google.cloud import storage
from PIL import Image
import io
from databricks.sdk import WorkspaceClient
from typing import Union, Optional


def upload_to_gcs(image_path_or_pil: Union[str, Image.Image], 
                  bucket_name: str = "innovation_garage01",
                  make_public: bool = True) -> Optional[str]:
    """Upload image to GCS and return public URL.
    
    Args:
        image_path_or_pil: Either a file path (str) or PIL Image object
        bucket_name: GCS bucket name
        make_public: Whether to make the uploaded file public
    
    Returns:
        Public URL of uploaded file, or None if upload failed
    """
    try:
        # Validate inputs
        if not bucket_name or not isinstance(bucket_name, str):
            raise ValueError("bucket_name must be a non-empty string")
        
        if not image_path_or_pil:
            raise ValueError("image_path_or_pil cannot be None or empty")
        
        # Get Databricks credentials
        gcp_credentials_json = os.getenv("GCP_KEY")
        
        # Parse JSON credentials and initialize GCS client
        gcp_credentials = json.loads(gcp_credentials_json)
        client = storage.Client.from_service_account_info(gcp_credentials)
        bucket = client.bucket(bucket_name)
        
        # Generate unique filename
        unique_filename = f"superhero_{uuid.uuid4().hex}.png"
        blob = bucket.blob(unique_filename)
        
        # Handle PIL Image or file path
        if isinstance(image_path_or_pil, Image.Image):
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            try:
                image_path_or_pil.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                blob.upload_from_file(img_byte_arr, content_type='image/png')
            finally:
                img_byte_arr.close()
        elif isinstance(image_path_or_pil, str):
            # Validate file exists
            if not os.path.exists(image_path_or_pil):
                raise FileNotFoundError(f"File not found: {image_path_or_pil}")
            
            # Upload from file path
            blob.upload_from_filename(image_path_or_pil)
        else:
            raise TypeError("image_path_or_pil must be either a PIL Image or file path string")
        

        public_url = f"https://storage.googleapis.com/{bucket_name}/{unique_filename}"

            
        return public_url
        
    except (ValueError, TypeError, FileNotFoundError) as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None