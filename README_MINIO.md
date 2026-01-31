# MinIO Setup Guide

## 1. Start MinIO
Run the following command in the project root to start MinIO using Docker:

```bash
docker-compose up -d
```

## 2. Access MinIO Console
- Open your browser and go to: [http://localhost:9001](http://localhost:9001)
- **Username**: `minioadmin`
- **Password**: `minioadmin`

## 3. Create a Bucket
1.  Log in to the Console.
2.  Click **Buckets** in the sidebar.
3.  Click **Create Bucket**.
4.  Enter `douyin-downloads` as the bucket name.
5.  Click **Create Bucket**.

## 4. Configure Downloader
Update your `config.yml` (or `config_simple.yml`) with the following settings:

```yaml
aws:
  enabled: true
  access_key_id: "minioadmin"
  secret_access_key: "minioadmin"
  region: "us-east-1"
  bucket_name: "douyin-downloads"
  endpoint_url: "http://localhost:9000"
```

## 5. Verify
Run the test script to make sure everything is connected:

```bash
python test_s3_upload.py
```
