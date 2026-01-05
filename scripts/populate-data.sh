#!/bin/bash
# Populate database with sample data

echo "🍽️  Meal Planner - Populate Sample Data"
echo "======================================="
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup-local.sh first."
    exit 1
fi

echo "📊 Populating database with sample data..."
source .venv/bin/activate
python populate_sample_data.py

echo ""
echo "✅ Done! You can now login with:"
echo "   Username: demo"
echo "   Password: password123"
echo ""
echo "Or try:"
echo "   Username: chef_alice"
echo "   Password: password123"
echo ""
