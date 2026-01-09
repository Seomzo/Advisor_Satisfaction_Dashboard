# Migration Guide: Local App → Streamlit Cloud

This guide explains the differences between the original local app and the new Streamlit version.

## 🎯 Quick Summary

**Original App:**
- React frontend + Node.js backend
- Runs locally on `http://localhost:5179`
- Requires Node.js, npm, and Python

**Streamlit App:**
- Single Python file
- Can run locally OR on Streamlit Cloud
- Only requires Python
- **Same exact UI and functionality**

## 📊 Side-by-Side Comparison

| Aspect | Original (Local) | Streamlit Version |
|--------|------------------|-------------------|
| **Languages** | JavaScript, Python | Python only |
| **Framework** | React + Express | Streamlit |
| **Dependencies** | Node.js, npm, Python | Python only |
| **Deployment** | Local machine only | Local OR Streamlit Cloud |
| **Cost** | Free (local) | Free (Streamlit Cloud) |
| **Setup Time** | ~10 minutes | ~2 minutes |
| **Update Method** | Manual restart | Auto-reload (dev) / Git push (cloud) |
| **Data Storage** | `storage/latest.json` | Session state + optional local |
| **UI Appearance** | Dark blue gradient design | **Identical** |
| **Functionality** | Full leaderboard, upload, expand | **Identical** |

## 🚀 How to Run

### Original App (Local)

```bash
# Install dependencies
npm install

# Run in TV mode
npm run tv

# Access at http://localhost:5179
```

### Streamlit App (Local)

```bash
# Install Streamlit
pip install streamlit

# Run app
streamlit run streamlit_app.py

# Access at http://localhost:8501
```

### Streamlit App (Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Deploy!

**URL:** `https://your-app.streamlit.app`

## 🎨 What Stayed the Same

✅ **Exact UI Design**
- Same dark blue gradient background
- Same card-based layout with glassmorphism
- Same gold/silver/bronze rank styling
- Same circular progress indicators
- Same typography and spacing

✅ **Full Functionality**
- Upload XLSX files
- View advisor leaderboard
- Expand/collapse advisor details
- Automatic field detection
- Type-aware rendering (percent, number, string)
- Smart thresholds for color coding

✅ **Data Processing**
- Same XLSX parsing logic (stdlib only)
- Same field type detection
- Same metadata extraction
- Same sorting and filtering

## 🔄 What Changed

### Architecture

**Before:** Separate frontend and backend
```
client/ (React)  ←→  server/ (Express)  ←→  parse_xlsx.py
```

**After:** All-in-one Streamlit app
```
streamlit_app.py (includes all logic)
```

### File Structure

**Original:**
```
Advisor_Satisfaction_Dashboard/
├── client/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── UploadPage.jsx
│   │   ├── api.js
│   │   └── utils.js
│   └── package.json
├── server/
│   ├── src/
│   │   └── index.js
│   ├── scripts/
│   │   └── parse_xlsx.py
│   └── package.json
└── package.json
```

**Streamlit:**
```
Advisor_Satisfaction_Dashboard/
├── streamlit_app.py          ← All logic here
├── requirements.txt           ← Just "streamlit"
├── .streamlit/
│   └── config.toml
└── STREAMLIT_README.md
```

### Navigation

**Original:**
- Routes: `/` (dashboard) and `/upload`
- Uses React Router

**Streamlit:**
- Single page with state management
- Button toggle between Dashboard and Upload views
- Uses `st.session_state.page`

### State Management

**Original:**
- React hooks (`useState`, `useEffect`)
- API calls to fetch data
- Local storage in `storage/latest.json`

**Streamlit:**
- `st.session_state` for everything
- Direct function calls (no API)
- Optional local storage (same location)

### Expandable Rows

**Original:**
```jsx
const [expandedIds, setExpandedIds] = useState(new Set());
// Click handler to toggle
```

**Streamlit:**
```python
if 'expanded_rows' not in st.session_state:
    st.session_state.expanded_rows = set()
# Button click to toggle
```

## 📦 Dependencies Comparison

### Original

**Frontend (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.0"
  }
}
```

**Backend (package.json):**
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1"
  }
}
```

**Python:** No packages needed (stdlib only)

### Streamlit

**requirements.txt:**
```
streamlit>=1.28.0
```

**That's it!** No other dependencies needed.

## 🎯 Use Cases

### When to Use Original (Local)

✅ Need complete control over server
✅ Running on a dedicated machine/TV
✅ Want to customize beyond Streamlit's capabilities
✅ Prefer JavaScript/React ecosystem
✅ Need advanced routing or multiple pages

