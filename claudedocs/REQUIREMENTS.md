# Douyin Downloader - Functional Requirements Document

## 1. Product Overview

### 1.1 Product Definition

Douyin Batch Downloader is a Python-based command-line tool that providing batch download capabilities for Douyin platform content. It supports watermark-free downloads for various content types including videos, photo collections, music, and live streams.

### 1.2 Core Value

- **Watermark-free Download** - Remove Douyin watermarks to get original high-definition content.
- **Batch Processing** - Supports batch downloads for user homepages, collections, etc.
- **Complete Metadata** - Save full work information (title, author, publishing time, etc.).
- **Automated Management** - Automatic Cookie acquisition, smart retry, incremental updates.
- **Flexible Configuration** - Supports multiple configuration methods and custom options.

---

## 2. Core Feature List

### 2.1 Feature Module Overview

```
Douyin Downloader Feature Architecture
│
├── 📥 Content Download Features
│   ├── Single Video Download
│   ├── Batch Video Download
│   ├── Photo Collection Download
│   ├── User Homepage Download
│   ├── Collection Download
│   ├── Music Collection Download
│   └── Live Stream Download
│
├── 🍪 Authentication Management Features
│   ├── Automatic Cookie Acquisition
│   ├── Manual Cookie Configuration
│   ├── Cookie Validation
│   └── Cookie Refresh
│
├── ⚙️ Download Control Features
│   ├── Concurrent Download Control
│   ├── Smart Retry Mechanism
│   ├── Rate Limiting
│   ├── Incremental Download
│   ├── Time Range Filtering
│   └── Quantity Limit
│
├── 💾 Data Management Features
│
└── 🔧 Configuration Management Features
```

### 2.2 Feature Priority

| Priority | Feature Module | Included Features |
|--------|---------|---------|
| **P0 Core** | Single Video Download | Single video watermark-free download |
| **P0 Core** | Batch Download | User homepage batch download |
| **P0 Core** | Cookie Management | Automatic/Manual Cookie acquisition |
| **P1 Important** | Multi-type Download | Photo collection, collection, music download |
| **P1 Important** | Incremental Update | Download only newly added content |
| **P1 Important** | Metadata Saving | Full information in JSON format |
| **P2 Optimization** | Additional Content | Cover, avatar, music download |
| **P2 Optimization** | Download Control | Retry, rate limiting, quantity control |
| **P3 Extension** | Time Filtering | Filter content by time range |
| **P3 Extension** | Live Download | Real-time live stream recording |

---

## 3. Detailed Download Feature Description

### 3.1 Single Video Download

#### Feature Description
Download a single Douyin video, supporting both short links and direct links.

#### Supported Links
- Shared short link: `https://v.douyin.com/xxxxx/`
- Direct web link: `https://www.douyin.com/video/1234567890123456789`

#### Download Content
| Item | Format | Required | Description |
|-------|------|---------|------|
| Video File | MP4 | ✅ Required | Watermark-free video |
| Video Cover | JPG | ⚪ Optional | Work cover image |
| Background Music | MP3 | ⚪ Optional | Original soundtrack |
| Author Avatar | JPG | ⚪ Optional | Author's avatar image |
| Metadata | JSON | ⚪ Optional | Complete work information |

#### Configuration Example
```yaml
link:
  - https://v.douyin.com/xxxxx/
music: true      # Whether to download music
cover: true      # Whether to download cover
avatar: true     # Whether to download avatar
json: true       # Whether to save metadata
```

#### File Naming Rules
```
[Title]_[WorkID].mp4
[Title]_[WorkID]_cover.jpg
[Title]_[WorkID]_music.mp3
[Title]_[WorkID]_data.json
```

---

## 3.2 Batch Video Download

#### Feature Description
Supports batch download of multiple links, processing several separate video links simultaneously.

#### Configuration Example
```yaml
link:
  - https://v.douyin.com/xxxxx1/
  - https://v.douyin.com/xxxxx2/
  - https://www.douyin.com/video/1234567890123456789
  - https://www.douyin.com/video/9876543210987654321
thread: 5        # Number of concurrent downloads
```

#### Batch Processing Characteristics
- Supports any number of video links
- Concurrent downloads for efficiency
- Single failure does not affect others
- Real-time progress display
- Statistics for successful/failed counts

---

### 3.3 Photo Collection Download

#### Feature Description
Download Douyin photo/text works (Photo Collections), supporting complete download of multi-image works.

#### Supported Links
- `https://www.douyin.com/note/xxxxx`

