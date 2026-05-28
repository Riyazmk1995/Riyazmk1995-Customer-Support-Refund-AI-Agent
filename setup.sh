#!/bin/bash

# Setup script for local development

echo "🚀 AI Refund Agent - Local Setup"
echo "=================================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python: $python_version"

# Create backend virtual environment
echo ""
echo "📦 Setting up Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Backend dependencies installed"

# Create frontend virtual environment
echo ""
echo "📦 Setting up Frontend..."
cd ../frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Frontend dependencies installed"

cd ..

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env file created from template"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python -m uvicorn main:app --reload"
echo "2. Frontend: cd frontend && source venv/bin/activate && streamlit run app.py"
echo ""
echo "Or use Docker Compose:"
echo "docker-compose up -d"