### When to Use Streamlit

✅ Want free cloud hosting
✅ Need to share with remote team
✅ Prefer Python over JavaScript
✅ Want faster development
✅ Need easy deployment
✅ Don't want to manage servers

## 🔐 Security Considerations

### Original App

- Runs on local network only
- Not accessible from internet
- No authentication built-in
- Data stored locally

### Streamlit Cloud

- **Public by default** (anyone with URL can access)
- Can add password protection (see README)
- Can use private GitHub repo
- Data in session state (not shared between users)
- **Important:** Don't deploy sensitive data on public apps

## 💾 Data Persistence

### Original App

✅ **Persistent:** Data saved to `storage/latest.json`
✅ Survives restarts
✅ One source of truth for all users

### Streamlit Local

✅ **Persistent:** Same as original (uses `storage/latest.json`)
✅ Survives restarts

### Streamlit Cloud

❌ **Not Persistent:** Session state only
❌ Lost on restart/refresh
🔄 Need to re-upload XLSX each session

**Solution for Cloud Persistence:**
- Connect to database (PostgreSQL, MongoDB)
- Use cloud storage (S3, GCS)
- Store data in secrets/environment

## 🚀 Deployment Options

### Original App

**Option 1: Local Machine**
```bash
npm run tv
# Access: http://localhost:5179
```

**Option 2: Network Access**
```bash
# Modify server/src/index.js to bind to 0.0.0.0
# Access from other devices: http://[your-ip]:5179
```

### Streamlit App

**Option 1: Local Machine**
```bash
streamlit run streamlit_app.py
# Access: http://localhost:8501
```

**Option 2: Network Access**
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
# Access from other devices: http://[your-ip]:8501
```

**Option 3: Streamlit Cloud (FREE)**
- Push to GitHub
- Deploy on share.streamlit.io
- Access: https://your-app.streamlit.app
- **Automatic updates** when you push to GitHub

## 🎓 Learning Curve

### Original App

**Required Knowledge:**
- JavaScript (React)
- Node.js (Express)
- npm/package management
- API development
- Frontend/backend architecture

### Streamlit App

**Required Knowledge:**
- Python (basic)
- That's it!

**No need to know:**
- HTML/CSS (built-in components)
- JavaScript (Streamlit handles it)
- API development
- Server management

## 🔧 Customization

### Original App

**Easy to customize:**
- Component logic (React)
- API endpoints
- Routing
- State management

**Harder to customize:**
- Build configuration
- Multiple files to modify

### Streamlit App

**Easy to customize:**
- Everything in one file
- Custom CSS injection
- Python logic

**Harder to customize:**
- Complex layouts
- Advanced interactions
- Custom components

## 📈 Performance

### Original App

- ⚡ Fast (optimized production build)
- 🔄 Minimal re-renders
- 📦 Smaller bundle size

### Streamlit App

- ⚡ Fast for typical use
- 🔄 Full page reruns on state change
- 📦 Larger initial load (includes framework)

**Verdict:** Both are plenty fast for this use case!

## 🐛 Debugging

### Original App

**Browser Console:**
- React DevTools
- Network tab for API calls
- JavaScript errors

**Server Logs:**
- Terminal output
- Python script errors

### Streamlit App

**Browser Console:**
- Streamlit error messages
- Python tracebacks shown in UI
- Network tab

**Terminal:**
- Python errors and warnings
- Streamlit framework logs

## 📝 Summary

The Streamlit version is a **complete recreation** of the original app with:

✅ **Same UI** - Pixel-perfect recreation
✅ **Same functionality** - All features preserved
✅ **Simpler stack** - Python only
✅ **Cloud-ready** - Deploy for free
✅ **Easier maintenance** - One file vs. many

**Bottom line:** Use Streamlit if you want cloud hosting and Python-only development. Use the original if you need local-only access or prefer React/Node.js.

## 🎯 Next Steps

1. **Test Streamlit locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Compare with original:**
   - Run both side-by-side
   - Upload same XLSX to both
   - Verify identical output

3. **Choose your path:**
   - **Local only:** Keep using original
   - **Cloud deployment:** Use Streamlit
   - **Both:** Keep both versions!

4. **Deploy to cloud:**
   - Follow `STREAMLIT_README.md`
   - Push to GitHub
   - Deploy on share.streamlit.io

---

**Questions?** Check `STREAMLIT_README.md` for detailed deployment instructions!

