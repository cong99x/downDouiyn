# -*- coding: utf-8 -*-
import os
import yaml
import logging
import sys
from utils.s3_uploader import S3Uploader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_s3_upload():
    # Load config
    config_path = 'config.yml'
    if not os.path.exists(config_path):
        config_path = 'config.example.yml'
        print(f"config.yml not found, using {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Check if AWS config exists
    if 'aws' not in config:
        print("❌ 'aws' section not found in configuration.")
        return
    
    # Force enable for testing if credentials are present
    if config['aws'].get('access_key_id') == "YOUR_AWS_ACCESS_KEY_ID":
        print("❌ Please configure real AWS credentials in the config file first.")
        return

    config['aws']['enabled'] = True # Force enable for test
    
    uploader = S3Uploader(config)
    
    if not uploader.enabled:
        print("❌ S3 Uploader failed to initialize. Check your credentials.")
        return

    # Create a dummy file
    test_file = "test_s3_upload.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file for Douyin Downloader S3 integration.")
    
    try:
        print(f"🚀 Attempting to upload {test_file}...")
        success = uploader.upload_file(test_file)
        
        if success:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed.")
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_s3_upload()
