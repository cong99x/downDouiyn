# Douyin Downloader Usage Instructions

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Cookie (Required for first use)
```bash
# Automatic acquisition (Recommended)
python cookie_extractor.py

# Or manual acquisition
python get_cookies_manual.py
```

### 3. Start Downloading

#### V1.0 Stable Version (Recommended for single videos)
```bash
# Edit config.yml configuration file
# Then run
python DouYinCommand.py
```

#### V2.0 Enhanced Version (Recommended for user homepages)
```bash
# Download user homepage
python downloader.py -u "https://www.douyin.com/user/xxxxx"

# Automatically get Cookie and download
python downloader.py --auto-cookie -u "https://www.douyin.com/user/xxxxx"
```

## 📋 Version Comparison

| Feature | V1.0 (DouYinCommand.py) | V2.0 (downloader.py) |
|------|------------------------|---------------------|
| Single video download | ✅ Fully functional | ⚠️ API Issues |
| User homepage download | ✅ Normal | ✅ Fully functional |
| Cookie Management | Manual Configuration | Automatic Acquisition |
| Complexity | Simple | Medium |
| Stability | High | Medium |

## 🎯 Recommended Use Cases

- **Download single biological video**: Use V1.0
- **Download user homepage**: Use V2.0
- **Batch download**: Use V2.0
- **Learning & Research**: Both versions are suitable

## 📞 Get Help

- View detailed documentation: `README.md`
- Report issues: [GitHub Issues](https://github.com/jiji262/douyin-downloader/issues)