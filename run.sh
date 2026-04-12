#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup.sh first:"
    echo "  chmod +x setup.sh"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the app
echo ""
echo "🚀 Starting Supplier Relationship Management Dashboard"
echo "📊 URL: http://127.0.0.1:8050/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