#### Download Content
| Item | Description |
|-------|------|
| All Images | JPG format, watermark-free |
| Background Music | MP3 format |
| Author Avatar | JPG format |
| Metadata | JSON format, contains image list |

#### File Organization Structure
```
Downloaded/
└── [AuthorNickname]/
    └── [Title]_[WorkID]/
        ├── [Title]_1.jpg
        ├── [Title]_2.jpg
        ├── [Title]_3.jpg
        ├── [Title]_music.mp3
        ├── avatar.jpg
        └── data.json
```

---

### 3.4 User Homepage Download

#### Feature Description
Batch download all works from a specified user homepage, supporting multiple download modes.

#### Supported Links
- `https://www.douyin.com/user/MS4wLjABAAAA...`

#### Download Modes

##### Mode 1: Published Works (post)
Download all works published by the user (including videos and photo collections).

```yaml
link:
  - https://www.douyin.com/user/xxxxx
mode:
  - post
number:
  post: 0          # 0 means all, >0 means latest N
increase:
  post: false      # Whether to enable incremental download
```

##### Mode 2: Liked Works (like)
Download works liked/favorited by the user (requires Cookie permission).

```yaml
mode:
  - like
number:
  like: 50         # Download last 50 liked works
increase:
  like: true       # Enable incremental update
```

##### Mode 3: All Collections (mix)
Download all collections created by the user.

```yaml
mode:
  - mix
number:
  allmix: 0        # Number of collections, 0 means all
  mix: 0           # Number of works within each collection
increase:
  allmix: false
  mix: false
```

##### Mixed Mode
Simultaneously download multiple types of content.

```yaml
mode:
  - post           # Published works
  - like           # Liked works
  - mix            # All collections
```

#### File Organization Structure
```
Downloaded/
└── [AuthorNickname]_[UserID]/
    ├── post/                    # Published works
    │   ├── [Work1]/
    │   ├── [Work2]/
    │   └── ...
    ├── like/                    # Liked works
    │   ├── [Work1]/
    │   └── ...
    └── mix/                     # Collections
        ├── [CollectionName1]/
        │   ├── [Work1]/
        │   └── ...
        └── [CollectionName2]/
            └── ...
```

---

### 3.5 Collection Download

#### Feature Description
Download all works within a single collection (album).

#### Supported Links
- `https://www.douyin.com/collection/xxxxx`

#### Configuration Example
```yaml
link:
  - https://www.douyin.com/collection/7123456789012345678
number:
  mix: 0           # Download count, 0=all
increase:
  mix: false       # Incremental update
```

#### Download Content
- All works in the collection (video/photo collection)
- Complete information for each work
- Collection metadata (JSON)

---

### 3.6 Music Collection Download

#### Feature Description
Download all works using a specific background music.

#### Supported Links
- `https://www.douyin.com/music/xxxxx`

#### Configuration Example
```yaml
link:
  - https://www.douyin.com/music/7123456789012345678
number:
  music: 20        # Download first 20 works using this music
increase:
  music: false
```

#### Application Scenarios
- Collect works related to trending music
- Research music usage trends
- Material collection

---

### 3.7 Live Download

#### Feature Description
Record ongoing live streams (experimental feature).

#### Supported Links
- `https://live.douyin.com/xxxxx`

#### Feature Characteristics
- Real-time live stream recording
- Automatic detection of live status
- Automatic reconnection on disconnection
- Segmented saving of live files

#### Notes
- Requires host to be live
- Recording quality depends on live stream quality
- Large file size, pay attention to disk space

---

## 4. Cookie Management Feature

### 4.1 Why Cookies are Needed

Douyin API requires user login status to access content. Cookies contain login credentials for:
- Accessing user homepage content
- Downloading liked works
- Obtaining complete video info
- Avoiding access restrictions

### 4.2 Automatic Cookie Acquisition (Recommended)

#### Feature Description
Use Playwright automation tool to open a browser and automatically acquire Cookies.

#### Tool Name
`cookie_extractor.py`

#### Steps

**Step 1: Install Playwright**
```bash
pip install playwright
playwright install chromium
```

**Step 2: Run the Tool**
```bash
python cookie_extractor.py
```

**Step 3: Choose Extraction Method**
```
Please select Cookie extraction method:
1. Use browser auto-extraction (Recommended)
2. Copy Cookie from existing browser
Please enter option (1-2): 1
```

