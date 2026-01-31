import sys
import os
from pathlib import Path
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import yaml
    from utils.s3_uploader import S3Uploader
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_init():
    print("--- Starting Debug ---")
    
    # Replicating logic from DownloadService
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "config.yml"
    
    print(f"1. Calculated Root Dir: {root_dir}")
    print(f"2. Config Path: {config_path}")
    print(f"3. Config Exists: {config_path.exists()}")
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"4. Config Content Loaded: {list(config.keys())}")
                
                aws_config = config.get('aws', {})
                print(f"5. AWS Config Section: {aws_config}")
                
                enabled = aws_config.get('enabled')
                print(f"6. AWS Enabled: {enabled} (Type: {type(enabled)})")
                
                if enabled:
                    print("7. Initializing S3Uploader...")
                    uploader = S3Uploader(
                        access_key_id=aws_config.get('access_key_id'),
                        secret_access_key=aws_config.get('secret_access_key'),
                        region=aws_config.get('region'),
                        bucket_name=aws_config.get('bucket_name'),
                        prefix=aws_config.get('prefix', ''),
                        endpoint_url=aws_config.get('endpoint_url')
                    )
                    print(f"8. Uploader initialized. Enabled: {uploader.enabled}")
                    
                    # Test Listing
                    print("9. Testing List Files...")
                    files = uploader.list_files()
                    print(f"10. Files found: {len(files)}")
                else:
                    print("AWS not enabled.")
        except Exception as e:
            print(f"Error reading/parsing config: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Config file not found!")

if __name__ == "__main__":
    test_init()
