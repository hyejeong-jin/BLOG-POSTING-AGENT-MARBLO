"""
AWS S3 client for photo upload, download, and management.

This module provides high-level functions for:
- Uploading photos to S3
- Generating presigned URLs for download/access
- Deleting photos from S3
- Listing photos
- Implementing exponential backoff retry logic
"""

import asyncio
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class S3Client:
    """
    AWS S3 client wrapper with retry logic and error handling.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.aws_s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = settings.aws_s3_bucket
    
    async def upload_file(
        self,
        file_path: str,
        s3_key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Upload a file to S3 with exponential backoff retry.
        
        Args:
            file_path: Local file path to upload
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the object
            
        Returns:
            S3 URL if successful, None if failed after retries
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Uploading file to S3",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                    max_retries=self.MAX_RETRIES,
                )
                
                # Prepare extra arguments
                extra_args = {
                    "ContentType": content_type,
                    "ServerSideEncryption": "AES256",  # Encrypt at rest
                }
                
                if metadata:
                    extra_args["Metadata"] = metadata
                
                # Upload file
                self.s3_client.upload_file(
                    file_path,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args,
                )
                
                # Build S3 URL
                s3_url = f"https://{self.bucket_name}.s3.{settings.aws_s3_region}.amazonaws.com/{s3_key}"
                
                logger.info(
                    "File uploaded successfully",
                    s3_key=s3_key,
                    s3_url=s3_url,
                )
                
                return s3_url
            
            except (ClientError, BotoCoreError) as e:
                error_code = getattr(e.response["Error"], "Code", str(e)) if hasattr(e, "response") else str(e)
                
                logger.warning(
                    "S3 upload failed",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                    error=error_code,
                )
                
                # Check if we should retry
                if attempt < self.MAX_RETRIES - 1:
                    # Exponential backoff
                    backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    logger.info(
                        "Retrying S3 upload",
                        s3_key=s3_key,
                        backoff_seconds=backoff_seconds,
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.error(
                        "S3 upload failed after retries",
                        s3_key=s3_key,
                        total_attempts=self.MAX_RETRIES,
                    )
                    return None
            
            except Exception as e:
                logger.error("Unexpected error during S3 upload", s3_key=s3_key, error=str(e))
                return None
        
        return None
    
    async def download_file(
        self,
        s3_key: str,
        file_path: str,
    ) -> bool:
        """
        Download a file from S3 to local storage.
        
        Args:
            s3_key: S3 object key
            file_path: Local file path to save to
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Downloading file from S3",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                )
                
                self.s3_client.download_file(
                    self.bucket_name,
                    s3_key,
                    file_path,
                )
                
                logger.info("File downloaded successfully", s3_key=s3_key)
                return True
            
            except (ClientError, BotoCoreError) as e:
                logger.warning(
                    "S3 download failed",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                if attempt < self.MAX_RETRIES - 1:
                    backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.error(
                        "S3 download failed after retries",
                        s3_key=s3_key,
                        total_attempts=self.MAX_RETRIES,
                    )
                    return False
            
            except Exception as e:
                logger.error("Unexpected error during S3 download", s3_key=s3_key, error=str(e))
                return False
        
        return False
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Deleting file from S3",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                )
                
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                )
                
                logger.info("File deleted successfully", s3_key=s3_key)
                return True
            
            except (ClientError, BotoCoreError) as e:
                logger.warning(
                    "S3 delete failed",
                    s3_key=s3_key,
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                if attempt < self.MAX_RETRIES - 1:
                    backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.error(
                        "S3 delete failed after retries",
                        s3_key=s3_key,
                        total_attempts=self.MAX_RETRIES,
                    )
                    return False
            
            except Exception as e:
                logger.error("Unexpected error during S3 delete", s3_key=s3_key, error=str(e))
                return False
        
        return False
    
    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration_seconds: int = 3600,
    ) -> Optional[str]:
        """
        Generate a presigned URL for accessing an S3 object.
        
        Args:
            s3_key: S3 object key
            expiration_seconds: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            logger.info("Generating presigned URL", s3_key=s3_key, expiration=expiration_seconds)
            
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration_seconds,
            )
            
            logger.info("Presigned URL generated", s3_key=s3_key)
            return presigned_url
        
        except Exception as e:
            logger.error("Error generating presigned URL", s3_key=s3_key, error=str(e))
            return None
    
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> Optional[list[dict]]:
        """
        List objects in S3 bucket with optional prefix.
        
        Args:
            prefix: S3 key prefix to filter by
            max_keys: Maximum number of objects to return
            
        Returns:
            List of object metadata dicts if successful, None otherwise
        """
        try:
            logger.info(
                "Listing S3 objects",
                prefix=prefix,
                max_keys=max_keys,
            )
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            
            objects = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    objects.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "modified": obj["LastModified"].isoformat(),
                        "etag": obj["ETag"],
                    })
            
            logger.info("Objects listed", prefix=prefix, count=len(objects))
            return objects
        
        except Exception as e:
            logger.error("Error listing S3 objects", prefix=prefix, error=str(e))
            return None


# Global S3 client instance
_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """
    Get or create the global S3 client instance.
    
    Returns:
        S3Client instance
    """
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client


