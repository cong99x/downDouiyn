# -*- coding: utf-8 -*-

import os
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self, config):
        """
        Initialize S3 Uploader
        :param config: Dictionary containing 'aws' configuration
        """
        self.config = config.get('aws', {})
        self.enabled = self.config.get('enabled', False)
        self.access_key = self.config.get('access_key_id')
        self.secret_key = self.config.get('secret_access_key')
        self.region = self.config.get('region', 'us-east-1')
        self.bucket = self.config.get('bucket_name')
        self.prefix = self.config.get('prefix', '')
        self.endpoint_url = self.config.get('endpoint_url') # Support MinIO/Custom S3
        
        self.s3_client = None
        if self.enabled:
            self._init_client()

    def _init_client(self):
        """Initialize boto3 client"""
        try:
            if not all([self.access_key, self.secret_key, self.bucket]):
                logger.warning("AWS S3 configuration incomplete. S3 upload disabled.")
                self.enabled = False
                return

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
            # Verify credentials by listing buckets (dry run)
            # self.s3_client.list_buckets()
            logger.info(f"AWS S3 Client initialized for bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {e}")
            self.enabled = False

    def upload_file(self, file_path, object_name=None):
        """
        Upload a file to an S3 bucket
        :param file_path: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        if not self.enabled or not self.s3_client:
            return False

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Add prefix if configured
        if self.prefix:
            object_name = f"{self.prefix.rstrip('/')}/{object_name}"

        try:
            logger.info(f"Uploading {file_path} to s3://{self.bucket}/{object_name}...")
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            logger.info(f"✅ Successfully uploaded to S3: {object_name}")
            return True
        except ClientError as e:
            logger.error(f"❌ AWS S3 Upload failed: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"❌ File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during S3 upload: {e}")
            return False

    def list_files(self, prefix=None):
        """
        List files in the S3 bucket
        :param prefix: Optional prefix to filter
        :return: List of object dictionaries
        """
        if not self.enabled or not self.s3_client:
            return []
            
        try:
            target_prefix = self.prefix
            if prefix:
                target_prefix = f"{self.prefix.rstrip('/')}/{prefix.lstrip('/')}" if self.prefix else prefix
                
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=target_prefix)
            
            files = []
            for page in pages:
                for obj in page.get('Contents', []):
                    files.append(obj)
            return files
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            return []
