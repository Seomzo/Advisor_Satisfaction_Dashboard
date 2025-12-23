# Advisor Satisfaction Dashboard

Full-screen dashboard for the daily Tekion **Service Employee Rank** Excel export (`.xlsx`).

## Setup on a new PC (recommended “TV mode”)
### 1) Install prerequisites
- **Node.js 18+**
- **Python 3** (the backend uses `python3` to parse the `.xlsx`)

### 2) Get the code
```bash
git clone https://github.com/Seomzo/Advisor_Satisfaction_Dashboard.git
cd Advisor_Satisfaction_Dashboard
```

### 3) Install dependencies
If you use conda, activate your env first (optional):

```bash
conda activate cursor
```

Then install:

```bash
npm install
```

### 4) Build + start (single URL)
```bash
npm run build --workspace client
npm run start --workspace server
```

### 5) Open on the TV
- Dashboard: `http://localhost:5179/`
- Upload page: `http://localhost:5179/upload`

## Daily workflow
1) Open `http://localhost:5179/upload`
2) Upload today’s Tekion `.xlsx`
3) You’ll be redirected back to the dashboard automatically
