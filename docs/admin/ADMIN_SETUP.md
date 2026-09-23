# MedNarrate Admin — Setup & Development Guide

## Prerequisites
- Node.js v18+ & npm / pnpm
- Python 3.11+
- PostgreSQL database (or local SQLite for development)

## Backend Local Setup
```bash
cd mednarrate-backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
pip install -r requirements.txt
python run_server.py
```

## Admin Frontend Setup
```bash
cd mednarrate-admin
npm install
npm run dev
```
The Admin portal will start at `http://localhost:3000` (or `http://localhost:3001` if port 3000 is occupied).

## Environment Variables Configuration
Create `.env.local` inside `mednarrate-admin`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
