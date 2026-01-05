#!/bin/bash
# Local Development Setup Script

echo "🍽️  Meal Planner - Local Development Setup"
echo "=========================================="
echo ""

# Backend setup
echo "🔧 Setting up Backend..."
cd backend

if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "🐍 Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install -e ".[dev]"

echo "📊 Setting up database..."
# Create SQLite database for local dev
export DATABASE_URL="sqlite+aiosqlite:///./meal_planner.db"
alembic upgrade head

echo ""
echo "✅ Backend setup complete!"
echo ""

# Frontend setup
cd ../frontend
echo "🔧 Setting up Frontend..."
echo "📦 Installing npm dependencies..."
npm install

echo ""
echo "✅ Frontend setup complete!"
echo ""

cd ..

echo "✨ Setup complete! To start development:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8180"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit http://localhost:3080"
echo ""
