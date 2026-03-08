#!/bin/bash
# Double-click this file to launch Project Photizo in your browser.
# If macOS asks for permission the first time, go to System Settings →
# Privacy & Security and click "Allow Anyway".

cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py
