# Douyin Downloader - No Watermark Batch Download Tool

![douyin-downloader](https://socialify.git.ci/jiji262/douyin-downloader/image?custom_description=Douyin%20batch%20download%20tool,%20remove%20watermark,%20supports%20video,%20images,%20collections,%20music%20(original%20sound).%20Free!%20Free!%20Free!&description=1&font=Jost&forks=1&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjiji262%2Fdouyin-downloader%2Frefs%2Fheads%2Fmain%2Fimg%2Flogo.png&name=1&owner=1&pattern=Circuit+Board&pulls=1&stargazers=1&theme=Light)

A powerful Douyin content batch download tool that supports videos, images, music, live streams, and more. Provides two versions: V1.0 (Stable) and V2.0 (Enhanced).

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Version Description](#-version-description)
- [V1.0 User Guide](#-v10-user-guide)
- [V2.0 User Guide](#-v20-user-guide)
- [Cookie Configuration Tool](#-cookie-configuration-tool)
- [Supported Link Types](#-supported-link-types)
- [Frequently Asked Questions](#-frequently-asked-questions)
- [Update Log](#-update-log)

## ⚡ Quick Start

![qun](./img/fuye.jpg)

### Environment Requirements

- **Python 3.9+**
- **Operating System**: Windows, macOS, Linux

### Installation Steps

1. **Clone the Project**
```bash
git clone https://github.com/jiji262/douyin-downloader.git
cd douyin-downloader
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Cookie** (Required for first use)
```bash
# Method 1: Automatic acquisition (Recommended)
python cookie_extractor.py

# Method 2: Manual acquisition
python get_cookies_manual.py
```

## 📦 Version Description

### V1.0 (DouYinCommand.py) - Stable Version
- ✅ **Verified**: Stable and reliable, extensively tested
- ✅ **Easy to Use**: Driven by configuration files, simple to operate
- ✅ **Full-Featured**: Supports downloading all content types
- ✅ **Single Video Download**: Fully functional
- ⚠️ **Manual Configuration Required**: Requires manual acquisition and configuration of Cookies

### V2.0 (downloader.py) - Enhanced Version
- 🚀 **Automatic Cookie Management**: Supports auto-acquisition and refreshing of Cookies
- 🚀 **Unified Entry**: Integrates all functions into a single script
- 🚀 **Asynchronous Architecture**: Better performance, supports concurrent downloads
- 🚀 **Smart Retry**: Automatic retry and error recovery
- 🚀 **Incremental Download**: Supports incremental updates to avoid repeated downloads
- ⚠️ **Single Video Download**: Currently API returns empty response (known issue)
- ✅ **User Homepage Download**: Fully functional

## 🎯 V1.0 User Guide

### Configuration Settings

1. **Edit Configuration File**
```bash
cp config.example.yml config.yml
# Edit config.yml file
```

2. **Configuration Example**
```yaml
# Download links
link:
  - https://v.douyin.com/xxxxx/                    # Single video
  - https://www.douyin.com/user/xxxxx              # User homepage
  - https://www.douyin.com/collection/xxxxx        # Collection

# Save path
path: ./Downloaded/

# Cookie configuration (Required)
cookies:
  msToken: YOUR_MS_TOKEN_HERE
  ttwid: YOUR_TTWID_HERE
  odin_tt: YOUR_ODIN_TT_HERE
  passport_csrf_token: YOUR_PASSPORT_CSRF_TOKEN_HERE
  sid_guard: YOUR_SID_GUARD_HERE

# Download options
music: True    # Download music
cover: True    # Download cover
avatar: True   # Download avatar
json: True     # Save JSON data

# Download mode
mode:
  - post       # Download published works
  # - like     # Download liked works
  # - mix      # Download collections

# Download quantity (0 for all)
number:
  post: 0      # Number of posts
  like: 0      # Number of likes
  allmix: 0    # Number of collections
  mix: 0       # Number of works within a single collection

# Other settings
thread: 5      # Number of download threads
database: True # Use database recording
```

### Running the Program

```bash
# Run using configuration file
python DouYinCommand.py

# Or use command line arguments
python DouYinCommand.py --cmd False
```

### Usage Examples

```bash
# Download a single video
# Set link to a single video URL in config.yml
python DouYinCommand.py

# Download user homepage
# Set link to a user homepage URL in config.yml
python DouYinCommand.py

# Download collection
# Set link to a collection URL in config.yml
python DouYinCommand.py
```

## 🚀 V2.0 User Guide

### Command Line Usage

```bash
# Download a single video (Requires pre-configured Cookie)
python downloader.py -u "https://v.douyin.com/xxxxx/"

# Download user homepage (Recommended)
python downloader.py -u "https://www.douyin.com/user/xxxxx"

# Automatically get Cookie and download
python downloader.py --auto-cookie -u "https://www.douyin.com/user/xxxxx"

# Specify save path
python downloader.py -u "LINK" --path "./my_videos/"

# Use configuration file
python downloader.py --config
```

### Configuration File Usage

1. **Create Configuration File**
```bash
cp config.example.yml config_simple.yml
```

2. **Configuration Example**
```yaml
# Download links
link:
  - https://www.douyin.com/user/xxxxx

# Save path
path: ./Downloaded/

# Automatic Cookie management
auto_cookie: true

# Download options
music: true
cover: true
avatar: true
json: true

# Download mode
mode:
  - post

# Download quantity
number:
  post: 10

# Incremental download
increase:
  post: false

# Database
database: true
```

3. **Run the Program**
```bash
python downloader.py --config
```

### Command Line Arguments

```bash
python downloader.py [options] [links...]

Options:
  -u, --url URL          Download link
  -p, --path PATH        Save path
  -c, --config           Use configuration file
  --auto-cookie          Automatically get Cookie
  --cookies COOKIES      Manually specify Cookie
  -h, --help            Show help information
```

## 🍪 Cookie Configuration Tool

### 1. cookie_extractor.py - Automatic Acquisition Tool

**Function**: Uses Playwright to automatically open the browser and acquire Cookies.

**Usage**:
```bash
# Install Playwright
pip install playwright
playwright install chromium

# Run automatic acquisition
python cookie_extractor.py
```

**Features**:
- ✅ Automatically opens browser
- ✅ Supports QR code login
- ✅ Automatically detects login status
- ✅ Automatically saves to configuration file
- ✅ Supports multiple login methods

**Steps**:
1. Run `python cookie_extractor.py`
2. Select extraction method (Option 1 recommended)
3. Complete login in the opened browser
4. Program automatically extracts and saves Cookie

### 2. get_cookies_manual.py - Manual Acquisition Tool

**Function**: Manually acquire Cookies through browser developer tools.

**Usage**:
```bash
python get_cookies_manual.py
```

**Features**:
- ✅ No Playwright installation required
- ✅ Detailed operation tutorial
- ✅ Supports Cookie validation
- ✅ Automatically saves to configuration file
- ✅ Supports backup and recovery

**Steps**:
1. Run `python get_cookies_manual.py`
2. Select "Get New Cookie"
3. Follow the tutorial to get Cookie in the browser
4. Paste the Cookie content
5. Program automatically parses and saves

### Cookie Acquisition Tutorial

#### Method 1: Browser Developer Tools

1. Open browser, visit [Douyin Web Version](https://www.douyin.com)
2. Log in to your Douyin account
3. Press `F12` to open developer tools
4. Switch to the `Network` tab
5. Refresh the page, find any request
6. Find the `Cookie` field in the request header
7. Copy the following key cookie values:
   - `msToken`
   - `ttwid`
   - `odin_tt`
   - `passport_csrf_token`
   - `sid_guard`

#### Method 2: Use Automatic Tool

```bash
# Recommended to use the automatic tool
python cookie_extractor.py
```

## 📋 Supported Link Types

### 🎬 Video Content
- **Single Video Share Link**: `https://v.douyin.com/xxxxx/`
- **Single Video Direct Link**: `https://www.douyin.com/video/xxxxx`
- **Image Collection (Note)**: `https://www.douyin.com/note/xxxxx`

### 👤 User Content
- **User Homepage**: `https://www.douyin.com/user/xxxxx`
  - Supports downloading all posts by the user
  - Supports downloading works liked by the user (permissions required)

### 📚 Collection Content
- **User Collections**: `https://www.douyin.com/collection/xxxxx`
- **Music Collections**: `https://www.douyin.com/music/xxxxx`

### 🔴 Live Content
- **Live Room**: `https://live.douyin.com/xxxxx`

## 🔧 Frequently Asked Questions

### Q: Why did single video download fail?
**A**: 
- V1.0: Please check if the Cookie is valid and ensures it contains necessary fields.
- V2.0: Known issue, API returns empty response, recommended to use user homepage download.

### Q: What if the Cookie expires?
**A**: 
- Use `python cookie_extractor.py` to re-acquire.
- Or use `python get_cookies_manual.py` for manual acquisition.

### Q: What if download speed is slow?
**A**: 
- Adjust the `thread` parameter to increase concurrency.
- Check your network connection.
- Avoid downloading too much content at once.

### Q: How to batch download?
**A**: 
- V1.0: Add multiple links in `config.yml`.
- V2.0: Pass multiple links via command line or use a configuration file.

### Q: What formats are supported?
**A**: 
- Video: MP4 format (No watermark)
- Image: JPG format
- Audio: MP3 format
- Data: JSON format

## 📝 Update Log

### V2.0 (2025-08)
- ✅ **Unified Entry**: Integrated all functions into `downloader.py`
- ✅ **Automatic Cookie Management**: Supports auto-acquisition and refreshing
- ✅ **Asynchronous Architecture**: Performance optimization, supports concurrent downloads
- ✅ **Smart Retry**: Automatic retry and error recovery
- ✅ **Incremental Download**: Supports incremental updates
- ✅ **User Homepage Download**: Fully functional
- ⚠️ **Single Video Download**: API returns empty response (known issue)

### V1.0 (2024-12)
- ✅ **Stable and Reliable**: Extensively tested and verified
- ✅ **Full-Featured**: Supports all content types
- ✅ **Single Video Download**: Fully functional
- ✅ **Configuration Driven**: Easy to use
- ✅ **Database Support**: Records download history

## ⚖️ Legal Disclaimer

- This project is for **learning and exchange** purposes only.
- Please comply with relevant laws, regulations, and platform terms of service.
- Not for commercial use or infringing on the rights of others.
- Please respect the original author's copyright for downloaded content.

## 🤝 Contribution Guide

Issues and Pull Requests are welcome!

### Reporting Issues
- Use [Issues](https://github.com/jiji262/douyin-downloader/issues) to report bugs.
- Please provide detailed error information and reproduction steps.

### Feature Suggestions
- Propose new feature suggestions in Issues.
- Describe functional requirements and use scenarios in detail.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**If this project helps you, please give it a ⭐ Star!**

[🐛 Report Issue](https://github.com/jiji262/douyin-downloader/issues) • [💡 Feature Suggestion](https://github.com/jiji262/douyin-downloader/issues) • [📖 View Documentation](https://github.com/jiji262/douyin-downloader/wiki)

Made with ❤️ by [jiji262](https://github.com/jiji262)

</div>