**Step 4: Complete Login**
- Tool automatically opens the browser.
- Login via QR Code/Phone number in the browser.
- Tool extracts Cookies after successful login.
- Cookies are automatically saved to the configuration file.

#### Extraction Modes

| Mode | Description | Scenario |
|-----|------|---------|
| Visual Mode | Displays browser window | First-time use, debugging |
| Headless Mode | Runs in the background | Automated scripts |

#### Configuration
```yaml
# Method 1: Specify auto-acquisition in config file
cookies: auto

# Method 2: Specify in configuration options
auto_cookie: true
```

---

### 4.3 Manual Cookie Acquisition

#### Feature Description
Manually copy Cookies via browser developer tools.

#### Tool Name
`get_cookies_manual.py`

#### Steps

**Step 1: Run the Tool**
```bash
python get_cookies_manual.py
```

**Step 2: Select Feature**
```
Cookie Management Tool
1. Get New Cookie
2. View Current Cookie
3. Backup Cookie
4. Restore Cookie
5. Exit
Please select (1-5): 1
```

**Step 3: Get Cookie**

1. Open browser and visit https://www.douyin.com
2. Log into your Douyin account.
3. Press `F12` to open developer tools.
4. Switch to `Network` tab.
5. Refresh the page (F5).
6. Click on any request.
7. Find the `Cookie` field in Request Headers.
8. Copy the entire Cookie string.

**Step 4: Paste Cookie**
```
Please paste Cookie content:
[Paste your copied Cookie]
```

**Step 5: Automatic Saving**
- Tool automatically parses the Cookie.
- Validates Cookie effectiveness.
- Saves to the configuration file.

#### Key Cookie Fields

| Field | Required | Description |
|-------|--------|------|
| msToken | ✅ Required | Main authentication token |
| ttwid | ✅ Required | Device identifier |
| odin_tt | ✅ Required | User identifier |
| passport_csrf_token | ⚪ Optional | CSRF protection |
| sid_guard | ⚪ Optional | Session protection |

---

### 4.4 Cookie Configuration Methods

#### Method 1: Automatic Acquisition (Easiest)
```yaml
cookies: auto
```

#### Method 2: Full Cookie String
```yaml
cookies: "msToken=xxx; ttwid=xxx; odin_tt=xxx; passport_csrf_token=xxx; sid_guard=xxx;"
```

#### Method 3: Key-Value Pairs
```yaml
cookies:
  msToken: YOUR_MS_TOKEN_HERE
  ttwid: YOUR_TTWID_HERE
  odin_tt: YOUR_ODIN_TT_HERE
  passport_csrf_token: YOUR_CSRF_TOKEN_HERE
  sid_guard: YOUR_SID_GUARD_HERE
```

#### Method 4: Environment Variables
```bash
export DOUYIN_COOKIE="msToken=xxx; ttwid=xxx; ..."
python downloader.py -u "URL"
```

---

### 4.5 Cookie Management Features

#### Cookie Validation
Automatically validates if the Cookie is effective:
- Checks required fields.
- Tests API access.
- Displays validation results.

#### Cookie Refresh
Periodically refreshes Cookie to maintain effectiveness:
- Detects if Cookie is about to expire.
- Automatically re-acquires.
- Seamlessly updates configuration.

#### Cookie Backup and Restore
```bash
# Backup
python get_cookies_manual.py
Select: 3. Backup Cookie

# Restore
python get_cookies_manual.py
Select: 4. Restore Cookie
```

---

## 5. Download Control Features

### 5.1 Concurrent Download Control

#### Feature Description
Controls the number of files downloaded simultaneously to improve efficiency.

#### Configuration Parameters
```yaml
thread: 5        # Concurrent count: 1-20
```

#### Concurrency Strategies
- **Low Concurrency (1-3)**: Use when network is unstable.
- **Medium Concurrency (5-10)**: Default recommended configuration.
- **High Concurrency (10-20)**: Use when network conditions are good.

#### Performance Impact
| Threads | Speed | CPU Usage | Network Load | Scenario |
|--------|------|---------|----------|---------|
| 1-3 | Slow | Low | Low | Unstable network |
| 5-10 | Fast | Medium | Medium | Daily use |
| 10-20 | Very Fast | High | High | Batch download |

---

### 5.2 Smart Retry Mechanism

#### Feature Description
Automatically retries on download failure to improve success rate.

#### Configuration Parameters
```yaml
retry_times: 3   # Retry count: 1-10
```

#### Retry Strategy
```
1st failure → wait 1s → retry
2nd failure → wait 2s → retry
3rd failure → wait 5s → retry
4th failure → mark as failed, log error
```

