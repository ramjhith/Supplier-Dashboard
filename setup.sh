#!/bin/bash

echo "================================"
echo "P6 Supplier Dashboard Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "✅ Virtual environment created and activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed successfully"
echo ""

echo "✨ Setup complete!"
echo ""
echo "To run the dashboard:"
echo "  1. source venv/bin/activate"
echo "  2. python app.py"
echo ""
echo "Then open http://127.0.0.1:8050/ in your browser"
echo ""
