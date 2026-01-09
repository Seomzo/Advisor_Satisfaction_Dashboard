# Quick Start Guide - Streamlit Version

## 🚀 Run Locally

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## ☁️ Deploy to Streamlit Cloud (Free)

1. **Push to GitHub** (if not already done)
2. **Go to** [share.streamlit.io](https://share.streamlit.io)
3. **Sign in** with GitHub
4. **Click "New app"**
5. **Select your repository** and set main file to `app.py`
6. **Click "Deploy"**

Your app will be live at: `https://your-app-name.streamlit.app`

## 📝 Usage

1. Open the app (local or cloud)
2. Use the **sidebar** to upload a Tekion `.xlsx` file
3. The dashboard will display advisor rankings
4. Click **"View Details"** on any card to see detailed KPIs

## ✅ What's Different?

- **Single Python file** - No Node.js or separate server needed
- **Sidebar upload** - File upload is in the sidebar
- **Streamlit components** - Uses native Streamlit UI elements
- **Cloud-ready** - Deploy to Streamlit Cloud with one click

## 🎯 Features Preserved

- ✅ Excel file parsing (pure Python, no pandas)
- ✅ Advisor rankings with satisfaction scores
- ✅ Expandable detail views
- ✅ Color-coded rankings (gold/silver/bronze)
- ✅ All KPI metrics displayed

