# Douyin Downloader Web Application

A modern web application for downloading Douyin/TikTok videos without watermark. Built with Vue.js frontend and Flask backend.

## 🌟 Features

- **Download Videos**: Paste a Douyin or TikTok URL to download videos without watermark
- **Manage Downloads**: View, preview, and manage all downloaded videos
- **Modern UI**: Beautiful glassmorphism design with smooth animations
- **Video Preview**: Watch videos directly in the browser
- **File Management**: Delete unwanted videos with confirmation

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn

## 🚀 Installation

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r backend/requirements-backend.txt
   ```

2. **Configure cookies** (Required for first use):
   ```bash
   # Method 1: Automatic (Recommended)
   python cookie_extractor.py
   
   # Method 2: Manual
   python get_cookies_manual.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

## 🎯 Running the Application

### Start Backend Server

```bash
# From project root directory
cd backend
python app.py
```

The backend API will start on `http://localhost:5000`

### Start Frontend Development Server

```bash
# From frontend directory
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173`

### Access the Application

Open your browser and navigate to: `http://localhost:5173`

## 📖 Usage

### Downloading Videos

1. Open the application in your browser
2. Navigate to the **Download** tab
3. Copy a Douyin or TikTok video URL
4. Paste the URL in the input field
5. Click **Download** button
6. Wait for the download to complete
7. Your video will be saved in the `Downloaded/aweme/` folder

### Managing Videos

1. Navigate to the **Management** tab
2. View all downloaded videos in a grid layout
3. Click on a video card to preview it
4. Click the delete button (🗑️) to remove a video
5. Use the **Refresh** button to reload the video list

## 🔧 API Endpoints

### Download Endpoint
```
POST /api/download
Content-Type: application/json

{
  "url": "https://v.douyin.com/xxxxx/"
}
```

### List Files
```
GET /api/files
```

### Get File Info
```
GET /api/files/<filename>
```

### Delete File
```
DELETE /api/files/<filename>
```

### Stream Video
```
GET /api/files/<filename>/stream
```

## 📁 Project Structure

```
douyin-downloader/
├── backend/                 # Flask backend
│   ├── controllers/        # HTTP request handlers
│   ├── services/           # Business logic
│   ├── dto/               # Data transfer objects
│   └── app.py             # Flask application
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── services/      # API client
│   │   ├── assets/        # Styles and assets
│   │   ├── App.vue        # Root component
│   │   └── main.js        # Entry point
│   ├── index.html         # HTML template
│   ├── package.json       # Dependencies
│   └── vite.config.js     # Vite configuration
├── apiproxy/              # Existing download logic
├── Downloaded/            # Downloaded videos folder
└── README.md             # This file
```

## 🎨 Technology Stack

### Backend
- **Flask**: Lightweight web framework
- **Flask-CORS**: Cross-origin resource sharing
- **Python 3.9+**: Programming language

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vite**: Fast build tool
- **Axios**: HTTP client
- **Vanilla CSS**: Custom styling with glassmorphism

## 🔒 Environment Variables

You can configure the application using environment variables:

- `DOWNLOAD_PATH`: Path to save downloaded videos (default: `./Downloaded`)
- `DOUYIN_COOKIE`: Douyin authentication cookie
- `PORT`: Backend server port (default: 5000)

## 🐛 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'flask'`
```bash
pip install -r backend/requirements-backend.txt
```

**Problem**: Download fails with authentication error
```bash
# Re-acquire cookies
python cookie_extractor.py
```

### Frontend Issues

**Problem**: `Cannot GET /api/download`
- Make sure the backend server is running on port 5000
- Check the proxy configuration in `vite.config.js`

**Problem**: CORS errors
- Verify Flask-CORS is installed
- Check CORS configuration in `backend/app.py`

## 📝 Notes

- Downloaded videos are saved in `Downloaded/aweme/` folder
- Each video includes metadata (JSON), cover image, and music file
- The application uses existing Python download logic from `apiproxy/`
- Backend follows SOLID principles with clear separation of concerns

## ⚖️ Legal Disclaimer

- This project is for **learning and personal use** only
- Please comply with relevant laws, regulations, and platform terms of service
- Not for commercial use or infringing on the rights of others
- Respect the original author's copyright for downloaded content

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

This project is licensed under the MIT License.

---

**Made with ❤️ for video enthusiasts**