#### Retry Scenarios
- Network timeout
- HTTP 5xx Server Error
- HTTP 429 Too Many Requests
- Temporary network failure
- Interrupted data transmission

#### Non-Retry Scenarios
- HTTP 404 Content Not Found
- HTTP 403 Forbidden
- Expired Cookie
- Incorrect link format

---

### 5.3 Rate Limiting

#### Feature Description
Controls request frequency to avoid triggering anti-crawler mechanisms.

#### Limiting Strategy
```python
max_per_second: 2      # Max 2 requests per second
min_interval: 0.5      # Min 500ms interval between requests
```

#### Protection Mechanism
- Automatic request speed control.
- Avoids account suspension.
- Avoids IP restriction.
- Complies with platform usage norms.

#### Application Scenarios
- Massive batch downloads.
- Long-duration runs.
- Multi-user homepage downloads.
- Collection batch downloads.

---

### 5.4 Incremental Download

#### Feature Description
Only downloads new content, avoiding repeated downloads of existing files.

#### Enabling Conditions
```yaml
database: true           # Database must be enabled
increase:
  post: true            # Enable increment for corresponding mode
  like: true
  mix: true
```

#### How it Works
1. Database records downloaded work IDs.
2. Queries database when fetching content list.
3. Skips already downloaded works.
4. Only downloads newly added works.
5. Updates database after successful download.

#### Database Table Structure
```sql
CREATE TABLE aweme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aweme_id TEXT UNIQUE NOT NULL,
    desc TEXT,
    create_time INTEGER,
    download_time INTEGER,
    author_id TEXT,
    author_name TEXT
);
```

#### Application Scenarios
- **Periodic Backup**: Daily/Weekly backup of new works.
- **Continuous Monitoring**: Following user updates.
- **Space Saving**: No repeated downloads.
- **Time Saving**: Skipping existing content.

#### Usage Example
```yaml
# First-time download: download all works
link:
  - https://www.douyin.com/user/xxxxx
mode:
  - post
increase:
  post: false
database: true

# Subsequent updates: only download new works
increase:
  post: true   # Set to true to enable incremental
```

---

### 5.5 Time Range Filtering

#### Feature Description
Filters content based on publishing time.

#### Configuration Parameters
```yaml
start_time: "2024-01-01"   # Start time
end_time: "2024-12-31"     # End time
```

#### Time Format
- Standard format: `YYYY-MM-DD`
- Example: `2024-01-01`, `2024-12-31`
- Leave empty for no limit.

#### Filtering Rules
| Config | Meaning |
|-----|------|
| start_time: "2024-01-01"<br>end_time: "" | Works after Jan 1, 2024 |
| start_time: ""<br>end_time: "2024-12-31" | Works before Dec 31, 2024 |
| start_time: "2024-01-01"<br>end_time: "2024-12-31" | Works within year 2024 |
| start_time: ""<br>end_time: "" | No time limit |

#### Application Scenarios
- Download works from a specific period.
- Limit content during an event.
- Only need latest N days of content.
- Exclude old content.

---

### 5.6 Quantity Limit

#### Feature Description
Limits the number of items downloaded for various content types.

#### Configuration Parameters
```yaml
number:
  post: 50      # Works published by user
  like: 30      # Works liked by user
  allmix: 5     # Number of collections to download
  mix: 20       # Number of works within a single collection
  music: 10     # Number of works in music collection
```

#### Quantity Rules
- `0` = Download all
- `> 0` = Download specified number (latest N items)

#### Example Configurations

**Scenario 1: Latest content only**
```yaml
number:
  post: 10      # Only download latest 10 works
```

**Scenario 2: Download everything**
```yaml
number:
  post: 0       # Download all works
```

**Scenario 3: Mixed configuration**
```yaml
number:
  post: 0       # All published works
  like: 50      # Only 50 liked works
  allmix: 0     # All collections
  mix: 10       # But only 10 works per collection
```

---

## 6. Data Management Features

### 6.1 Metadata Saving

#### Feature Description
Save full work information in JSON format.

#### Enabling Configuration
```yaml
json: true       # Enable metadata saving
```

#### Saved Content

