# Advisor Satisfaction Dashboard - Streamlit Version

Full-screen dashboard for the daily Tekion **Service Employee Rank** Excel export (`.xlsx`), now running on Streamlit.

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation & Run

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## ☁️ Deploy to Streamlit Cloud (Free)

Streamlit Cloud offers free hosting for public repositories. Here's how to deploy:

### Option 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   - Create a new repository on GitHub
   - Push this codebase to the repository

2. **Connect to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository
   - Set the main file path to `app.py`
   - Click "Deploy"

3. **Your app will be live!**
   - Streamlit Cloud will provide a URL like: `https://your-app-name.streamlit.app`
   - The app will automatically redeploy when you push changes to GitHub

### Option 2: Deploy from Local Git

If you have the Streamlit CLI installed:

```bash
streamlit deploy
```

## 📋 Requirements

The app only requires:
- `streamlit` (Python package)
- Python standard library (no external dependencies for Excel parsing)

## 🎯 Features

- **Excel File Upload**: Upload Tekion `.xlsx` files via the sidebar
- **Dashboard View**: View advisor rankings with satisfaction scores
- **Expandable Cards**: Click on any advisor to see detailed KPIs
- **Real-time Parsing**: Excel files are parsed instantly using pure Python
- **Responsive Design**: Works on desktop and tablet screens

## 📁 File Structure

```
.
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit configuration
└── README_STREAMLIT.md   # This file
```

## 🔧 Configuration

Edit `.streamlit/config.toml` to customize:
- Theme colors
- Server settings
- Browser behavior

## 💡 Usage

1. Open the app (locally or on Streamlit Cloud)
2. Use the sidebar to upload a Tekion Excel file
3. The dashboard will automatically update with the data
4. Click on any advisor card to expand and see detailed metrics

## 🆚 Differences from Original React App

- **Single Page**: Everything is in one Streamlit app (no separate upload page)
- **Sidebar Upload**: File upload is in the sidebar instead of a separate route
- **Streamlit Components**: Uses Streamlit's native components (expanders, columns, etc.)
- **No Node.js Required**: Pure Python application

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
- Run: `pip install -r requirements.txt`

### Excel file won't parse
- Make sure the file is a valid `.xlsx` format
- Check that the file contains "Employee" and "Rank" columns

### App won't start
- Check that port 8501 is not already in use
- Try: `streamlit run app.py --server.port 8502`

## 📝 Notes

- The app uses pure Python (stdlib) for Excel parsing - no pandas or openpyxl required
- Data is stored in session state (cleared on refresh)
- For persistent storage, consider adding a database or file storage

## 🔗 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cloud](https://share.streamlit.io/)
- [Streamlit Community](https://discuss.streamlit.io/)

