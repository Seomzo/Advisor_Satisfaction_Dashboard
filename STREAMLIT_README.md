# Advisor Satisfaction Dashboard - Streamlit Version

A beautiful, full-screen dashboard for daily Tekion Service Employee Rank Excel exports (`.xlsx`), now powered by Streamlit and ready for cloud deployment.

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.8 or higher

### Installation & Run

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install streamlit
   ```

3. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open in browser**
   - The app will automatically open at `http://localhost:8501`
   - Or manually navigate to the URL shown in terminal

## ☁️ Deploy to Streamlit Cloud (FREE)

Streamlit Cloud offers free hosting for public repositories. Here's how to deploy:

### Step 1: Push to GitHub

1. Make sure your repository is on GitHub
2. Ensure these files are in your repository:
   - `streamlit_app.py` (main app file)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (configuration)

### Step 2: Deploy on Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Configure deployment:**
   - **Repository:** Select your GitHub repo
   - **Branch:** `main` (or `master`)
   - **Main file path:** `streamlit_app.py`
   - **App URL:** Choose a custom URL (optional)

5. **Click "Deploy!"**

Your app will be live in a few minutes at `https://your-app-name.streamlit.app`

### Step 3: Share with Your Team

- Share the URL with anyone who needs access
- No login required for viewers
- Updates automatically when you push to GitHub

## 📖 How to Use

### Upload Page

1. Click the **"📤 Upload"** button in the top right
2. Drag and drop your Tekion XLSX file, or click to browse
3. The file will be processed automatically
4. You'll be redirected to the dashboard

### Dashboard View

- **Leaderboard**: Advisors ranked by satisfaction score
- **Expandable Cards**: Click the arrow (▸) to view detailed metrics
- **Color Coding**:
  - 🥇 Gold border = Rank #1
  - 🥈 Silver border = Rank #2
  - 🥉 Bronze border = Rank #3
- **Circular Progress**: Green = meeting threshold, Red = below threshold

## 🎨 Features

✅ **Exact UI Match**: Recreated the original design with dark blue gradients, glassmorphism effects, and premium styling

✅ **No Backend Required**: Pure Streamlit app - no Node.js, Express, or API endpoints needed

✅ **Expandable Advisor Cards**: Click to reveal detailed metrics for each advisor

✅ **Smart Field Detection**: Automatically identifies Employee, Rank, Score, Impact, and other fields

✅ **Type-Aware Rendering**: 
- Percentages shown with circular progress indicators
- Numbers displayed with monospace font
- Color-coded based on thresholds

✅ **Mobile Responsive**: Works on tablets and phones (though desktop recommended)

✅ **No Database**: Data stored in session state and optional local JSON file

## 📁 File Structure

```
Advisor_Satisfaction_Dashboard/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── storage/                   # Local data storage (optional)
│   └── latest.json           # Last uploaded file (persists locally)
├── STREAMLIT_README.md       # This file
└── README.md                  # Original local version README
```

## 🔧 Configuration

### Theme Customization

Edit `.streamlit/config.toml` to customize colors:

```toml
[theme]
primaryColor = "#43d0ff"      # Accent color
backgroundColor = "#070A14"    # Main background
secondaryBackgroundColor = "#0B1026"  # Cards background
textColor = "#EAF0FF"         # Text color
```

### Port Configuration

By default, Streamlit runs on port 8501. To change:

```toml
[server]
port = 8502
```

## 🆚 Differences from Original Version

| Feature | Original (Node.js + React) | Streamlit Version |
|---------|---------------------------|-------------------|
| **Backend** | Express.js API | No backend needed |
| **Frontend** | React with Vite | Streamlit UI |
| **Deployment** | Local only | Streamlit Cloud (free) |
| **File Storage** | Local filesystem | Session state + optional local |
| **Dependencies** | Node.js, npm, Python | Python only |
| **UI Framework** | Custom CSS + React | Custom CSS + Streamlit |
| **Data Persistence** | storage/latest.json | Session state (cloud) or local JSON (local) |

## ⚠️ Important Notes for Streamlit Cloud

### Data Persistence

- **Streamlit Cloud does NOT have persistent storage**
- Data only persists during the session
- You need to re-upload the XLSX file after the app restarts
- For production use with persistent storage, consider:
  - Connecting to a database (PostgreSQL, MongoDB, etc.)
  - Using Streamlit's file uploader each session
  - Storing files in cloud storage (S3, Google Cloud Storage)

### File Size Limits

- Streamlit Cloud has a default upload limit of 200MB
- The current app works with typical XLSX files (< 10MB)

### Session State

- Each user gets their own session
- Data is not shared between users
- Refreshing the page clears session state on Streamlit Cloud

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"

**Solution:**
```bash
pip install streamlit
```

### App won't load/stays blank

**Solution:**
1. Check browser console for errors (F12)
2. Clear browser cache
3. Try incognito/private mode

### XLSX parsing fails

**Solution:**
1. Ensure file is a valid `.xlsx` (not `.xls`)
2. Check that it has "Employee" and "Rank" columns
3. Verify the file isn't corrupted

### Can't deploy to Streamlit Cloud

**Checklist:**
- ✅ Repository is public on GitHub
- ✅ `requirements.txt` exists and has `streamlit>=1.28.0`
- ✅ `streamlit_app.py` exists in the root
- ✅ You're signed in with GitHub on share.streamlit.io

## 🔄 Updating Your Deployed App

Once deployed to Streamlit Cloud:

1. Make changes to your code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update dashboard"
   git push
   ```
3. Streamlit Cloud will automatically detect changes and redeploy
4. App updates in ~1-2 minutes

## 📊 Usage Workflow

### Daily Usage

1. **Morning**: Upload today's XLSX file
2. **Throughout Day**: View dashboard, share link with team
3. **Next Day**: Upload new file (replaces previous data)

### Sharing with Team

- **URL**: Share your Streamlit Cloud URL
- **Access**: No authentication required (public link)
- **Updates**: Everyone sees the same data
- **Security**: Don't include sensitive data in public apps

## 🎯 Best Practices

### For Local Development

- Keep the original React app as a backup
- Test XLSX files locally before uploading
- Save your storage/latest.json periodically

### For Production (Streamlit Cloud)

- Use a private repository if data is confidential
- Consider adding password protection (Streamlit supports auth)
- Monitor app usage on Streamlit Cloud dashboard
- Set up email notifications for app errors

## 🚀 Advanced: Adding Password Protection

To add simple password protection:

```python
import streamlit as st

# At the top of streamlit_app.py, after st.set_page_config()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if password == "your_secure_password":  # Change this!
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

# Rest of your app code...
```

## 📝 License

Same as the original project.

## 🙏 Credits

- **Original App**: Node.js + React version by original developer
- **Streamlit Conversion**: Maintains exact UI and functionality
- **Powered by**: [Streamlit](https://streamlit.io)

## 📞 Support

For issues with:
- **Streamlit Cloud**: Check [Streamlit Community Forum](https://discuss.streamlit.io)
- **XLSX Parsing**: Verify file format matches Tekion export structure
- **UI Issues**: Check browser console (F12) for JavaScript errors

---

**Ready to deploy?** Visit [share.streamlit.io](https://share.streamlit.io) and get your app online in minutes! 🚀

