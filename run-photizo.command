#!/bin/bash
# Double-click this file in Finder to launch HGB Capital locally
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV="$SCRIPT_DIR/venv"

cd "$SCRIPT_DIR"

echo "📦 Installing Python dependencies..."
"$VENV/bin/pip" install -r requirements.txt 2>&1 | grep -E "Successfully|already|ERROR" | head -20

echo ""
echo "🔍 Starting HGB Capital dashboard..."
echo "➜  Open http://localhost:8501 in your browser"
echo ""
"$VENV/bin/streamlit" run app.py
