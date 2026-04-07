#!/bin/bash
# Quick start script — runs both backend and frontend

set -e

echo "=== Clinical Prescreening Tool ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "ERROR: node not found. Please install Node.js 18+"
    exit 1
fi

# Setup backend
echo "[1/4] Installing Python dependencies..."
cd backend
pip install -r requirements.txt --quiet 2>/dev/null || pip install -r requirements.txt

# Seed database if it doesn't exist
if [ ! -f prescreen.db ]; then
    echo "[2/4] Seeding sample protocol..."
    python3 seed_sample_protocol.py
else
    echo "[2/4] Database already exists, skipping seed."
fi

# Setup frontend
echo "[3/4] Installing frontend dependencies..."
cd ../frontend
npm install --silent 2>/dev/null || npm install

# Start both
echo "[4/4] Starting servers..."
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""

cd ../backend
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd ../frontend
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
