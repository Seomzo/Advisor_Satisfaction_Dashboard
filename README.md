# Advisor Satisfaction Dashboard

Full-screen dashboard for the daily Tekion **Service Employee Rank** export (`.xlsx`).

## What it does
- **Upload** a Tekion-exported XLSX daily
- Server parses it into a stable JSON API (`/api/data`)
- React frontend renders a **big-screen “TV mode”** dashboard with:
  - podium + ranked advisor list
  - horizontally-scrollable KPI table (all columns)
  - auto-refresh every 30 seconds

## Tech stack
- **Backend**: Node.js (Express) + `python3` parser (stdlib only)
- **Frontend**: React (Vite)

## Setup (Mac)
Before installing packages, activate your environment:

```bash
conda activate cursor
```

Install dependencies (workspace install):

```bash
cd /Users/omaralsadoon/Desktop/tekion_automations/Advisor_Satisfaction_Dashboard
npm install
```

## Run (dev)
Terminal 1 (server):

```bash
cd /Users/omaralsadoon/Desktop/tekion_automations/Advisor_Satisfaction_Dashboard
npm run dev --workspace server
```

Terminal 2 (client):

```bash
cd /Users/omaralsadoon/Desktop/tekion_automations/Advisor_Satisfaction_Dashboard
npm run dev --workspace client
```

Open:
- Dashboard: `http://localhost:5173/`
- Upload: `http://localhost:5173/upload`

## Upload workflow (daily)
### Option A: Upload page
Go to `http://localhost:5173/upload` and select the latest `.xlsx`.

### Option B: curl

```bash
curl -F file=@"VW_EmployeeRank - Service_426085 Stevens Creek Volkswagen_12222025_221716.xlsx" http://localhost:5179/api/upload
```

## Production / big screen
Build the client, then run the server:

```bash
cd /Users/omaralsadoon/Desktop/tekion_automations/Advisor_Satisfaction_Dashboard
npm run build --workspace client
npm run start --workspace server
```

Then open `http://localhost:5179/` on the big screen.