**Video Work Metadata**
```json
{
  "aweme_id": "7123456789012345678",
  "desc": "Title/Description",
  "create_time": 1704038400,
  "author": {
    "uid": "MS4wLjABAAAA...",
    "nickname": "Nickname",
    "avatar_url": "https://..."
  },
  "video": {
    "play_url": "https://...",
    "cover_url": "https://...",
    "duration": 15,
    "ratio": "720p"
  },
  "music": {
    "title": "Music Title",
    "author": "Music Artist",
    "play_url": "https://..."
  },
  "statistics": {
    "digg_count": 1234,
    "comment_count": 567,
    "share_count": 89,
    "play_count": 12345
  }
}
```

**Photo Collection Metadata**
```json
{
  "aweme_id": "7123456789012345678",
  "desc": "Title",
  "images": [
    {
      "url": "https://...",
      "width": 1080,
      "height": 1440
    },
    ...
  ],
  "music": {...},
  "statistics": {...}
}
```

#### Application Scenarios
- Data analysis and research.
- Content management and retrieval.
- Batch processing and editing.
- Information backup and archiving.

---

### 6.2 Database Recording

#### Feature Description
Use SQLite database to record download history and work information.

#### Enabling Configuration
```yaml
database: true   # Enable database
```

#### Database File
- Filename: `data.db`
- Format: SQLite 3
- Location: Project root directory

#### Table Structure

**aweme (Work Record Table)**
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary Key, Auto-increment |
| aweme_id | TEXT | Unique Work ID (Unique Index) |
| desc | TEXT | Work Description |
| create_time | INTEGER | Publishing Timestamp |
| download_time | INTEGER | Download Timestamp |
| author_id | TEXT | Author ID |
| author_name | TEXT | Author Nickname |
| aweme_type | TEXT | Work Type (video/image) |
| file_path | TEXT | File Save Path |

#### Features
- Automatic recording of download history.
- Supports incremental download determination.
- Prevents repeated downloads.
- Download statistics and queries.
- Persistent data storage.

#### Database Operations

**Query Download History**
```sql
SELECT * FROM aweme ORDER BY download_time DESC LIMIT 10;
```

**Count Total Downloads**
```sql
SELECT COUNT(*) FROM aweme;
```

**Statistics by Author**
```sql
SELECT author_name, COUNT(*) as count
FROM aweme
GROUP BY author_id
ORDER BY count DESC;
```

---

### 6.3 File Organization and Management

#### Feature Description
Automatically organize downloaded files into a clear directory structure.

#### Enable Configuration
```yaml
folderstyle: true    # Enable folder organization
```

#### Organization Structure

**Standard Organization**
```
Downloaded/
├── [AuthorNickname1]_[UserID]/
│   ├── post/                           # Published works
│   │   ├── [Title1]_[ID]/
│   │   │   ├── [Title1].mp4
│   │   │   ├── [Title1]_cover.jpg
│   │   │   ├── [Title1]_music.mp3
│   │   │   ├── avatar.jpg
│   │   │   └── data.json
│   │   └── [Title2]_[ID]/
│   │       └── ...
│   ├── like/                           # Liked works
│   │   └── ...
│   └── mix/                            # Collections
│       ├── [CollectionName1]/
│       │   └── ...
│       └── [CollectionName2]/
│           └── ...
└── [AuthorNickname2]_[UserID]/
    └── ...
```

**Simplified Organization**
```yaml
folderstyle: false   # Disable folder organization
```

```
Downloaded/
├── [Title1]_[ID].mp4
├── [Title1]_[ID]_cover.jpg
├── [Title2]_[ID].mp4
└── ...
```

#### Naming Rules

**Filename Safety Processing**
- Remove special characters: `/ \ : * ? " < > |`
- Replace with underscores: `_`
- Limit length: Maximum 100 characters.
- Retain file extension.

**Example**
```
Original Title: Today's weather is so good! #travel #vlog
Filename: Today's_weather_is_so_good_travel_vlog_7123456789012345678.mp4
```

---

### 6.4 Download Statistics

#### Feature Description
Real-time display of download progress and statistical info.

#### Statistical Info

**Display During Download**
```
Downloading: [Title]
Progress: [████████--] 80% (8/10)
Success: 7 | Failed: 1 | Skipped: 0
Speed: 2.5 MB/s
Time Remaining: 00:02:15
```

**Display After Completion**
```
========================================
Download Completion Statistics
========================================
Total: 100
Success: 95
Failed: 3
Skipped: 2
Success Rate: 95.0%
Time Elapsed: 00:15:32
========================================
```

#### Real-time Progress Bar
Use Rich library to display beautiful progress bars:
- Real-time updates of progress percentage.
- Display current download speed.
- Estimated time remaining.
- Color-coded status indicators.
